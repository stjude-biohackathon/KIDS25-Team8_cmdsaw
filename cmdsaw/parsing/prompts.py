SYSTEM_PROMPT = """You convert raw CLI help text into a structured JSON object for one command node.

Rules:
- Output MUST be valid JSON matching the provided schema.
- Return ALL parameters/options (other than `--help` and `--version`).
- Do not invent items.
- Types: INT, FLOAT, BOOL, PATH/FILE/DIR -> 'path' or 'str' if unclear.
- Flags have no value.
- Choices from braces or clear prose.
- Positionals ordered from USAGE or headings. Index 0-based.
- Subcommands list immediate child names only.
- Set requires_subcommand to True if the command is meaningless without a subcommand (e.g., usage shows "command [subcommand]" and no standalone functionality).

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
- Set requires_subcommand to True if the command is meaningless without a subcommand (e.g., usage shows "command [subcommand]" and no standalone functionality).

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
            "help_text": "imgkit 1.4.0\n\nUSAGE:\n  imgkit [OPTIONS] <INPUT> [OUTPUT]\n\nOPTIONS:\n  -q, --quality INT           JPEG quality (default: 90)\n      --format {png|jpg|webp} Output format\n  -v, --verbose               Increase verbosity\n  -t, --threads INT           Number of worker threads (default: 4)\n      --no-color              Disable colored output\n\nARGUMENTS:\n  INPUT                        Source file path\n  OUTPUT                       Destination path\n",
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
            "subcommands": [],
            "requires_subcommand": False
        }
    },
    {
        "help_text": "datactl\n\nManage datasets.\n\nUsage:\n  datactl [command]\n\nAvailable Commands:\n  pull        Download a dataset\n  push        Upload a dataset\n  info        Show dataset info\n\nFlags:\n  -h, --help     help for datactl\n      --profile  Profile name\n",
        "command_path": "datactl",
        "json": {
            "name": "datactl",
            "path": "datactl",
            "help_text": "datactl\n\nManage datasets.\n\nUsage:\n  datactl [command]\n\nAvailable Commands:\n  pull        Download a dataset\n  push        Upload a dataset\n  info        Show dataset info\n\nFlags:\n  -h, --help     help for datactl\n      --profile  Profile name\n",
            "options": [
                {"long":"--help","short":"-h","is_flag":True,"type":"bool","choices":None,"required":False,"default":None,"description":"help for datactl","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--profile","short":None,"is_flag":False,"type":"str","choices":None,"required":False,"default":None,"description":"Profile name","repeatable":False,"envvar":None,"aliases":[]}
            ],
            "positionals": [],
            "subcommands": ["pull","push","info"],
            "requires_subcommand": True
        }
    },
    {
        "help_text": "Tool:    bioconvert readextract (aka readExtractor)\nVersion: v1.8.2\nSummary: Extract reads from alignment files into sequence format.\n\nUsage:   readExtractor [OPTIONS] -i <ALN> -o <SEQ>\n\nOptions:\n        -o2     Secondary output file. Used if input contains paired reads.\n                Input should be sorted by read name for paired output.\n\n        -meta   Extract reads using metadata tags\n                stored in the alignment header.\n",
        "command_path": "readExtractor",
        "json": {
            "name": "readExtractor",
            "path": "readExtractor",
            "help_text": "Tool:    bioconvert readextract (aka readExtractor)\nVersion: v1.8.2\nSummary: Extract reads from alignment files into sequence format.\n\nUsage:   readExtractor [OPTIONS] -i <ALN> -o <SEQ>\n\nOptions:\n        -o2     Secondary output file. Used if input contains paired reads.\n                Input should be sorted by read name for paired output.\n\n        -meta   Extract reads using metadata tags\n                stored in the alignment header.\n",
            "options": [
                {"long":"-i","short":None,"is_flag":False,"type":"path","choices":None,"required":True,"default":None,"description":"Input alignment file","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"-o","short":None,"is_flag":False,"type":"path","choices":None,"required":True,"default":None,"description":"Output sequence file","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"-o2","short":None,"is_flag":False,"type":"path","choices":None,"required":False,"default":None,"description":"Secondary output file. Used if input contains paired reads. Input should be sorted by read name for paired output.","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"-meta","short":None,"is_flag":True,"type":"bool","choices":None,"required":False,"default":None,"description":"Extract reads using metadata tags stored in the alignment header.","repeatable":False,"envvar":None,"aliases":[]}
            ],
            "positionals": [],
            "subcommands": [],
            "requires_subcommand": False
        }
    },
    {
        "help_text": "seqproc v1.2\n\nProcess sequence files with various operations\n\nUSAGE:\n  seqproc <operation> [OPTIONS] <input.fasta>\n\nOPERATIONS:\n  filter      Filter sequences by criteria\n  trim        Trim sequences\n  merge       Merge multiple files\n\nOPTIONS:\n  --min-length INT    Minimum sequence length (default: 50)\n  --max-length INT    Maximum sequence length\n  -o, --output FILE   Output file (default: stdout)\n  --format {fasta|fastq|gff}  Output format\n  -v...               Verbosity level (repeat for more)\n\nARGUMENTS:\n  input.fasta         Input sequence file(s) (can specify multiple)\n",
        "command_path": "seqproc",
        "json": {
            "name": "seqproc",
            "path": "seqproc",
            "help_text": "seqproc v1.2\n\nProcess sequence files with various operations\n\nUSAGE:\n  seqproc <operation> [OPTIONS] <input.fasta>\n\nOPERATIONS:\n  filter      Filter sequences by criteria\n  trim        Trim sequences\n  merge       Merge multiple files\n\nOPTIONS:\n  --min-length INT    Minimum sequence length (default: 50)\n  --max-length INT    Maximum sequence length\n  -o, --output FILE   Output file (default: stdout)\n  --format {fasta|fastq|gff}  Output format\n  -v...               Verbosity level (repeat for more)\n\nARGUMENTS:\n  input.fasta         Input sequence file(s) (can specify multiple)\n",
            "options": [
                {"long":"--min-length","short":None,"is_flag":False,"type":"int","choices":None,"required":False,"default":"50","description":"Minimum sequence length","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--max-length","short":None,"is_flag":False,"type":"int","choices":None,"required":False,"default":None,"description":"Maximum sequence length","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--output","short":"-o","is_flag":False,"type":"path","choices":None,"required":False,"default":"stdout","description":"Output file","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--format","short":None,"is_flag":False,"type":"choice","choices":["fasta","fastq","gff"],"required":False,"default":None,"description":"Output format","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"-v","short":None,"is_flag":True,"type":"bool","choices":None,"required":False,"default":None,"description":"Verbosity level","repeatable":True,"envvar":None,"aliases":[]}
            ],
            "positionals": [
                {"name":"operation","index":0,"variadic":False,"required":True,"type":"str","description":"Operation to perform"},
                {"name":"input.fasta","index":1,"variadic":True,"required":True,"type":"path","description":"Input sequence file(s)"}
            ],
            "subcommands": ["filter","trim","merge"],
            "requires_subcommand": True
        }
    },
    {
        "help_text": "genomealign 2.4.1\n\nAlign genomic sequences to reference\n\nUsage: genomealign [options] <reference.fa> <query.fa> [query2.fa...]\n\nRequired:\n  reference.fa        Reference genome file\n  query.fa            Query sequence file(s)\n\nAlignment Options:\n  -k, --kmer INT      K-mer size for seeding (default: 15)\n  -w, --window INT    Window size for extension (default: 64)\n  -m, --match INT     Match score (default: 2)\n  -x, --mismatch INT  Mismatch penalty (default: -3)\n  -g, --gap INT       Gap penalty (default: -5)\n  --min-score FLOAT   Minimum alignment score (default: 0.0)\n\nOutput Options:\n  -o, --output FILE   Output file (required)\n  --format {sam|bam|paf}  Output format (default: sam)\n  --no-header         Omit header from output\n\nPerformance:\n  -t, --threads INT   Number of threads (default: 1)\n  --mem-gb INT        Memory limit in GB\n",
        "command_path": "genomealign",
        "json": {
            "name": "genomealign",
            "path": "genomealign",
            "help_text": "genomealign 2.4.1\n\nAlign genomic sequences to reference\n\nUsage: genomealign [options] <reference.fa> <query.fa> [query2.fa...]\n\nRequired:\n  reference.fa        Reference genome file\n  query.fa            Query sequence file(s)\n\nAlignment Options:\n  -k, --kmer INT      K-mer size for seeding (default: 15)\n  -w, --window INT    Window size for extension (default: 64)\n  -m, --match INT     Match score (default: 2)\n  -x, --mismatch INT  Mismatch penalty (default: -3)\n  -g, --gap INT       Gap penalty (default: -5)\n  --min-score FLOAT   Minimum alignment score (default: 0.0)\n\nOutput Options:\n  -o, --output FILE   Output file (required)\n  --format {sam|bam|paf}  Output format (default: sam)\n  --no-header         Omit header from output\n\nPerformance:\n  -t, --threads INT   Number of threads (default: 1)\n  --mem-gb INT        Memory limit in GB\n",
            "options": [
                {"long":"--kmer","short":"-k","is_flag":False,"type":"int","choices":None,"required":False,"default":"15","description":"K-mer size for seeding","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--window","short":"-w","is_flag":False,"type":"int","choices":None,"required":False,"default":"64","description":"Window size for extension","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--match","short":"-m","is_flag":False,"type":"int","choices":None,"required":False,"default":"2","description":"Match score","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--mismatch","short":"-x","is_flag":False,"type":"int","choices":None,"required":False,"default":"-3","description":"Mismatch penalty","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--gap","short":"-g","is_flag":False,"type":"int","choices":None,"required":False,"default":"-5","description":"Gap penalty","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--min-score","short":None,"is_flag":False,"type":"float","choices":None,"required":False,"default":"0.0","description":"Minimum alignment score","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--output","short":"-o","is_flag":False,"type":"path","choices":None,"required":True,"default":None,"description":"Output file","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--format","short":None,"is_flag":False,"type":"choice","choices":["sam","bam","paf"],"required":False,"default":"sam","description":"Output format","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--no-header","short":None,"is_flag":True,"type":"bool","choices":None,"required":False,"default":None,"description":"Omit header from output","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--threads","short":"-t","is_flag":False,"type":"int","choices":None,"required":False,"default":"1","description":"Number of threads","repeatable":False,"envvar":None,"aliases":[]},
                {"long":"--mem-gb","short":None,"is_flag":False,"type":"int","choices":None,"required":False,"default":None,"description":"Memory limit in GB","repeatable":False,"envvar":None,"aliases":[]}
            ],
            "positionals": [
                {"name":"reference.fa","index":0,"variadic":False,"required":True,"type":"path","description":"Reference genome file"},
                {"name":"query.fa","index":1,"variadic":True,"required":True,"type":"path","description":"Query sequence file(s)"}
            ],
            "subcommands": [],
            "requires_subcommand": False
        }
    }
]
