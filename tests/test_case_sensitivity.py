"""Test case sensitivity in variable name generation."""
from cmdsaw.wdl import _sanitize_var_name


def test_sanitize_var_name_preserves_case():
    """Test that _sanitize_var_name preserves case to distinguish -s from -S."""
    # Test short options with different cases
    assert _sanitize_var_name("-s") == "v__s"
    assert _sanitize_var_name("-S") == "v__S"
    assert _sanitize_var_name("-s") != _sanitize_var_name("-S")
    
    # Test long options with different cases
    assert _sanitize_var_name("--output") == "output"
    assert _sanitize_var_name("--Output") == "Output"
    assert _sanitize_var_name("--output") != _sanitize_var_name("--Output")
    
    # Test hyphenated long options
    assert _sanitize_var_name("--output-file") == "output_file"
    assert _sanitize_var_name("--Output-File") == "Output_File"
    assert _sanitize_var_name("--output-file") != _sanitize_var_name("--Output-File")


def test_case_sensitive_short_options_in_wdl():
    """Test that case-sensitive short options generate different WDL variables."""
    from cmdsaw.parsing.schema import CommandDoc, OptionDoc
    from cmdsaw.wdl import _task_for
    from cmdsaw.parsing.resource_estimator import ResourceEstimate
    import cmdsaw.wdl as wdl_module
    
    # Mock the resource estimator to avoid LLM dependency
    original_estimate = wdl_module.estimate_resources
    wdl_module.estimate_resources = lambda *args, **kwargs: ResourceEstimate(cpu=2, mem_gb=4.0)
    
    try:
        # Create a command with case-sensitive short options only
        # This mimics tools like samtools that use -s and -S for different purposes
        cmd = CommandDoc(
            name='test',
            path='tool test',
            help_text='Test command',
            options=[
                OptionDoc(short='-s', type='float', required=False, description='lowercase s'),
                OptionDoc(short='-S', type='bool', is_flag=True, required=False, description='uppercase S'),
            ],
            positionals=[],
            subcommands=[],
            requires_subcommand=False
        )
        
        wdl_output = _task_for(cmd, "test-model", container_info=None)
        
        # Verify both variables are present and distinct
        assert 'v__s' in wdl_output, "Variable v__s (from -s) should be in WDL output"
        assert 'v__S' in wdl_output, "Variable v__S (from -S) should be in WDL output"
        
        # Verify they appear in different contexts (input declaration and command line)
        assert 'Float? v__s' in wdl_output, "v__s should be declared as Float"
        assert 'Boolean? v__S' in wdl_output, "v__S should be declared as Boolean"
        assert '"-s "' in wdl_output, "Command should include -s flag"
        assert '"-S"' in wdl_output, "Command should include -S flag"
        
    finally:
        # Restore original function
        wdl_module.estimate_resources = original_estimate


if __name__ == '__main__':
    test_sanitize_var_name_preserves_case()
    print("✓ test_sanitize_var_name_preserves_case passed")
    
    test_case_sensitive_short_options_in_wdl()
    print("✓ test_case_sensitive_short_options_in_wdl passed")
    
    print("\nAll case sensitivity tests passed!")
