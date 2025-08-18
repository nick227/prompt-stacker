"""
Prompt Stacker - Cursor Automation System

A powerful automation system for Cursor with beautiful Monokai-themed UI.
Enhanced with modular architecture, centralized configuration, error handling,
and performance monitoring.
"""

__version__ = "2.0.0"
__author__ = "Automation System"

# Import main functions for easy access
from .automator import run_automation

# Import new architecture components
from .config import config, get_automation_config, get_theme_config, get_ui_config
from .error_handler import handle_error, log_error, log_info, log_warning, safe_call
from .performance import (
    cleanup_memory,
    start_performance_monitoring,
    stop_performance_monitoring,
)
from .ui import RefactoredSessionUI as SessionUI
from .win_focus import CursorWindow

# Export all public components
__all__ = [
    # Core functionality
    "run_automation",
    "SessionUI",
    "CursorWindow",
    # Configuration
    "config",
    "get_ui_config",
    "get_theme_config",
    "get_automation_config",
    # Error handling
    "handle_error",
    "log_info",
    "log_warning",
    "log_error",
    "safe_call",
    # Performance
    "start_performance_monitoring",
    "stop_performance_monitoring",
    "cleanup_memory",
]
