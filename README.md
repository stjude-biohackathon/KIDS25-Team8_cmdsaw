# cmdsaw

LLM-only CLI help parser. Captures `--help` and `--version`, recurses into subcommands,
parses parameters with a structured-output LLM (Ollama via LangChain), and emits:
1) Structured JSON (Pydantic model)
2) WDL 1.2 tasks for each command and subcommand with resource estimates

Example:
```bash
cmdsaw --command samtools --model llama3.2:8b --output samtools.json --wdl-out samtools.wdl
```
