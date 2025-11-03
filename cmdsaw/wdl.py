from __future__ import annotations
import re
from typing import List
from .parsing.schema import CommandDoc, OptionDoc, PositionalDoc
from .parsing.resource_estimator import estimate_resources, ResourceEstimate

def _sanitize_task_name(path: str) -> str:
    """
    Convert a command path to a valid WDL task name.

    Replaces spaces and non-alphanumeric characters with underscores, and
    ensures the name starts with a letter.

    :param path: Command path (e.g., "samtools view")
    :type path: str
    :return: Sanitized task name suitable for WDL
    :rtype: str
    """
    s = re.sub(r"[^A-Za-z0-9_]+", "_", path.strip().replace(" ", "_"))
    if not s or not s[0].isalpha():
        s = f"t_{s}"
    return s

def _sanitize_var_name(name: str) -> str:
    """
    Convert an option name to a valid WDL variable name.

    Removes dashes, converts to lowercase, replaces special characters with
    underscores, and ensures the name starts with a letter.

    :param name: Option name (e.g., "--output-file" or "-o")
    :type name: str
    :return: Sanitized variable name suitable for WDL
    :rtype: str
    """
    s = name.lower()
    s = s.replace("--", "").replace("-", "_")
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    if not s or not s[0].isalpha():
        s = f"v_{s}"
    return s

def _wdl_type(opt_type: str, is_flag: bool, repeatable: bool) -> str:
    """
    Map a cmdsaw type to a WDL type.

    Converts internal parameter types to WDL types. Flags always become Boolean,
    and repeatable non-flag options become arrays.

    :param opt_type: Internal type (e.g., "int", "float", "str", "path")
    :type opt_type: str
    :param is_flag: Whether the option is a boolean flag
    :type is_flag: bool
    :param repeatable: Whether the option can be specified multiple times
    :type repeatable: bool
    :return: WDL type string (e.g., "Int", "Boolean", "Array[String]")
    :rtype: str
    """
    if is_flag:
        return "Boolean"
    mapping = {
        "int": "Int",
        "float": "Float",
        "bool": "Boolean",
        "path": "String",
        "choice": "String",
        "str": "String",
        "unknown": "String",
    }
    base = mapping.get(opt_type or "unknown", "String")
    return f"Array[{base}]" if repeatable and not is_flag else base

def _default_literal(wdl_t: str, default: str | None):
    """
    Convert a default value to a WDL literal.

    Formats default values according to their WDL type. Returns None if the
    default cannot be converted or is not provided.

    :param wdl_t: WDL type string (e.g., "Int", "Float", "Boolean", "String")
    :type wdl_t: str
    :param default: Default value as a string, or None
    :type default: str | None
    :return: WDL literal string, or None if conversion fails
    :rtype: str | None
    """
    if default is None:
        return None
    try:
        if wdl_t == "Int":
            return str(int(str(default).strip()))
        if wdl_t == "Float":
            return str(float(str(default).strip()))
        if wdl_t == "Boolean":
            d = str(default).strip().lower()
            if d in ("true","false"):
                return d
            return None
    except Exception:
        return None
    if wdl_t.startswith("Array["):
        return None
    s = str(default).replace('"', '\"')
    return f"\"{s}\""

def _flag_token(opt: OptionDoc) -> str:
    """
    Get the command-line flag string for an option.

    Returns the long form if available, otherwise the short form.

    :param opt: Option documentation object
    :type opt: OptionDoc
    :return: Flag string (e.g., "--output" or "-o")
    :rtype: str
    """
    return opt.long or opt.short or ""

def _option_command_fragment(var: str, opt: OptionDoc) -> str:
    """
    Generate WDL command fragment for an option.

    Creates a WDL placeholder expression that conditionally includes the option
    in the command line based on whether it is defined or set.

    :param var: WDL variable name
    :type var: str
    :param opt: Option documentation object
    :type opt: OptionDoc
    :return: WDL command fragment string
    :rtype: str
    """
    flag = _flag_token(opt)
    if opt.is_flag:
        return f'~{{if {var} then "{flag}" else ""}}'
    wtype = _wdl_type(opt.type, False, opt.repeatable)
    if wtype.startswith("Array["):
        return f'~{{if defined({var}) then sep=" " (["{flag}"] + {var}) else ""}}'
    return f'~{{if defined({var}) then "{flag} " + {var} else ""}}'

