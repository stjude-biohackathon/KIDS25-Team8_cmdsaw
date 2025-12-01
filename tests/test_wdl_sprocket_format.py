"""Test WDL formatting with sprocket integration."""
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from cmdsaw.wdl import _check_sprocket_available, _format_wdl_with_sprocket, emit_wdl
from cmdsaw.parsing.schema import CommandDoc, OptionDoc
from cmdsaw.parsing.resource_estimator import ResourceEstimate


def test_check_sprocket_available_not_installed():
    """Test sprocket availability check when sprocket is not installed."""
    with patch('shutil.which', return_value=None):
        assert not _check_sprocket_available()


def test_check_sprocket_available_installed():
    """Test sprocket availability check when sprocket is installed."""
    with patch('shutil.which', return_value='/usr/local/bin/sprocket'):
        assert _check_sprocket_available()


def test_format_wdl_with_sprocket_success():
    """Test successful WDL formatting with sprocket."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.wdl', delete=False) as f:
        wdl_path = f.name
        f.write("version 1.2\n\ntask example {}\n")
    
    try:
        # Mock subprocess.run to simulate successful sprocket execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = _format_wdl_with_sprocket(wdl_path)
            
            assert result is True
            # Verify sprocket was called with correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args == ["sprocket", "format", "overwrite", wdl_path]
    finally:
        if os.path.exists(wdl_path):
            os.unlink(wdl_path)


def test_format_wdl_with_sprocket_failure():
    """Test WDL formatting when sprocket fails."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.wdl', delete=False) as f:
        wdl_path = f.name
        f.write("version 1.2\n\ntask example {}\n")
    
    try:
        # Mock subprocess.run to simulate sprocket failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        
        with patch('subprocess.run', return_value=mock_result):
            result = _format_wdl_with_sprocket(wdl_path)
            
            assert result is False
    finally:
        if os.path.exists(wdl_path):
            os.unlink(wdl_path)


