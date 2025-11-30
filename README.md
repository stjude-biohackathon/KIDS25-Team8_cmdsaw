# cmdsaw

**Automated CLI Help Parser and Workflow Task Generator**

`cmdsaw` is a tool that automatically analyzes command-line tools by parsing their `--help` output using Large Language Models (LLMs). It discovers subcommands recursively, extracts parameter information, and generates workflow task definitions ready for use in computational pipelines.

## What Does cmdsaw Do?

`cmdsaw` takes any command-line tool and:

1. **Discovers Commands**: Recursively finds all commands and subcommands by parsing `--help` output
2. **Extracts Metadata**: Uses LLMs to understand parameters, options, flags, and positional arguments
3. **Generates Workflows**: Creates WDL 1.2 task definitions with resource estimates
4. **Outputs Structured Data**: Produces JSON documentation of the entire command structure

This automation is meant to eliminate the tedious manual work of documenting CLI tools and writing workflow task wrappers.

## Features

### Intelligent Parsing

- **LLM-Powered**: Uses advanced language models to understand CLI help text
- **Recursive Discovery**: Automatically finds all subcommands and nested commands
- **Parameter Detection**: Identifies options, flags, positionals, types, and defaults
- **Resource Estimation**: Predicts CPU and memory requirements for WDL tasks
- **Automatic Container Usage**: Uses the BioContainers registry for container images/bioconda (Docker, Singularity (Apptainer), bioconda)

### Filtering and Optimization

- **Smart Filtering**: Excludes `--help` & `--version` options from workflow tasks...supposedly
- **Subcommand Detection**: Skips commands that are meaningless without subcommands
- **Cache Support**: Caches LLM responses to speed up repeated analyses

### Interactive Features

- **Automatic Double-Check**: Enabled by default - verifies and fixes parsed JSON against original help text
- **Human-in-the-loop Review**: Verify discovered subcommands before processing or final JSON prior to output generation
- **LLM-Assisted Fixes**: Request LLM to fix specific issues you identify
- **Multi-Provider Support**: Use local Ollama or free Google Gemini API. Will probably add OpenAI/Anthropic in the future, though the goal is to minimize reliance on cloud APIs and provide local capabilities.

## Requirements

### LLM Provider Options

`cmdsaw` supports two LLM providers:

#### 1. Ollama (Local, Default)

