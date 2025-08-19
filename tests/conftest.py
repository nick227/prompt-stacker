"""
Pytest configuration and common fixtures for the test suite.

This module provides shared fixtures, test utilities, and configuration
for all tests in the automation system.
"""

import os
import sys
import tempfile
from unittest.mock import Mock

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return [
        "This is a test prompt",
        "Another test prompt with 'quotes'",
        "Multi-line\nprompt with\nline breaks",
        "Simple prompt",
        "Prompt with special chars: !@#$%^&*()",
    ]


@pytest.fixture
def sample_coordinates():
    """Sample coordinates for testing."""
    return {
        "input": (100, 200),
        "submit": (300, 400),
        "accept": (500, 600),
    }


@pytest.fixture
def mock_ui_widgets():
    """Mock UI widgets for testing services that depend on UI."""
    widgets = {
        "time_label": Mock(),
        "progress": Mock(),
        "pause_btn": Mock(),
        "current_box": Mock(),
        "next_box": Mock(),
        "status_label": Mock(),
        "prompt_list_frame": Mock(),
        "window": Mock(),
    }

    # Configure mock widgets
    for widget in widgets.values():
        if hasattr(widget, "configure"):
            widget.configure = Mock()
        if hasattr(widget, "set"):
            widget.set = Mock()
        if hasattr(widget, "get"):
            widget.get = Mock(return_value="")

    return widgets


@pytest.fixture
def mock_file_service():
    """Mock file service for testing."""
    mock_service = Mock()
    mock_service.parse_prompt_list.return_value = (True, ["test prompt"])
    mock_service.save_prompts.return_value = True
    return mock_service


@pytest.fixture
def mock_settings_store():
    """Mock settings store for testing."""
    mock_store = Mock()
    mock_store.load_coords.return_value = {"input": (100, 200)}
    mock_store.save_coords.return_value = True
    return mock_store


@pytest.fixture
def mock_mouse_listener():
    """Mock mouse listener for coordinate capture testing."""
    mock_listener = Mock()
    mock_listener.start.return_value = True
    mock_listener.stop.return_value = True
    return mock_listener


@pytest.fixture
def mock_tkinter():
    """Mock tkinter components for UI testing."""
    mock_tk = Mock()
    mock_tk.Tk.return_value = Mock()
    mock_tk.Toplevel.return_value = Mock()
    mock_tk.StringVar.return_value = Mock()
    mock_tk.IntVar.return_value = Mock()
    return mock_tk


@pytest.fixture
def mock_customtkinter():
    """Mock customtkinter components for UI testing."""
    mock_ctk = Mock()
    mock_ctk.CTk.return_value = Mock()
    mock_ctk.CTkToplevel.return_value = Mock()
    mock_ctk.CTkFrame.return_value = Mock()
    mock_ctk.CTkButton.return_value = Mock()
    mock_ctk.CTkLabel.return_value = Mock()
    mock_ctk.CTkEntry.return_value = Mock()
    mock_ctk.CTkTextbox.return_value = Mock()
    mock_ctk.CTkScrollableFrame.return_value = Mock()
    mock_ctk.CTkProgressBar.return_value = Mock()
    return mock_ctk


@pytest.fixture
def mock_pyautogui():
    """Mock pyautogui for automation testing."""
    mock_pag = Mock()
    mock_pag.click.return_value = None
    mock_pag.write.return_value = None
    mock_pag.hotkey.return_value = None
    mock_pag.position.return_value = (100, 200)
    return mock_pag


@pytest.fixture
def mock_pyperclip():
    """Mock pyperclip for clipboard testing."""
    mock_clip = Mock()
    mock_clip.copy.return_value = None
    mock_clip.paste.return_value = "test text"
    return mock_clip


@pytest.fixture
def mock_pynput():
    """Mock pynput for input testing."""
    mock_pynput = Mock()
    mock_pynput.mouse = Mock()
    mock_pynput.mouse.Button = Mock()
    mock_pynput.mouse.Listener = Mock()
    return mock_pynput


@pytest.fixture
def test_config():
    """Test configuration data."""
    return {
        "window": {
            "width": 800,
            "height": 600,
            "title": "Test Window",
        },
        "timers": {
            "default_wait": 5,
            "default_countdown": 10,
        },
        "coordinates": {
            "input": (100, 200),
            "submit": (300, 400),
        },
    }


@pytest.fixture
def mock_error_handler():
    """Mock error handler for testing."""
    mock_handler = Mock()
    mock_handler.handle_error = Mock()
    mock_handler.log_info = Mock()
    mock_handler.log_error = Mock()
    return mock_handler


@pytest.fixture
def mock_performance_monitor():
    """Mock performance monitor for testing."""
    mock_monitor = Mock()
    mock_monitor.start_performance_monitoring = Mock()
    mock_monitor.stop_performance_monitoring = Mock()
    mock_monitor.cleanup_memory = Mock()
    return mock_monitor


# Test markers for different test types
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test",
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test",
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running",
    )
    config.addinivalue_line(
        "markers", "ui: mark test as requiring UI components",
    )
    config.addinivalue_line(
        "markers", "automation: mark test as automation-related",
    )
