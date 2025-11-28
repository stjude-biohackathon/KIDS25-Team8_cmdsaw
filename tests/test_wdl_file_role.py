"""Test WDL generation includes file_role metadata."""
import re
from cmdsaw.parsing.schema import CommandDoc, OptionDoc, PositionalDoc
from cmdsaw.parsing.resource_estimator import ResourceEstimate
from cmdsaw.wdl import _inputs_block, _task_for


def test_inputs_block_includes_file_role():
    """Test that _inputs_block includes file_role in metadata."""
    # Create a command with various file roles
    cmd = CommandDoc(
        name="test_tool",
        path="test_tool",
        help_text="Test tool for file role tracking",
        options=[
            OptionDoc(
                long="--input",
                short="-i",
                type="path",
                required=True,
                description="Input file",
                file_role="input"
            ),
            OptionDoc(
                long="--output",
                short="-o",
                type="path",
                required=True,
                description="Output file",
                file_role="output"
            ),
            OptionDoc(
                long="--threads",
                short="-t",
                type="int",
                required=False,
                default="4",
                description="Number of threads",
                file_role="none"
            ),
        ],
        positionals=[
            PositionalDoc(
                name="reference",
                index=0,
                type="path",
                required=True,
                description="Reference genome",
                file_role="input"
            ),
        ],
        subcommands=[],
        requires_subcommand=False
    )
    
    # Create a mock resource estimate
    est = ResourceEstimate(cpu=4, mem_gb=8.0)
    
    # Generate inputs block and metadata
    inputs_str, metas = _inputs_block(cmd, est)
    
    # Join metadata for easier checking
    meta_str = "\n".join(metas)
    
    # Verify file_role is in metadata
    assert 'file_role=input' in meta_str, "Metadata should contain file_role=input"
    assert 'file_role=output' in meta_str, "Metadata should contain file_role=output"
    assert 'file_role=none' in meta_str, "Metadata should contain file_role=none"
    
    # Count occurrences
    input_count = meta_str.count('file_role=input')
    output_count = meta_str.count('file_role=output')
    none_count = meta_str.count('file_role=none')
    
    # We have 2 inputs (--input option and reference positional), 1 output, 1 none
    assert input_count == 2, f"Should have 2 inputs, got {input_count}"
    assert output_count == 1, f"Should have 1 output, got {output_count}"
    assert none_count == 1, f"Should have 1 none, got {none_count}"
    
    print("Metadata generated:")
    print("-" * 50)
    for meta in metas:
        print(meta)
    print("-" * 50)


def test_positional_file_role_in_metadata():
    """Test that positional arguments include file_role in metadata."""
    cmd = CommandDoc(
        name="simple_tool",
        path="simple_tool",
        help_text="Simple tool with positionals",
        options=[],
        positionals=[
            PositionalDoc(
                name="input_file",
                index=0,
                type="path",
                required=True,
                description="Input file path",
                file_role="input"
            ),
            PositionalDoc(
                name="output_file",
                index=1,
                type="path",
                required=True,
                description="Output file path",
                file_role="output"
            ),
        ],
        subcommands=[],
        requires_subcommand=False
    )
    
    est = ResourceEstimate(cpu=1, mem_gb=2.0)
    inputs_str, metas = _inputs_block(cmd, est)
    
    meta_str = "\n".join(metas)
    
    # Verify positionals have file_role in metadata
    assert 'file_role=input' in meta_str
    assert 'file_role=output' in meta_str
    assert 'positional index=0' in meta_str
    assert 'positional index=1' in meta_str
    
    # Check that the input file is at index 0 and output at index 1
    for meta in metas:
        if 'positional index=0' in meta:
            assert 'file_role=input' in meta
        if 'positional index=1' in meta:
            assert 'file_role=output' in meta


def test_file_role_all_types():
    """Test that file_role works for various parameter types."""
    cmd = CommandDoc(
        name="complex_tool",
        path="complex_tool",
        help_text="Complex tool",
        options=[
            # Required input file
            OptionDoc(long="--in1", type="path", required=True, file_role="input"),
            # Optional input file
            OptionDoc(long="--in2", type="path", required=False, file_role="input"),
            # Required output file
            OptionDoc(long="--out1", type="path", required=True, file_role="output"),
            # Optional output file
            OptionDoc(long="--out2", type="path", required=False, file_role="output"),
            # Non-path parameter
            OptionDoc(long="--config", type="str", required=False, file_role="none"),
        ],
        positionals=[],
        subcommands=[],
        requires_subcommand=False
    )
    
    est = ResourceEstimate(cpu=2, mem_gb=4.0)
    inputs_str, metas = _inputs_block(cmd, est)
    
    meta_str = "\n".join(metas)
    
    # Count file roles
    input_count = meta_str.count('file_role=input')
    output_count = meta_str.count('file_role=output')
    none_count = meta_str.count('file_role=none')
    
    assert input_count == 2, f"Should have 2 inputs, got {input_count}"
    assert output_count == 2, f"Should have 2 outputs, got {output_count}"
    assert none_count == 1, f"Should have 1 none, got {none_count}"


if __name__ == '__main__':
    print("Testing WDL generation with file_role metadata...")
    test_inputs_block_includes_file_role()
    print("✓ test_inputs_block_includes_file_role passed\n")
    
    test_positional_file_role_in_metadata()
    print("✓ test_positional_file_role_in_metadata passed\n")
    
    test_file_role_all_types()
    print("✓ test_file_role_all_types passed\n")
    
    print("All WDL file_role tests passed!")

