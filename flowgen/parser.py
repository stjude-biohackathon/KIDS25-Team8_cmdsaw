#!/usr/bin/env python3
"""
Parser module - LLM interaction and JSON validation
"""
import json
import requests
from typing import Dict, Any
from rich.console import Console
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama


console = Console()
SCHEMA = {
        "tool": "string",
        "version": "string",
        "commands": [
            {
                "name": "string",
                "description": "string",
                "is_subcommand": "boolean",
                "parameters": [
                    {
                        "name": "string",
                        "short": "string or null",
                        "type": "string (path|int|float|string|flag)",
                        "required": "boolean",
                        "flag": "boolean",
                        "default": "string or null",
                        "description": "string"
                    }
                ],
                "positional_args": [
                    {
                        "name": "string",
                        "type": "string",
                        "description": "string", 
                        "required": "boolean"
                    }
                ],
                "stdin": "boolean",
                "stdout": "boolean",
                "produces_files": ["list of strings"]
            }
        ],
        "bioconda": "string",
        "docker": "string",
        "singularity": "string"
    }


def build_prompt(help_text: str, tool_name: str, version: str = None) -> str:
    """
    Build a constrained prompt for the LLM to extract command parameters
    """
    schema = {
        "tool": "string",
        "version": "string",
        "commands": [
            {
                "name": "string",
                "description": "string",
                "is_subcommand": "boolean",
                "parameters": [
                    {
                        "name": "string",
                        "short": "string or null",
                        "type": "string (path|int|float|string|flag)",
                        "required": "boolean",
                        "flag": "boolean",
                        "default": "string or null",
                        "description": "string"
                    }
                ],
                "positional_args": [
                    {
                        "name": "string",
                        "type": "string",
                        "description": "string", 
                        "required": "boolean"
                    }
                ],
                "stdin": "boolean",
                "stdout": "boolean",
                "produces_files": ["list of strings"]
            }
        ],
        "containers":
            {
                "bioconda": "string",
                "docker": "string",
                "singularity": "string"
            }
    }
    
    example_json = {
        "tool": "ls",
        "version": "8.32",
        "commands": [
            {
                "name": "ls",
                "description": "List directory contents",
                "is_subcommand": False,
                "parameters": [
                    {
                        "name": "--all",
                        "short": "-a",
                        "type": "flag",
                        "required": False,
                        "flag": True,
                        "default": False,
                        "description": "Show hidden files"
                    },
                    {
                        "name": "--long",
                        "short": "-l",
                        "type": "flag", 
                        "required": False,
                        "flag": True,
                        "default": False,
                        "description": "Use long listing format"
                    }
                ],
                "positional_args": [
                    {
                        "name": "files",
                        "type": "string",
                        "description": "Files or directories to list",
                        "required": False
                    }
                ],
                "stdin": False,
                "stdout": True,
                "produces_files": []
            }
        ]
    }
    
    prompt = f"""You are a strict JSON generator. Do not produce any extra text. Respond only with JSON.

Here is the command help text:
{help_text}

Extract command information and return JSON conforming exactly to this schema:
{json.dumps(schema, indent=2)}

Example format:
{json.dumps(example_json, indent=2)}

Important rules:
- Only use information within the help text, do not use outside sources or context.
- Output MUST be valid JSON only.
- No extra text or explanations.
- Use type "flag" for boolean flags (no argument).
- Use type "path" for file/directory arguments.
- Use type "string" for text arguments.
- Use type "int" for integer arguments.
- Use type "float" for decimal arguments.
- Set "flag": true for parameters that don't take values.
- Set "flag": false for parameters that take values.
- Extract tool name as "{tool_name}" and version as "{version or 'unknown'}".
"""

    return prompt


