"""Parse each usage statement to capture all parameter names, their description, their default values, 
    if optional or required, if a flag, and their type (string, int, double, path, etc). 
    Create and pass structured JSON output to next agent (Ollama model supports this)."""

import json
import re
import requests
from typing import Dict, Any, List
from langgraph.graph import START, StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from sub_agents.schema import WorkflowState, ToolInfo, Subcommand, Parameter


def parse_version(version_string: str) -> str:
    """
    Extract numeric version from a version string.
    
    Strips common prefixes and extracts the version number pattern.
    Keeps semantic versioning including pre-release identifiers.
    
    Args:
        version_string: Raw version string from command output
        
    Returns:
        Cleaned version string with just numeric components
        
    Examples:
        >>> parse_version("v0.1.8")
        '0.1.8'
        >>> parse_version("running 9.2")
        '9.2'
        >>> parse_version("version: 1.8.4-a")
        '1.8.4-a'
        >>> parse_version("toastbox version 2.4.1")
        '2.4.1'
        >>> parse_version("Version 3.2.1-beta.1+build.123")
        '3.2.1-beta.1+build.123'
    """
    if not version_string:
        return ""
    
    # Pattern explanation:
    # \d+ - one or more digits (major version)
    # (?:\.\d+)* - zero or more groups of dot followed by digits (minor, patch, etc.)
    # (?:[-+][a-zA-Z0-9.]+)* - zero or more pre-release or build metadata segments
    pattern = r'\d+(?:\.\d+)*(?:[-+][a-zA-Z0-9.]+)*'
    
    match = re.search(pattern, version_string)
    if match:
        return match.group(0)
    
    # If no match found, return cleaned string (strip whitespace)
    return version_string.strip()


# Test cases
# if __name__ == "__main__":
#     test_cases = [
#         ("""v0.1.8 rahblah blah
#         toast is oh so tasty, yes
#         """, "0.1.8"),
#         ("running 9.2", "9.2"),
#         ("version: 1.8.4-a", "1.8.4-a"),
#         ("toastbox version 2.4.1", "2.4.1"),
#         ("Version 3.2.1", "3.2.1"),
#         ("v1.2.3-beta.1+build.123", "1.2.3-beta.1+build.123"),
#         ("Git version 2.39.1", "2.39.1"),
#         ("docker 24.0.5", "24.0.5"),
#         ("Python 3.11.4", "3.11.4"),
#         ("v10.0.0-rc.1", "10.0.0-rc.1"),
#         ("1.0", "1.0"),
#         ("5", "5"),
#     ]
    
#     print("Testing version parser:")
#     print("-" * 60)
#     for input_str, expected in test_cases:
#         result = parse_version(input_str)
#         status = "✓" if result == expected else "✗"
#         print(f"{status} parse_version('{input_str}')")
#         print(f"  Expected: '{expected}'")
#         print(f"  Got:      '{result}'")
#         if result != expected:
#             print("  FAILED!")
#         print()


def parsing_version_agent(state: WorkflowState) -> Dict[str, Any]:
    """
    Parsing agent: Uses LLM to parse help text and extract detailed parameter information.
    Takes the raw help/version text from invocation agent and produces structured subcommands and parameters.
    """
    tool_info = state.get("tool_info")
    if not tool_info:
        raise Exception("Tool info missing from state")
    
    if tool_info.get("error"):
        # Pass through error state
        return {"tool_info": tool_info}
    
    version_text = tool_info.get("version_text")
    
    if version_text:
        clean_version = parse_version(version_text)
        
        # Update tool_info with parsed results
        tool_info: ToolInfo = {
            **tool_info,
            "version": clean_version,
        }

        print(f"Extracted {clean_version} as version")
    else:
        print("No version_text found, skipping version extraction")
    
    return {
        "tool_info": tool_info
    }


