"""Attempt to assign standardized input and output format(s) from EDAM ontologies. 
    Also assign standardized operation tags from EDAM. 
    These are what will be used by Project 3 to validate inputs/outputs. 
    Pass structured JSON output to next agent."""

# Take input the structured JSON output from previous agent,
# Return structured JSON output with added EDAM terms for input/output formats and operations

"""Attempt to assign standardized input and output format(s) from EDAM ontologies. 
    Also assign standardized operation tags from EDAM. 
    These are what will be used by Project 3 to validate inputs/outputs. 
    Pass structured JSON output to next agent."""

import json
import re
import requests
from typing import Dict, Any, List, Optional
from langgraph.graph import START, StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from sub_agents.schema import WorkflowState, ToolInfo, Subcommand, StandardizedTool, EdamInput, EdamOutput


# EDAM Ontology mappings for common bioinformatics file formats
EDAM_FORMAT_MAPPINGS = {
    # Sequence formats
    ".fasta": "format_1929",  # FASTA sequence format
    ".fa": "format_1929",
    ".fastq": "format_1930",  # FASTQ sequence format
    ".fq": "format_1930",
    
    # Alignment formats  
    ".sam": "format_2573",    # SAM alignment format
    ".bam": "format_2572",    # BAM alignment format
    ".cram": "format_3462",   # CRAM alignment format
    
    # Index formats
    ".bai": "format_3327",    # BAM index format
    ".csi": "format_3326",    # CSI index format
    ".fai": "format_3327",    # FASTA index format
    
    # Variant formats
    ".vcf": "format_3016",    # VCF variant format
    ".bcf": "format_3020",    # BCF variant format
    
    # Annotation formats
    ".gff": "format_2305",    # GFF format
    ".gtf": "format_2306",    # GTF format
    ".bed": "format_3003",    # BED format
    
    # General formats
    ".txt": "format_2330",    # Textual format
    ".csv": "format_3752",    # CSV format
    ".json": "format_3464",   # JSON format
    ".xml": "format_2332",    # XML format
}

# EDAM Data type mappings
EDAM_DATA_MAPPINGS = {
    # Sequence data
    "sequence": "data_2044",         # Sequence
    "sequences": "data_0850",        # Sequence set
    "alignment": "data_1383",        # Sequence alignment
    "alignments": "data_1383", 
    
    # Genomic data
    "genome": "data_2340",           # Genome data
    "chromosome": "data_3002",       # Chromosome
    "gene": "data_0916",             # Gene features
    
    # Annotation data
    "annotation": "data_0582",       # Ontology annotation
    "features": "data_1255",         # Sequence features
    "variants": "data_3498",         # Sequence variations
    
    # Reference data
    "reference": "data_2340",        # Reference sequence
    "index": "data_0842",            # Identifier
}

# Common bioinformatics operations
EDAM_OPERATION_MAPPINGS = {
    "view": "operation_0564",        # Sequence visualisation
    "index": "operation_0227",       # Data indexing
    "sort": "operation_3802",        # Sorting
    "merge": "operation_3436",       # Aggregation
    "convert": "operation_0335",     # Format conversion
    "filter": "operation_3695",      # Filtering
    "extract": "operation_2422",     # Data retrieval
    "align": "operation_0292",       # Sequence alignment
    "map": "operation_0292",         # Sequence alignment
    "call": "operation_3227",        # Variant calling
    "annotate": "operation_0362",    # Annotation
}


def get_edam_term_for_suffix(suffix: str) -> str:
    """Get EDAM format term for file suffix."""
    return EDAM_FORMAT_MAPPINGS.get(suffix.lower(), "format_1915")  # default to "Format"


def get_edam_term_for_data_type(description: str) -> str:
    """Get EDAM data term based on parameter description."""
    description_lower = description.lower() if description else ""
    
    for keyword, edam_term in EDAM_DATA_MAPPINGS.items():
        if keyword in description_lower:
            return edam_term
    
    return "data_0006"  # default to "Data"


def get_edam_operation_for_command(command_name: str) -> str:
    """Get EDAM operation term for command."""
    command_lower = command_name.lower()
    
    for keyword, edam_term in EDAM_OPERATION_MAPPINGS.items():
        if keyword in command_lower:
            return edam_term
    
    return "operation_0004"  # default to "Operation"


def infer_file_type_from_parameter(param: Dict) -> Optional[str]:
    """Infer file type from parameter information."""
    param_name = param.get("name", "").lower()
    description = param.get("description", "").lower()
    param_type = param.get("type", "").lower()
    
    # Check for file extensions in description or name
    for suffix in EDAM_FORMAT_MAPPINGS.keys():
        if suffix in description or suffix in param_name:
            return suffix
    
    # Check for common file type keywords
    if "file" in param_type or "path" in param_type:
        if any(keyword in description for keyword in ["bam", "sam", "alignment"]):
            return ".bam"
        elif any(keyword in description for keyword in ["fasta", "sequence", "reference"]):
            return ".fasta"
        elif any(keyword in description for keyword in ["fastq", "reads"]):
            return ".fastq"
        elif any(keyword in description for keyword in ["vcf", "variant"]):
            return ".vcf"
        elif any(keyword in description for keyword in ["bed", "interval"]):
            return ".bed"
    
    return None


