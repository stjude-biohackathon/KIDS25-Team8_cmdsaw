from __future__ import annotations
import os, re, shutil, subprocess
from typing import Mapping, Sequence

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mK]")
_VERSION_RX = re.compile(r"(\d+\.\d+(?:\.\d+){0,2}(?:[-+A-Za-z0-9.]*)?)")

def which_or_raise(cmd: str) -> str:
    """
    Find the full path of a command or raise an error if not found.

    :param cmd: Command name to search for in PATH
    :type cmd: str
    :return: Full path to the command executable
    :rtype: str
    :raises CommandNotFound: If the command is not found in PATH
    """
    path = shutil.which(cmd)
    if not path:
        from .errors import CommandNotFound
        raise CommandNotFound(cmd)
    return path

def strip_ansi(s: str) -> str:
    """
    Remove ANSI escape codes from a string.

    :param s: String potentially containing ANSI escape codes
    :type s: str
    :return: String with all ANSI escape codes removed
    :rtype: str
    """
    return ANSI_RE.sub("", s)

def run_capture(cmdline: Sequence[str], timeout: int, env: Mapping[str, str] | None = None, cwd: str | None = None) -> tuple[str, int]:
    """
    Run a command and capture its output with timeout.

    Executes a command with modified environment variables (disabling pagers),
    captures both stdout and stderr, and strips ANSI escape codes from the output.

    :param cmdline: Command and arguments as a sequence of strings
    :type cmdline: Sequence[str]
    :param timeout: Maximum time in seconds to wait for command completion
    :type timeout: int
    :param env: Optional additional environment variables to set
    :type env: Mapping[str, str] | None
    :param cwd: Optional working directory for command execution
    :type cwd: str | None
    :return: Tuple of (output string, return code)
    :rtype: tuple[str, int]
    """
    base_env = os.environ.copy()
    base_env.update({"PAGER":"cat","MANPAGER":"cat","LC_ALL":"C"})
    if env: base_env.update(dict(env))
    proc = subprocess.run(
        list(cmdline),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=base_env,
        timeout=timeout,
        shell=False,
        text=True,
    )
    out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr and not proc.stdout else "")
    return strip_ansi(out).strip(), proc.returncode

def extract_version_number(text: str) -> str | None:
    """
    Extract a version number from text using pattern matching.

    Searches for version patterns (e.g., "1.2.3", "v2.0.1-beta") in the given text
    and returns the first match found. Removes leading 'v' if present.

    :param text: Text to search for version number
    :type text: str
    :return: Extracted version number, or None if not found
    :rtype: str | None
    """
    m = _VERSION_RX.search(text)
    if not m: return None
    v = m.group(1)
    return v[1:] if v.startswith("v") and v[1:].replace(".","").isdigit() else v
