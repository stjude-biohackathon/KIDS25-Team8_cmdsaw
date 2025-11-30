"""Test container info functionality."""
from cmdsaw.parsing.schema import ToolDoc, CmdSawResult, ParseDiagnostics, ContainerInfo


def test_container_info_schema():
    """Test that ContainerInfo can be created and serialized."""
    container_info = ContainerInfo(
        bioconda="bioconda::samtools=1.19",
        docker="quay.io/biocontainers/samtools:1.19--h50ea8bc_1",
        singularity="https://depot.galaxyproject.org/singularity/samtools:1.19--h50ea8bc_1"
    )
    
    # Verify fields are accessible
    assert container_info.bioconda == "bioconda::samtools=1.19"
    assert container_info.docker == "quay.io/biocontainers/samtools:1.19--h50ea8bc_1"
    assert container_info.singularity == "https://depot.galaxyproject.org/singularity/samtools:1.19--h50ea8bc_1"
    
    # Verify serialization
    container_dict = container_info.model_dump()
    assert container_dict['bioconda'] == "bioconda::samtools=1.19"
    assert container_dict['docker'] == "quay.io/biocontainers/samtools:1.19--h50ea8bc_1"
    assert container_dict['singularity'] == "https://depot.galaxyproject.org/singularity/samtools:1.19--h50ea8bc_1"


def test_tool_doc_with_container_info():
    """Test that ToolDoc can store container information."""
    container_info = ContainerInfo(
        bioconda="bioconda::samtools=1.19",
        docker="quay.io/biocontainers/samtools:1.19--h50ea8bc_1",
        singularity="https://depot.galaxyproject.org/singularity/samtools:1.19--h50ea8bc_1"
    )
    
    tool = ToolDoc(
        command='samtools',
        version='1.19',
        help_text='samtools help text',
        invocation=['samtools'],
        options=[],
        positionals=[],
        subcommands=[],
        captured_at='2025-11-10T00:00:00Z',
        container_info=container_info
    )
    
    # Verify container info is stored
    assert tool.container_info is not None
    assert tool.container_info.docker == "quay.io/biocontainers/samtools:1.19--h50ea8bc_1"
    
    # Verify serialization includes container info
    tool_dict = tool.model_dump()
    assert 'container_info' in tool_dict
    assert tool_dict['container_info']['docker'] == "quay.io/biocontainers/samtools:1.19--h50ea8bc_1"


def test_tool_doc_without_container_info():
    """Test that ToolDoc works without container information."""
    tool = ToolDoc(
        command='mytool',
        version='1.0.0',
        help_text='mytool help text',
        invocation=['mytool'],
        options=[],
        positionals=[],
        subcommands=[],
        captured_at='2025-11-10T00:00:00Z'
    )
    
    # Verify container info is None by default
    assert tool.container_info is None
    
    # Verify serialization works
    tool_dict = tool.model_dump()
    assert 'container_info' in tool_dict
    assert tool_dict['container_info'] is None


def test_cmdsaw_result_with_container_info():
    """Test that CmdSawResult properly serializes container information."""
    container_info = ContainerInfo(
        bioconda="bioconda::samtools=1.19",
        docker="quay.io/biocontainers/samtools:1.19--h50ea8bc_1",
        singularity="https://depot.galaxyproject.org/singularity/samtools:1.19--h50ea8bc_1"
    )
    
    tool = ToolDoc(
        command='samtools',
        version='1.19',
        help_text='samtools help text',
        invocation=['samtools'],
        options=[],
        positionals=[],
        subcommands=[],
        captured_at='2025-11-10T00:00:00Z',
        container_info=container_info
    )
    
    result = CmdSawResult(
        schema_version='1.0.0',
        tool=tool,
        diagnostics=ParseDiagnostics()
    )
    
    # Verify the complete result serializes correctly with container info
    result_dict = result.model_dump()
    assert 'tool' in result_dict
    assert 'container_info' in result_dict['tool']
    assert result_dict['tool']['container_info'] is not None
    assert result_dict['tool']['container_info']['docker'] == "quay.io/biocontainers/samtools:1.19--h50ea8bc_1"
    assert result_dict['tool']['container_info']['bioconda'] == "bioconda::samtools=1.19"
    assert result_dict['tool']['container_info']['singularity'] == "https://depot.galaxyproject.org/singularity/samtools:1.19--h50ea8bc_1"


if __name__ == '__main__':
    test_container_info_schema()
    print("✓ test_container_info_schema passed")
    
    test_tool_doc_with_container_info()
    print("✓ test_tool_doc_with_container_info passed")
    
    test_tool_doc_without_container_info()
    print("✓ test_tool_doc_without_container_info passed")
    
    test_cmdsaw_result_with_container_info()
    print("✓ test_cmdsaw_result_with_container_info passed")
    
    print("\nAll tests passed!")
