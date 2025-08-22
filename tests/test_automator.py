"""
Unit tests for Automator

Tests the core automation functionality, text pasting, and automation flow.
"""

from unittest.mock import Mock, patch

import pytest

# Import with fallback for relative import issues
try:
    from src.automator import run_automation
except ImportError:
    # Fallback for when running tests directly
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from automator import run_automation

# Import test utilities
from .test_utils import AutomationTestMixin, create_mock_ui_session


class TestAutomator(AutomationTestMixin):
    """Test cases for Automator module."""

    @pytest.fixture
    def mock_ui(self):
        """Create a mock UI for testing with AutomationController compatibility."""
        return create_mock_ui_session()

    @pytest.fixture
    def mock_pyautogui(self):
        """Mock pyautogui for testing."""
        with patch("src.automator.pyautogui") as mock_pag:
            mock_pag.click.return_value = None
            mock_pag.write.return_value = None
            mock_pag.hotkey.return_value = None
            mock_pag.position.return_value = (100, 200)
            yield mock_pag

    @pytest.fixture
    def mock_pyperclip(self):
        """Mock pyperclip for testing."""
        with patch("src.automator.pyperclip") as mock_clip:
            mock_clip.copy.return_value = None
            # Make paste return the same text that was copied
            def paste_side_effect():
                return mock_clip.copy.call_args[0][0] if mock_clip.copy.call_args else "test text"
            mock_clip.paste.side_effect = paste_side_effect
            yield mock_clip

    @pytest.fixture
    def mock_time(self):
        """Mock time module for testing."""
        with patch("src.automator.time") as mock_time:
            mock_time.sleep.return_value = None
            yield mock_time

    @pytest.fixture
    def mock_dpi(self):
        """Mock DPI awareness for testing."""
        with patch("src.automator.enable_windows_dpi_awareness") as mock_dpi:
            mock_dpi.return_value = None
            yield mock_dpi

    @pytest.fixture
    def mock_cursor_window(self):
        """Mock CursorWindow for testing."""
        with patch("src.automator.CursorWindow") as mock_win:
            mock_win_instance = Mock()
            mock_win.return_value = mock_win_instance
            yield mock_win_instance

    @pytest.mark.unit
    def test_paste_text_safely_success(self, mock_pyperclip, mock_time):
        """Test successful text pasting."""
        from src.automator import paste_text_safely

        result = paste_text_safely("test text")

        assert result is True
        mock_pyperclip.copy.assert_called_once_with("test text")
        mock_pyperclip.paste.assert_called_once()

    @pytest.mark.unit
    def test_paste_text_safely_failure(self, mock_pyperclip, mock_time):
        """Test text pasting failure."""
        from src.automator import paste_text_safely

        # Mock paste to return different text (override the side_effect)
        mock_pyperclip.paste.side_effect = lambda: "different text"

        result = paste_text_safely("test text")

        assert result is False

    @pytest.mark.unit
    def test_paste_text_safely_empty_text(self, mock_pyperclip, mock_time):
        """Test pasting empty text."""
        from src.automator import paste_text_safely

        result = paste_text_safely("")

        assert result is False
        mock_pyperclip.copy.assert_not_called()

    @pytest.mark.unit
    def test_paste_text_safely_none_text(self, mock_pyperclip, mock_time):
        """Test pasting None text."""
        from src.automator import paste_text_safely

        result = paste_text_safely(None)

        assert result is False
        mock_pyperclip.copy.assert_not_called()

    @pytest.mark.unit
    def test_click_button_or_fallback_success(self, mock_pyautogui, mock_time):
        """Test successful button clicking."""
        from src.automator import click_button_or_fallback

        # Create a mock CursorWindow
        mock_win = Mock()
        mock_win.window = None
        mock_win.connect.return_value = False

        result = click_button_or_fallback(mock_win, (100, 200), "fallback_key")

        assert result is True
        mock_pyautogui.click.assert_called_once_with(100, 200)

    @pytest.mark.unit
    def test_click_button_or_fallback_with_fallback(self, mock_pyautogui, mock_time):
        """Test button clicking with fallback."""
        from src.automator import click_button_or_fallback

        # Create a mock CursorWindow
        mock_win = Mock()
        mock_win.window = None
        mock_win.connect.return_value = False

        # Mock click to fail (return None)
        mock_pyautogui.click.return_value = None

        result = click_button_or_fallback(mock_win, (100, 200), "ctrl+enter")

        assert result is True
        mock_pyautogui.click.assert_called_once_with(100, 200)

    # DEPRECATED FUNCTION TESTS REMOVED
    # These tests were for run_automation_with_ui which has been removed
    # Use AutomationController tests instead

        # Test with UI that has no prompts - AutomationController should handle validation
        # This test has been removed since run_automation_with_ui is deprecated

    @pytest.mark.unit
    def test_thread_safety_features(self, mock_ui):
        """Test that thread safety features are properly mocked."""
        # Test that automation lock is present
        assert hasattr(mock_ui, "_automation_lock")
        assert hasattr(mock_ui, "_prompts_locked")

        # Test that get_prompts_safe method exists
        assert hasattr(mock_ui, "get_prompts_safe")
        assert callable(mock_ui.get_prompts_safe)

        # Test that the method returns the expected data
        prompts = mock_ui.get_prompts_safe()
        assert isinstance(prompts, list)
        assert len(prompts) > 0

    @pytest.mark.unit
    def test_run_automation_main_function(self):
        """Test the main run_automation function."""
        with patch("src.automator.SessionUI") as mock_ui_class:
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            mock_ui.wait_for_start.return_value = True
            mock_ui._started = True

            with patch("src.automation_controller.AutomationController") as mock_controller_class:
                mock_controller = Mock()
                mock_controller.start_automation.return_value = True
                mock_controller_class.return_value = mock_controller

                result = run_automation([])

                assert result is True
                mock_controller.start_automation.assert_called_once()

    @pytest.mark.unit
    def test_run_automation_main_function_no_start(self):
        """Test the main run_automation function when start is cancelled."""
        with patch("src.automator.SessionUI") as mock_ui_class:
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            mock_ui.wait_for_start.return_value = False
            mock_ui._started = False

            result = run_automation([])

            assert result is False

    @pytest.mark.unit
    def test_run_automation_main_function_with_prompts(self):
        """Test the main run_automation function with provided prompts."""
        test_prompts = ["Prompt 1", "Prompt 2"]

        with patch("src.automator.SessionUI") as mock_ui_class:
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            mock_ui.wait_for_start.return_value = True
            mock_ui._started = True

            with patch("src.automation_controller.AutomationController") as mock_controller_class:
                mock_controller = Mock()
                mock_controller.start_automation.return_value = True
                mock_controller_class.return_value = mock_controller

                result = run_automation(test_prompts)

                assert result is True
                mock_controller.start_automation.assert_called_once()
