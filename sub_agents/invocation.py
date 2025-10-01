"""Invocation agent: Executes CLI commands to capture help and version information."""

import subprocess
import json
from typing import Dict, Any
from langgraph.graph import START, StateGraph, END
from sub_agents.schema import WorkflowState, ToolInfo


def capture_help_and_version(executable: str) -> Dict[str, str]:
    """Run `<executable> --help` and `<executable> --version`, return text outputs."""
    help_text, version_text = None, None

    # --help
    try:
        result = subprocess.run(
            [executable, "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        help_text = (result.stdout or result.stderr).strip()
    except FileNotFoundError:
        raise Exception(f"Executable '{executable}' not found. Check that it is installed.")
    except subprocess.TimeoutExpired:
        raise Exception(f"Timeout running {executable} --help")
    except Exception as e:
        raise Exception(f"Error running {executable} --help: {e}")

    # --version
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            errors = "replace"
        )
        version_text = (result.stdout).strip()
    except Exception:
        version_text = None

    return {"help_text": help_text, "version_text": version_text}


def invocation_agent(state: WorkflowState) -> Dict[str, Any]:
    """
    Invocation agent: Captures CLI help and version information.
    Returns the raw text output for the parsing agent to process.
    """
    executable = state.get("executable")
    if not executable:
        raise Exception("Executable name missing from state")

    try:
        # Capture CLI text
        cli_output = capture_help_and_version(executable)
        
        # Create basic tool info with raw text
        tool_info: ToolInfo = {
            "tool": executable,
            "help_text": cli_output["help_text"],
            "version_text": cli_output["version_text"],
            "subcommands": [],
            "global_parameters": []
        }

        print("Complete invocation")
        
        return {"tool_info": tool_info}
        
    except Exception as e:
        # Return error state
        tool_info: ToolInfo = {
            "tool": executable,
            "error": str(e),
            "subcommands": [],
            "global_parameters": []
        }
        return {"tool_info": tool_info}


# Create invocation subgraph
invocation_builder = StateGraph(WorkflowState)
invocation_builder.add_node("invocation_agent", invocation_agent)
invocation_builder.add_edge(START, "invocation_agent")
invocation_builder.add_edge("invocation_agent", END)

# Compile the invocation graph for export
invocation_graph = invocation_builder.compile()


if __name__ == "__main__":
    # Simple test
    test_state = {"executable": "samtools"}
    result = invocation_graph.invoke(test_state)
    print(json.dumps(result, indent=2))