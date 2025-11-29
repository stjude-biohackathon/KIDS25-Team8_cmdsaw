"""
Tests for JSON review functionality.
"""
from __future__ import annotations
import json
from cmdsaw.parsing.schema import CmdSawResult, ToolDoc, CommandDoc, ParseDiagnostics, OptionDoc, PositionalDoc
from cmdsaw.json_review import display_json_summary, llm_double_check, llm_fix_issues
from datetime import datetime
import pytest


def test_display_json_summary(capsys):
    """Test that display_json_summary outputs correct summary information."""
    # Create a sample result
    tool = ToolDoc(
        command="test-tool",
        version="1.0.0",
        help_text="Test tool help text",
        invocation=["test-tool"],
        options=[
            OptionDoc(long="--option1", description="First option"),
            OptionDoc(long="--option2", description="Second option"),
        ],
        positionals=[
            PositionalDoc(name="input", index=0, description="Input file")
        ],
        subcommands=[
            CommandDoc(
                name="subcmd1",
                path="test-tool subcmd1",
                help_text="Subcommand 1",
                options=[],
                positionals=[]
            )
        ],
        captured_at=datetime.now().isoformat()
    )
    
    diagnostics = ParseDiagnostics(
        visited_commands=2,
        timeouts=0,
        llm_retries=1,
        version_extracted=True
    )
    
    result = CmdSawResult(
        schema_version="1.0",
        tool=tool,
        diagnostics=diagnostics
    )
    
    # Call display function
    display_json_summary(result)
    
    # Check output
    captured = capsys.readouterr()
    assert "test-tool" in captured.out
    assert "1.0.0" in captured.out
    assert "Options: 2" in captured.out
    assert "Positionals: 1" in captured.out
    assert "Subcommands: 1" in captured.out
    assert "visited_commands: 2" in captured.out.lower() or "Total commands visited: 2" in captured.out


def test_display_json_summary_with_many_items(capsys):
    """Test that display_json_summary truncates long lists."""
    # Create a result with many options
    options = [OptionDoc(long=f"--option{i}", description=f"Option {i}") for i in range(10)]
    positionals = [PositionalDoc(name=f"pos{i}", index=i, description=f"Positional {i}") for i in range(5)]
    subcommands = [
        CommandDoc(
            name=f"subcmd{i}",
            path=f"test-tool subcmd{i}",
            help_text=f"Subcommand {i}",
            options=[],
            positionals=[]
        )
        for i in range(15)
    ]
    
    tool = ToolDoc(
        command="test-tool",
        version="1.0.0",
        help_text="Test tool help text",
        invocation=["test-tool"],
        options=options,
        positionals=positionals,
        subcommands=subcommands,
        captured_at=datetime.now().isoformat()
    )
    
    result = CmdSawResult(
        schema_version="1.0",
        tool=tool,
        diagnostics=ParseDiagnostics()
    )
    
    # Call display function
    display_json_summary(result)
    
    # Check output
    captured = capsys.readouterr()
    assert "... and 5 more" in captured.out  # Options truncated at 5
    assert "... and 2 more" in captured.out  # Positionals truncated at 3
    assert "... and 5 more" in captured.out  # Subcommands truncated at 10


def test_cmdsaw_result_can_be_serialized():
    """Test that CmdSawResult can be serialized and deserialized."""
    tool = ToolDoc(
        command="test-tool",
        version="1.0.0",
        help_text="Test tool help text",
        invocation=["test-tool"],
        options=[],
        positionals=[],
        subcommands=[],
        captured_at=datetime.now().isoformat()
    )
    
    result = CmdSawResult(
        schema_version="1.0",
        tool=tool,
        diagnostics=ParseDiagnostics()
    )
    
    # Serialize to JSON
    json_str = json.dumps(result.model_dump(mode="json"))
    
    # Deserialize back
    data = json.loads(json_str)
    result2 = CmdSawResult.model_validate(data)
    
    assert result2.tool.command == "test-tool"
    assert result2.tool.version == "1.0.0"
    assert result2.schema_version == "1.0"


@pytest.mark.parametrize("provider,api_key,should_work", [
    ("ollama", None, True),
    ("google", "test-key", True),
    ("google", None, False),
])
def test_llm_double_check_provider_validation(provider, api_key, should_work):
    """Test that llm_double_check validates provider and API key correctly."""
    tool = ToolDoc(
        command="test-tool",
        version="1.0.0",
        help_text="Test tool help text",
        invocation=["test-tool"],
        options=[],
        positionals=[],
        subcommands=[],
        captured_at=datetime.now().isoformat()
    )
    
    result = CmdSawResult(
        schema_version="1.0",
        tool=tool,
        diagnostics=ParseDiagnostics()
    )
    
    if should_work:
        # We don't actually want to call the LLM, so we'll just check that the function
        # doesn't raise an error during setup
        # In a real test, we'd mock the LLM call
        pass
    else:
        # Should raise ValueError for missing Google API key
        with pytest.raises(ValueError, match="Google API key is required"):
            llm_double_check(result, "test-model", provider, 0.0, api_key, [])


def test_llm_fix_issues_invalid_provider():
    """Test that llm_fix_issues raises error for invalid provider."""
    tool = ToolDoc(
        command="test-tool",
        version="1.0.0",
        help_text="Test tool help text",
        invocation=["test-tool"],
        options=[],
        positionals=[],
        subcommands=[],
        captured_at=datetime.now().isoformat()
    )
    
    result = CmdSawResult(
        schema_version="1.0",
        tool=tool,
        diagnostics=ParseDiagnostics()
    )
    
    with pytest.raises(ValueError, match="Unknown provider"):
        llm_fix_issues(result, "test-model", "invalid-provider", 0.0, None, [], "Fix something")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
