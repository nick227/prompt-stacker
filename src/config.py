"""
Configuration Management System

Centralized configuration for the Cursor automation system.
Replaces hard-coded constants with a maintainable configuration system.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

# =============================================================================
# CONFIGURATION DATACLASSES
# =============================================================================


@dataclass
class UIConfig:
    """UI configuration settings."""

    # Window settings
    window_width: int = 840
    window_height: int = 800
    window_margin: int = 20

    # Layout constants
    card_radius: int = 12
    section_radius: int = 12
    padding: int = 16
    gutter: int = 12
    button_width: int = 80
    entry_width: int = 80
    path_entry_width: int = 250

    # Typography
    font_h1: tuple = ("Segoe UI Variable", 28, "bold")
    font_h2: tuple = ("Segoe UI", 13, "bold")
    font_body: tuple = ("Segoe UI", 12)

    # Timing
    tick_interval: int = 100
    capture_delay: float = 0.12
    countdown_tick: float = 0.1
    wait_tick: float = 0.05


@dataclass
class ThemeConfig:
    """Theme configuration for Monokai Dark theme."""

    # Color palette
    bg: str = "#272822"
    surface: str = "#3E3D32"
    surface_alt: str = "#2F2F2F"
    border: str = "#75715E"
    primary: str = "#F92672"
    primary_hover: str = "#FD5FF0"
    text: str = "#F8F8F2"
    white_text: str = "#FFFFFF"
    text_muted: str = "#75715E"
    accent: str = "#A6E22E"
    warning: str = "#E6DB74"
    error: str = "#F92672"
    success: str = "#A6E22E"

    # Button colors
    button_bg: str = "#2F2F2F"
    button_hover: str = "#1f1f1f"
    button_text: str = "#FFFFFF"
    button_start_active: str = "#58a807"
    button_start_active_hover: str = "#58a807"
    button_start_inactive: str = "#75715E"
    button_stop_active: str = "#910d0d"
    button_stop_active_hover: str = "#910d0d"
    button_pause_active: str = "#521559"
    button_pause_active_hover: str = "#2F2F2F"

    # Prompt list colors
    prompt_current_bg: str = "#000000"
    prompt_current_text: str = "#FFFFFF"
    prompt_standard_bg: str = "#3E3D32"
    prompt_standard_text: str = "#F8F8F2"

    # Button text constants
    btn_start: str = "Start"
    btn_stop: str = "Stop"
    btn_pause: str = "Pause"
    btn_resume: str = "Resume"
    btn_next: str = "Next"
    btn_retry: str = "Retry"
    btn_skip: str = "Skip"
    btn_cancel: str = "Cancel"


@dataclass
class AutomationConfig:
    """Automation configuration settings."""

    # Default timing values
    default_start_delay: int = 5
    default_main_wait: int = 300
    default_cooldown: float = 0.2
    default_get_ready_delay: float = 2.0

    # Automation constants
    focus_delay: float = 0.05
    clipboard_retry_attempts: int = 3
    clipboard_retry_delay: float = 0.2

    # PyAutoGUI settings
    pyautogui_pause: float = 0.1
    pyautogui_failsafe: bool = True


@dataclass
class FileConfig:
    """File and path configuration."""

    # Default paths
    default_prompt_list_dir: str = "prompt_lists"
    default_prompt_list_file: str = "prompt_list.py"
    settings_file: str = "coords.json"

    # File validation
    max_file_size_mb: int = 10
    supported_extensions: tuple = (".py", ".txt", ".csv")

    # Prompt list variable names
    default_prompt_variable: str = "prompt_list"
    alternative_variables: tuple = ("prompts", "prompt_list", "PROMPT_LIST")


@dataclass
class WindowConfig:
    """Window focus configuration."""

    # Cursor window detection
    default_title: str = "Cursor"
    title_pattern: str = ".*Cursor.*"
    connection_timeout: int = 5

    # Focus attempts
    focus_attempts: int = 5
    focus_delay: float = 0.3


@dataclass
class AppConfig:
    """Main application configuration."""

    # Application metadata
    name: str = "Prompt Stacker"
    version: str = "2.0.0"
    description: str = (
        "A powerful automation system for Cursor with beautiful Monokai-themed UI"
    )

    # Target configuration
    target_keys: tuple = ("input", "submit", "accept")
    target_labels: Dict[str, str] = field(
        default_factory=lambda: {
            "input": "Input",
            "submit": "Submit",
            "accept": "Accept",
        },
    )


# =============================================================================
# CONFIGURATION MANAGER
# =============================================================================


class ConfigManager:
    """Manages application configuration with environment overrides."""

    def __init__(self):
        """Initialize the configuration manager."""
        self.ui = UIConfig()
        self.theme = ThemeConfig()
        self.automation = AutomationConfig()
        self.file = FileConfig()
        self.window = WindowConfig()
        self.app = AppConfig()

        # Load environment overrides
        self._load_environment_overrides()

    def _load_environment_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        # UI overrides
        if os.getenv("PROMPT_STACKER_WINDOW_WIDTH"):
            self.ui.window_width = int(os.getenv("PROMPT_STACKER_WINDOW_WIDTH"))
        if os.getenv("PROMPT_STACKER_WINDOW_HEIGHT"):
            self.ui.window_height = int(os.getenv("PROMPT_STACKER_WINDOW_HEIGHT"))

        # Automation overrides
        if os.getenv("PROMPT_STACKER_START_DELAY"):
            self.automation.default_start_delay = int(
                os.getenv("PROMPT_STACKER_START_DELAY"),
            )
        if os.getenv("PROMPT_STACKER_MAIN_WAIT"):
            self.automation.default_main_wait = int(
                os.getenv("PROMPT_STACKER_MAIN_WAIT"),
            )
        if os.getenv("PROMPT_STACKER_COOLDOWN"):
            self.automation.default_cooldown = float(
                os.getenv("PROMPT_STACKER_COOLDOWN"),
            )

        # Window overrides
        if os.getenv("CURSOR_TARGET_TITLE"):
            self.window.default_title = os.getenv("CURSOR_TARGET_TITLE")
            self.window.title_pattern = f".*{self.window.default_title}.*"

    def get_default_prompt_list_path(self) -> str:
        """Get the default prompt list path."""
        try:
            # PyInstaller-compatible path resolution
            if getattr(sys, "frozen", False):
                # Running as executable
                base_path = Path(sys._MEIPASS)
                default_path = (
                    base_path
                    / self.file.default_prompt_list_dir
                    / self.file.default_prompt_list_file
                )
            else:
                # Running as script
                current_dir = Path(__file__).parent  # src directory
                project_root = current_dir.parent  # project root
                default_path = (
                    project_root
                    / self.file.default_prompt_list_dir
                    / self.file.default_prompt_list_file
                )

            return str(default_path.absolute())
        except (OSError, ValueError):
            return (f"{self.file.default_prompt_list_dir}/"
                   f"{self.file.default_prompt_list_file}")

    def get_settings_file_path(self) -> str:
        """Get the settings file path."""
        try:
            # PyInstaller-compatible path resolution
            if getattr(sys, "frozen", False):
                # Running as executable - use user directory
                base_path = Path.home() / "prompt_stacker_logs"
                return str((base_path / self.file.settings_file).absolute())
            # Running as script
            current_dir = Path(__file__).parent  # src directory
            return str((current_dir / self.file.settings_file).absolute())
        except (OSError, ValueError):
            return self.file.settings_file

    def validate_config(self) -> Dict[str, Any]:
        """Validate the current configuration."""
        errors = []
        warnings = []

        # Validate UI configuration
        if self.ui.window_width < 400:
            errors.append("Window width too small")
        if self.ui.window_height < 300:
            errors.append("Window height too small")

        # Validate automation configuration
        if self.automation.default_start_delay < 0:
            errors.append("Start delay cannot be negative")
        if self.automation.default_main_wait < 1:
            errors.append("Main wait must be at least 1 second")
        if self.automation.default_cooldown < 0:
            errors.append("Cooldown cannot be negative")

        # Validate file configuration
        if not self.file.supported_extensions:
            errors.append("No supported file extensions defined")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "ui": self.ui.__dict__,
            "theme": self.theme.__dict__,
            "automation": self.automation.__dict__,
            "file": self.file.__dict__,
            "window": self.window.__dict__,
            "app": self.app.__dict__,
        }

    def from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from dictionary."""
        if "ui" in config_dict:
            for key, value in config_dict["ui"].items():
                if hasattr(self.ui, key):
                    setattr(self.ui, key, value)

        if "theme" in config_dict:
            for key, value in config_dict["theme"].items():
                if hasattr(self.theme, key):
                    setattr(self.theme, key, value)

        if "automation" in config_dict:
            for key, value in config_dict["automation"].items():
                if hasattr(self.automation, key):
                    setattr(self.automation, key, value)

        if "file" in config_dict:
            for key, value in config_dict["file"].items():
                if hasattr(self.file, key):
                    setattr(self.file, key, value)

        if "window" in config_dict:
            for key, value in config_dict["window"].items():
                if hasattr(self.window, key):
                    setattr(self.window, key, value)

        if "app" in config_dict:
            for key, value in config_dict["app"].items():
                if hasattr(self.app, key):
                    setattr(self.app, key, value)


