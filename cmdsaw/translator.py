#!/usr/bin/env python3
"""
Translator module - Convert JSON to WDL tasks
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console

console = Console()


import os
import json
from pathlib import Path

def json_to_wdl(json_str: str, out_dir: str = "WDL", version: str = "1.21") -> bool:
    """
    Convert JSON command descriptions to multiple WDL task files.
    Creates one .wdl file per subcommand and a README.md.
    """
    try:
        data = json.loads(json_str)

        if not data.get("commands"):
            raise Exception("No commands found in JSON")

        tool_name = data.get("tool", "tool")
        tool_dir = Path(out_dir) / f"{tool_name}_{version}"
        tool_dir.mkdir(parents=True, exist_ok=True)

        # README.md
        readme = f"""# {tool_name} WDL Tasks (v{version})

This directory contains auto-generated WDL task definitions for `{tool_name}` commands.

Each subcommand has its own `.wdl` file, following the **WDL best practices**.
Tasks are designed to run inside `ubuntu:20.04` docker runtime.

## Example Usage
For examples of how to import and use these tasks, see:
[Wilds WDL library](https://github.com/openwdl/wdl/tree/main/standardLib)

---

Auto-generated.
"""
        with open(tool_dir / "README.md", "w") as f:
            f.write(readme)

        # Generate one WDL per command
        for command in data["commands"]:
            cmd_name = command["name"].replace("-", "_")
            file_name = f"{tool_name}_{cmd_name}.wdl"
            wdl_file = tool_dir / file_name

            task_block = build_wdl_task(tool_name, command)
            with open(wdl_file, "w") as f:
                f.write(task_block)

        return True

    except Exception as e:
        console.print(f"[red]Error generating WDL:[/red] {e}")
        return False


def build_wdl_task(tool_name: str, command: dict) -> str:
    """Generate a single WDL task string for one command."""
    cmd_name = command["name"].replace("-", "_")
    task_name = f"{tool_name}_{cmd_name}"

    inputs = []
    command_parts = [command["name"]]

    for param in command.get("parameters", []):
        param_name = param["name"].lstrip("-").replace("-", "_")
        param_type = map_type(param.get("type", "string"))
        is_required = param.get("required", False)
        is_flag = param.get("flag", False)
        default = param.get("default")

        if is_flag:
            inputs.append(f"    Boolean {param_name} = {str(default or False).lower()}")
            command_parts.append(f'~{{if ({param_name}) "{param["name"]}" else ""}}')
        else:
            if is_required:
                inputs.append(f"    {param_type} {param_name}")
            else:
                default_val = f'"{default}"' if default and param_type == "String" else str(default or "").lower()
                if param_type == "String" and not default:
                    default_val = '""'
                inputs.append(f"    {param_type}? {param_name} = {default_val}")

            if param_type == "File":
                command_parts.append(f'~{{if (defined({param_name})) "{param["name"]} " + {param_name} else ""}}')
            else:
                command_parts.append(f'~{{if (defined({param_name}) && {param_name} != "") "{param["name"]} " + {param_name} else ""}}')

    for pos_arg in command.get("positional_args", []):
        arg_name = pos_arg["name"].replace("-", "_")
        arg_type = map_type(pos_arg.get("type", "string"))
        is_required = pos_arg.get("required", True)

        if is_required:
            inputs.append(f"    {arg_type} {arg_name}")
            command_parts.append(f"~{{{arg_name}}}")
        else:
            inputs.append(f"    {arg_type}? {arg_name}")
            command_parts.append(f'~{{if (defined({arg_name})) {arg_name} else ""}}')

    outputs = []
    if command.get("stdout", False):
        outputs.append("    File stdout_file = stdout()")

    for output_file in command.get("produces_files", []):
        safe_name = output_file.replace(".", "_").replace("-", "_")
        outputs.append(f'    File {safe_name} = "{output_file}"')

    if not outputs:
        outputs.append("    File result = stdout()")

    task_block = f"""version 1.2

task {task_name} {{
  input {{
{chr(10).join(inputs) if inputs else "    # No inputs"}
  }}

  command <<<
    {tool_name} {' '.join(command_parts)}
  >>>

  output {{
{chr(10).join(outputs)}
  }}

  runtime {{
    docker: "ubuntu:20.04"
  }}
}}"""
    return task_block


def map_type(json_type: str) -> str:
    """Map JSON types to WDL types."""
    type_mapping = {
        "path": "File",
        "file": "File",
        "int": "Int",
        "integer": "Int",
        "float": "Float",
        "double": "Float",
        "flag": "Boolean",
        "boolean": "Boolean",
        "string": "String",
    }
    return type_mapping.get(json_type.lower(), "String")


import os
import json
from pathlib import Path

def json_to_nextflow(json_str: str, out_dir: str = "Nextflow", version: str = "1.21") -> bool:
    """
    Convert JSON command descriptions to Nextflow process modules.
    Creates one folder per subcommand with main.nf, meta.yml, and tests/main.nf.test.
    Also generates a conf file for including the modules.
    """
    try:
        data = json.loads(json_str)
        tool_name = data.get("tool", "tool")
        commands = data.get("commands", [])
        if not commands:
            raise Exception("No commands found in JSON")

        tool_dir = Path(out_dir) / f"{tool_name}_{version}"
        tool_dir.mkdir(parents=True, exist_ok=True)

        conf_lines = [
            f"manifest {{",
            f"    name = '{tool_name}'",
            f"    author = 'auto-generated'",
            f"}}",
            "",
            "includeConfig 'nextflow.config'"
        ]

        for cmd in commands:
            cmd_name = cmd["name"].replace("-", "_")
            cmd_dir = tool_dir / cmd_name
            tests_dir = cmd_dir / "tests"
            cmd_dir.mkdir(parents=True, exist_ok=True)
            tests_dir.mkdir(parents=True, exist_ok=True)

            # === main.nf ===
            inputs = []
            params = []
            command_parts = [cmd["name"]]

            for param in cmd.get("parameters", []):
                param_name = param["name"].lstrip("-").replace("-", "_")
                param_type = map_nf_type(param.get("type", "string"))
                is_required = param.get("required", False)
                is_flag = param.get("flag", False)

                # nextflow params
                if is_flag:
                    params.append(f"params.{param_name} = false")
                    command_parts.append(f"${{ params.{param_name} ? '{param['name']}' : '' }}")
                else:
                    params.append(f"params.{param_name} = ''")
                    command_parts.append(f"${{ params.{param_name} ? '{param['name']} ' + params.{param_name} : '' }}")

            # positional args
            for pos in cmd.get("positional_args", []):
                arg_name = pos["name"].replace("-", "_")
                params.append(f"params.{arg_name} = ''")
                command_parts.append(f"${{ params.{arg_name} }}")

            outputs = []
            if cmd.get("stdout", False):
                outputs.append("stdout")
            for f in cmd.get("produces_files", []):
                outputs.append(f)

            nf_process = f"""process {tool_name}_{cmd_name} {{
    input:
        path input_file optional true

    output:
        path("*.out")

    script:
    \"\"\"
    {tool_name} {' '.join(command_parts)} $input_file > result.out
    \"\"\"
}}"""

            with open(cmd_dir / "main.nf", "w") as f:
                f.write(nf_process)

            # === meta.yml ===
            meta_yml = f"""name: {tool_name}_{cmd_name}
description: Auto-generated Nextflow module for {tool_name} {cmd['name']}
keywords:
  - {tool_name}
  - {cmd['name']}
tools:
  - {tool_name}
"""
            with open(cmd_dir / "meta.yml", "w") as f:
                f.write(meta_yml)

            # === tests/main.nf.test ===
            nf_test = f"""nextflow.enable.dsl=2

include {{ {tool_name}_{cmd_name} }} from './main.nf'

workflow test_{cmd_name} {{
    {tool_name}_{cmd_name}()
}}
"""
            with open(tests_dir / "main.nf.test", "w") as f:
                f.write(nf_test)

        # === config file ===
        with open(tool_dir / "nextflow.config", "w") as f:
            f.write("\n".join(conf_lines))

        return True
    except Exception as e:
        console.print(f"[red]Error generating Nextflow:[/red] {e}")
        return False


def map_nf_type(json_type: str) -> str:
    """Map JSON types to Nextflow-style type hints (loosely)."""
    mapping = {
        "path": "path",
        "file": "path",
        "int": "integer",
        "integer": "integer",
        "float": "float",
        "double": "float",
        "flag": "boolean",
        "boolean": "boolean",
        "string": "string"
    }
    return mapping.get(json_type.lower(), "string")
