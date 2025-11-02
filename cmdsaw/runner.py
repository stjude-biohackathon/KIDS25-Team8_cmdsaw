from __future__ import annotations
from datetime import datetime
from typing import Iterable, Mapping, Optional
from .constants import HELP_FLAG_CANDIDATES, VERSION_FLAG_CANDIDATES, DEFAULT_TIMEOUT
from .utils import run_capture, extract_version_number

def try_help(command_path: list[str], help_flags: Iterable[str], *, timeout: int, env: Mapping[str,str] | None, cwd: str | None) -> tuple[str,int]:
    """
    Try multiple help flags to capture command help text.

    Iterates through provided help flags (e.g., --help, -h, help) and runs the
    command with each flag until output is obtained.

    :param command_path: Command and any subcommands as a list of strings
    :type command_path: list[str]
    :param help_flags: Iterable of help flag strings to try
    :type help_flags: Iterable[str]
    :param timeout: Maximum time in seconds to wait for each attempt
    :type timeout: int
    :param env: Optional environment variables to set
    :type env: Mapping[str,str] | None
    :param cwd: Optional working directory for command execution
    :type cwd: str | None
    :return: Tuple of (help text, exit code)
    :rtype: tuple[str,int]
    """
    for hf in help_flags:
        if hf == "help":
            cmdline = command_path + ["help"]
        else:
            cmdline = command_path + [hf]
        out, code = run_capture(cmdline, timeout=timeout, env=env, cwd=cwd)
        if out:
            return out, code
    return "", 1

def try_version(command_path: list[str], *, timeout: int, env: Mapping[str,str] | None, cwd: str | None) -> str | None:
    """
    Try to extract the version number from a command.

    Attempts multiple version flags (--version, -v) and extracts version
    information from the first line of output.

    :param command_path: Command and any subcommands as a list of strings
    :type command_path: list[str]
    :param timeout: Maximum time in seconds to wait for each attempt
    :type timeout: int
    :param env: Optional environment variables to set
    :type env: Mapping[str,str] | None
    :param cwd: Optional working directory for command execution
    :type cwd: str | None
    :return: Extracted version number, or None if not found
    :rtype: str | None
    """
    for vf in VERSION_FLAG_CANDIDATES:
        cmdline = command_path + [vf]
        out, _ = run_capture(cmdline, timeout=timeout, env=env, cwd=cwd)
        if out:
            v = extract_version_number(out.splitlines()[0])
            if v:
                return v
    return None

def now_iso() -> str:
    """
    Get the current UTC time as an ISO 8601 string.

    :return: Current UTC timestamp in ISO 8601 format with 'Z' suffix
    :rtype: str
    """
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
