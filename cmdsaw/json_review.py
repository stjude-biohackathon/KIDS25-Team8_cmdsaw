from __future__ import annotations
import json
import click
from typing import Optional, Union, List, Dict, Any
from .parsing.schema import CmdSawResult, CommandDoc
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI


def display_json_summary(result: CmdSawResult) -> None:
    """
    Display a summary of the parsed JSON result.
    
    :param result: The parsed command result to display
    :type result: CmdSawResult
    :return: None
    :rtype: None
    """
    click.echo("\n" + "=" * 80)
    click.echo("JSON PARSING RESULT SUMMARY")
    click.echo("=" * 80)
    
    tool = result.tool
    click.echo(f"\nTool: {tool.command}")
    if tool.version:
        click.echo(f"Version: {tool.version}")
    
    click.echo(f"\nOptions: {len(tool.options)}")
    for opt in tool.options[:5]:  # Show first 5
        flag = opt.long or opt.short or "unknown"
        click.echo(f"  - {flag}: {opt.description or '(no description)'}")
    if len(tool.options) > 5:
        click.echo(f"  ... and {len(tool.options) - 5} more")
    
    click.echo(f"\nPositionals: {len(tool.positionals)}")
    for pos in tool.positionals[:3]:  # Show first 3
        click.echo(f"  - {pos.name}: {pos.description or '(no description)'}")
    if len(tool.positionals) > 3:
        click.echo(f"  ... and {len(tool.positionals) - 3} more")
    
    click.echo(f"\nSubcommands: {len(tool.subcommands)}")
    for subcmd in tool.subcommands[:10]:  # Show first 10
        click.echo(f"  - {subcmd.name} ({len(subcmd.options)} options, {len(subcmd.positionals)} positionals)")
    if len(tool.subcommands) > 10:
        click.echo(f"  ... and {len(tool.subcommands) - 10} more")
    
    click.echo(f"\nDiagnostics:")
    click.echo(f"  - Total commands visited: {result.diagnostics.visited_commands}")
    click.echo(f"  - Timeouts: {result.diagnostics.timeouts}")
    click.echo(f"  - LLM retries: {result.diagnostics.llm_retries}")
    click.echo(f"  - Version extracted: {result.diagnostics.version_extracted}")
    
    click.echo("=" * 80)


def review_json_interactive(result: CmdSawResult, model_name: str, provider: str, temperature: float, google_api_key: Optional[str], all_docs: List[CommandDoc]) -> CmdSawResult:
    """
    Allow user to interactively review and correct the JSON result.
    
    Displays a summary of the parsed result and prompts the user to:
    - Accept the result as-is
    - Request LLM to fix specific issues
    - View full JSON
    - Exit without saving
    
    :param result: The parsed command result to review
    :type result: CmdSawResult
    :param model_name: Model name for LLM corrections
    :type model_name: str
    :param provider: LLM provider ('ollama' or 'google')
    :type provider: str
    :param temperature: Model temperature
    :type temperature: float
    :param google_api_key: Google API key (if using Google provider)
    :type google_api_key: Optional[str]
    :param all_docs: All parsed command documents
    :type all_docs: List[CommandDoc]
    :return: Reviewed (and potentially corrected) result
    :rtype: CmdSawResult
    """
    while True:
        display_json_summary(result)
        
        click.echo("\nReview Options:")
        click.echo("  [a] Accept and continue")
        click.echo("  [v] View full JSON")
        click.echo("  [f] Request LLM to fix issues")
        click.echo("  [e] Exit without saving")
        
        choice = click.prompt("\nYour choice", type=click.Choice(['a', 'v', 'f', 'e'], case_sensitive=False))
        
        if choice.lower() == 'a':
            click.echo("✓ JSON accepted")
            return result
        
        elif choice.lower() == 'v':
            json_str = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
            click.echo("\n" + "=" * 80)
            click.echo("FULL JSON OUTPUT")
            click.echo("=" * 80)
            click.echo(json_str)
            click.echo("=" * 80)
        
        elif choice.lower() == 'f':
            issues = click.prompt("\nDescribe the issues you want the LLM to fix")
            click.echo(f"\nRequesting LLM to fix: {issues}")
            result = llm_fix_issues(result, model_name, provider, temperature, google_api_key, all_docs, issues)
            click.echo("✓ LLM has attempted fixes")
        
        elif choice.lower() == 'e':
            click.echo("Exiting without saving...")
            raise click.Abort()


