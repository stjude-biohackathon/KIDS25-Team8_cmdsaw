# FlowJo CLI - Minimal MVP Implementation

## Overview
This is a minimal MVP implementation that generates WDL tasks from command-line help text using LLM parsing.

## Installation
```bash
pip install click requests
```

## Usage

### Basic command generation
```bash
python -m flowjo generate ls --outdir ./output
```

### Discover subcommands
```bash  
python -m flowjo generate samtools --discover-subcommands --outdir ./output
```

### Full usage
```bash
python -m flowjo generate <executable> [--discover-subcommands] [--format wdl] [--outdir DIR] [--skip-validation]
```

## Architecture

### Files implemented:
- `__init__.py` - Click-based CLI entry point
- `runner.py` - Execute subprocess and capture help text
- `parser.py` - LLM prompt building and JSON validation
- `translator.py` - Convert JSON to WDL tasks
- `templates/task.wdl` - WDL task template
- `test_basic.py` - Standalone test script

### Core functionality:
1. **Runner Module**: Captures `--help` and `--version` output, discovers subcommands using regex
2. **Parser Module**: Builds constrained prompts for Ollama, validates JSON responses
3. **Translator Module**: Converts JSON schemas to WDL 1.2 task files
4. **CLI**: Click-based interface with all required options

### Example workflow:
1. Run `samtools --help` → capture output
2. Discover subcommands like `view`, `sort`, etc.
3. Run `samtools view --help` for each subcommand
4. Send help text to Ollama with constrained prompt
5. Parse JSON response with parameter details
6. Generate WDL task file with proper inputs/outputs
7. Save both JSON and WDL files in organized directory structure

## Testing
Run the standalone test script:
```bash
python test_basic.py
```

This tests the core functionality without requiring external dependencies.

## Dependencies
- **click**: CLI framework
- **requests**: HTTP client for Ollama API
- **subprocess**: Built-in Python module for running commands
- **json**: Built-in Python module for JSON parsing
- **re**: Built-in Python module for regex operations

## Expected Output Structure
```
output/
  ls_8.32/              # tool_version directory
    ls_ls.wdl          # generated WDL task
    ls.json            # original JSON from LLM
```

## Notes
- Only WDL format currently supported (Nextflow placeholder)
- Uses Ollama running on localhost:11434 (phi3:3.8b model)
- Simple heuristic-based subcommand discovery
- Minimal error handling for MVP
- WDL 1.2 compatible output with proper type mapping