def test_format_wdl_with_sprocket_timeout():
    """Test WDL formatting when sprocket times out."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.wdl', delete=False) as f:
        wdl_path = f.name
        f.write("version 1.2\n\ntask example {}\n")
    
    try:
        # Mock subprocess.run to simulate timeout
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='sprocket', timeout=30)):
            result = _format_wdl_with_sprocket(wdl_path)
            
            assert result is False
    finally:
        if os.path.exists(wdl_path):
            os.unlink(wdl_path)


def test_emit_wdl_without_formatting():
    """Test emit_wdl generates WDL without formatting when format_wdl=False."""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.wdl', delete=False) as f:
        wdl_path = f.name
    
    try:
        # Mock estimate_resources to avoid calling Ollama
        with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
            mock_estimate.return_value = ResourceEstimate(cpu=2, mem_gb=4.0)
            
            # Generate WDL without formatting
            emit_wdl(
                tool_name="test_tool",
                docs=[cmd],
                out_path=wdl_path,
                model_name="gemma3:12b",
                format_wdl=False
            )
            
            # Verify file was created
            assert os.path.exists(wdl_path)
            
            # Verify file contains WDL
            with open(wdl_path, 'r') as f:
                content = f.read()
                assert "version 1.2" in content
                assert "task test_tool" in content
    finally:
        if os.path.exists(wdl_path):
            os.unlink(wdl_path)


def test_emit_wdl_with_formatting_sprocket_available():
    """Test emit_wdl formats WDL when format_wdl=True and sprocket is available."""
    cmd = CommandDoc(
        name="test_tool",
        path="test_tool",
        help_text="Test tool",
        options=[],
        positionals=[],
        subcommands=[],
        requires_subcommand=False
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.wdl', delete=False) as f:
        wdl_path = f.name
    
    try:
        # Mock estimate_resources and sprocket functions
        with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
            mock_estimate.return_value = ResourceEstimate(cpu=2, mem_gb=4.0)
            
            with patch('cmdsaw.wdl._check_sprocket_available', return_value=True):
                with patch('cmdsaw.wdl._format_wdl_with_sprocket', return_value=True) as mock_format:
                    # Generate WDL with formatting
                    emit_wdl(
                        tool_name="test_tool",
                        docs=[cmd],
                        out_path=wdl_path,
                        model_name="gemma3:12b",
                        format_wdl=True
                    )
                    
                    # Verify file was created
                    assert os.path.exists(wdl_path)
                    
                    # Verify sprocket formatting was called
                    mock_format.assert_called_once_with(wdl_path)
    finally:
        if os.path.exists(wdl_path):
            os.unlink(wdl_path)


def test_emit_wdl_with_formatting_sprocket_not_available():
    """Test emit_wdl prints warning when format_wdl=True but sprocket is not available."""
    cmd = CommandDoc(
        name="test_tool",
        path="test_tool",
        help_text="Test tool",
        options=[],
        positionals=[],
        subcommands=[],
        requires_subcommand=False
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.wdl', delete=False) as f:
        wdl_path = f.name
    
    try:
        # Mock estimate_resources and sprocket availability
        with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
            mock_estimate.return_value = ResourceEstimate(cpu=2, mem_gb=4.0)
            
            with patch('cmdsaw.wdl._check_sprocket_available', return_value=False):
                with patch('cmdsaw.wdl._format_wdl_with_sprocket') as mock_format:
                    # Generate WDL with formatting requested but sprocket unavailable
                    emit_wdl(
                        tool_name="test_tool",
                        docs=[cmd],
                        out_path=wdl_path,
                        model_name="gemma3:12b",
                        format_wdl=True
                    )
                    
                    # Verify file was still created
                    assert os.path.exists(wdl_path)
                    
                    # Verify sprocket formatting was NOT called
                    mock_format.assert_not_called()
    finally:
        if os.path.exists(wdl_path):
            os.unlink(wdl_path)


def test_emit_wdl_with_formatting_sprocket_fails():
    """Test emit_wdl handles sprocket formatting failure gracefully."""
    cmd = CommandDoc(
        name="test_tool",
        path="test_tool",
        help_text="Test tool",
        options=[],
        positionals=[],
        subcommands=[],
        requires_subcommand=False
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.wdl', delete=False) as f:
        wdl_path = f.name
    
    try:
        # Mock estimate_resources and sprocket functions
        with patch('cmdsaw.wdl.estimate_resources') as mock_estimate:
            mock_estimate.return_value = ResourceEstimate(cpu=2, mem_gb=4.0)
            
            with patch('cmdsaw.wdl._check_sprocket_available', return_value=True):
                with patch('cmdsaw.wdl._format_wdl_with_sprocket', return_value=False):
                    # Generate WDL with formatting that fails
                    emit_wdl(
                        tool_name="test_tool",
                        docs=[cmd],
                        out_path=wdl_path,
                        model_name="gemma3:12b",
                        format_wdl=True
                    )
                    
                    # Verify file was still created (unformatted)
                    assert os.path.exists(wdl_path)
                    
                    # Verify file contains valid WDL
                    with open(wdl_path, 'r') as f:
                        content = f.read()
                        assert "version 1.2" in content
                        assert "task test_tool" in content
    finally:
        if os.path.exists(wdl_path):
            os.unlink(wdl_path)


if __name__ == '__main__':
    test_check_sprocket_available_not_installed()
    print("✓ test_check_sprocket_available_not_installed passed")
    
    test_check_sprocket_available_installed()
    print("✓ test_check_sprocket_available_installed passed")
    
    test_format_wdl_with_sprocket_success()
    print("✓ test_format_wdl_with_sprocket_success passed")
    
    test_format_wdl_with_sprocket_failure()
    print("✓ test_format_wdl_with_sprocket_failure passed")
    
    test_format_wdl_with_sprocket_timeout()
    print("✓ test_format_wdl_with_sprocket_timeout passed")
    
    test_emit_wdl_without_formatting()
    print("✓ test_emit_wdl_without_formatting passed")
    
    test_emit_wdl_with_formatting_sprocket_available()
    print("✓ test_emit_wdl_with_formatting_sprocket_available passed")
    
    test_emit_wdl_with_formatting_sprocket_not_available()
    print("✓ test_emit_wdl_with_formatting_sprocket_not_available passed")
    
    test_emit_wdl_with_formatting_sprocket_fails()
    print("✓ test_emit_wdl_with_formatting_sprocket_fails passed")
    
    print("\nAll sprocket formatting tests passed!")