def llm_fix_issues(result: CmdSawResult, model_name: str, provider: str, temperature: float, google_api_key: Optional[str], all_docs: List[CommandDoc], issues: str) -> CmdSawResult:
    """
    Use LLM to fix specific issues in the parsed result.
    
    :param result: The parsed command result to fix
    :type result: CmdSawResult
    :param model_name: Model name for LLM
    :type model_name: str
    :param provider: LLM provider ('ollama' or 'google')
    :type provider: str
    :param temperature: Model temperature
    :type temperature: float
    :param google_api_key: Google API key (if using Google provider)
    :type google_api_key: Optional[str]
    :param all_docs: All parsed command documents
    :type all_docs: List[CommandDoc]
    :param issues: Description of issues to fix
    :type issues: str
    :return: Fixed result
    :rtype: CmdSawResult
    """
    # Build model
    if provider == "google":
        if not google_api_key:
            raise ValueError("Google API key is required when using the 'google' provider")
        model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=google_api_key
        )
    elif provider == "ollama":
        model = ChatOllama(model=model_name, temperature=temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    # Create structured output model
    structured = model.with_structured_output(CmdSawResult)
    
    # Build prompt
    current_json = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
    
    system_prompt = """You are a JSON correction assistant. The user has identified issues with a parsed CLI command structure.
Your task is to fix these specific issues while preserving all other correct information.

Rules:
- Fix ONLY the issues described by the user
- Preserve all other data exactly as it was
- Return a complete, valid CmdSawResult JSON object
- Do not add or remove information that wasn't mentioned in the issues
"""
    
    user_prompt = f"""Current JSON:
{current_json}

Issues to fix:
{issues}

Please return the corrected JSON that addresses these specific issues."""
    
    try:
        corrected: CmdSawResult = structured.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        return corrected
    except Exception as e:
        click.echo(f"Warning: LLM fix failed: {e}")
        click.echo("Returning original result")
        return result


def llm_double_check(result: CmdSawResult, model_name: str, provider: str, temperature: float, google_api_key: Optional[str], all_docs: List[CommandDoc]) -> CmdSawResult:
    """
    Use LLM to automatically verify and correct the parsed result.
    
    This function performs an automatic quality check on the parsed result,
    comparing it against the original help text to identify and fix:
    - Missing parameters
    - Incorrect types
    - Missing descriptions
    - Structural issues
    
    :param result: The parsed command result to verify
    :type result: CmdSawResult
    :param model_name: Model name for LLM
    :type model_name: str
    :param provider: LLM provider ('ollama' or 'google')
    :type provider: str
    :param temperature: Model temperature
    :type temperature: float
    :param google_api_key: Google API key (if using Google provider)
    :type google_api_key: Optional[str]
    :param all_docs: All parsed command documents
    :type all_docs: List[CommandDoc]
    :return: Verified (and potentially corrected) result
    :rtype: CmdSawResult
    """
    click.echo("\n" + "=" * 80)
    click.echo("PERFORMING LLM DOUBLE-CHECK")
    click.echo("=" * 80)
    
    # Build model
    if provider == "google":
        if not google_api_key:
            raise ValueError("Google API key is required when using the 'google' provider")
        model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=google_api_key
        )
    elif provider == "ollama":
        model = ChatOllama(model=model_name, temperature=temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    # Create structured output model
    structured = model.with_structured_output(CmdSawResult)
    
    # Build prompt with original help text and current JSON
    current_json = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
    
    system_prompt = """You are a quality assurance assistant for CLI command parsing.
Your task is to verify and correct a parsed CLI command structure against the original help text.

Verification checklist:
1. Are all options and flags from the help text included?
2. Are parameter types correct (int, float, str, path, bool, choice)?
3. Are required vs optional parameters correctly identified?
4. Are default values captured?
5. Are positional arguments in the correct order?
6. Are subcommands correctly listed?
7. Are descriptions clear and accurate?

Rules:
- Compare the JSON against the original help text
- Fix any missing or incorrect information
- Add missing parameters that were in the help text
- Correct parameter types if they are wrong
- Ensure all subcommands from help text are listed
- Preserve correct information
- Return a complete, valid CmdSawResult JSON object
"""
    
    # Collect help texts
    help_texts = {}
    help_texts[result.tool.command] = result.tool.help_text
    for doc in all_docs[1:]:  # Skip root which is already in tool
        help_texts[doc.path] = doc.help_text
    
    help_text_summary = "\n\n".join([f"Command: {path}\nHelp Text:\n{text}" for path, text in list(help_texts.items())[:5]])  # Limit to first 5 to avoid token limits
    
    user_prompt = f"""Original help text(s):
{help_text_summary}

Current parsed JSON:
{current_json}

Please verify the JSON against the help text and return a corrected version if any issues are found.
If the JSON is correct, return it unchanged."""
    
    try:
        click.echo("Running verification with LLM...")
        verified: CmdSawResult = structured.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        click.echo("✓ LLM double-check complete")
        
        # Show summary of changes if any
        original_options = len(result.tool.options)
        verified_options = len(verified.tool.options)
        if original_options != verified_options:
            click.echo(f"  - Options changed: {original_options} → {verified_options}")
        
        original_positionals = len(result.tool.positionals)
        verified_positionals = len(verified.tool.positionals)
        if original_positionals != verified_positionals:
            click.echo(f"  - Positionals changed: {original_positionals} → {verified_positionals}")
        
        original_subcommands = len(result.tool.subcommands)
        verified_subcommands = len(verified.tool.subcommands)
        if original_subcommands != verified_subcommands:
            click.echo(f"  - Subcommands changed: {original_subcommands} → {verified_subcommands}")
        
        if (original_options == verified_options and 
            original_positionals == verified_positionals and 
            original_subcommands == verified_subcommands):
            click.echo("  - No changes needed")
        
        click.echo("=" * 80)
        return verified
        
    except Exception as e:
        click.echo(f"Warning: LLM double-check failed: {e}")
        click.echo("Returning original result")
        click.echo("=" * 80)
        return result
