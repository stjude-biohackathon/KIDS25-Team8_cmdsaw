from __future__ import annotations
from datetime import datetime
from typing import Iterable, Mapping, Optional
from .constants import HELP_FLAG_CANDIDATES, VERSION_FLAG_CANDIDATES, DEFAULT_TIMEOUT
from .utils import run_capture, extract_version_number

def try_help(command_path: list[str], help_flags: Iterable[str], *, timeout: int, env: Mapping[str,str] | None, cwd: str | None) -> tuple[str,int]:
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
    for vf in VERSION_FLAG_CANDIDATES:
        cmdline = command_path + [vf]
        out, _ = run_capture(cmdline, timeout=timeout, env=env, cwd=cwd)
        if out:
            v = extract_version_number(out.splitlines()[0])
            if v:
                return v
    return None

def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
