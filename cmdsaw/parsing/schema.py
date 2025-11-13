from __future__ import annotations
from typing import Literal, Optional, List
from pydantic import BaseModel, Field

ScalarType = Literal["int","float","str","path","bool","choice","unknown"]

class OptionDoc(BaseModel):
    long: Optional[str] = None
    short: Optional[str] = None
    is_flag: bool = False
    type: ScalarType = "unknown"
    choices: Optional[List[str]] = None
    required: bool = False
    default: Optional[str] = None
    description: Optional[str] = None
    repeatable: bool = False
    envvar: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)

class PositionalDoc(BaseModel):
    name: str
    index: int
    variadic: bool = False
    required: bool = True
    type: ScalarType = "unknown"
    description: Optional[str] = None

class CommandDoc(BaseModel):
    name: str
    path: str
    help_text: str
    options: List[OptionDoc] = Field(default_factory=list)
    positionals: List[PositionalDoc] = Field(default_factory=list)
    subcommands: List[str] = Field(default_factory=list)
    requires_subcommand: bool = False

class ToolDoc(BaseModel):
    command: str
    version: Optional[str] = None
    help_text: str
    invocation: List[str]
    options: List[OptionDoc] = Field(default_factory=list)
    positionals: List[PositionalDoc] = Field(default_factory=list)
    subcommands: List[CommandDoc] = Field(default_factory=list)
    captured_at: str

class ParseDiagnostics(BaseModel):
    warnings: List[str] = Field(default_factory=list)
    timeouts: int = 0
    llm_retries: int = 0
    visited_commands: int = 0
    version_extracted: bool = False

class CmdSawResult(BaseModel):
    schema_version: str
    tool: ToolDoc
    diagnostics: ParseDiagnostics
