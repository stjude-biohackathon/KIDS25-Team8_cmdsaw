from __future__ import annotations
import json
from .parsing.schema import CmdSawResult

def to_json(result: CmdSawResult) -> str:
    return json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)

def write_json(path: str, result: CmdSawResult) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_json(result))
