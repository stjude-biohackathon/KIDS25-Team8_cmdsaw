from __future__ import annotations
import json
from .parsing.schema import CmdSawResult

def to_json(result: CmdSawResult) -> str:
    """
    Convert a CmdSawResult to a JSON string.

    :param result: The parsed command result to serialize
    :type result: CmdSawResult
    :return: Pretty-printed JSON string with 2-space indentation
    :rtype: str
    """
    return json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)

def write_json(path: str, result: CmdSawResult) -> None:
    """
    Write a CmdSawResult to a JSON file.

    :param path: File path where JSON will be written
    :type path: str
    :param result: The parsed command result to serialize
    :type result: CmdSawResult
    :return: None
    :rtype: None
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_json(result))