def classify_parameter_as_input_output(param: Dict, command_name: str) -> str:
    """Classify parameter as input, output, or option."""
    param_name = param.get("name", "").lower()
    description = param.get("description", "").lower()
    
    # Output indicators
    output_keywords = ["output", "out", "write", "save", "result"]
    if any(keyword in param_name or keyword in description for keyword in output_keywords):
        return "output"
    
    # Input indicators  
    input_keywords = ["input", "in", "read", "file", "reference", "alignment", "sequence"]
    if any(keyword in param_name or keyword in description for keyword in input_keywords):
        return "input"
    
    return "option"


def generate_command_template(tool_name: str, subcommand: Dict, inputs: List[EdamInput], outputs: List[EdamOutput]) -> str:
    """Generate command template for the standardized tool."""
    command_parts = [tool_name]
    
    if subcommand.get("name") != "main":
        command_parts.append(subcommand["name"])
    
    # Add common options
    command_parts.append("--threads ${task.cpus}")
    
    # Add input references
    for inp in inputs:
        if inp["name"] == "reference":
            command_parts.append("${reference}")
        elif inp["name"] == "alignment":
            command_parts.append("${alignment}")
    
    # Add generic args
    command_parts.append("$args")
    
    # Add output specification
    if outputs:
        command_parts.append("-o ${output_file}")
    
    # Add main input
    command_parts.append("$input")
    command_parts.append("$args2")
    
    return " ".join(command_parts)


def standardization_agent(state: WorkflowState) -> Dict[str, Any]:
    """
    Standardization agent: Converts parsed tool information to EDAM-standardized format.
    Takes parsed subcommands and creates standardized tool definitions with EDAM ontology terms.
    """
    tool_info = state.get("tool_info")
    parsed_subcommands = state.get("parsed_subcommands", [])
    
    if not tool_info or tool_info.get("error"):
        return {"tool_info": tool_info}
    
    tool_name = tool_info.get("tool", "")
    standardized_tools = []
    
    # Process each subcommand
    for subcommand in parsed_subcommands:
        print("Performing standardization for subcommand", subcommand)
        
        subcommand_name = subcommand.get("name", "main")
        
        # Create standardized tool ID and name
        tool_id = f"{tool_name}_{subcommand_name}".lower()
        tool_display_name = f"{tool_name}_{subcommand_name}".upper()
        
        # Process parameters to extract inputs and outputs
        inputs = []
        outputs = []
        
        parameters = subcommand.get("parameters", [])
        for param in parameters:
            param_classification = classify_parameter_as_input_output(param, subcommand_name)
            file_suffix = infer_file_type_from_parameter(param)
            
            if file_suffix and param_classification in ["input", "output"]:
                edam_term = get_edam_term_for_suffix(file_suffix)
                
                if param_classification == "input":
                    edam_input = EdamInput(
                        name=param.get("name", "input"),
                        suffix=file_suffix,
                        edam=edam_term,
                        optional=not param.get("required", False)
                    )
                    inputs.append(edam_input)
                    
                elif param_classification == "output":
                    edam_output = EdamOutput(
                        name=param.get("name", "output"),
                        suffix=file_suffix,
                        edam=edam_term,
                        optional=not param.get("required", False)
                    )
                    outputs.append(edam_output)
        
        # If no inputs/outputs detected, add defaults based on tool
        if not inputs and tool_name == "samtools":
            inputs.append(EdamInput(
                name="alignment",
                suffix=".bam",
                edam="format_2572",
                optional=False
            ))
        
        if not outputs and tool_name == "samtools":
            if subcommand_name == "view":
                outputs.extend([
                    EdamOutput(name="bam", suffix=".bam", edam="format_2572", optional=True),
                    EdamOutput(name="sam", suffix=".sam", edam="format_2573", optional=True)
                ])
        
        # Generate command template
        command_template = generate_command_template(tool_name, subcommand, inputs, outputs)
        
        # Create standardized tool
        standardized_tool = StandardizedTool(
            id=tool_id,
            name=tool_display_name,
            label="process_low",  # default process level
            inputs=inputs,
            outputs=outputs,
            commands=command_template
        )
        
        standardized_tools.append(standardized_tool)

        print("Complete standardization for standardized tool,", standardized_tool)
    
    return {
        "standardized_tools": standardized_tools
    }


# Create standardization subgraph
standardization_builder = StateGraph(WorkflowState)
standardization_builder.add_node("standardization_agent", standardization_agent)
standardization_builder.add_edge(START, "standardization_agent")
standardization_builder.add_edge("standardization_agent", END)

# Compile the standardization graph for export
standardization_graph = standardization_builder.compile()


# if __name__ == "__main__":
#     # Simple test with sample data
#     test_state = {
#         "tool_info": {
#             "tool": "samtools",
#             "version": "1.22.1",
#             "description": "Tools for manipulating SAM/BAM/CRAM files"
#         },
#         "parsed_subcommands": [
#             {
#                 "name": "view",
#                 "description": "SAM<->BAM<->CRAM conversion",
#                 "usage": "samtools view [options] <in.bam>|<in.sam>|<in.cram> [region ...]",
#                 "parameters": [
#                     {
#                         "name": "output",
#                         "description": "Write output to FILE",
#                         "type": "path",
#                         "required": False,
#                         "is_flag": False,
#                         "aliases": ["-o", "--output"]
#                     },
#                     {
#                         "name": "input",
#                         "description": "Input BAM/SAM/CRAM file",
#                         "type": "path", 
#                         "required": True,
#                         "is_flag": False,
#                         "aliases": []
#                     }
#                 ]
#             }
#         ]
#     }
    
#     result = standardization_graph.invoke(test_state)
#     print("Standardization Result:")
#     print(json.dumps(result, indent=2))