[Ollama](https://ollama.ai/) provides local LLM inference. No API keys or internet connection required for inference.

**Install Ollama:**
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

**Start Ollama:**
```bash
ollama serve
```

**Recommended Models:**

Based on our testing, the best performing models for CLI help parsing are:

- **`gemma3:12b`** - Excellent balance of speed and accuracy (default)
- **`deepseek-r1:14b`** - High accuracy, slightly slower

Pull a model before using cmdsaw:
```bash
ollama pull gemma3:12b
# or
ollama pull deepseek-r1:14b
```

Other models like `llama3.2`, `qwen3`, and `mistral` also work but may have varying accuracy.

#### 2. Google Gemini API (Cloud, Recommended for Complex Tools)

The Google Gemini API is **free** (with rate limits) and provides excellent accuracy for complex command-line tools.

**Advantages:**
- Free tier with generous limits (10 requests per minute, 250k tokens per minute, and 250 requests per day)
- No local GPU required
- Excellent accuracy on complex help text
- Faster for tools with many subcommands

**Setup:**
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set the environment variable:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```
3. Use the `--provider google` flag


**Recommended for:**
- Tools with 20+ subcommands
- Complex nested command structures (kubectl, docker, git)
- When local GPU resources are limited

## Installation

```bash
# Eventually...
# pip install cmdsaw
```

Or install from source:
```bash
git clone https://github.com/stjude-biohackathon/KIDS25-Team8_cmdsaw
cd KIDS25-Team8_cmdsaw
pip install -e .
```

## Quick Start

Analyze a command and generate WDL tasks:

```bash
cmdsaw --command samtools --model gemma3:12b
```

This will:
- Discover all samtools subcommands (view, sort, index, etc.)
- Parse their help text with the LLM
- Generate a JSON file with structured documentation
- Create WDL task definitions for each subcommand

## Usage

### Basic Usage

```bash
cmdsaw --command <tool-name> [OPTIONS]
```

### Common Options

- `--command <name>` - Command to analyze (required)
- `--model <name>` - Ollama model to use (default: gemma3:12b)
- `--output <file>` - Save JSON documentation to file
- `--wdl-out <file>` - Save WDL tasks to file
- `--max-depth <n>` - Maximum subcommand recursion depth (default: 1)
- `--concurrency <n>` - Parallel subcommand parsing (default: 4)
- `--subcommand-help-format <format>` - Format for subcommand help invocation (default: subcommand-help)
  - `subcommand-help` - Use format: `TOOL SUBCOMMAND --help` (e.g., `samtools view --help`)
  - `help-subcommand` - Use format: `TOOL --help SUBCOMMAND` (e.g., `samtools --help view`)

### Interactive Subcommand Review

Use `--review-subcommands` to manually verify and correct discovered subcommands:

```bash
cmdsaw --command kubectl --model gemma3:12b --review-subcommands
```

This opens an interactive interface where you can:
- **[c]** Confirm discovered subcommands
- **[a]** Add missing subcommands
- **[r]** Remove incorrect subcommands
- **[e]** Edit the complete list manually
- **[p]** Re-parse with emphasized LLM prompt

### JSON Review and Validation

#### Interactive JSON Review

Use `--review-json` to manually review and correct the final JSON output before saving (and WDL task generation):

```bash
cmdsaw --command samtools --model gemma3:12b --review-json
```

This opens an interactive interface where you can:
- **[a]** Accept the JSON as-is and continue
- **[v]** View the complete JSON output
- **[f]** Request the LLM to fix specific issues you identify
- **[e]** Exit without saving

When you select **[f]**, you can describe issues like:
- "Add missing default values for all options"
- "Fix the type of --threads to int"
- "Add descriptions for positional arguments"

#### Automatic LLM Double-Check (Enabled by Default)

**cmdsaw automatically verifies and corrects parsed JSON** by comparing it against the original help text. This happens by default before saving.

**What it does:**
- Compares parsed JSON against original help text
- Identifies missing or incorrect parameters
- Fixes type mismatches and missing descriptions
- Ensures all subcommands from help text are included
- Reports summary of any changes made

**To disable automatic verification:**
```bash
cmdsaw --command samtools --no-llm-double-check
```

**Recommended approach for complex tools:**
Use automatic verification with manual review:
```bash
cmdsaw --command kubectl --review-json
```
This will first automatically verify the JSON (default), then let you review it interactively.


## Output

### JSON Documentation

The JSON output contains complete structured information:

```json
{
  "schema_version": "1.0.0",
  "tool": {
    "command": "samtools",
    "version": "1.17",
    "subcommands": [
      {
        "name": "view",
        "path": "samtools view",
        "options": [...],
        "positionals": [...],
        "subcommands": []
      }
    ]
  }
}
```

### WDL Tasks

WDL 1.2 task definitions ready for use in workflows:

```wdl
version 1.2

task samtools_view {
    input {
        Int? cpu = 2
        Int? memory_gb = 4
        String? output
        File input_bam
    }
    command <<<
        samtools view \
            ~{if defined(output) then "--output " + output else ""} \
            ~{input_bam}
    >>>
    output {
        File result = select_first([output, "output.bam"])
    }
}
```

## Planned Features

### Nextflow Process Generation

Support for generating Nextflow process definitions is planned for a future release. This will complement the existing WDL support and enable cmdsaw to serve multiple workflow platforms.


## Troubleshooting

### Ollama Connection Issues

If you get connection errors:
1. Ensure Ollama is running: `ollama serve`
2. Check Ollama is accessible: `ollama list`
3. Verify the model is pulled: `ollama pull gemma2:12b`

### Incomplete Subcommand Discovery

If subcommands are missing:
1. Use `--review-subcommands` to manually verify
2. Try the **[p]** option to re-parse with emphasis

### Inaccurate Parameter Parsing

If parameters are missing or incorrect:
1. The automatic double-check (enabled by default) should fix most issues, but can also sometimes introduce them.
2. Use `--review-json` to manually review and request additional fixes.
3. Try a different model (e.g., `deepseek-r1:14b` for Ollama, or `gemini-2.0-flash-exp` for Google).
4. For complex tools, consider using Google Gemini API: `--provider google`.

### Google API Rate Limits

If you hit Google API rate limits (free tier: 10 requests/minute):
1. Reduce `--concurrency` to 1 or 2: `--concurrency 2`
2. The tool will automatically retry failed requests
3. For large tools, process in batches using `--max-depth 1` first
4. Consider upgrading to a paid tier for higher limits

### Slow Performance

To speed up analysis:
1. Increase `--concurrency`, especially if using an API (e.g., `--concurrency 4`)
2. Enable caching (enabled by default, disable with `--no-llm-cache`)
3. Use a smaller model like `llama3.2` for faster (but less accurate) results

## Contributing

Contributions are welcome! Please open issues or pull requests on GitHub.

## License

See LICENSE file for details.

## Citation

If you use cmdsaw in your research, please cite:

```
cmdsaw: Automated CLI Help Parser and Workflow Task Generator
St. Jude Children's Research Hospital Biohackathon 2025
https://github.com/stjude-biohackathon/KIDS25-Team8_cmdsaw
```
