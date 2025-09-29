# FlowGen CLI

**Generate WDL and Nextflow workflow tasks from command-line help text using AI**

FlowGen is a CLI tool that automatically converts command-line tool help documentation into workflow task definitions (WDL/Nextflow) using Large Language Models. It discovers subcommands, parses help text, and generates properly formatted workflow tasks ready for use in scientific pipelines.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd goal2-cli

# Install dependencies
pip install -r requirements.txt

# Ensure Ollama is running locally
ollama serve
```

### Basic Usage

```bash
# Discover and process commands from help-text file for samtools
python -m flowgen generate samtools --outdir ./output --help-text output/samtools_help.txt
```

## 📋 Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `executable` | Command-line tool to process | Required |
| `--format` | Output format (`wdl` or `nextflow`) | `wdl` |
| `--help-text` | Path to help text file (for testing) | `None` |
| `--outdir` | Output directory | `./output` |

## 🏗️ Architecture

### Core Components

```
flowgen/
├── __init__.py         # Click-based CLI interface with Rich styling
├── __main__.py         # Package entry point
├── runner.py           # Command execution and subcommand discovery
├── parser.py           # LLM interaction and JSON validation
├── translator.py       # JSON to WDL/Nextflow conversion
└── templates/          # Template files for output generation
```

### Workflow

1. **Command Execution**: Runs `tool --help` and `tool --version` to capture documentation
2. **Subcommand Discovery**: Uses regex patterns to find available subcommands
3. **LLM Processing**: Sends help text to Ollama with constrained prompts for JSON extraction
4. **Validation**: Validates JSON schema and parameter structure
5. **Translation**: Converts JSON to WDL/Nextflow task definitions
6. **Output Generation**: Creates organized directory structure with tasks and documentation

## 📦 Output Structure

```
output/
├── tool_WDL/                    # WDL format output
│   ├── README.md               # Documentation
│   ├── tool_command1.wdl       # Individual task files
│   ├── tool_command2.wdl
│   └── command1.json           # Original JSON responses
│
├── tool_NEXTFLOW/              # Nextflow format output
│   ├── main.nf                 # Main workflow
│   ├── nextflow.config         # Configuration
│   └── tests/                  # Test files
│
└── tool_help.txt               # Original help text
```

### Dependencies

- **click**: CLI framework
- **rich**: Enhanced terminal output
- **requests**: HTTP client for Ollama API
- **pathlib**: Path handling
- **json**: JSON processing
- **re**: Regular expressions

### Testing

```bash
# Test with pre-saved help text
python -m flowgen generate samtools --help-text output/samtools_help.txt
```

**Under development for the St. Jude Biohackathon 2025**