from __future__ import annotations
from typing import Optional, Tuple
from pydantic import ValidationError
from .schema import CommandDoc
from .prompts import SYSTEM_PROMPT, FEWSHOT
from langchain_ollama import ChatOllama

def _build_model(model_name: str, temperature: float = 0.0) -> ChatOllama:
    return ChatOllama(model=model_name, temperature=temperature)

def parse_command_help(*, model_name: str, command_path: str, help_text: str, retries: int = 2, cache_getset: Optional[Tuple] = None) -> CommandDoc:
    cache_get, cache_set = (cache_getset or (None, None))
    if cache_get:
        cached = cache_get(command_path, None, model_name, help_text)
        if cached:
            return CommandDoc.model_validate(cached)

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
            if cache_set:
                cache_set(command_path, None, model_name, help_text, result.model_dump())
            return result
        except ValidationError:
            if attempt >= retries:
                return CommandDoc(name=command_path.split()[-1], path=command_path, help_text=help_text, options=[], positionals=[], subcommands=[])
            user_blob += "\nReminder: Return ONLY valid JSON matching the CommandDoc schema."
