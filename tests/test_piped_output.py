"""Test piped output support and EDAM.tsv loading."""
from cmdsaw.parsing.schema import (
    OptionDoc, PositionalDoc, FileFormat, 
    generate_piped_output_filename
)
from cmdsaw.parsing.edam_mappings import get_edam_format, EXTENSION_TO_EDAM


def test_supports_piped_output_option():
    """Test that OptionDoc supports piped output flag."""
    # Output with piped support
    opt = OptionDoc(
        long="--output",
        type="path",
        file_role="output",
        supports_piped_output=True
    )
    assert opt.supports_piped_output is True
    
    # Output without piped support
    opt2 = OptionDoc(
        long="--output",
        type="path",
        file_role="output",
        supports_piped_output=False
    )
    assert opt2.supports_piped_output is False
    
    # Default is False
    opt3 = OptionDoc(long="--test", type="path")
    assert opt3.supports_piped_output is False


def test_supports_piped_output_positional():
    """Test that PositionalDoc supports piped output flag."""
    pos = PositionalDoc(
        name="output_file",
        index=0,
        type="path",
        file_role="output",
        supports_piped_output=True
    )
    assert pos.supports_piped_output is True
    
    # Default is False
    pos2 = PositionalDoc(name="file", index=0)
    assert pos2.supports_piped_output is False


def test_generate_piped_output_filename_basic():
    """Test basic filename generation for piped output."""
    # Simple command with format
    filename = generate_piped_output_filename(
        "samtools view",
        FileFormat(extension=".bam")
    )
    assert filename == "samtools_view_output.bam"
    
    # Command without format (defaults to .txt)
    filename2 = generate_piped_output_filename("grep")
    assert filename2 == "grep_output.txt"
    
    # Command with subcommands
    filename3 = generate_piped_output_filename(
        "bcftools filter",
        FileFormat(extension=".vcf")
    )
    assert filename3 == "bcftools_filter_output.vcf"


def test_generate_piped_output_filename_special_chars():
    """Test filename generation handles special characters."""
    # Command with dashes
    filename = generate_piped_output_filename(
        "some-tool sub-cmd",
        FileFormat(extension=".txt")
    )
    assert filename == "some_tool_sub_cmd_output.txt"
    assert " " not in filename
    assert "-" not in filename


def test_piped_output_serialization():
    """Test that supports_piped_output serializes correctly."""
    opt = OptionDoc(
        long="--output",
        type="path",
        file_role="output",
        file_format=FileFormat(extension=".txt"),
        supports_piped_output=True
    )
    
    opt_dict = opt.model_dump()
    assert "supports_piped_output" in opt_dict
    assert opt_dict["supports_piped_output"] is True


def test_edam_mappings_loaded():
    """Test that EDAM mappings are available."""
    # Check that we have some mappings
    assert len(EXTENSION_TO_EDAM) > 0
    
    # Check for key formats
    assert ".fasta" in EXTENSION_TO_EDAM or ".fa" in EXTENSION_TO_EDAM
    assert ".bam" in EXTENSION_TO_EDAM
    
    # Test get_edam_format function
    fasta = get_edam_format(".fasta")
    assert fasta is not None
    assert fasta[0] == "format_1929"
    
    bam = get_edam_format(".bam")
    assert bam is not None
    assert bam[0] == "format_2572"


def test_piped_output_with_format():
    """Test complete workflow with piped output and format."""
    opt = OptionDoc(
        long="--output",
        short="-o",
        type="path",
        required=False,
        default="stdout",
        description="Output file (default: stdout)",
        file_role="output",
        file_format=FileFormat(extension=".bam", edam_format="format_2572"),
        supports_piped_output=True
    )
    
    # Verify all fields
    assert opt.file_role == "output"
    assert opt.supports_piped_output is True
    assert opt.file_format is not None
    assert opt.file_format.extension == ".bam"
    assert opt.file_format.edam_format == "format_2572"
    
    # Generate default filename
    filename = generate_piped_output_filename("samtools view", opt.file_format)
    assert filename == "samtools_view_output.bam"


if __name__ == '__main__':
    test_supports_piped_output_option()
    print("✓ test_supports_piped_output_option passed")
    
    test_supports_piped_output_positional()
    print("✓ test_supports_piped_output_positional passed")
    
    test_generate_piped_output_filename_basic()
    print("✓ test_generate_piped_output_filename_basic passed")
    
    test_generate_piped_output_filename_special_chars()
    print("✓ test_generate_piped_output_filename_special_chars passed")
    
    test_piped_output_serialization()
    print("✓ test_piped_output_serialization passed")
    
    test_edam_mappings_loaded()
    print("✓ test_edam_mappings_loaded passed")
    
    test_piped_output_with_format()
    print("✓ test_piped_output_with_format passed")
    
    print("\nAll piped output tests passed!")
