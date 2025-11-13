from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Mapping, Set, Tuple
from .parsing.schema import CommandDoc, ToolDoc, CmdSawResult, ParseDiagnostics
from .parsing.llm_parser import parse_command_help
from .parsing.cache import ParseCache
from .constants import DEFAULT_TIMEOUT, DEFAULT_MAX_DEPTH, DEFAULT_CONCURRENCY, SCHEMA_VERSION
from .runner import try_help, try_version, now_iso
from .utils import which_or_raise

def _review_subcommands(discovered: List[str], root_cmd: str, help_text: str = None, model_name: str = None, provider: str = "ollama", temperature: float = 0.0, google_api_key: str = None, cache_getset: tuple = None) -> List[str]:
    """
    Interactive review of discovered subcommands.
    
    Allows user to confirm, add missing, remove extraneous subcommands, or
    re-parse with LLM using an emphasized prompt for better subcommand detection.
    
    :param discovered: List of discovered subcommand names
    :type discovered: List[str]
    :param root_cmd: Root command name
    :type root_cmd: str
    :param help_text: Original help text for re-parsing
    :type help_text: str
    :param model_name: LLM model name for re-parsing
    :type model_name: str
    :param provider: LLM provider to use ('ollama' or 'google')
    :type provider: str
    :param temperature: Model temperature for re-parsing
    :type temperature: float
    :param google_api_key: Google API key for re-parsing
    :type google_api_key: str
    :param cache_getset: Cache functions tuple for re-parsing
    :type cache_getset: tuple
    :return: Reviewed and modified list of subcommands
    :rtype: List[str]
    """
    print(f"\n{'='*60}")
    print(f"SUBCOMMAND REVIEW for '{root_cmd}'")
    print(f"{'='*60}")
    print(f"\nDiscovered {len(discovered)} subcommand(s):")
    for i, subcmd in enumerate(discovered, 1):
        print(f"  {i}. {subcmd}")
    
    print(f"\nOptions:")
    print(f"  [c] Confirm and continue with these subcommands")
    print(f"  [a] Add missing subcommands")
    print(f"  [r] Remove extraneous subcommands")
    print(f"  [e] Edit the full list manually")
    if help_text and model_name:
        print(f"  [p] Re-parse with LLM (emphasize subcommand discovery)")
    
    while True:
        prompt_choices = "c/a/r/e/p" if help_text and model_name else "c/a/r/e"
        choice = input(f"\nYour choice [{prompt_choices}]: ").strip().lower()
        
        if choice == 'c':
            print(f"Confirmed. Proceeding with {len(discovered)} subcommand(s).")
            return discovered
        
        elif choice == 'a':
            print(f"\nEnter subcommands to add (comma-separated, or press Enter to cancel):")
            additions = input("> ").strip()
            if additions:
                new_subcmds = [s.strip() for s in additions.split(',') if s.strip()]
                discovered.extend(new_subcmds)
                print(f"Added {len(new_subcmds)} subcommand(s).")
                print(f"Current list: {', '.join(discovered)}")
            else:
                print("No subcommands added.")
        
        elif choice == 'r':
            print(f"\nCurrent subcommands:")
            for i, subcmd in enumerate(discovered, 1):
                print(f"  {i}. {subcmd}")
            print(f"\nEnter numbers to remove (comma-separated, or press Enter to cancel):")
            removals = input("> ").strip()
            if removals:
                try:
                    indices = [int(x.strip()) - 1 for x in removals.split(',') if x.strip()]
                    to_remove = [discovered[i] for i in indices if 0 <= i < len(discovered)]
                    for subcmd in to_remove:
                        discovered.remove(subcmd)
                    print(f"Removed {len(to_remove)} subcommand(s).")
                    print(f"Current list: {', '.join(discovered)}")
                except (ValueError, IndexError) as e:
                    print(f"Invalid input: {e}. Please try again.")
            else:
                print("No subcommands removed.")
        
        elif choice == 'e':
            print(f"\nEnter the complete list of subcommands (comma-separated):")
            print(f"Current: {', '.join(discovered)}")
            new_list = input("> ").strip()
            if new_list:
                discovered = [s.strip() for s in new_list.split(',') if s.strip()]
                print(f"Updated to {len(discovered)} subcommand(s): {', '.join(discovered)}")
            else:
                print("No changes made.")
        
        elif choice == 'p':
            if not help_text or not model_name:
                print(f"Re-parsing not available (missing help text or model name).")
                continue
            
            print(f"\nRe-parsing with LLM using emphasized prompt for subcommand discovery...")
            print(f"This will invoke the model again with special emphasis on finding ALL subcommands.")
            
            # Import here to avoid circular dependency
            from .parsing.llm_parser import parse_command_help_with_emphasis
            
            try:
                reparsed_doc = parse_command_help_with_emphasis(
                    model_name=model_name,
                    provider=provider,
                    temperature=temperature,
                    google_api_key=google_api_key,
                    command_path=root_cmd,
                    help_text=help_text,
                    retries=2,
                    cache_getset=None,  # Don't use cache for emphasized re-parse
                )
                
                if reparsed_doc.subcommands:
                    discovered = list(reparsed_doc.subcommands)
                    print(f"Re-parsing complete. Found {len(discovered)} subcommand(s): {', '.join(discovered)}")
                else:
                    print(f"Re-parsing complete. No subcommands found.")
            except Exception as e:
                print(f"Re-parsing failed: {e}")
                print(f"Keeping original list.")
        
        else:
            valid_choices = "c, a, r, e, p" if help_text and model_name else "c, a, r, or e"
            print(f"Invalid choice. Please enter {valid_choices}.")
    
    return discovered