# =============================================================================
# GLOBAL CONFIGURATION INSTANCE
# =============================================================================

# Global configuration instance
config = ConfigManager()


# Convenience accessors
def get_ui_config() -> UIConfig:
    """Get UI configuration."""
    return config.ui


def get_theme_config() -> ThemeConfig:
    """Get theme configuration."""
    return config.theme


def get_automation_config() -> AutomationConfig:
    """Get automation configuration."""
    return config.automation


def get_file_config() -> FileConfig:
    """Get file configuration."""
    return config.file


def get_window_config() -> WindowConfig:
    """Get window configuration."""
    return config.window


def get_app_config() -> AppConfig:
    """Get application configuration."""
    return config.app


# =============================================================================
# BACKWARD COMPATIBILITY CONSTANTS
# =============================================================================

# These constants provide backward compatibility with existing code
# They should be gradually replaced with config.theme.* and config.ui.*

# Colors
try:
    COLOR_BG = config.theme.bg
    COLOR_SURFACE = config.theme.surface
    COLOR_SURFACE_ALT = config.theme.surface_alt
    COLOR_BORDER = config.theme.border
    COLOR_PRIMARY = config.theme.primary
    COLOR_PRIMARY_HOVER = config.theme.primary_hover
    COLOR_TEXT = config.theme.text
    WHITE_COLOR_TEXT = config.theme.white_text
    COLOR_TEXT_MUTED = config.theme.text_muted
    COLOR_ACCENT = config.theme.accent
    COLOR_WARNING = config.theme.warning
    COLOR_ERROR = config.theme.error
    COLOR_SUCCESS = config.theme.success
