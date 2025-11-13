# Copilot Instructions for cmdsaw

## Repository Overview

**cmdsaw** is a Python CLI tool that parses command-line tool help text using LLMs to generate WDL 1.2 workflow tasks. It recursively discovers subcommands and extracts parameters.

- **Type**: Python 3.10+ CLI application (~1500 lines)
- **Build**: Hatchling (PEP 517)
- **Key Dependencies**: click, pydantic, langchain, langchain-ollama, ollama, rich
- **Critical Requirement**: Ollama must be running locally for LLM inference

## Project Structure

```
cmdsaw/                        # Main package (11 files)
├── cli.py                     # CLI entry point (104 lines)
├── discovery.py               # Command tree builder (262 lines)
├── wdl.py                     # WDL task generator (298 lines)
├── runner.py, serialize.py, utils.py, errors.py, constants.py
└── parsing/                   # LLM parsing (5 files)
    ├── llm_parser.py          # LLM interaction (136 lines)
    ├── prompts.py             # LLM prompts (148 lines)
    ├── schema.py              # Pydantic models (57 lines)
    ├── cache.py, resource_estimator.py
tests/
├── test_tool_no_subcommands.py  # Schema tests (161 lines, 3 tests)
└── test_end_to_end.py           # Placeholder (1 test)
pyproject.toml                 # Build config, dependencies, entry point
README.md                      # Full documentation
```

## Installation & Setup

**Always install in editable mode:**
```bash
pip install -e .  # Fast: ~10-15s, no compilation
```

**Runtime Requirement - Ollama:** The CLI requires Ollama running locally. Tests do NOT require Ollama.
```bash
ollama serve                # Start Ollama service
ollama pull gemma3:12b      # Pull recommended model
```

Without Ollama running, CLI fails with `httpx.ConnectError`.

## Building & Testing

**Install pytest first:** `pip install pytest`

**Run tests** (4 tests, ~0.04s, all pass):
```bash
python -m pytest tests/ -v           # Verbose
python -m pytest tests/              # Quiet
python tests/test_tool_no_subcommands.py  # Direct execution
```

**No linters configured.** No ruff, flake8, pylint, mypy, or configs exist in pyproject.toml.

**CLI Usage:**
```bash
cmdsaw --help                        # View options
cmdsaw --command ls --model gemma3:12b --output ls.json --wdl-out ls.wdl
```

**Defaults:** Model: gemma3:12b, Max depth: 1, Concurrency: 4, Timeout: 30s (in constants.py)

## Architecture & Data Flow

**Key Modules:**
- `cli.py`: Click-based CLI entry point
- `discovery.py`: Recursive tree builder with ThreadPoolExecutor for parallel subcommand parsing
- `parsing/llm_parser.py`: LLM interaction via langchain-ollama
- `parsing/schema.py`: Pydantic models (CommandDoc, ToolDoc, OptionDoc, PositionalDoc, CmdSawResult)
- `wdl.py`: WDL 1.2 task generation with resource estimation

**Flow:** CLI → discovery → runner (exec --help) → llm_parser (LLM) → schema (Pydantic) → serialize (JSON) + wdl (tasks)

**Testing:** Unit tests only. No e2e tests. Tests focus on Pydantic serialization, parameter preservation, edge cases.

**pyproject.toml:** Build config only. No linting/formatting tools. Entry: `cmdsaw = "cmdsaw.cli:main"`. Version: 0.2.0.

## Common Issues & Solutions

**1. `httpx.ConnectError`:** Ollama not running. Fix: `ollama serve` then `ollama list` to verify.

**2. Model not found:** Pull model first: `ollama pull gemma3:12b` or `ollama pull deepseek-r1:14b`

**3. Import errors:** Reinstall: `pip uninstall -y cmdsaw && pip install -e .`

**4. Testing without Ollama:** Tests don't need Ollama (data structure tests only). Don't add e2e tests requiring Ollama without mocking.

**5. Direct test execution:** `python tests/test_tool_no_subcommands.py` works (has `if __name__ == '__main__'`).

## Key Features

**LLM Integration:** langchain-ollama, caches responses in `~/.cache/cmdsaw/` (disable: `--no-llm-cache`), prompts in `parsing/prompts.py`

**Command Discovery:** Recursive (`--max-depth`, default: 1), parallel ThreadPoolExecutor (4 concurrent), interactive review (`--review-subcommands`)

**WDL:** Version 1.2, auto resource estimation, filters `--help` params, handles tools with/without subcommands

**Pydantic Models:** CommandDoc, ToolDoc, OptionDoc, PositionalDoc, CmdSawResult (all serialize via `model_dump()`)

## Validation & Development Guidelines

**Before submitting:** `pip install -e .` → `python -m pytest tests/ -v` → `cmdsaw --help` → `python -c "from cmdsaw import __version__; print(__version__)"`

**Adding dependencies:** Add to `pyproject.toml` dependencies, then `pip install -e .`

**Adding modules:** Place in `cmdsaw/`, verify import paths match structure

**For Coding Agents - Trust These Instructions:**
- Use `pip install -e .` always
- Tests don't need Ollama
- No linting configured (don't add unless requested)
- Generates WDL 1.2 (Nextflow planned, not implemented)
- Default model: gemma3:12b
- LLM caching enabled by default
- Keep edits minimal
- Run tests after changes
- Follow patterns: type hints, docstrings, Pydantic models
- Don't modify test fixtures without understanding purpose
