# Copilot Instructions for cmdsaw

## Repository Overview

**cmdsaw** is a Python CLI tool that automatically analyzes command-line tools by parsing their `--help` output using Large Language Models (LLMs). It discovers subcommands recursively, extracts parameter information, and generates WDL (Workflow Description Language) 1.2 task definitions for computational pipelines.

- **Type**: Python CLI application and library
- **Size**: Small (~1500 lines of Python code)
- **Languages**: Python 3.10+
- **Build System**: Hatchling (PEP 517)
- **Key Dependencies**: click, pydantic, langchain, langchain-ollama, ollama, rich
- **External Requirement**: Requires Ollama running locally for LLM inference

## Project Structure

```
KIDS25-Team8_cmdsaw/
├── cmdsaw/                     # Main package directory
│   ├── __init__.py            # Package initialization, version info
│   ├── cli.py                 # Main CLI entry point (104 lines)
│   ├── constants.py           # Default configuration values
│   ├── discovery.py           # Command tree building logic (262 lines)
│   ├── errors.py              # Custom exception classes
│   ├── runner.py              # Command execution utilities (75 lines)
│   ├── serialize.py           # JSON serialization (28 lines)
│   ├── utils.py               # Utility functions (84 lines)
│   ├── wdl.py                 # WDL task generation (298 lines)
│   └── parsing/               # LLM parsing subpackage
│       ├── cache.py           # LLM response caching (83 lines)
│       ├── llm_parser.py      # LLM-based help text parser (136 lines)
│       ├── prompts.py         # LLM prompts for parsing (148 lines)
│       ├── resource_estimator.py  # Resource estimation for WDL (42 lines)
│       └── schema.py          # Pydantic data models (57 lines)
├── tests/                     # Test directory
│   ├── fixtures/
│   │   └── fake_help.txt     # Test fixture
│   ├── test_end_to_end.py    # Placeholder test
│   └── test_tool_no_subcommands.py  # Schema/serialization tests (161 lines)
├── pyproject.toml            # Project configuration and dependencies
├── README.md                 # User documentation
├── Testing.ipynb             # Development notebook
└── .gitignore               # Git ignore patterns
```

## Installation & Setup

### Installing the Package

**Always install in editable mode for development:**

```bash
pip install -e .
```

This installs:
- The `cmdsaw` package in development mode
- All dependencies from pyproject.toml
- The `cmdsaw` CLI command

**Installation is fast** (~10-15 seconds) and does not require compilation.

### Runtime Requirements

**IMPORTANT**: cmdsaw requires Ollama to be running locally. The tool will fail with connection errors if Ollama is not available.

To install and run Ollama:
```bash
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
# Then start the service:
ollama serve

# Pull a recommended model (required before using cmdsaw):
ollama pull gemma3:12b
```

**For testing without Ollama**: The test suite does NOT require Ollama because it only tests data structures and serialization. Only the end-to-end tool execution requires Ollama.

## Building & Testing

### Running Tests

Tests use pytest. **Always install pytest first** if not already available:

```bash
pip install pytest
```

**Run all tests:**
```bash
python -m pytest tests/ -v
```

**Run tests without verbose output:**
```bash
python -m pytest tests/
```

**Run individual test files directly (alternative method):**
```bash
python tests/test_tool_no_subcommands.py
```

**Test execution time**: ~0.04 seconds (very fast)

**Current test count**: 4 tests, all passing
- 1 placeholder test in test_end_to_end.py
- 3 schema/serialization tests in test_tool_no_subcommands.py

### Linting & Code Quality

**No linters are currently configured** in this repository. The pyproject.toml only contains build configuration, not linting tools like ruff, flake8, pylint, or mypy.

If adding linting, consider:
- ruff (modern, fast Python linter)
- mypy (type checking - project uses type hints)
- No existing .ruff_cache, .flake8, or other linter configs exist

### Running the CLI Tool

**Basic command structure:**
```bash
cmdsaw --command <tool-name> --model <model> [OPTIONS]
```

**Example (requires Ollama running):**
```bash
cmdsaw --command ls --model gemma3:12b --output ls.json --wdl-out ls.wdl
```

**View help:**
```bash
cmdsaw --help
```

**Default values:**
- Model: `gemma3:12b` (configured in constants.py)
- Max depth: 1
- Concurrency: 4
- Timeout: 30 seconds

## Development Workflow

### Making Code Changes

1. **Edit source files** in `cmdsaw/` or `cmdsaw/parsing/`
2. **Reinstall is NOT required** when using `pip install -e .` (editable mode)
3. **Run tests immediately** to verify changes:
   ```bash
   python -m pytest tests/ -v
   ```

### Adding New Features

**Key modules to understand:**
- `cli.py`: Entry point, parses CLI arguments using Click
- `discovery.py`: Recursive command tree building, parallel processing
- `parsing/llm_parser.py`: LLM interaction via langchain-ollama
- `parsing/schema.py`: Pydantic models for all data structures
- `wdl.py`: WDL task generation with resource estimation

