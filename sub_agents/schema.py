from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState

class Parameter(BaseModel):
    """Represents a CLI parameter with all its attributes and metadata."""
    
    description: Optional[str] = Field(
        None, 
        description="Description of the parameter, if provided in help text"
    )
    type: Optional[str] = Field(
        None, 
        description="Parameter data type (str, int, float, path, bool, etc.)"
    )
    required: bool = Field(
        False, 
        description="True if required parameter, false if optional"
    )
    is_input: bool = Field(
        False, 
        description="True if parameter represents an input file or directory"
    )
    is_output: bool = Field(
        False, 
        description="True if parameter represents an output file or directory"
    )
    default_value: Optional[str] = Field(
        None, 
        description="Default value for the parameter if not provided"
    )
    is_flag: bool = Field(
        False, 
        description="True if flag parameter (no argument), false if takes argument"
    )
    positional: Optional[Literal["first", "last"]] = Field(
        None,
        description="Position of parameter relative to executable/subcommand: 'first' for immediately after command, 'last' for end of command line"
    )
    short: Optional[str] = Field(
        None, 
        description="Short name like -h or -v"
    )
    long: Optional[str] = Field(
        None, 
        description="Long name like --help or --verbose"
    )

class GlobalParameters(BaseModel):
    """Global parameters that apply to all subcommands of a tool."""
    
    parameters: Optional[List[Parameter]] = Field(
        None, 
        description="List of global parameters that apply across all subcommands"
    )

class ContainerInfo(BaseModel):
    """Container image information for a tool from BioContainers and other sources."""
    
    bioconda: Optional[str] = Field(
        None, 
        description="Bioconda package name for the tool"
    )
    docker: Optional[str] = Field(
        None, 
        description="Docker image name/tag for the tool"
    )
    singularity: Optional[str] = Field(
        None, 
        description="Singularity image URI for the tool"
    )

class EdamInput(BaseModel):
    """Represents an EDAM-standardized input file or data type."""
    
    name: str = Field(
        description="Name of the input parameter or file"
    )
    suffix: str = Field(
        description="File extension like .bam, .fasta, .fastq"
    )
    edam: str = Field(
        description="EDAM ontology term identifier like data_1383"
    )
    optional: bool = Field(
        default=False, 
        description="True if this input is optional, false if required"
    )

class EdamOutput(BaseModel):
    """Represents an EDAM-standardized output file or data type."""
    
    name: str = Field(
        description="Name of the output parameter or file"
    )
    suffix: str = Field(
        description="File extension like .bam, .sam, .vcf"
    )
    edam: str = Field(
        description="EDAM format ontology term like format_2572"
    )
    optional: bool = Field(
        default=False, 
        description="True if this output is optional, false if always generated"
    )

class StandardizedTool(BaseModel):
    """Represents a standardized tool with EDAM ontology terms for workflow generation."""
    
    id: str = Field(
        description="Unique tool identifier in tool_subcommand format like 'samtools_view'"
    )
    name: str = Field(
        description="Uppercase name for the tool like 'SAMTOOLS_VIEW'"
    )
    label: str = Field(
        description="Process label for workflow generation like 'process_low'"
    )
    inputs: List[EdamInput] = Field(
        default_factory=list, 
        description="List of standardized input specifications"
    )
    outputs: List[EdamOutput] = Field(
        default_factory=list, 
        description="List of standardized output specifications"
    )
    commands: str = Field(
        description="Template command string for workflow generation"
    )

class Subcommand(BaseModel):
    """Represents a CLI subcommand with its parameters and metadata."""
    
    name: str = Field(
        description="Name of the subcommand"
    )
    description: Optional[str] = Field(
        None, 
        description="Description of what the subcommand does"
    )
    parameters: Optional[List[Parameter]] = Field(
        None, 
        description="List of parameters specific to this subcommand"
    )
    usage: Optional[str] = Field(
        None, 
        description="Usage string or example for the subcommand"
    )
    
class SubcommandNames(BaseModel):
    """Container for a list of tool subcommand names."""
    
    names: Optional[List[str]] = Field(
        None, 
        description="List of available subcommand names for a tool"
    )

class ToolInfo(BaseModel):
    """Complete information about a CLI tool including all subcommands and metadata."""
    
    tool: str = Field(
        description="Name of the command-line tool"
    )
    version: Optional[str] = Field(
        None, 
        description="Version of the tool if available"
    )
    description: Optional[str] = Field(
        None, 
        description="Description of what the tool does"
    )
    subcommands: List[Subcommand] = Field(
        default_factory=list, 
        description="List of available subcommands for the tool"
    )
    global_parameters: Optional[GlobalParameters] = Field(
        None, 
        description="Parameters that apply to all subcommands"
    )
    help_text: Optional[str] = Field(
        None, 
        description="Raw help text output from the tool"
    )
    version_text: Optional[str] = Field(
        None, 
        description="Raw version text output from the tool"
    )
    containers: Optional[ContainerInfo] = Field(
        None, 
        description="Container image information for the tool"
    )
    error: Optional[str] = Field(
        None, 
        description="Error message if tool information could not be retrieved"
    )

class WorkflowState(MessagesState):
    """State passed between agents in the cmdsaw workflow with comprehensive tracking of all processing stages."""
    
    # Input parameters
    executable: Optional[str] = Field(
        None, 
        description="Name or path of the command-line tool to process"
    )
    target_format: Optional[str] = Field(
        None, 
        description="Target workflow format to generate: 'wdl' or 'nextflow'"
    )
    
    # Invocation agent outputs
    tool_info: Optional[ToolInfo] = Field(
        None, 
        description="Complete information about the CLI tool including subcommands and parameters"
    )
    
    # Parsing agent outputs  
    parsed_subcommands: Optional[List[Subcommand]] = Field(
        None, 
        description="Parsed subcommands extracted from tool help text"
    )
    
    # Standardization agent outputs
    standardized_tools: Optional[List[StandardizedTool]] = Field(
        None, 
        description="Tools standardized with EDAM ontology terms for workflow generation"
    )
    
    # Troubleshooting agent outputs
    validation_errors: Optional[List[str]] = Field(
        None, 
        description="List of validation errors found during processing"
    )
    suggested_fixes: Optional[List[str]] = Field(
        None, 
        description="List of suggested fixes for validation errors"
    )
    
    # Generator agent outputs
    generated_nextflow: Optional[str] = Field(
        None, 
        description="Generated Nextflow workflow code"
    )
    generated_wdl: Optional[str] = Field(
        None, 
        description="Generated WDL workflow code"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the workflow generation process"
    )