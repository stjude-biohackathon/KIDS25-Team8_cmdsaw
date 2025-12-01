from __future__ import annotations
import time
import os
import click
from .constants import DEFAULT_MODEL, DEFAULT_TIMEOUT, DEFAULT_MAX_DEPTH, DEFAULT_CONCURRENCY, DEFAULT_TEMPERATURE, DEFAULT_PROVIDER, DEFAULT_SUBCOMMAND_HELP_FORMAT
from .discovery import build_tree
from .serialize import write_json
from .wdl import emit_wdl
from .json_review import review_json_interactive, llm_double_check as perform_llm_double_check
from .parsing.edam_mappings import enrich_with_edam

@click.command()
@click.option("--command", required=True, help="Root command to inspect, e.g. samtools")
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Model to use (format depends on provider)")
@click.option("--provider", default=DEFAULT_PROVIDER, show_default=True, type=click.Choice(["ollama", "google"]), help="LLM provider (ollama or google)")
@click.option("--temperature", default=DEFAULT_TEMPERATURE, show_default=True, type=float, help="Model temperature (0.0 = deterministic, higher = more random)")
@click.option("--google-api-key", help="Google API key (or set GOOGLE_API_KEY environment variable)")
@click.option("--output", type=click.Path(dir_okay=False, writable=True), help="Write JSON to this file")
@click.option("--wdl-out", type=click.Path(dir_okay=False, writable=True), help="Write WDL tasks to this file")
@click.option("--timeout", default=DEFAULT_TIMEOUT, show_default=True, help="Per-invocation timeout (s)")
@click.option("--max-depth", "max_depth", default=DEFAULT_MAX_DEPTH, show_default=True, help="Max subcommand recursion depth")
@click.option("--concurrency", default=DEFAULT_CONCURRENCY, show_default=True, help="Max parallel subcommand parses")
@click.option("--help-flags", default="--help -h", show_default=True, help="Help flags to try in order")
@click.option("--subcommand-help-format", default=DEFAULT_SUBCOMMAND_HELP_FORMAT, show_default=True, type=click.Choice(["subcommand-help", "help-subcommand", "tool-subcommand", "subcommand-only"]), help="Format for subcommand help invocation")
@click.option("--workdir", type=click.Path(file_okay=False, exists=True), help="Working directory")
@click.option("--env", multiple=True, help="Extra env vars: KEY=VAL", metavar="KEY=VAL")
@click.option("--no-llm-cache", is_flag=True, default=False, help="Disable on-disk LLM parse cache")
@click.option("--review-subcommands", is_flag=True, default=False, help="Enable interactive review of discovered subcommands")
@click.option("--review-json", is_flag=True, default=False, help="Enable interactive review of JSON output before saving")
@click.option("--llm-check", is_flag=True, default=False, help="Enable automatic LLM verification of parsed JSON")
@click.option("--piped", is_flag=True, default=False, help="Enable piped output support for all output parameters with auto-generated filenames")
def main(command, model, provider, temperature, google_api_key, output, wdl_out, timeout, max_depth, concurrency, help_flags, subcommand_help_format, workdir, env, no_llm_cache, review_subcommands, review_json, llm_check, piped):
    """
    Parse CLI help text using LLM and emit structured documentation.

    Main entry point for the cmdsaw CLI tool. Parses a command's help text
    recursively for all subcommands using an LLM, then outputs structured JSON
    and optionally WDL task definitions.

    :param command: Root command to inspect (e.g., 'samtools')
    :type command: str
    :param model: Model name to use for parsing (format depends on provider)
    :type model: str
    :param provider: LLM provider to use ('ollama' or 'google')
    :type provider: str
    :param temperature: Model temperature (0.0 = deterministic, higher = more random)
    :type temperature: float
    :param google_api_key: Google API key (optional, can use GOOGLE_API_KEY env var)
    :type google_api_key: str | None
    :param output: Optional file path to write JSON output
    :type output: str | None
    :param wdl_out: Optional file path to write WDL task definitions
    :type wdl_out: str | None
    :param timeout: Per-invocation timeout in seconds
    :type timeout: int
    :param max_depth: Maximum subcommand recursion depth
    :type max_depth: int
    :param concurrency: Maximum parallel subcommand parses
    :type concurrency: int
    :param help_flags: Space-separated help flags to try
    :type help_flags: str
    :param subcommand_help_format: Format for subcommand help invocation ('subcommand-help', 'help-subcommand', 'tool-subcommand', or 'subcommand-only')
    :type subcommand_help_format: str
    :param workdir: Optional working directory for command execution
    :type workdir: str | None
    :param env: Tuple of KEY=VAL environment variable strings
    :type env: tuple[str, ...]
    :param no_llm_cache: Whether to disable LLM parse cache
    :type no_llm_cache: bool
    :param review_subcommands: Whether to enable interactive review of subcommands
    :type review_subcommands: bool
    :param review_json: Whether to enable interactive review of JSON output
    :type review_json: bool
    :param llm_check: Whether to enable automatic LLM verification of JSON
    :type llm_check: bool
    :param piped: Whether to enable piped output support for all output parameters
    :type piped: bool
    :return: None
    :rtype: None
    """
    start_time = time.time()
    
    # Validate Google API key if using Google provider
    if provider == "google":
        api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise click.ClickException(
                "Google API key is required when using the 'google' provider. "
                "Please provide it via --google-api-key or set the GOOGLE_API_KEY environment variable."
            )
        google_api_key = api_key
    
    click.echo(f"Starting cmdsaw for command: {command}")
    click.echo(f"Using provider: {provider}")
    click.echo(f"Using model: {model}")
    click.echo(f"Temperature: {temperature}")
    click.echo(f"Max depth: {max_depth}, Concurrency: {concurrency}")
    env_map = {}
    for kv in env:
        if "=" in kv:
            k, v = kv.split("=", 1)
            env_map[k] = v
    flags = tuple(x for x in help_flags.split() if x)

    click.echo(f"Building command tree...")
    result, all_docs = build_tree(
        root_cmd=command,
        model_name=model,
        provider=provider,
        temperature=temperature,
        google_api_key=google_api_key,
        timeout=timeout,
        max_depth=max_depth,
        env=env_map or None,
        cwd=workdir,
        help_flags=flags,
        concurrency=concurrency,
        use_cache=not no_llm_cache,
        review_subcommands=review_subcommands,
        subcommand_help_format=subcommand_help_format,
    )

    click.echo(f"\nFound {len(all_docs)} total commands (including root)")
    click.echo(f"Found {len(all_docs) - 1} subcommands")
    
    if len(all_docs) > 1:
        click.echo("\nAll discovered subcommands:")
        for doc in all_docs[1:]:  # Skip root command
            click.echo(f"  - {doc.path}")
    
    # Enrich with EDAM format information
    click.echo("\nEnriching with EDAM format information...")
    enrich_with_edam(result.tool)
    for doc in all_docs:
        enrich_with_edam(doc)
    
    # Apply piped output configuration if specified
    if piped:
        click.echo(f"\nEnabling piped output for all commands...")
        
        # Apply to all_docs (all subcommands)
        for doc in all_docs:
            doc.piped_output = True
            click.echo(f"  - Enabled piped output for {doc.path}")
        
        # Also update the result.tool
        result.tool.piped_output = True
        
        # Update subcommands in result.tool
        for subcmd in result.tool.subcommands:
            subcmd.piped_output = True
    
    # Apply LLM double-check if enabled
    if llm_check:
        result = perform_llm_double_check(result, model, provider, temperature, google_api_key, all_docs)
    
    # Apply interactive review if requested
    if review_json:
        result = review_json_interactive(result, model, provider, temperature, google_api_key, all_docs)
    
    # Set default output filenames if not provided
    version = result.tool.version or "unknown"
    if not output:
        output = f"{command}_{version}.json"
    if not wdl_out:
        wdl_out = f"{command}_{version}.wdl"
    
    click.echo(f"\nWriting JSON output to: {output}")
    write_json(output, result)
    click.echo(f"Generating WDL tasks to: {wdl_out}")
    emit_wdl(tool_name=command, docs=all_docs, out_path=wdl_out, model_name=model, provider=provider, temperature=temperature, google_api_key=google_api_key, container_info=result.tool.container_info)
    
    elapsed_time = time.time() - start_time
    click.echo(f"\nTotal execution time: {elapsed_time:.2f} seconds")