def call_model(prompt: str, model: str = "llama3.1:8b") -> CommandSchema:
    """
    Call Ollama model with streaming enabled.
    Stream output live, and optionally write to a file.
    """
    # url = "http://localhost:11434/api/generate"
    console.print(f"[blue]Calling Ollama model[/blue] [bold cyan]{model}[/bold cyan]...")

    # payload = {
    #     "model": model,
    #     "prompt": prompt,
    #     "stream": True,
    #     "system": "You are a strict JSON generator. Only produce valid JSON objects. No extra text."
    # }
    
    model = ChatOllama(
        model=model,
        temperature=0,
        # other params...
    )

    try:
        # # stream=True here is for requests, not Ollama
        # with requests.post(url, json=payload, stream=True, timeout=120) as response:
        #     response.raise_for_status()

        #     collected_chunks = []

        #     out_file = "output/response.json"  
        #     file_handle = open(out_file, "w", encoding="utf-8") if out_file else None

        #     for line in response.iter_lines():
        #         if line:
        #             try:
        #                 data = json.loads(line.decode("utf-8"))
        #                 chunk = data.get("response", "")
        #                 collected_chunks.append(chunk)

        #                 # Write to file immediately if specified
        #                 if file_handle:
        #                     file_handle.write(chunk)
        #                     file_handle.flush()

        #                 if data.get("done", False):
        #                     break
        #             except json.JSONDecodeError:
        #                 # Sometimes partial lines can appear
        #                 continue

        #     if file_handle:
        #         file_handle.close()

        #     raw_response = "".join(collected_chunks)
        #     cleaned_response = clean_json_response(raw_response)
        #     return cleaned_response
        model_with_structure = model.with_structured_output(CommandSchema)
        response = model_with_structure.invoke(prompt)

    except Exception as e:
        raise Exception(f"Error calling Ollama: {e}")
    
    return response

def clean_json_response(response: str) -> str:
    """
    Clean up common JSON formatting issues from LLM responses
    """
    # Remove code block markers
    response = response.strip()
    if response.startswith('```json'):
        response = response[7:]
    if response.startswith('```'):
        response = response[3:]
    if response.endswith('```'):
        response = response[:-3]
    
    # Split into lines for line-by-line cleaning
    lines = response.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip obviously malformed lines
        if 'zxA=' in line or line.strip().startswith('zxA='):
            continue
            
        # Fix common syntax issues
        line = line.replace(',"', ',"')  # Fix spacing
        line = line.replace(': null', ': "null"')  # Convert null to string if needed
        
        cleaned_lines.append(line)
    
    # Rejoin and fix trailing commas
    response = '\n'.join(cleaned_lines)
    
    # Remove trailing commas before closing brackets/braces
    import re
    response = re.sub(r',\s*([}\]])', r'\1', response)
    
    return response.strip()


def validate_json(json_str: str) -> Dict[str, Any]:
    """
    Validate that the string is valid JSON with required fields
    """
    # Display the JSON string for debugging with syntax highlighting
    console.print("\n[blue]Raw JSON response stored in output/llama_response.json [/blue]")
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON parsing failed at position {e.pos}[/red]")
        # Show the problematic area
        error_start = max(0, e.pos - 50)
        error_end = min(len(json_str), e.pos + 50)
        error_context = json_str[error_start:error_end]
        console.print(f"[yellow]Context:[/yellow] ...{error_context}...")
        raise Exception(f"Invalid JSON: {e}")
    
    # Check required top-level fields
    required_fields = ['tool', 'commands']
    for field in required_fields:
        if field not in data:
            console.print(f"[red]Missing required field:[/red] {field}")
            raise Exception(f"Missing required field: {field}")
    
    # Validate commands structure
    if not isinstance(data['commands'], list):
        console.print("[red]Error:[/red] 'commands' must be a list")
        raise Exception("'commands' must be a list")
    
    if not data['commands']:
        console.print("[red]Error:[/red] 'commands' list cannot be empty")
        raise Exception("'commands' list cannot be empty")
    
    for i, cmd in enumerate(data['commands']):
        if not isinstance(cmd, dict):
            console.print(f"[red]Error:[/red] Command {i} must be a dict")
            raise Exception(f"Command {i} must be a dict")
        
        cmd_required = ['name', 'description']
        for field in cmd_required:
            if field not in cmd:
                console.print(f"[red]Error:[/red] Command {i} missing required field: {field}")
                raise Exception(f"Command {i} missing required field: {field}")
        
        # Ensure parameters exists (can be empty list)
        if 'parameters' not in cmd:
            cmd['parameters'] = []
        
        # Ensure positional_args exists (can be empty list)
        if 'positional_args' not in cmd:
            cmd['positional_args'] = []
    
    console.print("[green]JSON validation passed[/green]")
    return data