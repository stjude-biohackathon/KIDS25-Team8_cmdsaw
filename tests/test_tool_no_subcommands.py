"""Test handling of tools with no subcommands."""
from cmdsaw.parsing.schema import CommandDoc, ToolDoc, CmdSawResult, ParseDiagnostics, OptionDoc, PositionalDoc


def test_tool_with_no_subcommands_preserves_parameters():
    """Test that a tool with no subcommands preserves its options and positionals in ToolDoc."""
    # Create a root command with parameters but no subcommands (like grep, cat, etc.)
    root_doc = CommandDoc(
        name='mytool',
        path='mytool',
        help_text='My tool does stuff',
        options=[
            OptionDoc(long='--output', short='-o', is_flag=False, type='path', required=True),
            OptionDoc(long='--verbose', short='-v', is_flag=True, type='bool', required=False),
        ],
        positionals=[
            PositionalDoc(name='input', index=0, required=True, type='path', description='Input file'),
        ],
        subcommands=[],
        requires_subcommand=False
    )
    
    # Create ToolDoc with root command's parameters
    tool = ToolDoc(
        command='mytool',
        version='1.0.0',
        help_text='My tool does stuff',
        invocation=['mytool'],
        options=root_doc.options,
        positionals=root_doc.positionals,
        subcommands=[],
        captured_at='2025-11-10T00:00:00Z'
    )
    
    # Verify the parameters are preserved
    assert len(tool.options) == 2, "Tool should have 2 options"
    assert len(tool.positionals) == 1, "Tool should have 1 positional"
    assert tool.subcommands == [], "Tool should have no subcommands"
    
    # Verify serialization includes the parameters
    tool_dict = tool.model_dump()
    assert 'options' in tool_dict, "Serialized tool should have options field"
    assert 'positionals' in tool_dict, "Serialized tool should have positionals field"
    assert len(tool_dict['options']) == 2, "Serialized tool should have 2 options"
    assert len(tool_dict['positionals']) == 1, "Serialized tool should have 1 positional"


def test_tool_with_subcommands_preserves_root_parameters():
    """Test that a tool with subcommands preserves both root and subcommand parameters."""
    # Create a root command with some parameters and subcommands (like git)
    root_doc = CommandDoc(
        name='mytool',
        path='mytool',
        help_text='My tool with subcommands',
        options=[
            OptionDoc(long='--help', short='-h', is_flag=True, type='bool', required=False),
        ],
        positionals=[],
        subcommands=['subcmd1', 'subcmd2'],
        requires_subcommand=True
    )
    
    # Create a subcommand with its own parameters
    subcommand = CommandDoc(
        name='subcmd1',
        path='mytool subcmd1',
        help_text='Subcommand help',
        options=[
            OptionDoc(long='--output', short='-o', is_flag=False, type='path', required=False),
        ],
        positionals=[
            PositionalDoc(name='input', index=0, required=True, type='path', description='Input file'),
        ],
        subcommands=[],
        requires_subcommand=False
    )
    
    # Create ToolDoc with both root and subcommand parameters
    tool = ToolDoc(
        command='mytool',
        version='1.0.0',
        help_text='My tool with subcommands',
        invocation=['mytool'],
        options=root_doc.options,
        positionals=root_doc.positionals,
        subcommands=[subcommand],
        captured_at='2025-11-10T00:00:00Z'
    )
    
    # Verify root parameters are preserved
    assert len(tool.options) == 1, "Root tool should have 1 option"
    assert len(tool.positionals) == 0, "Root tool should have 0 positionals"
    
    # Verify subcommand parameters are preserved
    assert len(tool.subcommands) == 1, "Tool should have 1 subcommand"
    assert len(tool.subcommands[0].options) == 1, "Subcommand should have 1 option"
    assert len(tool.subcommands[0].positionals) == 1, "Subcommand should have 1 positional"
    
    # Verify serialization includes all parameters
    tool_dict = tool.model_dump()
    assert len(tool_dict['options']) == 1, "Serialized root should have 1 option"
    assert len(tool_dict['subcommands']) == 1, "Serialized tool should have 1 subcommand"
    assert len(tool_dict['subcommands'][0]['options']) == 1, "Serialized subcommand should have 1 option"
    assert len(tool_dict['subcommands'][0]['positionals']) == 1, "Serialized subcommand should have 1 positional"


def test_cmdsaw_result_serialization_with_no_subcommands():
    """Test that CmdSawResult properly serializes tools with no subcommands."""
    root_doc = CommandDoc(
        name='simpletool',
        path='simpletool',
        help_text='A simple tool',
        options=[
            OptionDoc(long='--flag', short='-f', is_flag=True, type='bool', required=False),
        ],
        positionals=[
            PositionalDoc(name='file', index=0, required=True, type='path', description='File to process'),
        ],
        subcommands=[],
        requires_subcommand=False
    )
    
    tool = ToolDoc(
        command='simpletool',
        version='2.0.0',
        help_text='A simple tool',
        invocation=['simpletool'],
        options=root_doc.options,
        positionals=root_doc.positionals,
        subcommands=[],
        captured_at='2025-11-10T00:00:00Z'
    )
    
    result = CmdSawResult(
        schema_version='1.0.0',
        tool=tool,
        diagnostics=ParseDiagnostics()
    )
    
    # Verify the complete result serializes correctly
    result_dict = result.model_dump()
    assert 'tool' in result_dict
    assert 'options' in result_dict['tool']
    assert 'positionals' in result_dict['tool']
    assert len(result_dict['tool']['options']) == 1
    assert len(result_dict['tool']['positionals']) == 1
    assert result_dict['tool']['options'][0]['long'] == '--flag'
    assert result_dict['tool']['positionals'][0]['name'] == 'file'


if __name__ == '__main__':
    test_tool_with_no_subcommands_preserves_parameters()
    print("✓ test_tool_with_no_subcommands_preserves_parameters passed")
    
    test_tool_with_subcommands_preserves_root_parameters()
    print("✓ test_tool_with_subcommands_preserves_root_parameters passed")
    
    test_cmdsaw_result_serialization_with_no_subcommands()
    print("✓ test_cmdsaw_result_serialization_with_no_subcommands passed")
    
    print("\nAll tests passed!")
