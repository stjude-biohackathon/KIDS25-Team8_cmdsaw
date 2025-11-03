SYSTEM_PROMPT = """You convert raw CLI help text into a structured JSON object for one command node.

Rules:
- Output MUST be valid JSON matching the provided schema.
- Do not invent items.
- Types: INT, FLOAT, BOOL, PATH/FILE/DIR -> 'path' or 'str' if unclear.
- Flags have no value.
- Choices from braces or clear prose.
- Positionals ordered from USAGE or headings. Index 0-based.
- Subcommands list immediate child names only.
- Repeatable if stated or shown with '...'.

Return only JSON.
"""

EMPHASIZED_SUBCOMMAND_PROMPT = """You convert raw CLI help text into a structured JSON object for one command node.

Rules:
- Output MUST be valid JSON matching the provided schema.
- Do not invent items.
- Types: INT, FLOAT, BOOL, PATH/FILE/DIR -> 'path' or 'str' if unclear.
- Flags have no value.
- Choices from braces or clear prose.
- Positionals ordered from USAGE or headings. Index 0-based.
- Repeatable if stated or shown with '...'.

**CRITICAL: SUBCOMMAND DISCOVERY**
PAY SPECIAL ATTENTION to discovering ALL available subcommands. This is the MOST IMPORTANT part of your task.
- Look for sections like "Commands:", "Available Commands:", "Subcommands:", "COMMANDS:"
- Check "Usage:" or "USAGE:" lines that show command hierarchy
- Examine any list of command names that can be invoked as subcommands
- Include ALL subcommand names found, even if they appear in different sections
- Subcommands are often listed with brief descriptions - extract the command name from each line
- Do NOT skip or omit any subcommands - completeness is critical
- List immediate child subcommand names only (not nested sub-subcommands)

Return only JSON.
"""

FEWSHOT = [
    {
        "help_text": "imgkit 1.4.0\n\nUSAGE:\n  imgkit [OPTIONS] <INPUT> [OUTPUT]\n\nOPTIONS:\n  -q, --quality INT           JPEG quality (default: 90)\n      --format {png|jpg|webp} Output format\n  -v, --verbose               Increase verbosity\n  -t, --threads INT           Number of worker threads (default: 4)\n      --no-color              Disable colored output\n\nARGUMENTS:\n  INPUT                        Source file path\n  OUTPUT                       Destination path\n",
        "command_path": "imgkit",
        "json": {
            "name": "imgkit",
            "path": "imgkit",
            "help_text": "imgkit 1.4.0...",
            "options": [
                {"long":"--quality","short":"-q","is_flag":False,"type":"int","choices":None,"required":False,"default":"90","description":"JPEG quality","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--format","short":None,"is_flag":False,"type":"choice","choices":["png","jpg","webp"],"required":False,"default":None,"description":"Output format","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--verbose","short":"-v","is_flag":True,"type":"bool","choices":None,"required":False,"default":None,"description":"Increase verbosity","repeatable":True,"envvar":None,"aliases":[]},
                {"long":"--threads","short":"-t","is_flag":False,"type":"int","choices":None,"required":False,"default":"4","description":"Number of worker threads","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--no-color","short":None,"is_flag":True,"type":"bool","choices":None,"required":False,"default":None,"description":"Disable colored output","repeatable":False,"envvar":None,"aliases":[]}
            ],
            "positionals": [
                {"name":"INPUT","index":0,"variadic":False,"required":True,"type":"path","description":"Source file path"},
                {"name":"OUTPUT","index":1,"variadic":False,"required":False,"type":"path","description":"Destination path"}
            ],
            "subcommands": []
        }
    },
    {
        "help_text": "datactl\n\nManage datasets.\n\nUsage:\n  datactl [command]\n\nAvailable Commands:\n  pull        Download a dataset\n  push        Upload a dataset\n  info        Show dataset info\n\nFlags:\n  -h, --help     help for datactl\n      --profile  Profile name\n",
        "command_path": "datactl",
        "json": {
            "name": "datactl",
            "path": "datactl",
            "help_text": "datactl...",
            "options": [
                {"long":"--help","short":"-h","is_flag":True,"type":"bool","choices":None,"required":False,"default":None,"description":"help for datactl","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--profile","short":None,"is_flag":False,"type":"str","choices":None,"required":False,"default":None,"description":"Profile name","repeatable":False,"envvar":None,"aliases":[]}
            ],
            "positionals": [],
            "subcommands": ["pull","push","info"]
        }
    }
]