**Data flow:**
1. CLI → discovery.py → runner.py (execute `--help`)
2. runner.py → parsing/llm_parser.py (parse help text with LLM)
3. llm_parser.py → parsing/schema.py (structure into Pydantic models)
4. discovery.py → serialize.py (output JSON)
5. discovery.py → wdl.py (generate WDL tasks)

### Testing Changes

**Tests are unit/integration tests** focusing on:
- Data structure serialization (ToolDoc, CommandDoc, etc.)
- Parameter preservation (options, positionals)
- Edge cases (tools with/without subcommands)

**No end-to-end tests exist** that require Ollama or external commands. The test_end_to_end.py file only contains a placeholder.

**When adding tests:**
- Place in `tests/` directory
- Use pytest conventions
- Import from `cmdsaw.parsing.schema` for data models
- Follow existing test patterns in test_tool_no_subcommands.py

## Configuration Files

### pyproject.toml

Contains:
- Build system: hatchling
- Package metadata: name, version (0.2.0), description
- Python requirement: >=3.10
- Dependencies list (click, pydantic, langchain, etc.)
- Entry point: `cmdsaw = "cmdsaw.cli:main"`
- Wheel packages: `["cmdsaw"]`

**No tool configurations** for linting, formatting, or testing are present.

### .gitignore

Standard Python gitignore with additions for:
- Virtual environments (.venv, venv, env)
- Build artifacts (dist/, build/, *.egg-info)
- Cache directories (__pycache__, .pytest_cache, .ruff_cache)
- IDE files (.vscode, .idea, .cursorignore)
- Test coverage (.coverage, htmlcov)

## Common Pitfalls & Workarounds

### 1. Ollama Connection Errors

**Error**: `httpx.ConnectError` when running cmdsaw

**Cause**: Ollama is not running or not accessible

**Solution**: 
```bash
# Start Ollama in a separate terminal
ollama serve

# Verify it's running
ollama list
```

### 2. Model Not Found

**Error**: Model not available or 404 error

**Solution**: Pull the model first
```bash
ollama pull gemma3:12b
# or
ollama pull deepseek-r1:14b
```

### 3. Testing Without Ollama

**Important**: Current tests do NOT require Ollama. They test data structures only. Do not add end-to-end tests that require Ollama unless you're prepared to mock it or skip those tests in CI.

### 4. Import Errors After Changes

If you get import errors after modifying package structure:

```bash
# Reinstall in editable mode
pip uninstall -y cmdsaw
pip install -e .
```

### 5. Testing Individual Modules

Some test files (like test_tool_no_subcommands.py) can be run directly:
```bash
python tests/test_tool_no_subcommands.py
```

This works because they have `if __name__ == '__main__':` blocks.

## Key Architecture Points

### LLM Integration

- Uses langchain and langchain-ollama for LLM interaction
- Caches LLM responses in `~/.cache/cmdsaw/` (disabled with `--no-llm-cache`)
- Prompts defined in `parsing/prompts.py`
- Model selection via `--model` flag (default: gemma3:12b)

### Command Discovery

- Recursive depth controlled by `--max-depth` (default: 1)
- Parallel processing via ThreadPoolExecutor (default: 4 concurrent)
- Interactive review mode: `--review-subcommands` flag

### WDL Generation

- Version 1.2 WDL tasks
- Automatic resource estimation (CPU, memory)
- Filters out `--help` parameters (never useful in workflow tasks)
- Handles tools with and without subcommands

### Data Models (Pydantic)

- `CommandDoc`: Single command/subcommand
- `ToolDoc`: Complete tool with subcommands
- `OptionDoc`: Command-line option/flag
- `PositionalDoc`: Positional argument
- `CmdSawResult`: Full result with diagnostics
- All models serialize to JSON via `model_dump()`

## Validation Steps

Before submitting changes:

1. **Install in editable mode**: `pip install -e .`
2. **Run all tests**: `python -m pytest tests/ -v`
3. **Verify CLI loads**: `cmdsaw --help`
4. **Check imports**: `python -c "from cmdsaw import __version__; print(__version__)"`

If adding new dependencies:
5. **Add to pyproject.toml** under `dependencies`
6. **Reinstall**: `pip install -e .`

If adding new modules:
7. **Ensure they're in cmdsaw/ directory**
8. **Verify import paths** match package structure

## Instructions for Coding Agents

**Trust these instructions.** Only perform additional searches if:
- Information here is incomplete or unclear
- You need to understand implementation details not covered
- You encounter errors not documented here

**Key points:**
- Always use `pip install -e .` for installation
- Tests do NOT require Ollama
- No linting is configured; don't add it unless specifically requested
- The tool generates WDL 1.2 tasks, not Nextflow (future feature)
- Default model is gemma3:12b (best balance of speed/accuracy)
- LLM caching is enabled by default for performance

**When making changes:**
- Keep edits minimal and surgical
- Run tests after each change
- Don't modify test fixtures without understanding their purpose
- Follow existing code patterns (type hints, docstrings, Pydantic models)
