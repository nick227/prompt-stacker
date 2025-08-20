"""
Test Utilities for Automation System

Shared utilities, fixtures, and mock objects for testing the automation system.
This module centralizes common test patterns and reduces code duplication.
"""

import threading
from unittest.mock import Mock, patch


def create_mock_ui_session(**kwargs) -> Mock:
    """
    Create a standardized mock UI session for testing.
    
    This factory function creates a mock UI session with all the necessary
    attributes and methods required by the AutomationController and legacy code.
    
    Args:
        **kwargs: Additional attributes to set on the mock
    
    Returns:
        Mock object configured for automation testing
    """
    ui = Mock()

    # Mock coordinate service for AutomationController validation
    mock_coordinate_service = Mock()
    mock_coordinate_service.validate_coordinates.return_value = {
        "input": True,
        "submit": True,
        "accept": True,
    }
    ui.coordinate_service = mock_coordinate_service

    # Mock countdown service
    mock_countdown_service = Mock()
    mock_countdown_service.is_active.return_value = False
    mock_countdown_service.is_paused.return_value = False
    ui.countdown_service = mock_countdown_service

    # Thread safety attributes
    ui._automation_lock = threading.Lock()
    ui._prompts_locked = False
    ui._prompts = ["Test prompt 1", "Test prompt 2", "Test prompt 3"]

    # Legacy compatibility methods
    ui.get_prompts_safe = Mock(return_value=["Test prompt 1", "Test prompt 2", "Test prompt 3"])
    ui.current_prompt_index = 0
    ui.update_prompt_index_from_automation = Mock()
    ui.get_wait_time = Mock(return_value=1)
    ui.get_countdown_time = Mock(return_value=2)
    ui.get_coords = Mock(return_value={
        "input": (100, 200),
        "submit": (300, 400),
        "accept": (500, 600),
    })
    ui.get_timers = Mock(return_value=(5, 300, 0.2, 2.0))
    ui.countdown = Mock(return_value={"cancelled": False})
    ui.bring_to_front = Mock()

    # Timer variable access for AutomationController
    ui.main_wait_var = Mock()
    ui.main_wait_var.get.return_value = "300"
    ui.get_ready_delay_var = Mock()
    ui.get_ready_delay_var.get.return_value = "2"
    ui.start_delay_var = Mock()
    ui.start_delay_var.get.return_value = "5"
    ui.cooldown_var = Mock()
    ui.cooldown_var.get.return_value = "0.2"

    # UI-specific attributes
    ui.prompts = ["Test prompt 1", "Test prompt 2", "Test prompt 3"]

    # Apply any custom attributes
    for key, value in kwargs.items():
        setattr(ui, key, value)

    return ui


def mock_automation_controller_success():
    """
    Create a mock AutomationController that returns success.
    
    Returns:
        Context manager for patching AutomationController
    """
    return patch("src.automation_controller.AutomationController")


def mock_automation_controller_failure() -> patch:
    """
    Create a mock AutomationController that returns failure.
    
    Returns:
        Context manager for patching AutomationController
    """
    def _patch():
        with patch("src.automation_controller.AutomationController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller.start_automation.return_value = False
            mock_controller_class.return_value = mock_controller
            yield mock_controller_class, mock_controller

    return _patch()


def mock_automation_controller_with_context() -> patch:
    """
    Create a mock AutomationController with context for single prompt testing.
    
    Returns:
        Context manager for patching AutomationController
    """
    def _patch():
        with patch("src.automation_controller.AutomationController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller.start_automation.return_value = True
            # Mock context to handle the prompt index assignment
            mock_context = Mock()
            mock_controller._context = mock_context
            mock_controller_class.return_value = mock_controller
            yield mock_controller_class, mock_controller, mock_context

    return _patch()


class AutomationTestMixin:
    """
    Mixin class providing common automation testing utilities.
    
    This class can be inherited by test classes to provide common
    automation testing functionality.
    """

    def create_ui_mock(self, **kwargs):
        """Create a mock UI session for this test."""
        return create_mock_ui_session(**kwargs)

    def assert_automation_success(self, result, mock_controller_class, mock_controller):
        """Assert that automation completed successfully."""
        assert result is True
        mock_controller_class.assert_called_once()
        mock_controller.start_automation.assert_called_once()

    def assert_automation_failure(self, result, mock_controller_class=None, mock_controller=None):
        """Assert that automation failed."""
        assert result is False
        if mock_controller_class:
            mock_controller_class.assert_called_once()
        if mock_controller:
            mock_controller.start_automation.assert_called_once()


# Legacy test patterns that should be migrated to the new architecture
DEPRECATED_PATTERNS = [
    "run_automation_with_ui.*patch.*src.automator",
    "mock_ui.countdown.return_value",
    "paste_text_safely.*return_value",
    "click_button_or_fallback.*return_value",
]

RECOMMENDED_PATTERNS = [
    "Use mock_automation_controller_success() for successful automation tests",
    "Use mock_automation_controller_failure() for failed automation tests",
    "Use create_mock_ui_session() for standardized UI mocks",
    "Use AutomationTestMixin for common test utilities",
]
