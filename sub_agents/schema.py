from langgraph.graph import MessagesState
from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict

class Parameter(TypedDict, total=False):
    """Represents a CLI parameter."""
    name: str
    description: Optional[str]
    type: str  # string, int, double, path, flag, etc.
    required: bool
    default_value: Optional[str]
    is_flag: bool
    aliases: List[str]  # alternative names like -h, --help

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
    command: str
    help_text: Optional[str]
    description: Optional[str]
    parameters: Optional[List[Parameter]]
    usage: Optional[str]

class ToolInfo(TypedDict, total=False):
    """Represents information about a CLI tool."""
    tool: str
    version: Optional[str] 
    description: Optional[str]
    subcommands: List[Subcommand]
    global_parameters: List[Parameter]  # parameters that apply to all subcommands
    help_text: Optional[str]
    version_text: Optional[str]
    containers: Optional[ContainerInfo]
    error: Optional[str]

class WorkflowState(MessagesState):
    """State passed between agents in the flowgen workflow."""
    # Input
    executable: Optional[str]
    target_format: Optional[str]  # 'wdl' or 'nextflow'
    
    # Invocation agent outputs
    tool_info: Optional[ToolInfo]
    
    # Standardization agent outputs
    standardized_tools: Optional[List[StandardizedTool]]
    
    # Troubleshooting agent outputs
    validation_errors: Optional[List[str]]
    suggested_fixes: Optional[List[str]]
    
    # Generator agent outputs
    generated_nextflow: Optional[str]
    generated_wdl: Optional[str]
    metadata: Optional[Dict[str, Any]]