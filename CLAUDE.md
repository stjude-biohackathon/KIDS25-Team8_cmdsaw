# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FlowGen is a CLI tool that automatically converts command-line tool help documentation into workflow task definitions (WDL/Nextflow) using Large Language Models. This is a St. Jude Biohackathon 2025 project with a dual architecture approach: a streamlined MVP and a sophisticated agent-based system.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Start Ollama service (required dependency)
ollama serve
```

### Running the CLI (MVP Implementation)
```bash
# Basic usage - generate WDL tasks from a command-line tool
python -m flowgen generate <executable> --outdir ./output

# Discover and process subcommands
python -m flowgen generate samtools --discover-subcommands --outdir ./output

# Use pre-saved help text (for testing/reproducibility)
python -m flowgen generate samtools --help-text output/samtools_help.txt

# Generate Nextflow format instead of WDL
python -m flowgen generate samtools --format nextflow --outdir ./output

# Use different LLM model
python -m flowgen generate samtools --model llama3.1:8b

# Debug mode with validation skipping
python -m flowgen generate samtools --debug --skip-validation
```

### Testing and Development
```bash
# Interactive testing via Jupyter notebook
jupyter notebook Testing.ipynb

# Run agent-based system (advanced)
python agent.py
```

## Architecture Overview

### Dual Implementation Strategy

**MVP Implementation (flowgen/)** - Production-ready pipeline:
- Linear workflow: CLI → Runner → Parser → Translator → Output
- Direct Ollama integration with streaming responses
- Regex-based subcommand discovery
- Rich terminal UI with progress feedback

**Agent System (sub_agents/ + agent.py)** - Advanced research:
- LangGraph state machine with specialized agents
- TypedDict state management (`WorkflowState`)
- Modular agent nodes: Invocation → Parsing → Standardization → Generation
- EDAM ontology integration and BioContainers lookup

### Key Components

**Runner Module (flowgen/runner.py)**:
- `run_help(executable, args)` - Command execution and help capture
- `discover_subcoms(help_text)` - Regex pattern matching for subcommands
- Handles both main tool help and individual subcommand help

**Parser Module (flowgen/parser.py)**:
- `build_prompt()` - Constructs LLM prompts with strict JSON schema constraints
- `call_model()` - Ollama API integration with streaming output
- `validate_json()` - Schema validation for parameter extraction
- Enforces specific JSON structure for tool metadata

**Translator Module (flowgen/translator.py)**:
- `json_to_wdl()` - Converts JSON parameters to WDL 1.2 task definitions
- `json_to_nextflow()` - Generates Nextflow process modules
- Type mapping: `path→File`, `int→Int`, `flag→Boolean`, etc.
- Creates README documentation and test files

**Schema Definitions (sub_agents/schema.py)**:
- `WorkflowState` - Central state machine data structure
- `Parameter` - CLI parameter type definitions
- `ToolInfo` - Complete tool metadata with container information

## Dependencies and External Requirements

### Required Services
- **Ollama** - Must be running on `localhost:11434` for LLM inference
- **Command-line tools** - Target tools must be installed for help text capture

### Python Dependencies
- `click>=8.0.0` - CLI framework with command definitions
- `rich>=13.0.0` - Enhanced terminal output (colors, progress, panels)
- `requests>=2.25.0` - HTTP client for Ollama API
- `langgraph` + `langchain-*` - Agent orchestration framework
- `langchain-ollama` - LLM integration

### Default Models
- Default: `llama3.2:3b` (for speed)
- Alternative: `llama3.1:8b` (for better accuracy)

## File Organization Patterns

### Input Processing
- Help text capture via subprocess execution
- Version extraction from `--version` output
- Subcommand discovery using regex patterns targeting common help formats

### Output Structure
```
output/
├── {tool}_WDL/                 # WDL format
│   ├── README.md              # Documentation
│   ├── {tool}_{command}.wdl   # One task per subcommand
│   └── {command}.json         # Original LLM JSON response
├── {tool}_NEXTFLOW/           # Nextflow format
│   ├── nextflow.config
│   ├── {command}/
│   │   ├── main.nf
│   │   ├── meta.yml
│   │   └── tests/main.nf.test
└── {tool}_help.txt            # Captured help text
```

### JSON Schema Enforcement
The parser enforces a strict JSON schema for extracted tool metadata:
- Tool name, version, and description
- Commands array with parameters, positional args, and I/O specifications
- Parameter types: `path`, `int`, `float`, `string`, `flag`
- Container information: bioconda, docker, singularity

## Development Workflow

### Testing Strategy
- **Notebook-based**: `Testing.ipynb` for interactive development
- **Reproducible testing**: Use `--help-text` flag with pre-saved help files
- **No formal test suite**: Project is in research/hackathon phase

### Code Generation Templates
- WDL 1.2 compatible task definitions
- Nextflow DSL2 process modules with nf-core conventions
- Metadata files (meta.yml) for tool documentation
- Test file generation for both formats

### Error Handling
- Fail fast with descriptive Rich console output
- JSON validation at each stage
- Ollama connection checking
- Command execution error capture

## Agent System (Advanced)

### State Machine Flow
1. **Invocation Agent** (`sub_agents/invocation.py`) - Command execution
2. **Parsing Agent** (`sub_agents/parsing.py`) - Parameter extraction
3. **Standardization Agent** (`sub_agents/standardization.py`) - EDAM mapping
4. **Container Agent** (`sub_agents/containers.py`) - BioContainers lookup
5. **Generator Agents** (WDL/Nextflow) - Code generation

### LangGraph Integration
- Uses `WorkflowState` TypedDict for state passing
- Conditional edges based on processing results
- Extensible for adding new agent nodes

## Important Implementation Details

### Subcommand Discovery
Uses regex patterns to find subcommands in help text:
- Looks for section headers: "Commands:", "Available commands:", etc.
- Extracts from indented command lists
- Filters common false positives (help, version, usage, options)

### LLM Integration
- Streaming responses with real-time console output
- JSON cleaning (removes code blocks, fixes trailing commas)
- Model response caching in `llama_response.json`
- Constrained prompts for consistent parameter extraction

### Type System
Parameter type mapping between CLI help text and workflow languages:
- `path` types become `File` in WDL, `path` in Nextflow
- `flag` types become `Boolean` with default values
- Required vs optional parameter handling
- Positional argument vs named parameter distinction

## Repository Status

- **Main branch**: Clean working directory
- **Development stage**: Active biohackathon project
- **No CI/CD**: Manual testing and development
- **No formal releases**: Research/prototype phase