except AttributeError:
    # Fallback values if config is not fully initialized
    COLOR_BG = "#272822"
    COLOR_SURFACE = "#3E3D32"
    COLOR_SURFACE_ALT = "#2F2F2F"
    COLOR_BORDER = "#75715E"
    COLOR_PRIMARY = "#F92672"
    COLOR_PRIMARY_HOVER = "#FD5FF0"
    COLOR_TEXT = "#F8F8F2"
    WHITE_COLOR_TEXT = "#FFFFFF"
    COLOR_TEXT_MUTED = "#75715E"
    COLOR_ACCENT = "#A6E22E"
    COLOR_WARNING = "#E6DB74"
    COLOR_ERROR = "#F92672"
    COLOR_SUCCESS = "#A6E22E"

COLOR_MODIFIED = "#3B82F6"  # Blue color for modified files

# Button colors
try:
    BUTTON_BG = config.theme.button_bg
    BUTTON_HOVER = config.theme.button_hover
    BUTTON_TEXT = config.theme.button_text
    BUTTON_START_ACTIVE = config.theme.button_start_active
    BUTTON_START_ACTIVE_HOVER = config.theme.button_start_active_hover
    BUTTON_STOP_ACTIVE = config.theme.button_stop_active
    BUTTON_STOP_ACTIVE_HOVER = config.theme.button_stop_active_hover
    BUTTON_START_INACTIVE = config.theme.button_start_inactive
    BUTTON_PAUSE_ACTIVE = config.theme.button_pause_active
    BUTTON_PAUSE_ACTIVE_HOVER = config.theme.button_pause_active_hover
