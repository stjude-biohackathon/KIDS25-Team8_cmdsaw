from __future__ import annotations
from typing import Optional, Tuple
from pydantic import ValidationError
from .schema import CommandDoc
from .prompts import SYSTEM_PROMPT, FEWSHOT
from langchain_ollama import ChatOllama

def _build_model(model_name: str, temperature: float = 0.0) -> ChatOllama:
    """
    Create a ChatOllama model instance for LLM parsing.

    :param model_name: Name of the Ollama model to use
    :type model_name: str
    :param temperature: Sampling temperature (0.0 for deterministic)
    :type temperature: float
    :return: Configured ChatOllama instance
    :rtype: ChatOllama
    """
    return ChatOllama(model=model_name, temperature=temperature)

def parse_command_help(*, model_name: str, command_path: str, help_text: str, retries: int = 2, cache_getset: Optional[Tuple] = None) -> CommandDoc:
    """
    Parse command help text using an LLM to extract structured documentation.

    Uses few-shot prompting with an Ollama model to convert raw help text
    into a structured CommandDoc. Supports caching and retry logic for
    validation errors.

    :param model_name: Name of the Ollama model to use for parsing
    :type model_name: str
    :param command_path: Full command path (e.g., "samtools view")
    :type command_path: str
    :param help_text: Raw help text output from the command
    :type help_text: str
    :param retries: Number of retry attempts on validation failure
    :type retries: int
    :param cache_getset: Optional tuple of (get_func, set_func) for caching
    :type cache_getset: Optional[Tuple]
    :return: Parsed command documentation
    :rtype: CommandDoc
    """
    cache_get, cache_set = (cache_getset or (None, None))
    if cache_get:
        cached = cache_get(command_path, None, model_name, help_text)
        if cached:
            print(f"  Cache HIT for: {command_path}")
            return CommandDoc.model_validate(cached)
        print(f"  Cache MISS for: {command_path}")

    print(f"  Parsing with LLM model {model_name}...")
    model = _build_model(model_name)
    structured = model.with_structured_output(CommandDoc)

    fewshot_blob = ""
    for ex in FEWSHOT:
        fewshot_blob += f"\n### Example help:\n{ex['help_text']}\n### Example JSON:\n{ex['json']}\n"
    user_blob = f"command_path: {command_path}\n\nhelp_text:\n{help_text}\n"

    for attempt in range(retries + 1):
        try:
            result: CommandDoc = structured.invoke([
                {"role": "system", "content": SYSTEM_PROMPT + fewshot_blob},
                {"role": "user", "content": user_blob},
            ])
            print(f"  Successfully parsed: {command_path}")
            if cache_set:
                cache_set(command_path, None, model_name, help_text, result.model_dump())
                print(f"  Cached result for: {command_path}")
            return result
        except ValidationError as e:
            if attempt >= retries:
                print(f"  WARNING: Validation failed after {retries} retries for {command_path}, returning empty doc")
                return CommandDoc(name=command_path.split()[-1], path=command_path, help_text=help_text, options=[], positionals=[], subcommands=[])
            print(f"  Validation error on attempt {attempt + 1}, retrying...")
            user_blob += "\nReminder: Return ONLY valid JSON matching the CommandDoc schema."
