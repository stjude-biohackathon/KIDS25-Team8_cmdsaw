import re
from typing import Dict, Any, List
from langgraph.graph import START, StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
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
    Takes the raw version text from invocation agent and produces structured subcommands and parameters.
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


def find_subcommand_agent(state: WorkflowState) -> Dict[str, Any]:
    """
    Parsing agent: Uses LLM to parse help text and extract detailed parameter information.
    Takes the raw help text from invocation agent and rips any subcommands.
    """
    tool_info = state.get("tool_info")
    if not tool_info:
        raise Exception("Tool info missing from state")
    
    if tool_info.get("error"):
        # Pass through error state
        return {"tool_info": tool_info}
    
    help_text = tool_info.get("help_text")
    
    if not help_text:
        raise Exception("Help text missing from tool info")
    
    # System instruction for detailed parsing
    system_msg = SystemMessage(content="""
You are an expert CLI parser that extracts any and all subcommands from help output text for a given executable.
Given a command-line tool's help output, produce a list of subcommands (if any).
If no subcommands are found, return an empty list.

Rules:
- Only output the list, no additional text.

Example help text:
    toastbox - A delightful notification and message management tool

    Usage: toastbox [OPTIONS] COMMAND

    A command-line tool for creating, managing, and delivering toast notifications
    and messages across your system and network.

    Options:
    -t, --threads INT     Number of threads to use (default: 1)
    -m, --mode STR        Operation mode (default: "standard"), can be "standard", "silent", or "verbose"
    -aa, --all            Include all files if provided (default: false)
    -i, --input STR       Path to input file
    -o, --output STR      Path to output file
    -v, --version         Show version information
    -c, --config STR      Path to config file (default: ~/.toastbox/config.yml)
    -q, --quiet           Suppress all non-error output
    -h, --help            Show this help message

    Basic Commands:
    send      Send a toast notification
    listen    Start listening for incoming toasts
    history   View notification history
    config    Manage toastbox configuration
    
    Other Commands:
    update    Update toastbox to the latest version
    remove    Uninstall toastbox from your system

    Run 'toastbox COMMAND --help' for more information on a command.
    
Example output for toastbox help text:
    ["send", "listen", "history", "config", "update", "remove"]

Other example help text:
    rahblah - Spouts nonsense for fun
    
    rahblah [OPTIONS]
    
    -l, --length int    Length of nonsense to generate in words (default: 10)
    -f, --funny bool    Make the nonsense funny (default: false)
    -r, --repeat int   Number of times to repeat the nonsense (default: 1)
    -o, --output str    Path to output file (default: stdout)
    -h, --help         Show this help message
    
Example output for rahblah help text:
    []
""")

    # Human input
    human_msg = HumanMessage(content=f"""
Parse the below help ouput and extract the name of any subcommands.
DO NOT GENERATE ANY EXTRA or ADDITIONAL TEXT.

--help output:
{help_text}


""")
    
    llm = init_chat_model("llama3.2:3b", model_provider="ollama")
    llm = llm.with_structured_output(SubcommandNames)

    messages = [system_msg, human_msg]
    
    print("Invoking LLM to identify (sub)commands")

    ai_msg = llm.invoke(messages)
    sub_names = ai_msg.get("names")
    
    if sub_names:
        print(f"Identified subcommands: {sub_names}")
        subcommands = [Subcommand(name=name) for name in sub_names]
        
        # Update tool_info with parsed results
        tool_info: ToolInfo = {
            **tool_info,
            "subcommands": subcommands
        }

    else:
        print("No subcommands found, skipping subcommand extraction")
    
    return {
        "tool_info": tool_info
    }


