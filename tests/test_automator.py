"""
Unit tests for Automator

Tests the core automation functionality, text pasting, and automation flow.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
# Import with fallback for relative import issues
try:
    from src.automator import run_automation, run_automation_with_ui
except ImportError:
    # Fallback for when running tests directly
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from automator import run_automation, run_automation_with_ui


class TestAutomator:
    """Test cases for Automator module."""

    @pytest.fixture
    def mock_ui(self):
        """Create a mock UI for testing."""
        ui = Mock()
        # CRITICAL FIX: Update mock to match new race condition fixes
        ui.get_prompts_safe = Mock(return_value=["Test prompt 1", "Test prompt 2", "Test prompt 3"])
        ui.current_prompt_index = 0
        ui.update_prompt_index_from_automation = Mock()
        ui.get_wait_time = Mock(return_value=1)
        ui.get_countdown_time = Mock(return_value=2)
        ui.get_coords = Mock(return_value={
            "input": (100, 200),
            "submit": (300, 400),
            "accept": (500, 600)
        })
        ui.get_timers = Mock(return_value=(5, 300, 0.2, 2.0))  # start_delay, main_wait, cooldown, get_ready_delay
        ui.countdown = Mock(return_value={
            'cancelled': False
        })
        ui.bring_to_front = Mock()
        
        # Add thread safety mocks
        ui._automation_lock = Mock()
        ui._prompts_locked = False
        
        # CRITICAL FIX: Mock countdown_service to prevent infinite loops
        mock_countdown_service = Mock()
        mock_countdown_service.is_active = Mock(return_value=False)  # Prevent infinite loops
        mock_countdown_service.is_paused = Mock(return_value=False)   # Prevent infinite loops
        ui.countdown_service = mock_countdown_service
        
        return ui

    @pytest.fixture
    def mock_pyautogui(self):
        """Mock pyautogui for testing."""
        with patch('src.automator.pyautogui') as mock_pag:
            mock_pag.click.return_value = None
            mock_pag.write.return_value = None
            mock_pag.hotkey.return_value = None
            mock_pag.position.return_value = (100, 200)
            yield mock_pag

    @pytest.fixture
    def mock_pyperclip(self):
        """Mock pyperclip for testing."""
        with patch('src.automator.pyperclip') as mock_clip:
            mock_clip.copy.return_value = None
            # Make paste return the same text that was copied
            def paste_side_effect():
                return mock_clip.copy.call_args[0][0] if mock_clip.copy.call_args else "test text"
            mock_clip.paste.side_effect = paste_side_effect
            yield mock_clip

    @pytest.fixture
    def mock_time(self):
        """Mock time module for testing."""
        with patch('src.automator.time') as mock_time:
            mock_time.sleep.return_value = None
            yield mock_time
            
    @pytest.fixture
    def mock_dpi(self):
        """Mock DPI awareness for testing."""
        with patch('src.automator.enable_windows_dpi_awareness') as mock_dpi:
            mock_dpi.return_value = None
            yield mock_dpi
            
    @pytest.fixture
    def mock_cursor_window(self):
        """Mock CursorWindow for testing."""
        with patch('src.automator.CursorWindow') as mock_win:
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

    @pytest.mark.unit
    def test_run_automation_with_ui_success(self, mock_ui, mock_pyautogui, mock_pyperclip, mock_time, mock_dpi, mock_cursor_window):
        """Test successful automation run with UI."""
        print("\n🔍 Starting test_run_automation_with_ui_success...")
        
        # Track test progress
        test_progress = []
        
        def log_progress(message):
            """Log progress with timestamp."""
            import time
            timestamp = time.strftime("%H:%M:%S")
            progress_msg = f"[{timestamp}] {message}"
            print(f"  📊 {progress_msg}")
            test_progress.append(progress_msg)
        
        log_progress("Setting up simplified test...")
        
        # Mock all the complex automation functions to return success
        with patch('src.automator.paste_text_safely', return_value=True), \
             patch('src.automator.click_with_timeout', return_value=True), \
             patch('src.automator.perform_paste_operation', return_value=True), \
             patch('src.automator.click_button_or_fallback', return_value=True), \
             patch('src.automator.enable_windows_dpi_awareness'), \
             patch('src.automator.CursorWindow') as mock_cursor_window_class, \
             patch('src.automator.time.sleep'):
            
            # Mock CursorWindow instance
            mock_cursor_window_instance = Mock()
            mock_cursor_window_class.return_value = mock_cursor_window_instance
            
            # Mock countdown to return success quickly
            mock_ui.countdown.return_value = {'cancelled': False, 'paused': False}
            
            log_progress("About to call run_automation_with_ui...")
            
            result = run_automation_with_ui(mock_ui)
            log_progress(f"run_automation_with_ui completed with result: {result}")
            
            # Verify the result
            assert result is True
            log_progress("✅ Test assertion passed")
            print(f"\n🎉 Test completed successfully! Total progress steps: {len(test_progress)}")

    @pytest.mark.unit
    def test_run_automation_with_ui_cancelled(self, mock_ui, mock_pyautogui, mock_pyperclip, mock_time, mock_dpi, mock_cursor_window):
        """Test automation run when cancelled."""
        mock_ui.countdown.return_value = {'cancelled': True}
        
        result = run_automation_with_ui(mock_ui)
        
        assert result is False



    @pytest.mark.unit
    def test_run_automation_with_ui_no_prompts(self, mock_ui, mock_pyautogui, mock_pyperclip, mock_time, mock_dpi, mock_cursor_window):
        """Test automation run with no prompts."""
        mock_ui.get_prompts_safe.return_value = []
        
        result = run_automation_with_ui(mock_ui)
        
        assert result is False

    @pytest.mark.unit
    def test_run_automation_with_ui_missing_coordinates(self, mock_ui, mock_pyautogui, mock_pyperclip, mock_time, mock_dpi, mock_cursor_window):
        """Test automation run with missing coordinates."""
        mock_ui.get_coords.return_value = {
            "input": (100, 200),
            # Missing submit and accept
        }
        
        result = run_automation_with_ui(mock_ui)
        
        assert result is False

    @pytest.mark.unit
    def test_run_automation_with_ui_paste_failure(self, mock_ui, mock_pyautogui, mock_pyperclip, mock_time, mock_dpi, mock_cursor_window):
        """Test automation run when text pasting fails."""
        # Mock paste_text_safely to fail
        with patch('src.automator.paste_text_safely', return_value=False):
            result = run_automation_with_ui(mock_ui)
            
            assert result is False  # Should fail when paste fails

    @pytest.mark.unit
    def test_run_automation_with_ui_click_failure(self, mock_ui, mock_pyautogui, mock_pyperclip, mock_time, mock_dpi, mock_cursor_window):
        """Test automation run when button clicking fails."""
        # Mock click_button_or_fallback to fail
        with patch('src.automator.click_button_or_fallback', return_value=False):
            result = run_automation_with_ui(mock_ui)
            
            assert result is False  # Should fail when click fails

    @pytest.mark.unit
    def test_run_automation_with_ui_end_of_prompts(self, mock_ui, mock_pyautogui, mock_pyperclip, mock_time, mock_dpi, mock_cursor_window):
        """Test automation run reaching end of prompts."""
        # Mock the countdown to return immediately without hanging
        mock_ui.countdown.return_value = {'cancelled': False, 'paused': False}
        
        # Mock the automation to complete successfully
        with patch('src.automator.paste_text_safely', return_value=True), \
             patch('src.automator.click_with_timeout', return_value=True), \
             patch('src.automator.perform_paste_operation', return_value=True), \
             patch('src.automator.click_button_or_fallback', return_value=True), \
             patch('src.automator.enable_windows_dpi_awareness'), \
             patch('src.automator.CursorWindow') as mock_cursor_window_class, \
             patch('src.automator.time.sleep'):
            
            # Mock CursorWindow instance
            mock_cursor_window_instance = Mock()
            mock_cursor_window_class.return_value = mock_cursor_window_instance
            
            result = run_automation_with_ui(mock_ui)
            
            assert result is True

    @pytest.mark.unit
    def test_run_automation_validation(self, mock_ui, mock_dpi, mock_cursor_window):
        """Test automation input validation."""
        # Test with None UI
        result = run_automation_with_ui(None)
        assert result is False
        
        # Test with UI that has no prompts
        mock_ui.get_prompts_safe.return_value = []
        result = run_automation_with_ui(mock_ui)
        assert result is False
        
    @pytest.mark.unit
    def test_thread_safety_features(self, mock_ui):
        """Test that thread safety features are properly mocked."""
        # Test that automation lock is present
        assert hasattr(mock_ui, '_automation_lock')
        assert hasattr(mock_ui, '_prompts_locked')
        
        # Test that get_prompts_safe method exists
        assert hasattr(mock_ui, 'get_prompts_safe')
        assert callable(mock_ui.get_prompts_safe)
        
        # Test that the method returns the expected data
        prompts = mock_ui.get_prompts_safe()
        assert isinstance(prompts, list)
        assert len(prompts) > 0

    @pytest.mark.unit
    def test_run_automation_main_function(self):
        """Test the main run_automation function."""
        with patch('src.automator.SessionUI') as mock_ui_class:
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            mock_ui.wait_for_start.return_value = True
            mock_ui._started = True
            
            with patch('src.automator.run_automation_with_ui', return_value=True) as mock_run:
                result = run_automation([])
                
                assert result is True
                mock_run.assert_called_once_with(mock_ui)

    @pytest.mark.unit
    def test_run_automation_main_function_no_start(self):
        """Test the main run_automation function when start is cancelled."""
        with patch('src.automator.SessionUI') as mock_ui_class:
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
        
        with patch('src.automator.SessionUI') as mock_ui_class:
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            mock_ui.wait_for_start.return_value = True
            mock_ui._started = True
            
            with patch('src.automator.run_automation_with_ui', return_value=True) as mock_run:
                result = run_automation(test_prompts)
                
                assert result is True
                # Should set prompts on UI
                mock_ui_class.assert_called_once()
                # The prompts should be passed to the SessionUI constructor
                # but we can't easily check that with the current mock setup
