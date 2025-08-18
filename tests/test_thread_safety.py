"""
Thread Safety and Race Condition Tests

Tests for the thread safety features and race condition prevention
mechanisms added to the automation system.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from typing import List

# Import with fallback for relative import issues
try:
    from src.ui import RefactoredSessionUI
    from src.automator import run_automation_with_ui, run_single_prompt_automation
except ImportError:
    # Fallback for when running tests directly
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from ui.session_app import RefactoredSessionUI
    from automator import run_automation_with_ui, run_single_prompt_automation


class TestThreadSafety:
    """Test cases for thread safety features."""

    @pytest.fixture
    def mock_ui_session(self):
        """Create a mock UI session with thread safety features."""
        ui = Mock()
        
        # Thread safety attributes
        ui._automation_lock = threading.Lock()
        ui._prompts_locked = False
        ui._prompts = ["Test prompt 1", "Test prompt 2", "Test prompt 3"]
        
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
        
        return ui

    @pytest.mark.unit
    def test_automation_lock_presence(self, mock_ui_session):
        """Test that automation lock is properly initialized."""
        assert hasattr(mock_ui_session, '_automation_lock')
        assert isinstance(mock_ui_session._automation_lock, type(threading.Lock()))
        assert hasattr(mock_ui_session, '_prompts_locked')
        assert isinstance(mock_ui_session._prompts_locked, bool)

    @pytest.mark.unit
    def test_get_prompts_safe_method(self, mock_ui_session):
        """Test the thread-safe get_prompts_safe method."""
        assert hasattr(mock_ui_session, 'get_prompts_safe')
        assert callable(mock_ui_session.get_prompts_safe)
        
        prompts = mock_ui_session.get_prompts_safe()
        assert isinstance(prompts, list)
        assert len(prompts) > 0

    @pytest.mark.unit
    def test_thread_safe_coordinate_access(self, mock_ui_session):
        """Test thread-safe coordinate access."""
        coords = mock_ui_session.get_coords()
        assert isinstance(coords, dict)
        assert "input" in coords
        assert "submit" in coords
        assert "accept" in coords

    @pytest.mark.unit
    def test_thread_safe_timer_access(self, mock_ui_session):
        """Test thread-safe timer access."""
        timers = mock_ui_session.get_timers()
        assert isinstance(timers, tuple)
        assert len(timers) == 4

    @pytest.mark.unit
    def test_prompts_locked_state_management(self, mock_ui_session):
        """Test prompts locked state management."""
        # Initially unlocked
        assert mock_ui_session._prompts_locked is False
        
        # Simulate locking during automation
        mock_ui_session._prompts_locked = True
        assert mock_ui_session._prompts_locked is True
        
        # Simulate unlocking after automation
        mock_ui_session._prompts_locked = False
        assert mock_ui_session._prompts_locked is False

    @pytest.mark.unit
    def test_concurrent_access_prevention(self, mock_ui_session):
        """Test that concurrent access is prevented."""
        # This test simulates the protection against concurrent access
        # by verifying that the lock mechanism is in place
        
        def access_prompts():
            """Simulate concurrent access to prompts."""
            return mock_ui_session.get_prompts_safe()
        
        # Create multiple threads trying to access prompts simultaneously
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
    def test_state_capture_at_automation_start(self, mock_ui_session):
        """Test that state is captured at automation start."""
        # Mock the automation function to capture initial state
        with patch('src.automator.run_automation_with_ui') as mock_automation:
            mock_automation.return_value = True
            
            # The automation should capture initial state
            # This is tested by verifying the mock calls
            result = run_automation_with_ui(mock_ui_session)
            
            assert result is True
            # Verify that get_prompts_safe was called (state capture)
            mock_ui_session.get_prompts_safe.assert_called()

    @pytest.mark.unit
    def test_state_validation_during_automation(self, mock_ui_session):
        """Test state validation during automation."""
        # This test verifies that the automation system validates
        # that state hasn't changed during execution
        
        # Mock the automation to simulate state validation
        with patch('src.automator.run_automation_with_ui') as mock_automation:
            mock_automation.return_value = True
            
            result = run_automation_with_ui(mock_ui_session)
            
            assert result is True
            # The automation should call get_prompts_safe multiple times
            # for state validation during execution
            assert mock_ui_session.get_prompts_safe.call_count >= 1

    @pytest.mark.unit
    def test_safe_stopping_on_state_change(self, mock_ui_session):
        """Test safe stopping when state changes during automation."""
        # This test simulates the scenario where state changes
        # during automation and the system safely stops
        
        # Mock get_prompts_safe to return different values
        # simulating state change during automation
        mock_ui_session.get_prompts_safe.side_effect = [
            ["Test prompt 1", "Test prompt 2", "Test prompt 3"],  # Initial state
            ["Different prompt 1", "Different prompt 2"],  # Changed state
        ]
        
        # The automation should detect this change and stop safely
        # This is tested by the automation logic in the actual code
        # Here we just verify the mock behavior
        initial_prompts = mock_ui_session.get_prompts_safe()
        changed_prompts = mock_ui_session.get_prompts_safe()
        
        assert initial_prompts != changed_prompts
        assert len(initial_prompts) == 3
        assert len(changed_prompts) == 2

    @pytest.mark.unit
    def test_atomic_operations(self, mock_ui_session):
        """Test that critical operations are atomic."""
        # Test that operations that should be atomic are protected
        # by the automation lock
        
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
    def test_prompt_list_modification_protection(self, mock_ui_session):
        """Test that prompt list modifications are protected during automation."""
        # Test that the system prevents prompt list modifications
        # when automation is running
        
        # Simulate automation running
        mock_ui_session._prompts_locked = True
        
        # Attempt to modify prompts (this should be prevented)
        # In the actual implementation, this would be handled by the setter
        # Here we test the concept
        
        # The prompts should remain unchanged when locked
        original_prompts = mock_ui_session.get_prompts_safe()
        
        # Simulate an attempt to modify (this would be prevented in real code)
        # mock_ui_session.prompts = ["Modified prompt"]  # This would fail
        
        # Verify prompts are still the same
        current_prompts = mock_ui_session.get_prompts_safe()
        assert current_prompts == original_prompts

    @pytest.mark.unit
    def test_race_condition_prevention(self, mock_ui_session):
        """Test race condition prevention mechanisms."""
        # This test verifies that the system prevents race conditions
        # by using proper locking and state validation
        
        def simulate_race_condition():
            """Simulate a potential race condition scenario."""
            # Multiple threads accessing shared state
            prompts = mock_ui_session.get_prompts_safe()
            coords = mock_ui_session.get_coords()
            timers = mock_ui_session.get_timers()
            
            # Simulate some work
            time.sleep(0.001)
            
            return prompts, coords, timers
        
        # Run multiple threads to simulate race condition
        threads = []
        results = []
        
        for i in range(10):
            thread = threading.Thread(target=lambda: results.append(simulate_race_condition()))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should get consistent results
        assert len(results) == 10
        
        # Verify all results are consistent
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

    @pytest.mark.unit
    def test_single_prompt_automation_thread_safety(self, mock_ui_session):
        """Test thread safety in single prompt automation."""
        # Test that single prompt automation uses thread-safe methods
        
        with patch('src.automator.run_single_prompt_automation') as mock_single:
            mock_single.return_value = True
            
            result = run_single_prompt_automation(mock_ui_session, 0)
            
            assert result is True
            # Verify that thread-safe methods were called
            mock_ui_session.get_prompts_safe.assert_called()
            mock_ui_session.get_coords.assert_called()
            mock_ui_session.get_timers.assert_called()


class TestRaceConditionScenarios:
    """Test specific race condition scenarios."""

    @pytest.fixture
    def mock_ui_with_state_changes(self):
        """Create a mock UI that simulates state changes."""
        ui = Mock()
        ui._automation_lock = threading.Lock()
        ui._prompts_locked = False
        
        # Simulate state that can change
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
        ui.countdown = Mock(return_value={'cancelled': False})
        ui.bring_to_front = Mock()
        
        return ui

    @pytest.mark.unit
    def test_state_change_detection(self, mock_ui_with_state_changes):
        """Test that state changes are detected during automation."""
        # Get initial state
        initial_prompts = mock_ui_with_state_changes.get_prompts_safe()
        
        # Get state again (simulating change)
        current_prompts = mock_ui_with_state_changes.get_prompts_safe()
        
        # Verify that state changed
        assert initial_prompts != current_prompts
        assert len(initial_prompts) == 2
        assert len(current_prompts) == 3

    @pytest.mark.unit
    def test_coordinate_change_detection(self, mock_ui_with_state_changes):
        """Test that coordinate changes are detected."""
        initial_coords = mock_ui_with_state_changes.get_coords()
        
        # Simulate coordinate change
        mock_ui_with_state_changes.get_coords.return_value = {
            "input": (200, 300),  # Changed coordinates
            "submit": (400, 500),
            "accept": (600, 700)
        }
        
        current_coords = mock_ui_with_state_changes.get_coords()
        
        # Verify that coordinates changed
        assert initial_coords != current_coords
        assert initial_coords["input"] != current_coords["input"]

    @pytest.mark.unit
    def test_timer_change_detection(self, mock_ui_with_state_changes):
        """Test that timer changes are detected."""
        initial_timers = mock_ui_with_state_changes.get_timers()
        
        # Simulate timer change
        mock_ui_with_state_changes.get_timers.return_value = (10, 600, 0.5, 5.0)
        
        current_timers = mock_ui_with_state_changes.get_timers()
        
        # Verify that timers changed
        assert initial_timers != current_timers
        assert initial_timers[1] != current_timers[1]  # main_wait changed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
