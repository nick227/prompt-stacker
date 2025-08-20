"""
Prompt Stacker - Automation System

A Python application for automating repetitive text input tasks.
"""

try:
    from .automator import run_automation
    from .config import get_automation_config, get_theme_config, get_ui_config
    from .ui import SessionUI
except ImportError:
    # Fallback for when running as script
    pass

__version__ = "2.0.0"
__author__ = "Automation System"

# Import new architecture components
from .error_handler import handle_error, log_error, log_info, log_warning, safe_call
from .performance import (
    start_performance_monitoring,
    stop_performance_monitoring,
)
from .win_focus import CursorWindow

# Public API
__all__ = [
    # Main UI
    "SessionUI",
    # Automation
    "run_automation",
    # Window management
    "CursorWindow",
    # Configuration
    "get_ui_config",
    "get_theme_config",
    "get_automation_config",
    # Error handling
    "handle_error",
    "log_error",
    "log_info",
    "log_warning",
    "safe_call",
    # Performance
    "start_performance_monitoring",
    "stop_performance_monitoring",
]