except AttributeError:
    # Fallback values if config is not fully initialized
    BUTTON_BG = "#2F2F2F"
    BUTTON_HOVER = "#1f1f1f"
    BUTTON_TEXT = "#FFFFFF"
    BUTTON_START_ACTIVE = "#58a807"
    BUTTON_START_ACTIVE_HOVER = "#58a807"
    BUTTON_STOP_ACTIVE = "#910d0d"
    BUTTON_STOP_ACTIVE_HOVER = "#910d0d"
    BUTTON_START_INACTIVE = "#75715E"
    BUTTON_PAUSE_ACTIVE = "#521559"
    BUTTON_PAUSE_ACTIVE_HOVER = "#2F2F2F"

# Prompt colors
try:
    PROMPT_CURRENT_BG = config.theme.prompt_current_bg
    PROMPT_CURRENT_TEXT = config.theme.prompt_current_text
    PROMPT_STANDARD_BG = config.theme.prompt_standard_bg
    PROMPT_STANDARD_TEXT = config.theme.prompt_standard_text
except AttributeError:
    # Fallback values if config is not fully initialized
    PROMPT_CURRENT_BG = "#000000"
    PROMPT_CURRENT_TEXT = "#FFFFFF"
    PROMPT_STANDARD_BG = "#3E3D32"
    PROMPT_STANDARD_TEXT = "#F8F8F2"

# Fonts
try:
    FONT_H1 = config.ui.font_h1
    FONT_H2 = config.ui.font_h2
    FONT_BODY = config.ui.font_body

    # Layout
    WINDOW_WIDTH = config.ui.window_width
    WINDOW_HEIGHT = config.ui.window_height
    WINDOW_MARGIN = config.ui.window_margin
    CARD_RADIUS = config.ui.card_radius
    SECTION_RADIUS = config.ui.section_radius
    PADDING = config.ui.padding
    GUTTER = config.ui.gutter
    BUTTON_WIDTH = config.ui.button_width
    ENTRY_WIDTH = config.ui.entry_width
    PATH_ENTRY_WIDTH = config.ui.path_entry_width

    # Timing
    TICK_INTERVAL = config.ui.tick_interval
    CAPTURE_DELAY = config.ui.capture_delay
    COUNTDOWN_TICK = config.ui.countdown_tick
    WAIT_TICK = config.ui.wait_tick
except AttributeError:
    # Fallback values if config is not fully initialized
    FONT_H1 = ("Segoe UI Variable", 28, "bold")
    FONT_H2 = ("Segoe UI", 13, "bold")
    FONT_BODY = ("Segoe UI", 12)

    # Layout
    WINDOW_WIDTH = 840
    WINDOW_HEIGHT = 800
    WINDOW_MARGIN = 20
    CARD_RADIUS = 12
    SECTION_RADIUS = 12
    PADDING = 16
    GUTTER = 12
    BUTTON_WIDTH = 80
    ENTRY_WIDTH = 80
    PATH_ENTRY_WIDTH = 250

    # Timing
    TICK_INTERVAL = 100
    CAPTURE_DELAY = 0.12
    COUNTDOWN_TICK = 0.1
    WAIT_TICK = 0.05

# Button text
try:
    BTN_START = config.theme.btn_start
    BTN_STOP = config.theme.btn_stop
    BTN_PAUSE = config.theme.btn_pause
    BTN_RESUME = config.theme.btn_resume
    BTN_NEXT = config.theme.btn_next
    BTN_RETRY = config.theme.btn_retry
    BTN_SKIP = config.theme.btn_skip
    BTN_CANCEL = config.theme.btn_cancel
except AttributeError:
    # Fallback values if config is not fully initialized
    BTN_START = "Start"
    BTN_STOP = "Stop"
    BTN_PAUSE = "Pause"
    BTN_RESUME = "Resume"
    BTN_NEXT = "Next"
    BTN_RETRY = "Retry"
    BTN_SKIP = "Skip"
    BTN_CANCEL = "Cancel"

# Target keys and labels
try:
    TARGET_KEYS = config.app.target_keys
    LABELS = config.app.target_labels
except AttributeError:
    # Fallback values if config is not fully initialized
    TARGET_KEYS = ["input", "submit", "accept"]
    LABELS = ["Input Field", "Submit Button", "Accept Button"]

# Prompt state constants
PROMPT_STATE_CURRENT = "current"
PROMPT_STATE_NORMAL = "normal"