def build_tree(
    *,
    root_cmd: str,
    model_name: str,
    provider: str = "ollama",
    temperature: float = 0.0,
    google_api_key: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_depth: int = DEFAULT_MAX_DEPTH,
    env: Optional[Mapping[str,str]] = None,
    cwd: Optional[str] = None,
    help_flags: tuple[str,...] = ("--help","-h","help"),
    concurrency: int = DEFAULT_CONCURRENCY,
    use_cache: bool = True,
    review_subcommands: bool = False,
) -> Tuple[CmdSawResult, List[CommandDoc]]:
    """
    Build a complete documentation tree for a command and its subcommands.

    Recursively discovers and parses help text for a root command and all its
    subcommands using an LLM. Supports concurrent parsing and result caching.

    :param root_cmd: Name of the root command to inspect
    :type root_cmd: str
    :param model_name: Model name to use for parsing
    :type model_name: str
    :param provider: LLM provider to use ('ollama' or 'google')
    :type provider: str
    :param temperature: Model temperature (0.0 = deterministic)
    :type temperature: float
    :param google_api_key: Google API key (required for Google provider)
    :type google_api_key: Optional[str]
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
    :param review_subcommands: Whether to enable interactive review of subcommands
    :type review_subcommands: bool
    :return: Tuple of (complete result, list of all command docs)
    :rtype: Tuple[CmdSawResult, List[CommandDoc]]
    """
    print(f"Resolving command path for: {root_cmd}")
    bin_path = which_or_raise(root_cmd)
    print(f"  Resolved to: {bin_path}")
    diagnostics = ParseDiagnostics()
    cache = ParseCache() if use_cache else None
    cache_getset = (cache.get, cache.set) if cache else None
    if cache:
        print(f"LLM cache enabled at: {cache.root}")
    else:
        print("LLM cache disabled")

    help_text, _ = try_help([bin_path], help_flags, timeout=timeout, env=env, cwd=cwd)
    version = try_version([bin_path], timeout=timeout, env=env, cwd=cwd)
    diagnostics.version_extracted = bool(version)

    print(f"\nParsing root command with LLM...")
    root_doc: CommandDoc = parse_command_help(
        model_name=model_name,
        provider=provider,
        temperature=temperature,
        google_api_key=google_api_key,
        command_path=root_cmd,
        help_text=help_text,
        retries=2,
        cache_getset=cache_getset,
    )
    visited: Set[str] = set([root_doc.path])
    
    # Handle subcommand review if enabled
    subcommands_to_process = list(root_doc.subcommands)
    if root_doc.subcommands:
        print(f"Discovered {len(root_doc.subcommands)} subcommand(s) in root: {', '.join(root_doc.subcommands)}")
    else:
        print("No subcommands discovered in root")
    
    if review_subcommands:
        subcommands_to_process = _review_subcommands(
            subcommands_to_process, 
            root_cmd,
            help_text=help_text,
            model_name=model_name,
            provider=provider,
            temperature=temperature,
            google_api_key=google_api_key,
            cache_getset=cache_getset
        )
    
    queue: List[tuple[str,int]] = [(name, 1) for name in subcommands_to_process]

    subdocs: Dict[str, CommandDoc] = {}

    def process_one(path: str, depth: int) -> tuple[str, CommandDoc]:
        print(f"  Processing subcommand: {path} (depth={depth})")
        parts = path.split()
        bin_ = which_or_raise(parts[0])
        help_t, _ = try_help([bin_] + parts[1:], help_flags, timeout=timeout, env=env, cwd=cwd)
        doc = parse_command_help(
            model_name=model_name,
            provider=provider,
            temperature=temperature,
            google_api_key=google_api_key,
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
        options=root_doc.options,
        positionals=root_doc.positionals,
        subcommands=[subdocs[k] for k in sorted(subdocs.keys()) if k.count(" ")==1],
        captured_at=now_iso(),
    )
    result = CmdSawResult(schema_version=SCHEMA_VERSION, tool=tool, diagnostics=diagnostics)
    all_docs: List[CommandDoc] = [root_doc] + [subdocs[k] for k in sorted(subdocs.keys())]
    return result, all_docs
