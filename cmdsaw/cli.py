from __future__ import annotations
import click
from .constants import DEFAULT_MODEL, DEFAULT_TIMEOUT, DEFAULT_MAX_DEPTH, DEFAULT_CONCURRENCY
from .discovery import build_tree
from .serialize import to_json, write_json
from .wdl import emit_wdl

@click.command()
@click.option("--command", required=True, help="Root command to inspect, e.g. samtools")
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Ollama model to use")
@click.option("--output", type=click.Path(dir_okay=False, writable=True), help="Write JSON to this file")
@click.option("--wdl-out", type=click.Path(dir_okay=False, writable=True), help="Write WDL tasks to this file")
@click.option("--timeout", default=DEFAULT_TIMEOUT, show_default=True, help="Per-invocation timeout (s)")
@click.option("--max-depth", "max_depth", default=DEFAULT_MAX_DEPTH, show_default=True, help="Max subcommand recursion depth")
@click.option("--concurrency", default=DEFAULT_CONCURRENCY, show_default=True, help="Max parallel subcommand parses")
@click.option("--help-flags", default="--help -h", show_default=True, help="Help flags to try in order")
@click.option("--workdir", type=click.Path(file_okay=False, exists=True), help="Working directory")
@click.option("--env", multiple=True, help="Extra env vars: KEY=VAL", metavar="KEY=VAL")
@click.option("--no-llm-cache", is_flag=True, default=False, help="Disable on-disk LLM parse cache")
def main(command, model, output, wdl_out, timeout, max_depth, concurrency, help_flags, workdir, env, no_llm_cache):
    env_map = {}
    for kv in env:
        if "=" in kv:
            k, v = kv.split("=", 1)
            env_map[k] = v
    flags = tuple(x for x in help_flags.split() if x)

    result, all_docs = build_tree(
        root_cmd=command,
        model_name=model,
        timeout=timeout,
        max_depth=max_depth,
        env=env_map or None,
        cwd=workdir,
        help_flags=flags,
        concurrency=concurrency,
        use_cache=not no_llm_cache,
    )

    if output:
        write_json(output, result)
    if wdl_out:
        emit_wdl(tool_name=command, docs=all_docs, out_path=wdl_out, model_name=model)

    click.echo(to_json(result))
