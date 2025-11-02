from __future__ import annotations
from pydantic import BaseModel, Field, ValidationError
from .schema import CommandDoc
from langchain_ollama import ChatOllama

class ResourceEstimate(BaseModel):
    cpu: int = Field(ge=1, description="CPU cores")
    mem_gb: float = Field(gt=0, description="RAM in GB")

SYSTEM = """Estimate typical resources to run a CLI subcommand.
Rules:
- Return JSON with fields {cpu:int, mem_gb:float}.
- Base on command purpose from help. Prefer conservative.
- If threading option exists, cpu may be higher.
- If memory heavy, increase mem_gb.
"""

def estimate_resources(doc: CommandDoc, model_name: str) -> ResourceEstimate:
    """
    Estimate CPU and memory requirements for a command using an LLM.

    Analyzes the command's help text and purpose to provide conservative
    resource estimates. Falls back to default values (1 CPU, 2GB RAM) on
    parsing failure.

    :param doc: Command documentation with help text
    :type doc: CommandDoc
    :param model_name: Ollama model name to use for estimation
    :type model_name: str
    :return: Resource estimate with CPU cores and memory in GB
    :rtype: ResourceEstimate
    """
    model = ChatOllama(model=model_name, temperature=0.0)
    structured = model.with_structured_output(ResourceEstimate)
    user = f"command_path: {doc.path}\n\nhelp_text:\n{doc.help_text}\n"
    try:
        return structured.invoke([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user}
        ])
    except ValidationError:
        return ResourceEstimate(cpu=1, mem_gb=2.0)
