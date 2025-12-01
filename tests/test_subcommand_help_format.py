"""Test subcommand help format parameter functionality."""

from cmdsaw.runner import try_help
from cmdsaw.utils import run_capture
from unittest.mock import patch, MagicMock


def test_try_help_root_command_ignores_format():
    """Test that root command help invocation ignores format parameter."""
    # Mock run_capture to return help text
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("help text", 0)
        
        # Test with root command (single element list)
        help_text, code = try_help(
            ['ls'], 
            ['--help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='help-subcommand'
        )
        
        # Should always append help flag at the end for root command
        mock_run.assert_called_once_with(['ls', '--help'], timeout=30, env=None, cwd=None)
        assert help_text == "help text"
        assert code == 0


def test_try_help_subcommand_default_format():
    """Test that subcommand uses default format: TOOL SUBCOMMAND --help"""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("subcommand help", 0)
        
        # Test with subcommand using default format
        help_text, code = try_help(
            ['git', 'commit'], 
            ['--help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='subcommand-help'
        )
        
        # Should use format: git commit --help
        mock_run.assert_called_once_with(['git', 'commit', '--help'], timeout=30, env=None, cwd=None)
        assert help_text == "subcommand help"


def test_try_help_subcommand_alternate_format():
    """Test that subcommand uses alternate format: TOOL --help SUBCOMMAND"""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("subcommand help", 0)
        
        # Test with subcommand using alternate format
        help_text, code = try_help(
            ['git', 'commit'], 
            ['--help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='help-subcommand'
        )
        
        # Should use format: git --help commit
        mock_run.assert_called_once_with(['git', '--help', 'commit'], timeout=30, env=None, cwd=None)
        assert help_text == "subcommand help"


def test_try_help_nested_subcommand_default_format():
    """Test nested subcommand with default format."""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("nested help", 0)
        
        # Test with nested subcommand
        help_text, code = try_help(
            ['git', 'remote', 'add'], 
            ['--help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='subcommand-help'
        )
        
        # Should use format: git remote add --help
        mock_run.assert_called_once_with(['git', 'remote', 'add', '--help'], timeout=30, env=None, cwd=None)
        assert help_text == "nested help"


def test_try_help_nested_subcommand_alternate_format():
    """Test nested subcommand with alternate format."""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("nested help", 0)
        
        # Test with nested subcommand using alternate format
        help_text, code = try_help(
            ['git', 'remote', 'add'], 
            ['--help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='help-subcommand'
        )
        
        # Should use format: git --help remote add
        mock_run.assert_called_once_with(['git', '--help', 'remote', 'add'], timeout=30, env=None, cwd=None)
        assert help_text == "nested help"


def test_try_help_multiple_flags_tries_all():
    """Test that multiple help flags are tried in order."""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        # First call returns empty, second returns help
        mock_run.side_effect = [("", 1), ("help text", 0)]
        
        help_text, code = try_help(
            ['git', 'commit'], 
            ['--help', '-h'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='subcommand-help'
        )
        
        # Should try both flags
        assert mock_run.call_count == 2
        assert help_text == "help text"


def test_try_help_help_keyword_default_format():
    """Test that 'help' keyword works with default format."""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("help text", 0)
        
        help_text, code = try_help(
            ['git', 'commit'], 
            ['help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='subcommand-help'
        )
        
        # Should use: git commit help
        mock_run.assert_called_once_with(['git', 'commit', 'help'], timeout=30, env=None, cwd=None)


def test_try_help_help_keyword_alternate_format():
    """Test that 'help' keyword works with alternate format."""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("help text", 0)
        
        help_text, code = try_help(
            ['git', 'commit'], 
            ['help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='help-subcommand'
        )
        
        # Should use: git help commit
        mock_run.assert_called_once_with(['git', 'help', 'commit'], timeout=30, env=None, cwd=None)


def test_try_help_returns_empty_when_no_output():
    """Test that empty string is returned when no help output is obtained."""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("", 1)
        
        help_text, code = try_help(
            ['nonexistent', 'command'], 
            ['--help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='subcommand-help'
        )
        
        assert help_text == ""
        assert code == 1


def test_try_help_tool_subcommand_format():
    """Test that tool-subcommand format works: TOOL SUBCOMMAND (no help flag)"""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("subcommand output", 0)
        
        help_text, code = try_help(
            ['git', 'status'], 
            ['--help'],  # This should be ignored for tool-subcommand format
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='tool-subcommand'
        )
        
        # Should use format: git status (no help flag)
        mock_run.assert_called_once_with(['git', 'status'], timeout=30, env=None, cwd=None)
        assert help_text == "subcommand output"
        assert code == 0


def test_try_help_subcommand_only_format():
    """Test that subcommand-only format works: SUBCOMMAND (no tool prefix)"""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("subcommand output", 0)
        
        help_text, code = try_help(
            ['mytool', 'status'], 
            ['--help'],  # This should be ignored for subcommand-only format
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='subcommand-only'
        )
        
        # Should use format: status (just the subcommand)
        mock_run.assert_called_once_with(['status'], timeout=30, env=None, cwd=None)
        assert help_text == "subcommand output"
        assert code == 0


def test_try_help_nested_subcommand_tool_subcommand_format():
    """Test nested subcommand with tool-subcommand format."""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("nested output", 0)
        
        help_text, code = try_help(
            ['git', 'remote', 'add'], 
            ['--help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='tool-subcommand'
        )
        
        # Should use format: git remote add (no help flag)
        mock_run.assert_called_once_with(['git', 'remote', 'add'], timeout=30, env=None, cwd=None)
        assert help_text == "nested output"


def test_try_help_nested_subcommand_subcommand_only_format():
    """Test nested subcommand with subcommand-only format."""
    with patch('cmdsaw.runner.run_capture') as mock_run:
        mock_run.return_value = ("nested output", 0)
        
        help_text, code = try_help(
            ['git', 'remote', 'add'], 
            ['--help'], 
            timeout=30, 
            env=None, 
            cwd=None, 
            subcommand_help_format='subcommand-only'
        )
        
        # Should use format: remote add (just subcommands)
        mock_run.assert_called_once_with(['remote', 'add'], timeout=30, env=None, cwd=None)
        assert help_text == "nested output"
