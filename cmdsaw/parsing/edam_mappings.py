"""
Mapping of common file extensions to EDAM format ontology terms.
Based on EDAM ontology: https://edamontology.org/
"""

# Extension to EDAM format mapping
# Format: extension -> (edam_id, edam_label)
EXTENSION_TO_EDAM = {
    # Sequence formats
    ".fasta": ("format_1929", "FASTA"),
    ".fa": ("format_1929", "FASTA"),
    ".fna": ("format_1929", "FASTA"),
    ".ffn": ("format_1929", "FASTA"),
    ".faa": ("format_1929", "FASTA"),
    ".frn": ("format_1929", "FASTA"),
    ".fastq": ("format_1930", "FASTQ"),
    ".fq": ("format_1930", "FASTQ"),
    
    # Alignment formats
    ".sam": ("format_2573", "SAM"),
    ".bam": ("format_2572", "BAM"),
    ".cram": ("format_3462", "CRAM"),
    ".maf": ("format_3008", "MAF"),
    
    # Variant formats
    ".vcf": ("format_3016", "VCF"),
    ".bcf": ("format_3020", "BCF"),
    
    # Annotation formats
    ".gff": ("format_2305", "GFF"),
    ".gff3": ("format_1975", "GFF3"),
    ".gtf": ("format_2306", "GTF"),
    ".bed": ("format_3003", "BED"),
    ".bigbed": ("format_3004", "bigBed"),
    ".bb": ("format_3004", "bigBed"),
    ".bedgraph": ("format_3583", "bedGraph"),
    ".wig": ("format_3005", "WIG"),
    ".bigwig": ("format_3006", "bigWig"),
    ".bw": ("format_3006", "bigWig"),
    
    # Tabular formats
    ".tsv": ("format_3475", "TSV"),
    ".tab": ("format_3475", "TSV"),
    ".csv": ("format_3752", "CSV"),
    ".txt": ("format_2330", "Textual format"),
    
    # XML/HTML formats
    ".xml": ("format_2332", "XML"),
    ".html": ("format_2331", "HTML"),
    ".htm": ("format_2331", "HTML"),
    
    # JSON formats
    ".json": ("format_3464", "JSON"),
    
    # Image formats
    ".png": ("format_3603", "PNG"),
    ".jpg": ("format_3579", "JPEG"),
    ".jpeg": ("format_3579", "JPEG"),
    ".gif": ("format_3467", "GIF"),
    ".svg": ("format_3604", "SVG"),
    ".tiff": ("format_3591", "TIFF"),
    ".tif": ("format_3591", "TIFF"),
    ".pdf": ("format_3508", "PDF"),
    
    # Compressed formats
    ".gz": ("format_3989", "gzip"),
    ".bz2": ("format_3987", "bzip2"),
    ".zip": ("format_3987", "Zip"),
    ".tar": ("format_3987", "tar"),
    
    # HDF5 formats
    ".h5": ("format_3590", "HDF5"),
    ".hdf5": ("format_3590", "HDF5"),
    
    # Bioinformatics specific
    ".pdb": ("format_1476", "PDB"),
    ".sdf": ("format_3814", "SDF"),
    ".mol": ("format_3815", "MOL"),
    ".mol2": ("format_3816", "MOL2"),
    ".phylip": ("format_1997", "PHYLIP"),
    ".nexus": ("format_1912", "Nexus"),
    ".newick": ("format_1910", "Newick"),
    ".stockholm": ("format_1961", "Stockholm"),
    ".clustal": ("format_1982", "Clustal"),
}

def get_edam_format(extension: str) -> tuple[str, str] | None:
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
