from pydantic import BaseModel, Field
from typing import List, Optional, Union

class Parameter(BaseModel):
    name: str
    short: Optional[str] = Field(None, description="Name of the parameter")
    type: Union[int, str, bool, list, float] = Field(..., description="Type of parameter value") 
    required: bool = Field(..., description="True if parameter is required, otherwise False")
    flag: bool = Field(..., description="True if this is a flag parameter")
    default: Optional[str] = Field(None, description="Default value if any, or None")
    description: str = Field(..., description = "Description of the parameter")

class PositionalArg(BaseModel):
    name: str = Field(..., description="Name of positional argument")
    type: str = Field(..., description="Type of positional argument")
    description: str = Field(..., description="Description of the positional argument")
    required: bool = Field(..., description="True if the positional argument is required, otherwise False")

class Command(BaseModel):
    name: str = Field(..., description="Name of the command or subcommand")
    description: str = Field(..., description="Description of the command/subcommand")
    is_subcommand: bool = Field(..., description="True if this is a subcommand, False if top-level command")
    parameters: List[Parameter] = Field(..., description="List of option/flag parameters for this command")
    positional_args: List[PositionalArg] = Field(..., description="List of positional arguments for this command")
    stdin: bool = Field(..., description="True if this command accepts stdin input")
    stdout: bool = Field(..., description="True if this command produces stdout output")
    produces_files: List[str] = Field(..., description="List of filenames or file types produced by this command")

class Containers(BaseModel):
    bioconda: str = Field(..., description="Bioconda package name, if available")
    docker: str = Field(..., description="Docker image name, if available")
    singularity: str = Field(..., description="Singularity image name, if available")

class CommandSchema(BaseModel):
    tool: str = Field(..., description="Name of the tool (e.g., 'ls')")
    version: str = Field(..., description="Version of the tool (e.g., '8.32')")
    commands: List[Command] = Field(..., description="List of commands and subcommands for this tool")
    containers: Containers = Field(..., description="Container images for the tool")