def _inputs_block(cmd: CommandDoc, est: ResourceEstimate) -> tuple[str, list[str]]:
    """
    Generate WDL input block and parameter metadata.

    Creates input declarations for all options and positionals, including
    resource estimates (CPU and memory). Also generates metadata strings
    for parameter documentation.

    :param cmd: Command documentation object
    :type cmd: CommandDoc
    :param est: Resource estimate for the command
    :type est: ResourceEstimate
    :return: Tuple of (input block string, list of metadata strings)
    :rtype: tuple[str, list[str]]
    """
    lines: list[str] = []
    metas: list[str] = []
    lines.extend([
        f"Int? cpu = {est.cpu}",
        f"Int? memory_gb = {int(round(est.mem_gb))}",
    ])
    metas.extend([
        '  "cpu": "Estimated CPU cores"',
        '  "memory_gb": "Estimated RAM in GB"'
    ])
    for opt in cmd.options:
        var = _sanitize_var_name(opt.long or opt.short or "opt")
        wtype = _wdl_type(opt.type, opt.is_flag, opt.repeatable)
        optional = "" if opt.required and not opt.is_flag else "?"
        default_lit = _default_literal(wtype, opt.default)
        if default_lit is not None and optional == "":
            decl = f"{wtype} {var} = {default_lit}"
        else:
            decl = f"{wtype}{optional} {var}"
        lines.append(decl)
        metas.append(f'  "{var}": "desc={opt.description or ""}; flag={_flag_token(opt)}; required={opt.required}; repeatable={opt.repeatable}; type={opt.type}"')
    for pos in sorted(cmd.positionals, key=lambda p: p.index):
        var = _sanitize_var_name(pos.name)
        wtype = _wdl_type(pos.type, False, pos.variadic)
        optional = "?" if not pos.required else ""
        lines.append(f"{wtype}{optional} {var}")
        metas.append(f'  "{var}": "positional index={pos.index}; desc={pos.description or ""}; required={pos.required}"')
    return "\n  ".join(lines), metas

def _command_block(cmd: CommandDoc) -> str:
    """
    Generate WDL command block for a command.

    Constructs the command line with all options and positional arguments
    using WDL placeholder syntax.

    :param cmd: Command documentation object
    :type cmd: CommandDoc
    :return: WDL command block string
    :rtype: str
    """
    parts: list[str] = [cmd.path]
    for opt in cmd.options:
        var = _sanitize_var_name(opt.long or opt.short or "opt")
        parts.append(_option_command_fragment(var, opt))
    for pos in sorted(cmd.positionals, key=lambda p: p.index):
        var = _sanitize_var_name(pos.name)
        if pos.required:
            parts.append(f"~{{{var}}}")
        else:
            parts.append(f'~{{if defined({var}) then {var} else ""}}')
    return " \\\n    ".join(parts)

def _task_for(doc: CommandDoc, model_name: str) -> str:
    """
    Generate a complete WDL task definition for a command.

    Creates a WDL 1.2 task with input declarations, command block,
    runtime requirements, and parameter metadata.

    :param doc: Command documentation object
    :type doc: CommandDoc
    :param model_name: Ollama model name for resource estimation
    :type model_name: str
    :return: Complete WDL task definition as a string
    :rtype: str
    """
    tname = _sanitize_task_name(doc.path)
    est = estimate_resources(doc, model_name=model_name)
    inputs, metas = _inputs_block(doc, est)
    cmd_block = _command_block(doc)
    meta_block = ",\n".join(metas) if metas else ""
    cpu_default = est.cpu
    mem_default = int(round(est.mem_gb))
    return f"""task {tname} {{
    input {{
        {inputs if inputs else ""}
    }}
    command <<<
        {cmd_block}
    >>>
    runtime {{
        cpu: ~{{{{select_first([cpu, {cpu_default}])}}}}
        memory: "~{{{{select_first([memory_gb, {mem_default}])}}}}G"
    }}
    parameter_meta {{
        {meta_block}
    }}
}}"""

def emit_wdl(*, tool_name: str, docs: List[CommandDoc], out_path: str, model_name: str) -> None:
    """
    Write WDL task definitions for all commands to a file.

    Generates WDL 1.2 tasks for each command and subcommand, handling
    name collisions by appending numeric suffixes.

    :param tool_name: Name of the root tool (unused but kept for API compatibility)
    :type tool_name: str
    :param docs: List of command documentation objects
    :type docs: List[CommandDoc]
    :param out_path: File path where WDL will be written
    :type out_path: str
    :param model_name: Ollama model name for resource estimation
    :type model_name: str
    :return: None
    :rtype: None
    """
    print(f"\nGenerating WDL 1.2 tasks for {len(docs)} command(s)...")
    header = 'version 1.2'
    seen = set()
    tasks = []
    for d in docs:
        t = _task_for(d, model_name=model_name)
        name = _sanitize_task_name(d.path)
        if name in seen:
            idx = 2
            while f"{name}_{idx}" in seen:
                idx += 1
            t = t.replace(f"task {name} ", f"task {name}_{idx} ")
            print(f"  Generated WDL task: {name}_{idx} (renamed due to collision)")
            seen.add(f"{name}_{idx}")
        else:
            print(f"  Generated WDL task: {name}")
            seen.add(name)
        tasks.append(t)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + "\n\n" + "\n\n".join(tasks) + "\n")
    print(f"WDL tasks written to: {out_path}")
