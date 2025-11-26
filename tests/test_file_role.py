"""Test file_role field for tracking input/output files."""
from cmdsaw.parsing.schema import CommandDoc, ToolDoc, OptionDoc, PositionalDoc


def test_option_file_role_field():
    """Test that OptionDoc has file_role field with correct values."""
    # Test input file
    input_opt = OptionDoc(
        long="--input",
        short="-i",
        is_flag=False,
        type="path",
        required=True,
        description="Input file",
        file_role="input"
    )
    assert input_opt.file_role == "input"
    
    # Test output file
    output_opt = OptionDoc(
        long="--output",
        short="-o",
        is_flag=False,
        type="path",
        required=True,
        description="Output file",
        file_role="output"
    )
    assert output_opt.file_role == "output"
    
    # Test non-file parameter
    flag_opt = OptionDoc(
        long="--verbose",
        short="-v",
        is_flag=True,
        type="bool",
        required=False,
        description="Verbose output",
        file_role="none"
    )
    assert flag_opt.file_role == "none"
    
    # Test default value is "none"
    default_opt = OptionDoc(
        long="--threads",
        type="int"
    )
    assert default_opt.file_role == "none"


def test_positional_file_role_field():
    """Test that PositionalDoc has file_role field with correct values."""
    # Test input file
    input_pos = PositionalDoc(
        name="input_file",
        index=0,
        required=True,
        type="path",
        description="Input sequence file",
        file_role="input"
    )
    assert input_pos.file_role == "input"
    
    # Test output file
    output_pos = PositionalDoc(
        name="output_file",
        index=1,
        required=True,
        type="path",
        description="Output result file",
        file_role="output"
    )
    assert output_pos.file_role == "output"
    
    # Test non-file positional
    name_pos = PositionalDoc(
        name="operation",
        index=0,
        required=True,
        type="str",
        description="Operation name",
        file_role="none"
    )
    assert name_pos.file_role == "none"
    
    # Test default value is "none"
    default_pos = PositionalDoc(
        name="arg",
        index=0
    )
    assert default_pos.file_role == "none"


def test_file_role_serialization():
    """Test that file_role is preserved in serialization."""
    cmd = CommandDoc(
        name="test_cmd",
        path="test_cmd",
        help_text="Test command",
        options=[
            OptionDoc(long="--input", type="path", file_role="input"),
            OptionDoc(long="--output", type="path", file_role="output"),
            OptionDoc(long="--threads", type="int", file_role="none")
        ],
        positionals=[
            PositionalDoc(name="source", index=0, type="path", file_role="input"),
            PositionalDoc(name="dest", index=1, type="path", file_role="output")
        ],
        subcommands=[],
        requires_subcommand=False
    )
    
    # Serialize and check
    cmd_dict = cmd.model_dump()
    
    assert cmd_dict["options"][0]["file_role"] == "input"
    assert cmd_dict["options"][1]["file_role"] == "output"
    assert cmd_dict["options"][2]["file_role"] == "none"
    
    assert cmd_dict["positionals"][0]["file_role"] == "input"
    assert cmd_dict["positionals"][1]["file_role"] == "output"


def test_file_role_in_tool_doc():
    """Test that file_role works correctly in ToolDoc context."""
    tool = ToolDoc(
        command="mytool",
        version="1.0.0",
        help_text="My tool",
        invocation=["mytool"],
        options=[
            OptionDoc(long="-i", type="path", description="Input", file_role="input"),
            OptionDoc(long="-o", type="path", description="Output", file_role="output")
        ],
        positionals=[
            PositionalDoc(name="input_file", index=0, type="path", file_role="input")
        ],
        subcommands=[],
        captured_at="2025-11-26T00:00:00Z"
    )
    
    tool_dict = tool.model_dump()
    
    assert len(tool_dict["options"]) == 2
    assert tool_dict["options"][0]["file_role"] == "input"
    assert tool_dict["options"][1]["file_role"] == "output"
    
    assert len(tool_dict["positionals"]) == 1
    assert tool_dict["positionals"][0]["file_role"] == "input"


def test_file_role_literal_type():
    """Test that file_role only accepts valid literal values."""
    # Valid values should work
    OptionDoc(long="--test", file_role="input")
    OptionDoc(long="--test", file_role="output")
    OptionDoc(long="--test", file_role="none")
    
    # Invalid values should raise validation error
    try:
        OptionDoc(long="--test", file_role="invalid")
        assert False, "Should have raised validation error for invalid file_role"
    except Exception as e:
        # Pydantic validation error expected
        assert "validation error" in str(e).lower() or "literal" in str(e).lower()


if __name__ == '__main__':
    test_option_file_role_field()
    print("✓ test_option_file_role_field passed")
    
    test_positional_file_role_field()
    print("✓ test_positional_file_role_field passed")
    
    test_file_role_serialization()
    print("✓ test_file_role_serialization passed")
    
    test_file_role_in_tool_doc()
    print("✓ test_file_role_in_tool_doc passed")
    
    test_file_role_literal_type()
    print("✓ test_file_role_literal_type passed")
    
    print("\nAll file_role tests passed!")
