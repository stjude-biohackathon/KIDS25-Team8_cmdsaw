#!/usr/bin/env python3
"""
Runner module - Execute commands and capture help text
"""
import subprocess
import re
from typing import List, Tuple, Optional


def run_help(executable: str, args: List[str] = None) -> Tuple[str, Optional[str]]:
    """
    Run executable with --help and optionally --version
    
    Returns:
        Tuple of (help_text, version)
    """
    if args is None:
        args = []
    
    # Run help command
    help_cmd = [executable] + args + ['--help']
    try:
        result = subprocess.run(
            help_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        help_text = result.stdout
        if result.stderr and not help_text:
            help_text = result.stderr
    except subprocess.TimeoutExpired:
        raise Exception(f"Timeout running {' '.join(help_cmd)}")
    except FileNotFoundError:
        raise Exception(f"Executable '{executable}' not found")
    except Exception as e:
        raise Exception(f"Error running {' '.join(help_cmd)}: {e}")
    
    # Try to get version
    version = None
    try:
        version_cmd = [executable, '--version']
        version_result = subprocess.run(
            version_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        version_text = version_result.stdout or version_result.stderr
        # Extract version number using regex
        version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', version_text)
        if version_match:
            version = version_match.group(1)
    except:
        # Version is optional, continue without it
        pass
    
    return help_text, version


def discover_subcoms(help_text: str) -> List[str]:
    """
    Discover subcommands from help text using simple heuristics
    
    Looks for patterns like:
    Commands:
      command1    Description
      command2    Description
    
    Or:
    Available commands:
      command1    Description
    """
    subcommands = []
    
    # Common patterns for subcommand sections
    section_patterns = [
        r'Commands?:',
        r'Available commands?:',
        r'Subcommands?:',
        r'Available subcommands?:'
    ]
    
    lines = help_text.split('\n')
    in_commands_section = False
    
    for line in lines:
        # Check if we're entering a commands section
        if not in_commands_section:
            for pattern in section_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    in_commands_section = True
                    break
        else:
            # Look for command entries (lines starting with whitespace + word)
            match = re.match(r'\s+(\w[\w-]*)\s+', line)
            if match:
                cmd = match.group(1)
                # Skip common non-commands
                if cmd.lower() not in ['usage', 'options', 'arguments', 'help', 'version']:
                    subcommands.append(cmd)
            elif line.strip() == '' or not line.startswith(' '):
                # Empty line or non-indented line ends the section
                if line.strip() and not re.match(r'\s', line):
                    in_commands_section = False
    
    return subcommands