from __future__ import annotations
import os, re, shutil, subprocess
from typing import Mapping, Sequence

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mK]")
_VERSION_RX = re.compile(r"(\d+\.\d+(?:\.\d+){0,2}(?:[-+A-Za-z0-9.]*)?)")

def which_or_raise(cmd: str) -> str:
    path = shutil.which(cmd)
    if not path:
        from .errors import CommandNotFound
        raise CommandNotFound(cmd)
    return path

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

def run_capture(cmdline: Sequence[str], timeout: int, env: Mapping[str, str] | None = None, cwd: str | None = None) -> tuple[str, int]:
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
    m = _VERSION_RX.search(text)
    if not m: return None
    v = m.group(1)
    return v[1:] if v.startswith("v") and v[1:].replace(".","").isdigit() else v
