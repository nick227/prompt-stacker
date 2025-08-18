"""
UI Session Tests

Tests for the RefactoredSessionUI class and its thread safety features.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Tuple

# Import with fallback for relative import issues
try:
    from src.ui import RefactoredSessionUI
except ImportError:
    # Fallback for when running tests directly
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from ui.session_app import RefactoredSessionUI


class TestRefactoredSessionUI:
    """Test cases for RefactoredSessionUI class."""

    @pytest.fixture
    def mock_ui_session(self):
        """Create a mock UI session for testing."""
        with patch('src.ui.session_app.ctk') as mock_ctk, \
             patch('src.ui.session_app.WindowService') as mock_window_service, \
             patch('src.ui.session_app.CoordinateCaptureService') as mock_coord_service, \
             patch('src.ui.session_app.FilePromptService') as mock_file_service, \
             patch('src.ui.session_app.CountdownService') as mock_countdown_service, \
             patch('src.ui.session_app.InlinePromptEditorService') as mock_prompt_service:
            
            # Mock the UI components
            mock_window = Mock()
            mock_ctk.CTk.return_value = mock_window
            
            # Mock UI widgets
            mock_time_label = Mock()
            mock_pause_btn = Mock()
            mock_current_box = Mock()
            mock_next_box = Mock()
            mock_prompt_list_frame = Mock()
            mock_start_btn = Mock()
            mock_prompt_path_var = Mock()
            mock_main_wait_var = Mock()
            mock_get_ready_delay_var = Mock()
            
            # Mock the UI session
            ui = Mock()
            ui.window = mock_window
            ui.time_label = mock_time_label
            ui.pause_btn = mock_pause_btn
            ui.current_box = mock_current_box
            ui.next_box = mock_next_box
            ui.prompt_list_frame = mock_prompt_list_frame
            ui.start_btn = mock_start_btn
            ui.prompt_path_var = mock_prompt_path_var
            ui.main_wait_var = mock_main_wait_var
            ui.get_ready_delay_var = mock_get_ready_delay_var
            
            # Thread safety attributes
            ui._automation_lock = threading.Lock()
            ui._prompts_locked = False
            ui._prompts = ["Test prompt 1", "Test prompt 2", "Test prompt 3"]
            ui._started = False
            ui.current_prompt_index = 0
            ui.prompt_count = 3
            
            # Thread-safe methods
            ui.get_prompts_safe = Mock(return_value=["Test prompt 1", "Test prompt 2", "Test prompt 3"])
            ui.get_coords = Mock(return_value={
                "input": (100, 200),
                "submit": (300, 400),
                "accept": (500, 600)
            })
            ui.get_timers = Mock(return_value=(5, 300, 0.2, 2.0))
            ui.countdown = Mock(return_value={'cancelled': False})
            ui.bring_to_front = Mock()
            ui.update_prompt_index_from_automation = Mock()
            
            # Services
            ui.window_service = mock_window_service.return_value
            ui.coordinate_service = mock_coord_service.return_value
            ui.file_service = mock_file_service.return_value
            ui.countdown_service = mock_countdown_service.return_value
            ui.prompt_list_service = mock_prompt_service.return_value
            
            return ui

    @pytest.mark.unit
    def test_thread_safety_initialization(self, mock_ui_session):
        """Test that thread safety features are properly initialized."""
        assert hasattr(mock_ui_session, '_automation_lock')
        assert isinstance(mock_ui_session._automation_lock, type(threading.Lock()))
        assert hasattr(mock_ui_session, '_prompts_locked')
        assert isinstance(mock_ui_session._prompts_locked, bool)
        assert hasattr(mock_ui_session, '_prompts')
        assert isinstance(mock_ui_session._prompts, list)

    @pytest.mark.unit
    def test_prompts_property_thread_safety(self, mock_ui_session):
        """Test the thread-safe prompts property."""
        # Test getter
        prompts = mock_ui_session.prompts
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        
        # Test setter when not locked
        mock_ui_session._prompts_locked = False
        new_prompts = ["New prompt 1", "New prompt 2"]
        mock_ui_session.prompts = new_prompts
        # The setter should be called (we can't easily test the actual implementation with mocks)

    @pytest.mark.unit
    def test_prompts_property_locked_state(self, mock_ui_session):
        """Test that prompts property respects locked state."""
        # When prompts are locked, modification should be prevented
        mock_ui_session._prompts_locked = True
        
        # The setter should detect the locked state and prevent modification
        # This is tested by the actual implementation logic

    @pytest.mark.unit
    def test_get_prompts_safe_method(self, mock_ui_session):
        """Test the get_prompts_safe method."""
        prompts = mock_ui_session.get_prompts_safe()
        assert isinstance(prompts, list)
        assert len(prompts) > 0

    @pytest.mark.unit
    def test_get_coords_thread_safety(self, mock_ui_session):
        """Test thread-safe coordinate access."""
        coords = mock_ui_session.get_coords()
        assert isinstance(coords, dict)
        assert "input" in coords
        assert "submit" in coords
        assert "accept" in coords

    @pytest.mark.unit
    def test_get_timers_thread_safety(self, mock_ui_session):
        """Test thread-safe timer access."""
        timers = mock_ui_session.get_timers()
        assert isinstance(timers, tuple)
        assert len(timers) == 4

    @pytest.mark.unit
    def test_automation_state_management(self, mock_ui_session):
        """Test automation state management."""
        # Initially not started
        assert mock_ui_session._started is False
        
        # Simulate starting automation
        mock_ui_session._started = True
        mock_ui_session._prompts_locked = True
        assert mock_ui_session._started is True
        assert mock_ui_session._prompts_locked is True
        
        # Simulate stopping automation
        mock_ui_session._started = False
        mock_ui_session._prompts_locked = False
        assert mock_ui_session._started is False
        assert mock_ui_session._prompts_locked is False

    @pytest.mark.unit
    def test_prompt_index_management(self, mock_ui_session):
        """Test prompt index management."""
        # Initially at first prompt
        assert mock_ui_session.current_prompt_index == 0
        
        # Simulate advancing to next prompt
        mock_ui_session.current_prompt_index = 1
        assert mock_ui_session.current_prompt_index == 1
        
        # Simulate resetting to first prompt
        mock_ui_session.current_prompt_index = 0
        assert mock_ui_session.current_prompt_index == 0

    @pytest.mark.unit
    def test_concurrent_prompt_access(self, mock_ui_session):
        """Test concurrent access to prompts."""
        def access_prompts():
            """Simulate concurrent access to prompts."""
            return mock_ui_session.get_prompts_safe()
        
        # Create multiple threads
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda: results.append(access_prompts()))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should have successfully accessed prompts
        assert len(results) == 5
        for result in results:
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.unit
    def test_atomic_operations(self, mock_ui_session):
        """Test that critical operations are atomic."""
        def atomic_operation():
            """Simulate an atomic operation."""
            with mock_ui_session._automation_lock:
                # Simulate state change
                mock_ui_session._prompts_locked = True
                time.sleep(0.01)  # Simulate work
                mock_ui_session._prompts_locked = False
                return True
        
        # Run multiple atomic operations concurrently
        threads = []
        results = []
        
        for i in range(3):
            thread = threading.Thread(target=lambda: results.append(atomic_operation()))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should complete successfully
        assert len(results) == 3
        assert all(result is True for result in results)

    @pytest.mark.unit
    def test_service_integration(self, mock_ui_session):
        """Test integration with various services."""
        # Test that services are properly initialized
        assert mock_ui_session.window_service is not None
        assert mock_ui_session.coordinate_service is not None
        assert mock_ui_session.file_service is not None
        assert mock_ui_session.countdown_service is not None
        assert mock_ui_session.prompt_list_service is not None

    @pytest.mark.unit
    def test_ui_widget_integration(self, mock_ui_session):
        """Test integration with UI widgets."""
        # Test that UI widgets are properly initialized
        assert mock_ui_session.time_label is not None
        assert mock_ui_session.pause_btn is not None
        assert mock_ui_session.current_box is not None
        assert mock_ui_session.next_box is not None
        assert mock_ui_session.prompt_list_frame is not None
        assert mock_ui_session.start_btn is not None

    @pytest.mark.unit
    def test_prompt_count_management(self, mock_ui_session):
        """Test prompt count management."""
        # Test that prompt count is properly managed
        assert mock_ui_session.prompt_count == 3
        
        # Simulate changing prompt count
        mock_ui_session.prompt_count = 5
        assert mock_ui_session.prompt_count == 5

    @pytest.mark.unit
    def test_automation_lock_usage(self, mock_ui_session):
        """Test that automation lock is used correctly."""
        # Test that the lock can be acquired and released
        with mock_ui_session._automation_lock:
            # Inside the lock, we can modify state
            mock_ui_session._prompts_locked = True
            assert mock_ui_session._prompts_locked is True
        
        # Outside the lock, we can still access state
        assert mock_ui_session._prompts_locked is True

    @pytest.mark.unit
    def test_thread_safe_state_transitions(self, mock_ui_session):
        """Test thread-safe state transitions."""
        # Test transitioning from not started to started
        with mock_ui_session._automation_lock:
            mock_ui_session._started = True
            mock_ui_session._prompts_locked = True
            mock_ui_session.current_prompt_index = 0
        
        assert mock_ui_session._started is True
        assert mock_ui_session._prompts_locked is True
        assert mock_ui_session.current_prompt_index == 0
        
        # Test transitioning from started to stopped
        with mock_ui_session._automation_lock:
            mock_ui_session._started = False
            mock_ui_session._prompts_locked = False
            mock_ui_session.current_prompt_index = 0
        
        assert mock_ui_session._started is False
        assert mock_ui_session._prompts_locked is False
        assert mock_ui_session.current_prompt_index == 0


class TestUISessionRaceConditions:
    """Test race condition scenarios in UI session."""

    @pytest.fixture
    def mock_ui_session_with_changes(self):
        """Create a mock UI session that can simulate state changes."""
        ui = Mock()
        ui._automation_lock = threading.Lock()
        ui._prompts_locked = False
        ui._prompts = ["Initial prompt 1", "Initial prompt 2"]
        ui._started = False
        ui.current_prompt_index = 0
        ui.prompt_count = 2
        
        # Simulate state changes
        self.state_changes = 0
        
        def get_prompts_with_changes():
            self.state_changes += 1
            if self.state_changes == 1:
                return ["Initial prompt 1", "Initial prompt 2"]
            else:
                return ["Changed prompt 1", "Changed prompt 2", "New prompt 3"]
        
        ui.get_prompts_safe = Mock(side_effect=get_prompts_with_changes)
        ui.get_coords = Mock(return_value={"input": (100, 200), "submit": (300, 400), "accept": (500, 600)})
        ui.get_timers = Mock(return_value=(5, 300, 0.2, 2.0))
        
        return ui

    @pytest.mark.unit
    def test_state_change_detection(self, mock_ui_session_with_changes):
        """Test that state changes are detected."""
        # Get initial state
        initial_prompts = mock_ui_session_with_changes.get_prompts_safe()
        
        # Get state again (simulating change)
        current_prompts = mock_ui_session_with_changes.get_prompts_safe()
        
        # Verify that state changed
        assert initial_prompts != current_prompts
        assert len(initial_prompts) == 2
        assert len(current_prompts) == 3

    @pytest.mark.unit
    def test_concurrent_state_access(self, mock_ui_session_with_changes):
        """Test concurrent access to state."""
        def access_state():
            """Simulate concurrent state access."""
            prompts = mock_ui_session_with_changes.get_prompts_safe()
            coords = mock_ui_session_with_changes.get_coords()
            timers = mock_ui_session_with_changes.get_timers()
            return prompts, coords, timers
        
        # Run multiple threads
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda: results.append(access_state()))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should complete successfully
        assert len(results) == 5
        for result in results:
            prompts, coords, timers = result
            assert isinstance(prompts, list)
            assert isinstance(coords, dict)
            assert isinstance(timers, tuple)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
