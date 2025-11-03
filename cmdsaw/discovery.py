from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Mapping, Set, Tuple
from .parsing.schema import CommandDoc, ToolDoc, CmdSawResult, ParseDiagnostics
from .parsing.llm_parser import parse_command_help
from .parsing.cache import ParseCache
from .constants import DEFAULT_TIMEOUT, DEFAULT_MAX_DEPTH, DEFAULT_CONCURRENCY, SCHEMA_VERSION
from .runner import try_help, try_version, now_iso
from .utils import which_or_raise

def build_tree(
    *,
    root_cmd: str,
    model_name: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_depth: int = DEFAULT_MAX_DEPTH,
    env: Optional[Mapping[str,str]] = None,
    cwd: Optional[str] = None,
    help_flags: tuple[str,...] = ("--help","-h","help"),
    concurrency: int = DEFAULT_CONCURRENCY,
    use_cache: bool = True,
) -> Tuple[CmdSawResult, List[CommandDoc]]:
    """
    Build a complete documentation tree for a command and its subcommands.

    Recursively discovers and parses help text for a root command and all its
    subcommands using an LLM. Supports concurrent parsing and result caching.

    :param root_cmd: Name of the root command to inspect
    :type root_cmd: str
    :param model_name: Ollama model name to use for parsing
    :type model_name: str
    :param timeout: Per-invocation timeout in seconds
    :type timeout: int
    :param max_depth: Maximum recursion depth for subcommands
    :type max_depth: int
    :param env: Optional environment variables for command execution
    :type env: Optional[Mapping[str,str]]
    :param cwd: Optional working directory for command execution
    :type cwd: Optional[str]
    :param help_flags: Tuple of help flags to try in order
    :type help_flags: tuple[str,...]
    :param concurrency: Maximum number of parallel subcommand parses
    :type concurrency: int
    :param use_cache: Whether to use on-disk LLM parse cache
    :type use_cache: bool
    :return: Tuple of (complete result, list of all command docs)
    :rtype: Tuple[CmdSawResult, List[CommandDoc]]
    """
    print(f"Resolving command path for: {root_cmd}")
    bin_path = which_or_raise(root_cmd)
    print(f"  Resolved to: {bin_path}")
    
    diagnostics = ParseDiagnostics()
    cache = ParseCache() if use_cache else None
    cache_getset = (cache.get, cache.set) if cache else None
    if use_cache:
        print(f"LLM cache enabled at: {cache.root}")
    else:
        print("LLM cache disabled")

    help_text, _ = try_help([bin_path], help_flags, timeout=timeout, env=env, cwd=cwd)
    version = try_version([bin_path], timeout=timeout, env=env, cwd=cwd)
    diagnostics.version_extracted = bool(version)

    print(f"\nParsing root command with LLM...")
    root_doc: CommandDoc = parse_command_help(
        model_name=model_name,
        command_path=root_cmd,
        help_text=help_text,
        retries=2,
        cache_getset=cache_getset,
    )
    visited: Set[str] = set([root_doc.path])
    queue: List[tuple[str,int]] = [(name, 1) for name in root_doc.subcommands]
    
    if root_doc.subcommands:
        print(f"Discovered {len(root_doc.subcommands)} subcommand(s) in root: {', '.join(root_doc.subcommands)}")
    else:
        print("No subcommands discovered in root")

    subdocs: Dict[str, CommandDoc] = {}

    def process_one(path: str, depth: int) -> tuple[str, CommandDoc]:
        print(f"  Processing subcommand: {path} (depth={depth})")
        parts = path.split()
        bin_ = which_or_raise(parts[0])
        help_t, _ = try_help([bin_] + parts[1:], help_flags, timeout=timeout, env=env, cwd=cwd)
        doc = parse_command_help(
            model_name=model_name,
            command_path=path,
            help_text=help_t,
            retries=2,
            cache_getset=cache_getset,
        )
        if doc.subcommands:
            print(f"    Found {len(doc.subcommands)} sub-subcommand(s): {', '.join(doc.subcommands)}")
        return path, doc

    print(f"\nProcessing subcommands (max_depth={max_depth}, concurrency={concurrency})...")
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        while queue:
            futures = []
            while queue and len(futures) < concurrency:
                name, depth = queue.pop(0)
                full_path = f"{root_cmd} {name}"
                if full_path in visited or depth > max_depth:
                    continue
                visited.add(full_path)
                futures.append(ex.submit(process_one, full_path, depth))
            for fut in as_completed(futures):
                path, doc = fut.result()
                subdocs[path] = doc
                diagnostics.visited_commands += 1
                for child in doc.subcommands:
                    queue.append((f"{path} {child}", path.count(" ") + 1))

    tool = ToolDoc(
        command=root_cmd,
        version=version,
        help_text=help_text,
        invocation=[bin_path],
        subcommands=[subdocs[k] for k in sorted(subdocs.keys()) if k.count(" ")==1],
        captured_at=now_iso(),
    )
    result = CmdSawResult(schema_version=SCHEMA_VERSION, tool=tool, diagnostics=diagnostics)
    all_docs: List[CommandDoc] = [root_doc] + [subdocs[k] for k in sorted(subdocs.keys())]
    return result, all_docs
