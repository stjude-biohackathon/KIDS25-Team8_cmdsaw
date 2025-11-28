"""Test piped output support and EDAM.tsv loading."""
from cmdsaw.parsing.schema import (
    OptionDoc, CommandDoc, ToolDoc, FileFormat, 
    generate_piped_output_filename
)
from cmdsaw.parsing.edam_mappings import get_edam_format, EXTENSION_TO_EDAM


def test_supports_piped_output_command():
    """Test that CommandDoc supports piped output flag."""
    # Command with piped output support
    cmd = CommandDoc(
        name="view",
        path="samtools view",
        help_text="View SAM/BAM files",
        options=[
            OptionDoc(long="--output", type="path", file_role="output")
        ],
        supports_piped_output=True
    )
    assert cmd.supports_piped_output is True
    
    # Command without piped support
    cmd2 = CommandDoc(
        name="view",
        path="samtools view",
        help_text="View SAM/BAM files",
        options=[
            OptionDoc(long="--output", type="path", file_role="output")
        ],
        supports_piped_output=False
    )
    assert cmd2.supports_piped_output is False
    
    # Default is False
    cmd3 = CommandDoc(name="test", path="test", help_text="Test command")
    assert cmd3.supports_piped_output is False


def test_supports_piped_output_tool():
    """Test that ToolDoc supports piped output flag."""
    tool = ToolDoc(
        command="samtools",
        help_text="Samtools help text",
        invocation=["samtools"],
        captured_at="2024-01-01",
        options=[
            OptionDoc(long="--output", type="path", file_role="output")
        ],
        supports_piped_output=True
    )
    assert tool.supports_piped_output is True
    
    # Default is False
    tool2 = ToolDoc(
        command="test",
        help_text="Test tool",
        invocation=["test"],
        captured_at="2024-01-01"
    )
    assert tool2.supports_piped_output is False


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
    """Test that supports_piped_output serializes correctly on commands."""
    cmd = CommandDoc(
        name="view",
        path="samtools view",
        help_text="View SAM/BAM files",
        options=[
            OptionDoc(long="--output", type="path", file_role="output",
                     file_format=FileFormat(extension=".txt"))
        ],
        supports_piped_output=True
    )
    
    cmd_dict = cmd.model_dump()
    assert "supports_piped_output" in cmd_dict
    assert cmd_dict["supports_piped_output"] is True


def test_edam_mappings_loaded():
    """Test that EDAM mappings are available."""
    # Check that we have some mappings
    assert len(EXTENSION_TO_EDAM) > 0
    
    # Check for key formats (from EDAM.tsv)
    assert ".fasta" in EXTENSION_TO_EDAM or ".fa" in EXTENSION_TO_EDAM
    assert ".bam" in EXTENSION_TO_EDAM
    
    # Test get_edam_format function
    fasta = get_edam_format(".fasta")
    assert fasta is not None
    # EDAM.tsv may have multiple FASTA formats, just verify we got a valid one
    assert fasta[0].startswith("format_")
    assert "FASTA" in fasta[1]
    
    bam = get_edam_format(".bam")
    assert bam is not None
    assert bam[0] == "format_2572"  # BAM format should be consistent


def test_piped_output_with_format():
    """Test complete workflow with piped output and format."""
    cmd = CommandDoc(
        name="view",
        path="samtools view",
        help_text="View SAM/BAM files",
        options=[
            OptionDoc(
                long="--output",
                short="-o",
                type="path",
                required=False,
                default="stdout",
                description="Output file (default: stdout)",
                file_role="output",
                file_format=FileFormat(extension=".bam", edam_format="format_2572")
            )
        ],
        supports_piped_output=True
    )
    
    # Verify command has piped output enabled
    assert cmd.supports_piped_output is True
    
    # Verify option has file_role and format
    opt = cmd.options[0]
    assert opt.file_role == "output"
    assert opt.file_format is not None
    assert opt.file_format.extension == ".bam"
    assert opt.file_format.edam_format == "format_2572"
    
    # Generate default filename
    filename = generate_piped_output_filename("samtools view", opt.file_format)
    assert filename == "samtools_view_output.bam"


if __name__ == '__main__':
    test_supports_piped_output_command()
    print("✓ test_supports_piped_output_command passed")
    
    test_supports_piped_output_tool()
    print("✓ test_supports_piped_output_tool passed")
    
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
