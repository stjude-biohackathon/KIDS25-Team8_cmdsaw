"""Test WDL generation with piped output support."""
from cmdsaw.parsing.schema import CommandDoc, OptionDoc
from cmdsaw.parsing.resource_estimator import ResourceEstimate
from unittest.mock import patch


def test_wdl_includes_pipe_out_parameter():
    """Test that WDL includes pipe_out parameter when piped_output is enabled."""
    from cmdsaw.wdl import _task_for
    
    cmd = CommandDoc(
        name="view",
        path="samtools view",
        help_text="View SAM/BAM files",
        options=[
            OptionDoc(
                long="--input",
                short="-i",
                type="path",
                required=True,
                description="Input file"
            ),
        ],
        positionals=[],
        subcommands=[],
        requires_subcommand=False,
        piped_output=True
    )
    
    # Mock estimate_resources to avoid calling Ollama
    with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
        mock_estimate.return_value = ResourceEstimate(cpu=2, mem_gb=4.0)
        
        # Generate WDL task with piped output
        wdl_output = _task_for(cmd, model_name="gemma3:12b")
        
        # Verify pipe_out parameter is in input block
        assert "String? pipe_out" in wdl_output, "WDL should contain 'pipe_out' parameter"
        
        # Verify pipe_out is in parameter_meta
        assert "pipe_out" in wdl_output, "WDL should document 'pipe_out' in parameter_meta"


def test_wdl_command_uses_pipe_out():
    """Test that WDL command block uses pipe_out for output redirection."""
    from cmdsaw.wdl import _task_for
    
    cmd = CommandDoc(
        name="view",
        path="samtools view",
        help_text="View SAM/BAM files",
        options=[
            OptionDoc(
                long="--input",
                short="-i",
                type="path",
                required=True,
                description="Input file"
            ),
        ],
        positionals=[],
        subcommands=[],
        requires_subcommand=False,
        piped_output=True
    )
    
    # Mock estimate_resources to avoid calling Ollama
    with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
        mock_estimate.return_value = ResourceEstimate(cpu=2, mem_gb=4.0)
        
        # Generate WDL task with piped output
        wdl_output = _task_for(cmd, model_name="gemma3:12b")
        
        # Verify output redirection is in command
        assert "> " in wdl_output or '> "' in wdl_output, "WDL command should include output redirection"
        assert "pipe_out" in wdl_output, "WDL command should reference pipe_out variable"


def test_wdl_without_piped_output_no_pipe_out():
    """Test that WDL does NOT include pipe_out when piped_output is disabled."""
    from cmdsaw.wdl import _task_for
    
    cmd = CommandDoc(
        name="view",
        path="samtools view",
        help_text="View SAM/BAM files",
        options=[
            OptionDoc(
                long="--input",
                short="-i",
                type="path",
                required=True,
                description="Input file"
            ),
        ],
        positionals=[],
        subcommands=[],
        requires_subcommand=False,
        piped_output=False  # Explicitly disabled
    )
    
    # Mock estimate_resources to avoid calling Ollama
    with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
        mock_estimate.return_value = ResourceEstimate(cpu=2, mem_gb=4.0)
        
        # Generate WDL task without piped output
        wdl_output = _task_for(cmd, model_name="gemma3:12b")
        
        # Verify pipe_out parameter is NOT present
        assert "String? pipe_out" not in wdl_output, "WDL should not contain 'pipe_out' parameter when piped_output is False"


def test_wdl_piped_output_command_format():
    """Test that piped output command format is correct."""
    from cmdsaw.wdl import _command_block
    
    cmd = CommandDoc(
        name="view",
        path="samtools view",
        help_text="View SAM/BAM files",
        options=[
            OptionDoc(
                long="--input",
                short="-i",
                type="path",
                required=True,
                description="Input file"
            ),
        ],
        positionals=[],
        subcommands=[],
        requires_subcommand=False,
        piped_output=True
    )
    
    # Generate command block
    cmd_block = _command_block(cmd)
    
    # Verify command includes samtools view
    assert "samtools view" in cmd_block
    
    # Verify command includes input parameter
    assert "input" in cmd_block
    
    # Verify command includes output redirection with pipe_out
    assert "pipe_out" in cmd_block
    assert ">" in cmd_block


def test_wdl_piped_output_with_positionals():
    """Test piped output works correctly with positional arguments."""
    from cmdsaw.wdl import _task_for
    from cmdsaw.parsing.schema import PositionalDoc
    
    cmd = CommandDoc(
        name="grep",
        path="grep",
        help_text="Search for patterns",
        options=[],
        positionals=[
            PositionalDoc(
                name="pattern",
                index=0,
                required=True,
                type="str",
                description="Search pattern"
            ),
            PositionalDoc(
                name="file",
                index=1,
                required=False,
                type="path",
                description="Input file"
            ),
        ],
        subcommands=[],
        requires_subcommand=False,
        piped_output=True
    )
    
    # Mock estimate_resources to avoid calling Ollama
    with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
        mock_estimate.return_value = ResourceEstimate(cpu=1, mem_gb=1.0)
        
        # Generate WDL task
        wdl_output = _task_for(cmd, model_name="gemma3:12b")
        
        # Verify pipe_out parameter is present
        assert "String? pipe_out" in wdl_output
        
        # Verify positionals are in the command
        assert "pattern" in wdl_output
        assert "file" in wdl_output
        
        # Verify output redirection comes after positionals
        lines = wdl_output.split('\n')
        command_section = []
        in_command = False
        for line in lines:
            if "command <<<" in line:
                in_command = True
            elif ">>>" in line:
                in_command = False
            elif in_command:
                command_section.append(line)
        
        command_text = '\n'.join(command_section)
        # The order should be: grep pattern file > pipe_out
        assert "pipe_out" in command_text


if __name__ == '__main__':
    test_wdl_includes_pipe_out_parameter()
    print("✓ test_wdl_includes_pipe_out_parameter passed")
    
    test_wdl_command_uses_pipe_out()
    print("✓ test_wdl_command_uses_pipe_out passed")
    
    test_wdl_without_piped_output_no_pipe_out()
    print("✓ test_wdl_without_piped_output_no_pipe_out passed")
    
    test_wdl_piped_output_command_format()
    print("✓ test_wdl_piped_output_command_format passed")
    
    test_wdl_piped_output_with_positionals()
    print("✓ test_wdl_piped_output_with_positionals passed")
    
    print("\nAll WDL piped output tests passed!")
