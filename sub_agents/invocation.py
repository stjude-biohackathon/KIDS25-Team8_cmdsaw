"""Invocation agent: Executes CLI commands to capture help and version information."""

import subprocess
import json
from typing import Dict, Any, Optional
from sub_agents.schema import WorkflowState, ToolInfo


def capture_help(executable: str, subcommand: Optional[str] = None) -> Dict[str, str]:
    """Run `<executable> [subcommand] --help`, return output."""
    help_text = None

    # Build command list
    cmd = [executable]
    if subcommand:
        cmd.append(subcommand)
    cmd.append("--help")

    # --help
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        help_text = (result.stdout or result.stderr).strip()
    except FileNotFoundError:
        command_str = " ".join(cmd)
        raise Exception(f"Executable '{executable}' not found. Check that it is installed.")
    except subprocess.TimeoutExpired:
        command_str = " ".join(cmd)
        raise Exception(f"Timeout running {command_str}")
    except Exception as e:
        command_str = " ".join(cmd)
        raise Exception(f"Error running {command_str}: {e}")

    return {"help_text": help_text}


def capture_version(executable: str) -> Dict[str, str]:
    """Run `<executable> --version`, return text outputs."""
    version_text = None

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

    return {"version_text": version_text}


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
        help_output = capture_help(executable)
        version_output = capture_version(executable)
        
        # Create basic tool info with raw text
        tool_info: ToolInfo = {
            "tool": executable,
            "help_text": help_output["help_text"],
            "version_text": version_output["version_text"],
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


def subcommand_invocation_agent(state: WorkflowState) -> Dict[str, Any]:
    """
    Subcommand invocation agent: Captures help text for each discovered subcommand.
    Takes the tool_info with subcommands list and populates each subcommand's help_text.
    """
    tool_info = state.get("tool_info")
    if not tool_info:
        raise Exception("Tool info missing from state")
    
    if tool_info.get("error"):
        # Pass through error state
        return {"tool_info": tool_info}
    
    executable = tool_info.get("tool")
    subcommands = tool_info.get("subcommands", [])
    
    if not executable:
        raise Exception("Executable name missing from tool info")
    
    if not subcommands:
        print("No subcommands found, skipping subcommand help capture")
        return {"tool_info": tool_info}
    
    print(f"Capturing help text for {len(subcommands)} subcommands...")
    
    # Update each subcommand with its help text
    updated_subcommands = []
    for subcommand in subcommands:
        subcommand_name = subcommand.get("name")
        if not subcommand_name:
            print(f"Warning: Subcommand missing name, skipping")
            updated_subcommands.append(subcommand)
            continue
        
        try:
            # Capture help text for this subcommand
            help_output = capture_help(executable, subcommand_name)
            
            # Update subcommand with help text
            updated_subcommand = {
                **subcommand,
                "help_text": help_output["help_text"]
            }
            updated_subcommands.append(updated_subcommand)
            
            print(f"Captured help for subcommand: {subcommand_name}")
            
        except Exception as e:
            print(f"Failed to capture help for subcommand '{subcommand_name}': {e}")
            # Keep original subcommand without help text
            updated_subcommands.append(subcommand)
    
    # Update tool_info with subcommands that now have help text
    updated_tool_info: ToolInfo = {
        **tool_info,
        "subcommands": updated_subcommands
    }
    
    print("Complete subcommand invocation")
    
    return {"tool_info": updated_tool_info}