def parse_globals_agent(state: WorkflowState) -> Dict[str, Any]:
    """
    Takes the raw help text from invocation agent and identifies any global parameters, 
    including their short and long forms, default values, type, if an input or output file (or directory), and if required or optional.
    """
    tool_info = state.get("tool_info")
    if not tool_info:
        raise Exception("Tool info missing from state")
    
    if tool_info.get("error"):
        # Pass through error state
        return {"tool_info": tool_info}
    
    help_text = tool_info.get("help_text")
    
    if not help_text:
        raise Exception("Help text missing from tool info")
    
    # System instruction for detailed parsing
    system_msg = SystemMessage(content="""
You are an expert CLI parser that extracts any and all global parameters from a tool's help output text.
Given a command-line tool's help output, produce a list of global parameters (if any).
If no global parameters are found, return an empty list.

Rules:
- Only output the list, no additional text.
- Each parameter should be valid JSON following the schema:
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "Parameter",
    "description": "Represents a CLI parameter.",
    "properties": {
        "description": {
            "type": ["string", "null"],
            "description": "Description of the parameter, if provided"
        },
        "type": {
            "type": ["string", "null"],
            "description": "Parameter type (str, int, float, path, bool, etc.)"
        },
        "required": {
            "type": "boolean",
            "description": "True if required, false if optional"
        },
        "is_input": {
            "type": "boolean",
            "description": "True if input file or directory"
        },
        "is_output": {
            "type": "boolean",
            "description": "True if output file or directory"
        },
        "default_value": {
            "type": ["string", "null"],
            "description": "Default value for the parameter"
        },
        "is_flag": {
            "type": "boolean",
            "description": "True if flag (no argument), false if takes argument"
        },
        "short": {
            "type": "string",
            "description": "Short name like -h"
        },
        "long": {
            "type": ["string", "null"],
            "description": "Long name like --help"
        }
    },
    "required": ["required", "is_input", "is_output", "is_flag", "short"],
    "additionalProperties": false
}

Example help text:
    toastbox - A totally necessary interface to my toaster from the CLI

    Usage: toastbox [OPTIONS] COMMAND

    A command-line tool for controlling your toaster.

    Options:
    -m, --mode STR        Operation mode (default: "standard"), can be "standard" or "bagel"
    -t, --toastiness INT  Toast level from 1 (light) to 5 (dark) (default: 3)
    -b, --buzz BOOL       Enable buzzer sound when done (default: false)
    -l, --log FILE       Path to log file (default: /var/log/toastbox.log)
    -v, --version         Show version information
    -h, --help            Show this help message
    
Example output for toastbox help text:
    [
        {
            "description": "Operation mode (default: \"standard\"), can be \"standard\" or \"bagel\"",
            "type": "str", 
            "required": False,
            "is_input": False,
            "is_output": False,
            "default_value": "standard",
            "is_flag": False,
            "short": "-m",
            "long": "--mode"
        },
        {
            "description": "Toast level from 1 (light) to 5 (dark) (default: 3)",
            "type": "int",
            "required": False, 
            "is_input": False,
            "is_output": False,
            "default_value": "3",
            "is_flag": False,
            "short": "-t",
            "long": "--toastiness"
        },
        {
            "description": "Enable buzzer sound when done (default: false)",
            "type": "bool",
            "required": False,
            "is_input": False,
            "is_output": False, 
            "default_value": "false",
            "is_flag": True,
            "short": "-b",
            "long": "--buzz"
        },
        {
            "description": "Path to log file (default: /var/log/toastbox.log)",
            "type": "path",
            "required": False,
            "is_input": False,
            "is_output": True,
            "default_value": "/var/log/toastbox.log",
            "is_flag": False,
            "short": "-l", 
            "long": "--log"
        },
        {
            "description": "Show version information",
            "type": None,
            "required": False,
            "is_input": False,
            "is_output": False,
            "default_value": None,
            "is_flag": True,
            "short": "-v",
            "long": "--version"
        },
        {
            "description": "Show this help message", 
            "type": None,
            "required": False,
            "is_input": False,
            "is_output": False,
            "default_value": None,
            "is_flag": True,
            "short": "-h",
            "long": "--help"
        }
    ]

Other example help text:
    todo - Create and manage a todo list from the command line
    
    todo [COMMAND] [OPTIONS]

    commands:
      add       Add a new todo item
      list      List all todo items
      remove    Remove a todo item by its ID
      complete  Mark a todo item as completed by its ID
      clear     Clear all completed todo items
    
Example output for rahblah help text:
    []
""")

    # Human input
    human_msg = HumanMessage(content=f"""
Parse the below help ouput and extract the global parameters.

--help output:
{help_text}


DO NOT GENERATE ANY EXTRA or ADDITIONAL TEXT
""")
    
    llm = init_chat_model("deepseek-r1:14b", model_provider="ollama")
    llm = llm.with_structured_output(GlobalParameters)

    messages = [system_msg, human_msg]
    
    print("Invoking LLM to identify global parameters")

    ai_msg = llm.invoke(messages)
    parameters = ai_msg.get("parameters")
    print(parameters)
    
    if parameters:
        print(f"Identified {len(parameters)} global parameters")
        
        # Update tool_info with parsed results
        tool_info: ToolInfo = {
            **tool_info,
            "global_parameters": parameters
        }

    else:
        print("No global parameters found, skipping global parameter extraction")
    
    return {
        "tool_info": tool_info
    }

# Create invocation & parser graphs subgraph
# graph_builder = StateGraph(WorkflowState)
# graph_builder.add_node("invocation_agent", invocation_agent)
# graph_builder.add_node("parsing_version_agent", parsing_version_agent)
# graph_builder.add_node("container_agent", container_agent)
# graph_builder.add_node("find_subcommands_agent", find_subcommands_agent)
# graph_builder.add_node("parse_globals_agent", parse_globals_agent)
# graph_builder.add_edge(START, "invocation_agent")
# graph_builder.add_edge("invocation_agent", "parsing_version_agent")
# graph_builder.add_edge("parsing_version_agent", "container_agent")
# graph_builder.add_edge("container_agent", "find_subcommands_agent")
# graph_builder.add_edge("find_subcommands_agent", "parse_globals_agent")
# graph_builder.add_edge("parse_globals_agent", END)

# # Compile the invocation graph for export
# invocation_graph = graph_builder.compile()

# if __name__ == "__main__":
#     # Simple test
#     test_state = {"executable": "salmon"}
#     result = invocation_graph.invoke(test_state)
#     print(result)