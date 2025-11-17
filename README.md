# cmdsaw

**Automated CLI Help Parser and Workflow Task Generator**

`cmdsaw` is a tool that automatically analyzes command-line tools by parsing their `--help` output using Large Language Models (LLMs). It discovers subcommands recursively, extracts parameter information, and generates workflow task definitions ready for use in computational pipelines.

## What Does cmdsaw Do?

`cmdsaw` takes any command-line tool and:

1. **Discovers Commands**: Recursively finds all commands and subcommands by parsing `--help` output
2. **Extracts Metadata**: Uses LLMs to understand parameters, options, flags, and positional arguments
3. **Generates Workflows**: Creates WDL 1.2 task definitions with resource estimates
4. **Outputs Structured Data**: Produces JSON documentation of the entire command structure

This automation eliminates the tedious manual work of documenting CLI tools and writing workflow task wrappers.

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
- ✅ Free tier with generous limits
- ✅ No local GPU required
- ✅ Excellent accuracy on complex help text
- ✅ Faster for tools with many subcommands

**Setup:**
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set the environment variable:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```
3. Use the `--provider google` flag

**Rate Limits:**
- Free tier: 15 requests per minute, 1500 requests per day
- For large tools with many subcommands, you may need to adjust `--concurrency` to avoid hitting rate limits

**Example Usage:**
```bash
# Using Google Gemini for a complex tool
cmdsaw --command kubectl \
    --provider google \
    --model gemini-2.0-flash-exp \
    --concurrency 2 \
    --max-depth 2
```

**Recommended for:**
- Tools with 20+ subcommands
- Complex nested command structures (kubectl, docker, git)
- When local GPU resources are limited
- Production workflows requiring highest accuracy

## Installation

```bash
pip install cmdsaw
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
cmdsaw --command samtools --model gemma2:12b --output samtools.json --wdl-out samtools.wdl
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
- `--model <name>` - Ollama model to use (default: llama3.2)
- `--output <file>` - Save JSON documentation to file
- `--wdl-out <file>` - Save WDL tasks to file
- `--max-depth <n>` - Maximum subcommand recursion depth (default: 3)
- `--concurrency <n>` - Parallel subcommand parsing (default: 4)

### Interactive Subcommand Review

Use `--review-subcommands` to manually verify and correct discovered subcommands:

```bash
cmdsaw --command kubectl --model gemma2:12b --review-subcommands
```

This opens an interactive interface where you can:
- **[c]** Confirm discovered subcommands
- **[a]** Add missing subcommands
- **[r]** Remove incorrect subcommands
- **[e]** Edit the complete list manually
- **[p]** Re-parse with emphasized LLM prompt

### JSON Review and Validation

#### Interactive JSON Review

Use `--review-json` to manually review and correct the final JSON output before saving:

```bash
cmdsaw --command samtools --model gemma2:12b --review-json
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

**For complex tools with many subcommands, consider using Google Gemini API:**
```bash
cmdsaw --command docker \
    --provider google \
    --model gemini-2.0-flash-exp \
    --concurrency 2 \
    --review-json
```

### Advanced Options

```bash
cmdsaw --command docker \
    --model deepseek-r1:14b \
    --output docker.json \
    --wdl-out docker.wdl \
    --max-depth 2 \
    --concurrency 8 \
    --review-subcommands
```

**For complex tools, use Google Gemini API for best results:**
```bash
cmdsaw --command kubectl \
    --provider google \
    --model gemini-2.0-flash-exp \
    --max-depth 3 \
    --concurrency 2 \
    --review-json
```

**Note:** The free Google API tier has rate limits (15 requests/minute). Reduce `--concurrency` if you hit limits.
```

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

**Note:** The `--help` parameter is automatically excluded from generated tasks as it's meant for interactive use only.

## Features

### Intelligent Parsing

- **LLM-Powered**: Uses advanced language models to understand CLI help text
- **Recursive Discovery**: Automatically finds all subcommands and nested commands
- **Parameter Detection**: Identifies options, flags, positionals, types, and defaults
- **Resource Estimation**: Predicts CPU and memory requirements for WDL tasks

### Filtering and Optimization

- **Smart Filtering**: Excludes `--help` options from workflow tasks
- **Subcommand Detection**: Skips commands that are meaningless without subcommands
- **Cache Support**: Caches LLM responses to speed up repeated analyses

### Interactive Features

- **Automatic Double-Check**: Enabled by default - verifies and fixes parsed JSON against original help text
- **Human Review**: Verify discovered subcommands before processing
- **JSON Review**: Manually review and correct final JSON output before saving
- **LLM-Assisted Fixes**: Request LLM to fix specific issues you identify
- **Re-parsing**: Request LLM to re-analyze with emphasis on completeness
- **Progress Messages**: Clear console output showing what's happening
- **Multi-Provider Support**: Use local Ollama or free Google Gemini API

## Planned Features

### Nextflow Process Generation

Support for generating Nextflow process definitions is planned for a future release. This will complement the existing WDL support and enable cmdsaw to serve multiple workflow platforms.

## Examples

### Analyze a Simple Tool

```bash
cmdsaw --command grep --model gemma2:12b --output grep.json
```

### Analyze a Complex Tool with Many Subcommands

**Using Ollama (local):**
```bash
cmdsaw --command kubectl \
    --model deepseek-r1:14b \
    --max-depth 3 \
    --concurrency 8 \
    --review-subcommands \
    --output kubectl.json \
    --wdl-out kubectl.wdl
```

**Using Google Gemini (recommended for complex tools):**
```bash
cmdsaw --command kubectl \
    --provider google \
    --model gemini-2.0-flash-exp \
    --max-depth 3 \
    --concurrency 2 \
    --review-json \
    --output kubectl.json \
    --wdl-out kubectl.wdl
```

### Analyze with Interactive Review

```bash
cmdsaw --command samtools \
    --model gemma2:12b \
    --review-json \
    --output samtools.json
```

This will:
1. Parse samtools and all subcommands
2. Automatically verify and fix the JSON (default behavior)
3. Let you review and make additional corrections
4. Save the final verified JSON

### Disable Automatic Verification

If you want to skip the automatic double-check (not recommended):
```bash
cmdsaw --command simple-tool \
    --no-llm-double-check \
    --output output.json
```

### Analyze with Custom Environment

```bash
cmdsaw --command myapp \
    --model gemma2:12b \
    --workdir /path/to/app \
    --env PATH=/custom/path \
    --output myapp.json
```

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
1. The automatic double-check (enabled by default) should fix most issues
2. Use `--review-json` to manually review and request additional fixes
3. Try a different model (e.g., `deepseek-r1:14b` for Ollama, or `gemini-2.0-flash-exp` for Google)
4. For complex tools, consider using Google Gemini API: `--provider google`

### Google API Rate Limits

If you hit Google API rate limits (free tier: 15 requests/minute):
1. Reduce `--concurrency` to 1 or 2: `--concurrency 2`
2. The tool will automatically retry failed requests
3. For large tools, process in batches using `--max-depth 1` first
4. Consider upgrading to a paid tier for higher limits

### Slow Performance

To speed up analysis:
1. Increase `--concurrency` (e.g., `--concurrency 16`)
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