def parsing_agent(state: WorkflowState) -> Dict[str, Any]:
    """
    Parsing agent: Uses LLM to parse help text and extract detailed parameter information.
    Takes the raw help/version text from invocation agent and produces structured subcommands and parameters.
    """
    tool_info = state.get("tool_info")
    if not tool_info:
        raise Exception("Tool info missing from state")
    
    if tool_info.get("error"):
        # Pass through error state
        return {"tool_info": tool_info}
    
    help_text = tool_info.get("help_text")
    executable = tool_info.get("tool")
    
    if not help_text:
        raise Exception("Help text missing from tool info")

    url = "http://localhost:11434/api/generate"
    

    # System instruction for detailed parsing
    system_msg = SystemMessage(content="""
You are an expert CLI parser that extracts detailed subcommands and parameters information from help text.
Given a command-line tool's help output, produce structured JSON with subcommands and their parameters.

For each subcommand, extract:
- name: subcommand name
- description: what the subcommand does
- usage: how to use the subcommand
- parameters: list of parameters for the subcommand
- is_flag: true for boolean flags, false for value parameters
- aliases: alternative names like [-h, --help]

Rules:
- Only output valid JSON, no additional text
- Extract ALL parameters for each subcommand
- Infer parameter types from descriptions and usage patterns
- Mark parameters as required/optional based on help text formatting
- For tools without subcommands, put all parameters under a "main" subcommand
- If parsing fails, return error in the JSON
""")

    # Example JSON format
    example_json = {
        "tool": "samtools",
        "description": "Tools for manipulating SAM/BAM/CRAM files",
        "subcommands": [
            {
                "name": "view",
                "description": "SAM<->BAM<->CRAM conversion",
                "usage": "samtools view [options] <in.bam>|<in.sam>|<in.cram> [region ...]",
                "parameters": []
            },
            {
                "name": "index",
                "description": "Index a BAM file",
                "usage": "samtools index [options] <in.bam> [out.index]",
                "parameters": []
            }
        ]
    }

    # Human input
    human_msg = HumanMessage(content=f"""
Tool: {executable}

Parse the below help ouput and extract detailed parameter information for each subcommand. Strictly generate the json in the below format.

--help output:
{help_text}

Output JSON should follow this format:

{json.dumps(example_json, indent=2)}

DO NOT GENERATE ANY EXTRA or ADDITIONAL TEXT
""")

    payload = {
        "model": "llama3.1:8b",
        "system": system_msg.content,
        "prompt": human_msg.content,
        "stream": True,
    }

    try:
        with requests.post(url, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()

            collected_chunks = []

            out_file = "llama_response.txt"  
            file_handle = open(out_file, "w", encoding="utf-8") if out_file else None

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        chunk = data.get("response", "")
                        collected_chunks.append(chunk)

                        # Write to file immediately if specified
                        if file_handle:
                            file_handle.write(chunk)
                            file_handle.flush()

                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        # Sometimes partial lines can appear
                        continue

            if file_handle:
                file_handle.close()

            raw_response = "".join(collected_chunks)
            
            raw_response = re.sub('```json', '', raw_response)
            raw_response = re.sub('```', '', raw_response).strip()
            parsed = json.loads(raw_response)
        
        # Update tool_info with parsed results
        updated_tool_info: ToolInfo = {
            **tool_info,
            "description": parsed.get("description"),
            "subcommands": parsed.get("subcommands", []),
            "global_parameters": parsed.get("global_parameters", [])
        }

        print("Complete parsing")
        
        return {
            "tool_info": updated_tool_info,
            "parsed_subcommands": parsed.get("subcommands", [])
        }
        
    except Exception as e:
        # Return error state
        error_tool_info: ToolInfo = {
            **tool_info,
            "error": f"LLM parsing failed: {str(e)}"
        }
        return {"tool_info": error_tool_info}


# Create parsing subgraph
parsing_builder = StateGraph(WorkflowState)
parsing_builder.add_node("parsing_agent", parsing_agent)
parsing_builder.add_edge(START, "parsing_agent")
parsing_builder.add_edge("parsing_agent", END)

# Compile the parsing graph for export
parsing_graph = parsing_builder.compile()



# if __name__ == "__main__":
#     # Simple test
    
#     # load test state from test.json
#     with open("test.json") as f:
#         test_state = json.load(f)

#     result = parsing_graph.invoke(test_state)
#     print(json.dumps(result, indent=2))