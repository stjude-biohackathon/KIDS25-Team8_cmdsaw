from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import MessagesState

class Parameter(TypedDict, total=False):
    """Represents a CLI parameter."""
    description: Optional[str] # description of the parameter, if provided
    type: Optional[str]  # str, int, float, path, bool, etc.
    required: bool  # true if required, false if optional
    is_input: bool  # true if input file or directory
    is_output: bool # true if output file or directory
    default_value: Optional[str]
    is_flag: bool # true if flag (no argument), false if takes argument
    short: str  # short name like -h
    long: Optional[str]   # long name like --help

class GlobalParameters(TypedDict, total=False):
    """Names of tool (sub)commands."""
    parameters: Optional[List[Parameter]]

class ContainerInfo(TypedDict, total=False):
    """Container image information for a tool from BioContainers."""
    bioconda: Optional[str]
    docker: Optional[str]
    singularity: Optional[str]

class EdamInput(TypedDict, total=False):
    """Represents an EDAM-standardized input."""
    name: str
    suffix: str  # file extension like .bam, .fasta
    edam: str    # EDAM ontology term like data_1383
    optional: bool

class EdamOutput(TypedDict, total=False):
    """Represents an EDAM-standardized output."""
    name: str
    suffix: str  # file extension like .bam, .sam
    edam: str    # EDAM ontology term like format_2572
    optional: bool

class StandardizedTool(TypedDict, total=False):
    """Represents a standardized tool with EDAM ontology terms."""
    id: str           # tool_subcommand format like "samtools_view"
    name: str         # uppercase name like "SAMTOOLS_VIEW"
    label: str        # process label like "process_low"
    inputs: List[EdamInput]
    outputs: List[EdamOutput]
    commands: str     # template command string

class Subcommand(TypedDict, total=False):
    """Represents a CLI subcommand."""
    name: str
    description: Optional[str]
    parameters: Optional[List[Parameter]]
    usage: Optional[str]
    
class SubcommandNames(TypedDict, total=False):
    """Names of tool (sub)commands."""
    names: Optional[List[str]]

class ToolInfo(TypedDict, total=False):
    """Represents information about a CLI tool."""
    tool: str
    version: Optional[str] 
    description: Optional[str]
    subcommands: List[Subcommand]
    global_parameters: Optional[GlobalParameters]  # parameters that apply to all subcommands
    help_text: Optional[str]
    version_text: Optional[str]
    containers: Optional[ContainerInfo]
    error: Optional[str]

class WorkflowState(MessagesState):
    """State passed between agents in the cmdsaw workflow."""
    # Input
    executable: Optional[str]
    target_format: Optional[str]  # 'wdl' or 'nextflow'
    
    # Invocation agent outputs
    tool_info: Optional[ToolInfo]
    
    # Parsing agent outputs  
    parsed_subcommands: Optional[List[Subcommand]]
    
    # Standardization agent outputs
    standardized_tools: Optional[List[StandardizedTool]]
    standardized_parameters: Optional[List[Parameter]]
    
    # Troubleshooting agent outputs
    validation_errors: Optional[List[str]]
    suggested_fixes: Optional[List[str]]
    
    # Generator agent outputs
    generated_nextflow: Optional[str]
    generated_wdl: Optional[str]
    metadata: Optional[Dict[str, Any]]