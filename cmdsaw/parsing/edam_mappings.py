"""
Mapping of file extensions to EDAM format ontology terms.
Based on EDAM ontology: https://edamontology.org/

This module parses the EDAM.tsv file to build format mappings.
The EDAM.tsv file should be included as package data.
"""

import csv
import re
from pathlib import Path
from typing import Dict, Tuple, Optional

# Try to find EDAM.tsv in common locations
_EDAM_TSV_PATHS = [
    Path(__file__).parent / "EDAM.tsv",
    Path(__file__).parent.parent.parent / "EDAM.tsv",
    Path.home() / ".cache" / "cmdsaw" / "EDAM.tsv",
]

def _parse_edam_tsv(tsv_path: str) -> Dict[str, Tuple[str, str]]:
    """
    Parse EDAM.tsv file to extract format mappings.
    
    :param tsv_path: Path to EDAM.tsv file
    :return: Dictionary mapping extensions to (edam_id, label)
    """
    extension_map = {}
    
    # Priority mapping: prefer exact format names over derived/specific formats
    priority_formats = {}  # extension -> list of (format_id, name, priority)
    
    try:
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if not row or not row[0].startswith('http://edamontology.org/format_'):
                    continue
                
                uri = row[0]
                format_id = uri.split('/')[-1]
                name = row[1].strip() if len(row) > 1 else ''
                synonyms = row[2].strip() if len(row) > 2 else ''
                description = row[3].strip() if len(row) > 3 else ''
                
                if not name:
                    continue
                
                # Combine all text fields for searching
                all_text = f"{name} {synonyms} {description}".lower()
                
                # Determine priority (lower is better)
                # Prefer simple format names over complex ones
                priority = len(name)  # Shorter names are simpler
                if "search" in name.lower() or "results" in name.lower():
                    priority += 1000  # Deprioritize search/result formats
                
                # Extract extensions from various patterns
                # Pattern 1: Direct extensions like ".bam", ".vcf"
                extension_pattern = re.findall(r'\.([a-z0-9]{2,8})(?:\s|,|;|\)|$)', all_text)
                for ext in extension_pattern:
                    ext_key = f".{ext}"
                    if ext_key not in priority_formats:
                        priority_formats[ext_key] = []
                    priority_formats[ext_key].append((format_id, name, priority))
                
                # Pattern 2: Format names that match common extensions
                format_extensions = {
                    'fasta': ['.fasta', '.fa', '.fna', '.ffn', '.faa', '.frn'],
                    'fastq': ['.fastq', '.fq'],
                    'bam': ['.bam'],
                    'sam': ['.sam'],
                    'vcf': ['.vcf'],
                    'bcf': ['.bcf'],
                    'bed': ['.bed'],
                    'gff': ['.gff', '.gff3'],
                    'gtf': ['.gtf'],
                    'wig': ['.wig'],
                    'bigwig': ['.bigwig', '.bw'],
                    'bigbed': ['.bigbed', '.bb'],
                    'bedgraph': ['.bedgraph'],
                    'cram': ['.cram'],
                    'maf': ['.maf'],
                    'tsv': ['.tsv', '.tab'],
                    'csv': ['.csv'],
                    'json': ['.json'],
                    'xml': ['.xml'],
                    'html': ['.html', '.htm'],
                    'pdf': ['.pdf'],
                    'png': ['.png'],
                    'jpeg': ['.jpg', '.jpeg'],
                    'gif': ['.gif'],
                    'svg': ['.svg'],
                    'tiff': ['.tiff', '.tif'],
                    'phylip': ['.phylip'],
                    'nexus': ['.nexus'],
                    'newick': ['.newick'],
                    'stockholm': ['.stockholm'],
                    'clustal': ['.clustal'],
                    'pdb': ['.pdb'],
                    'sdf': ['.sdf'],
                    'mol': ['.mol'],
                    'mol2': ['.mol2'],
                    'hdf5': ['.h5', '.hdf5'],
                    'gzip': ['.gz'],
                    'bzip2': ['.bz2'],
                    'zip': ['.zip'],
                    'tar': ['.tar'],
                }
                
                name_lower = name.lower()
                for format_name, extensions in format_extensions.items():
                    # Check if this is an exact match or contains the format name
                    if name_lower == format_name or (format_name in name_lower and len(name_lower) < len(format_name) + 10):
                        for ext in extensions:
                            if ext not in priority_formats:
                                priority_formats[ext] = []
                            priority_formats[ext].append((format_id, name, priority))
        
        # Select best format for each extension (lowest priority value)
        for ext, candidates in priority_formats.items():
            if candidates:
                best = min(candidates, key=lambda x: x[2])
                extension_map[ext] = (best[0], best[1])
                
    except Exception as e:
        # If EDAM.tsv cannot be parsed, raise an error
        raise RuntimeError(
            f"Failed to parse EDAM.tsv file. Please ensure the file is present and valid. Error: {e}"
        )
    
    return extension_map

# Load from EDAM.tsv
_EDAM_LOADED = {}
_edam_file_found = False
for path in _EDAM_TSV_PATHS:
    if path.exists():
        _EDAM_LOADED = _parse_edam_tsv(str(path))
        _edam_file_found = True
        break

if not _edam_file_found:
    import warnings
    warnings.warn(
        "EDAM.tsv file not found. File format mappings will be unavailable. "
        "Please ensure EDAM.tsv is included in the package.",
        RuntimeWarning
    )

# Use only the loaded mappings from EDAM.tsv
EXTENSION_TO_EDAM = _EDAM_LOADED

def get_edam_format(extension: str) -> Optional[Tuple[str, str]]:
    """
    Get EDAM format ID and label for a file extension.
    
    :param extension: File extension (with or without leading dot)
    :return: Tuple of (edam_id, edam_label) or None if not found
    """
    if not extension:
        return None
    
    # Ensure extension starts with dot
    if not extension.startswith('.'):
        extension = '.' + extension
    
    # Convert to lowercase for matching
    extension = extension.lower()
    
    return EXTENSION_TO_EDAM.get(extension)

def get_edam_uri(edam_id: str) -> str:
    """
    Convert EDAM format ID to full URI.
    
    :param edam_id: EDAM format ID (e.g., 'format_1929')
    :return: Full EDAM URI
    """
    return f"http://edamontology.org/{edam_id}"
