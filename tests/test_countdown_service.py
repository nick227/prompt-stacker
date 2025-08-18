"""
Unit tests for CountdownService.

Tests the countdown functionality for the automation system.
"""

import pytest
from unittest.mock import Mock, patch
from countdown_service import CountdownService


class TestCountdownService:
    """Test cases for CountdownService."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        mock_widgets = {
            'time_label': Mock(),
            'progress': Mock(),
            'pause_btn': Mock(),
            'current_box': Mock(),
            'next_box': Mock()
        }
        return CountdownService(mock_widgets)
    
    @pytest.mark.unit
    def test_init(self, service):
        """Test service initialization."""
        assert service.countdown_active is False
        assert service.paused is False
        assert service.cancelled is False

        assert service.on_countdown_complete is None
    
    @pytest.mark.unit
    def test_start_countdown_success(self, service):
        """Test successful countdown start."""
        callback = Mock()
        
        with patch('countdown_service.time.sleep') as mock_sleep:
            result = service.start_countdown(5, "Current text", "Next text", "Last text", callback)
        
        assert service.countdown_active is False  # Countdown completes immediately in test
        assert result['cancelled'] is False
    
    @pytest.mark.unit
    def test_start_countdown_zero_seconds(self, service):
        """Test countdown with zero seconds."""
        callback = Mock()
        
        with patch('countdown_service.time.sleep') as mock_sleep:
            result = service.start_countdown(0, "Current text", "Next text", "Last text", callback)
        
        assert service.countdown_active is False  # Countdown completes immediately
        assert result['cancelled'] is False
    
    @pytest.mark.unit
    def test_start_countdown_negative_seconds(self, service):
        """Test countdown with negative seconds."""
        callback = Mock()
        
        with patch('countdown_service.time.sleep') as mock_sleep:
            result = service.start_countdown(-5, "Current text", "Next text", "Last text", callback)
        
        assert service.countdown_active is False  # Countdown completes immediately
        assert result['cancelled'] is False
    
    @pytest.mark.unit
    def test_start_countdown_with_callback(self, service):
        """Test countdown with callback function."""
        callback = Mock()
        
        with patch('countdown_service.time.sleep') as mock_sleep:
            result = service.start_countdown(1, "Current text", "Next text", "Last text", callback)
        
        callback.assert_called_once()
    
    @pytest.mark.unit
    def test_start_countdown_without_callback(self, service):
        """Test countdown without callback function."""
        with patch('countdown_service.time.sleep') as mock_sleep:
            result = service.start_countdown(1, "Current text", "Next text", "Last text", None)
        
        # Should not raise error
        assert result is not None
    
    @pytest.mark.unit
    def test_toggle_pause(self, service):
        """Test pausing countdown."""
        service.countdown_active = True
        service.pause_btn.configure = Mock()
        
        service.toggle_pause()
        
        assert service.paused is True
        service.pause_btn.configure.assert_called()
    
    @pytest.mark.unit
    def test_resume_countdown(self, service):
        """Test resuming countdown."""
        service.countdown_active = True
        service.paused = True
        service.pause_btn.configure = Mock()
        
        service.toggle_pause()  # Resume
        
        assert service.paused is False
        service.pause_btn.configure.assert_called()
    
    @pytest.mark.unit
    def test_cancel_countdown(self, service):
        """Test cancelling countdown."""
        service.countdown_active = True
        service.cancel()
        
        assert service.cancelled is True
        assert service.countdown_active is False
    

    
    @pytest.mark.unit
    def test_reset_state(self, service):
        """Test resetting state."""
        service.paused = True
        service.cancelled = True
        
        service._reset_state()
        
        assert service.paused is False
        assert service.cancelled is False
    
    @pytest.mark.unit
    def test_get_final_state(self, service):
        """Test getting final state."""
        service.cancelled = True
        service.paused = True
        
        state = service._get_final_state()
        
        assert state['cancelled'] is True
        assert state['paused'] is True
    
    @pytest.mark.unit
    def test_update_display_with_progress(self, service):
        """Test updating display with progress bar."""
        service.progress.set = Mock()
        
        service._update_display(5.0, 10.0, "Current", "Next")
        
        service.progress.set.assert_called_once_with(0.5)
    
    @pytest.mark.unit
    def test_update_display_zero_total(self, service):
        """Test updating display with zero total."""
        service.progress.set = Mock()
        
        service._update_display(5.0, 0.0, "Current", "Next")
        
        service.progress.set.assert_called_once_with(0.0)
    
    @pytest.mark.unit
    def test_update_display_no_progress(self, service):
        """Test updating display without progress bar."""
        service.progress = None
        service.time_label.configure = Mock()
        
        service._update_display(5.0, 10.0, "Current", "Next")
        
        service.time_label.configure.assert_called_once_with(text="5")
    
    @pytest.mark.unit
    def test_update_display_no_widgets(self, service):
        """Test updating display without widgets."""
        service.time_label = None
        service.progress = None
        service.pause_btn = None
        service.current_box = None
        service.next_box = None
        
        # Should not raise error
        service._update_display(5.0, 10.0, "Current", "Next")
    
    @pytest.mark.unit
    def test_countdown_loop_normal_completion(self, service):
        """Test normal countdown loop completion."""
        with patch('countdown_service.time.sleep') as mock_sleep:
            service._countdown_loop(5.0, 5.0, "Current", "Next", "Last")
        
        assert service.countdown_active is False
    
    @pytest.mark.unit
    def test_countdown_loop_cancelled(self, service):
        """Test countdown loop when cancelled."""
        service.cancelled = True
        
        with patch('countdown_service.time.sleep') as mock_sleep:
            service._countdown_loop(5.0, 5.0, "Current", "Next", "Last")
        
        assert service.countdown_active is False
    
    @pytest.mark.unit
    def test_countdown_loop_paused_resumed(self, service):
        """Test countdown loop with pause/resume."""
        service.paused = True
        
        with patch('countdown_service.time.sleep') as mock_sleep:
            service._countdown_loop(1.0, 1.0, "Current", "Next", "Last")
        
        assert service.countdown_active is False
    
    @pytest.mark.unit
    def test_countdown_loop_very_short_duration(self, service):
        """Test countdown loop with very short duration."""
        with patch('countdown_service.time.sleep') as mock_sleep:
            service._countdown_loop(0.1, 0.1, "Current", "Next", "Last")
        
        assert service.countdown_active is False
    
    @pytest.mark.unit
    def test_countdown_loop_with_none_texts(self, service):
        """Test countdown loop with None texts."""
        with patch('countdown_service.time.sleep') as mock_sleep:
            service._countdown_loop(1.0, 1.0, None, None, None)
        
        assert service.countdown_active is False
    
    @pytest.mark.unit
    def test_countdown_loop_callback_error(self, service):
        """Test countdown loop when callback raises error."""
        callback = Mock(side_effect=Exception("Callback error"))
        service.on_countdown_complete = callback
        
        with patch('countdown_service.time.sleep') as mock_sleep:
            # Should not raise error, should still complete
            service._countdown_loop(1.0, 1.0, "Current", "Next", "Last")
        
        assert service.countdown_active is False
    
    @pytest.mark.unit
    def test_is_active_true(self, service):
        """Test countdown active status when true."""
        service.countdown_active = True
        assert service.is_active() is True
    
    @pytest.mark.unit
    def test_is_active_false(self, service):
        """Test countdown active status when false."""
        service.countdown_active = False
        assert service.is_active() is False
    
    @pytest.mark.unit
    def test_is_paused_true(self, service):
        """Test paused status when true."""
        service.paused = True
        assert service.is_paused() is True
    
    @pytest.mark.unit
    def test_is_paused_false(self, service):
        """Test paused status when false."""
        service.paused = False
        assert service.is_paused() is False
    
    @pytest.mark.unit
    def test_stop(self, service):
        """Test stopping the service."""
        service.countdown_active = True
        service.stop()
        
        assert service.countdown_active is False
        assert service.cancelled is True
