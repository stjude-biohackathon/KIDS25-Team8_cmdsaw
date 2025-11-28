"""Test WDL generation uses requirements section per WDL 1.2 spec."""
from cmdsaw.parsing.schema import CommandDoc, OptionDoc, ContainerInfo
from cmdsaw.parsing.resource_estimator import ResourceEstimate
from unittest.mock import patch


def test_wdl_uses_requirements_section():
    """Test that WDL generation uses 'requirements' section instead of deprecated 'runtime'."""
    # Import _task_for here to enable patching
    from cmdsaw.wdl import _task_for
    
    cmd = CommandDoc(
        name="test_tool",
        path="test_tool",
        help_text="Test tool",
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
        requires_subcommand=False
    )
    
    # Mock estimate_resources to avoid calling Ollama
    with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
        mock_estimate.return_value = ResourceEstimate(cpu=2, mem_gb=4.0)
        
        # Generate WDL task without container
        wdl_output = _task_for(cmd, model_name="gemma3:12b")
        
        # Verify requirements section is present
        assert "requirements {" in wdl_output, "WDL should contain 'requirements' section"
        
        # Verify runtime section is NOT present
        assert "runtime {" not in wdl_output, "WDL should not contain deprecated 'runtime' section"
        
        # Verify cpu and memory are in requirements
        assert "cpu:" in wdl_output, "requirements section should contain 'cpu'"
        assert "memory:" in wdl_output, "requirements section should contain 'memory'"


def test_wdl_requirements_with_container():
    """Test that container attribute is used in requirements section."""
    from cmdsaw.wdl import _task_for
    
    container_info = ContainerInfo(
        bioconda=None,
        docker="quay.io/biocontainers/samtools:1.19--h50ea8bc_1",
        singularity=None
    )
    
    cmd = CommandDoc(
        name="samtools",
        path="samtools view",
        help_text="View SAM/BAM/CRAM files",
        options=[],
        positionals=[],
        subcommands=[],
        requires_subcommand=False
    )
    
    # Mock estimate_resources to avoid calling Ollama
    with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
        mock_estimate.return_value = ResourceEstimate(cpu=4, mem_gb=8.0)
        
        # Generate WDL task with container
        wdl_output = _task_for(cmd, model_name="gemma3:12b", container_info=container_info)
        
        # Verify requirements section contains container attribute
        assert "requirements {" in wdl_output
        assert 'container: "quay.io/biocontainers/samtools:1.19--h50ea8bc_1"' in wdl_output
        
        # Verify it's using 'container' not 'docker' (WDL 1.2 spec)
        assert "container:" in wdl_output, "requirements should use 'container' attribute"


def test_wdl_requirements_format():
    """Test that requirements section has correct WDL 1.2 format."""
    from cmdsaw.wdl import _task_for
    
    cmd = CommandDoc(
        name="test_tool",
        path="test_tool",
        help_text="Test tool",
        options=[],
        positionals=[],
        subcommands=[],
        requires_subcommand=False
    )
    
    # Mock estimate_resources to avoid calling Ollama
    with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
        mock_estimate.return_value = ResourceEstimate(cpu=1, mem_gb=2.0)
        
        wdl_output = _task_for(cmd, model_name="gemma3:12b")
        
        # Verify cpu format
        assert 'cpu:' in wdl_output
        assert 'select_first([cpu,' in wdl_output
        
        # Verify memory format with units
        assert 'memory:' in wdl_output
        assert 'select_first([memory_gb,' in wdl_output
        assert 'G"' in wdl_output  # Memory should have 'G' suffix


if __name__ == '__main__':
    test_wdl_uses_requirements_section()
    print("✓ test_wdl_uses_requirements_section passed")
    
    test_wdl_requirements_with_container()
    print("✓ test_wdl_requirements_with_container passed")
    
    test_wdl_requirements_format()
    print("✓ test_wdl_requirements_format passed")
    
    print("\nAll WDL requirements section tests passed!")
