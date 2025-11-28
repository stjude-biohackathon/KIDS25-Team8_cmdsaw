from __future__ import annotations
from typing import Literal, Optional, List
from pydantic import BaseModel, Field

ScalarType = Literal["int","float","str","path","bool","choice","unknown"]
FileRole = Literal["input","output","none"]

class FileFormat(BaseModel):
    """File format information with extension and optional EDAM ontology term."""
    extension: str = Field(..., description="File extension including the dot (e.g., '.csv', '.bam')")
    edam_format: Optional[str] = Field(None, description="EDAM format ontology term (e.g., 'format_1929' for FASTA)")
    edam_uri: Optional[str] = Field(None, description="Full EDAM URI (e.g., 'http://edamontology.org/format_1929')")

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
    file_role: FileRole = "none"
    file_format: Optional[FileFormat] = None

class PositionalDoc(BaseModel):
    name: str
    index: int
    variadic: bool = False
    required: bool = True
    type: ScalarType = "unknown"
    description: Optional[str] = None
    file_role: FileRole = "none"
    file_format: Optional[FileFormat] = None

class CommandDoc(BaseModel):
    name: str
    path: str
    help_text: str
    options: List[OptionDoc] = Field(default_factory=list)
    positionals: List[PositionalDoc] = Field(default_factory=list)
    subcommands: List[str] = Field(default_factory=list)
    requires_subcommand: bool = False
    supports_piped_output: bool = False

class ToolDoc(BaseModel):
    command: str
    version: Optional[str] = None
    help_text: str
    invocation: List[str]
    options: List[OptionDoc] = Field(default_factory=list)
    positionals: List[PositionalDoc] = Field(default_factory=list)
    subcommands: List[CommandDoc] = Field(default_factory=list)
    captured_at: str
    container_info: Optional["ContainerInfo"] = None
    supports_piped_output: bool = False

class ParseDiagnostics(BaseModel):
    warnings: List[str] = Field(default_factory=list)
    timeouts: int = 0
    llm_retries: int = 0
    visited_commands: int = 0
    version_extracted: bool = False
    
class ContainerInfo(BaseModel):
    bioconda: Optional[str]
    docker: Optional[str]
    singularity: Optional[str]

class CmdSawResult(BaseModel):
    schema_version: str
    tool: ToolDoc
    diagnostics: ParseDiagnostics

def generate_piped_output_filename(command_path: str, file_format: Optional[FileFormat] = None) -> str:
    """
    Generate a default output filename for piped output.
    
    :param command_path: Full command path (e.g., "samtools view" or "grep")
    :type command_path: str
    :param file_format: Optional file format to determine extension
    :type file_format: Optional[FileFormat]
    :return: Default output filename
    :rtype: str
    
    Examples:
        >>> generate_piped_output_filename("samtools view", FileFormat(extension=".bam"))
        'samtools_view_output.bam'
        >>> generate_piped_output_filename("grep")
        'grep_output.txt'
    """
    # Convert command path to valid filename
    safe_name = command_path.replace(" ", "_").replace("/", "_").replace("-", "_")
    
    # Determine extension
    if file_format and file_format.extension:
        extension = file_format.extension
    else:
        extension = ".txt"
    
    return f"{safe_name}_output{extension}"
