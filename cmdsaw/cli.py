from __future__ import annotations
import time
import os
import click
from .constants import DEFAULT_MODEL, DEFAULT_TIMEOUT, DEFAULT_MAX_DEPTH, DEFAULT_CONCURRENCY, DEFAULT_TEMPERATURE, DEFAULT_PROVIDER
from .discovery import build_tree
from .serialize import to_json, write_json
from .wdl import emit_wdl

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
@click.option("--workdir", type=click.Path(file_okay=False, exists=True), help="Working directory")
@click.option("--env", multiple=True, help="Extra env vars: KEY=VAL", metavar="KEY=VAL")
@click.option("--no-llm-cache", is_flag=True, default=False, help="Disable on-disk LLM parse cache")
@click.option("--review-subcommands", is_flag=True, default=False, help="Enable interactive review of discovered subcommands")
def main(command, model, provider, temperature, google_api_key, output, wdl_out, timeout, max_depth, concurrency, help_flags, workdir, env, no_llm_cache, review_subcommands):
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
    :param workdir: Optional working directory for command execution
    :type workdir: str | None
    :param env: Tuple of KEY=VAL environment variable strings
    :type env: tuple[str, ...]
    :param no_llm_cache: Whether to disable LLM parse cache
    :type no_llm_cache: bool
    :param review_subcommands: Whether to enable interactive review of subcommands
    :type review_subcommands: bool
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
    )

    click.echo(f"\nFound {len(all_docs)} total commands (including root)")
    click.echo(f"Found {len(all_docs) - 1} subcommands")
    
    if len(all_docs) > 1:
        click.echo("\nAll discovered subcommands:")
        for doc in all_docs[1:]:  # Skip root command
            click.echo(f"  - {doc.path}")
    
    # Set default output filenames if not provided
    version = result.tool.version or "unknown"
    if not output:
        output = f"{command}_{version}.json"
    if not wdl_out:
        wdl_out = f"{command}_{version}.wdl"
    
    click.echo(f"\nWriting JSON output to: {output}")
    write_json(output, result)
    click.echo(f"Generating WDL tasks to: {wdl_out}")
    emit_wdl(tool_name=command, docs=all_docs, out_path=wdl_out, model_name=model)
    
    elapsed_time = time.time() - start_time
    click.echo(f"\nTotal execution time: {elapsed_time:.2f} seconds")

