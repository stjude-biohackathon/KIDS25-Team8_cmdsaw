from __future__ import annotations
import re
from typing import List
from .parsing.schema import CommandDoc, OptionDoc, PositionalDoc
from .parsing.resource_estimator import estimate_resources, ResourceEstimate

def _sanitize_task_name(path: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]+", "_", path.strip().replace(" ", "_"))
    if not s or not s[0].isalpha():
        s = f"t_{s}"
    return s

def _sanitize_var_name(name: str) -> str:
    s = name.lower()
    s = s.replace("--", "").replace("-", "_")
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    if not s or not s[0].isalpha():
        s = f"v_{s}"
    return s

def _wdl_type(opt_type: str, is_flag: bool, repeatable: bool) -> str:
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
    return opt.long or opt.short or ""

def _option_command_fragment(var: str, opt: OptionDoc) -> str:
    flag = _flag_token(opt)
    if opt.is_flag:
        return f'~{{if {var} then "{flag}" else ""}}'
    wtype = _wdl_type(opt.type, False, opt.repeatable)
    if wtype.startswith("Array["):
        return f'~{{if defined({var}) then sep=" " (["{flag}"] + {var}) else ""}}'
    return f'~{{if defined({var}) then "{flag} " + {var} else ""}}'

def _inputs_block(cmd: CommandDoc, est: ResourceEstimate) -> tuple[str, list[str]]:
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
            seen.add(f"{name}_{idx}")
        else:
            seen.add(name)
        tasks.append(t)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + "\n\n" + "\n\n".join(tasks) + "\n")
