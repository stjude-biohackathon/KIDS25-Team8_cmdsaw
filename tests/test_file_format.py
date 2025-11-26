"""Test file_format field for tracking file formats and EDAM ontology."""
from cmdsaw.parsing.schema import CommandDoc, ToolDoc, OptionDoc, PositionalDoc, FileFormat
from cmdsaw.parsing.edam_mappings import get_edam_format, get_edam_uri


def test_file_format_class():
    """Test that FileFormat class works correctly."""
    # Test with just extension
    fmt1 = FileFormat(extension=".bam")
    assert fmt1.extension == ".bam"
    assert fmt1.edam_format is None
    assert fmt1.edam_uri is None
    
    # Test with full data
    fmt2 = FileFormat(
        extension=".fasta",
        edam_format="format_1929",
        edam_uri="http://edamontology.org/format_1929"
    )
    assert fmt2.extension == ".fasta"
    assert fmt2.edam_format == "format_1929"
    assert fmt2.edam_uri == "http://edamontology.org/format_1929"


def test_option_with_file_format():
    """Test that OptionDoc can have file_format."""
    opt = OptionDoc(
        long="--input",
        type="path",
        file_role="input",
        file_format=FileFormat(extension=".bam", edam_format="format_2572")
    )
    
    assert opt.file_format is not None
    assert opt.file_format.extension == ".bam"
    assert opt.file_format.edam_format == "format_2572"
    
    # Test serialization
    opt_dict = opt.model_dump()
    assert "file_format" in opt_dict
    assert opt_dict["file_format"]["extension"] == ".bam"
    assert opt_dict["file_format"]["edam_format"] == "format_2572"


def test_positional_with_file_format():
    """Test that PositionalDoc can have file_format."""
    pos = PositionalDoc(
        name="input_file",
        index=0,
        type="path",
        file_role="input",
        file_format=FileFormat(extension=".fastq", edam_format="format_1930")
    )
    
    assert pos.file_format is not None
    assert pos.file_format.extension == ".fastq"
    assert pos.file_format.edam_format == "format_1930"
    
    # Test serialization
    pos_dict = pos.model_dump()
    assert "file_format" in pos_dict
    assert pos_dict["file_format"]["extension"] == ".fastq"


def test_file_format_optional():
    """Test that file_format is optional and defaults to None."""
    opt = OptionDoc(long="--threads", type="int", file_role="none")
    assert opt.file_format is None
    
    pos = PositionalDoc(name="operation", index=0, type="str", file_role="none")
    assert pos.file_format is None


def test_command_with_file_formats():
    """Test CommandDoc with mixed file formats."""
    cmd = CommandDoc(
        name="test_tool",
        path="test_tool",
        help_text="Test tool",
        options=[
            OptionDoc(
                long="--input",
                type="path",
                file_role="input",
                file_format=FileFormat(extension=".bam")
            ),
            OptionDoc(
                long="--output",
                type="path",
                file_role="output",
                file_format=FileFormat(extension=".vcf", edam_format="format_3016")
            ),
            OptionDoc(long="--threads", type="int", file_role="none")
        ],
        positionals=[
            PositionalDoc(
                name="reference",
                index=0,
                type="path",
                file_role="input",
                file_format=FileFormat(extension=".fasta")
            )
        ],
        subcommands=[],
        requires_subcommand=False
    )
    
    cmd_dict = cmd.model_dump()
    
    # Check that file formats are preserved
    assert cmd_dict["options"][0]["file_format"]["extension"] == ".bam"
    assert cmd_dict["options"][1]["file_format"]["extension"] == ".vcf"
    assert cmd_dict["options"][1]["file_format"]["edam_format"] == "format_3016"
    assert cmd_dict["options"][2]["file_format"] is None
    assert cmd_dict["positionals"][0]["file_format"]["extension"] == ".fasta"


def test_edam_mappings():
    """Test EDAM ontology mapping functions."""
    # Test common formats
    fasta_edam = get_edam_format(".fasta")
    assert fasta_edam is not None
    assert fasta_edam[0] == "format_1929"
    assert fasta_edam[1] == "FASTA"
    
    bam_edam = get_edam_format(".bam")
    assert bam_edam is not None
    assert bam_edam[0] == "format_2572"
    assert bam_edam[1] == "BAM"
    
    # Test case insensitivity
    fq_edam = get_edam_format(".FQ")
    assert fq_edam is not None
    assert fq_edam[0] == "format_1930"
    
    # Test without leading dot
    vcf_edam = get_edam_format("vcf")
    assert vcf_edam is not None
    assert vcf_edam[0] == "format_3016"
    
    # Test unknown format
    unknown = get_edam_format(".unknown")
    assert unknown is None
    
    # Test URI generation
    uri = get_edam_uri("format_1929")
    assert uri == "http://edamontology.org/format_1929"


if __name__ == '__main__':
    test_file_format_class()
    print("✓ test_file_format_class passed")
    
    test_option_with_file_format()
    print("✓ test_option_with_file_format passed")
    
    test_positional_with_file_format()
    print("✓ test_positional_with_file_format passed")
    
    test_file_format_optional()
    print("✓ test_file_format_optional passed")
    
    test_command_with_file_formats()
    print("✓ test_command_with_file_formats passed")
    
    test_edam_mappings()
    print("✓ test_edam_mappings passed")
    
    print("\nAll file_format tests passed!")
