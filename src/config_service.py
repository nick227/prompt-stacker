"""
Configuration Service for User Preferences

This module handles user configuration and preferences including:
- Path preference saving and loading
- User settings management

Author: Automation System
Version: 1.0
"""

from pathlib import Path


class ConfigService:
    """Service for managing user configuration and preferences."""

    def __init__(self):
        """Initialize the configuration service."""
        self.config_dir = Path.home() / ".prompt_stacker"
        self.config_file = self.config_dir / "prompt_list_path.txt"
        self.timer_config_file = self.config_dir / "timer_settings.json"
        self.last_directory_file = self.config_dir / "last_directory.txt"

    def save_path_preference(self, path: str) -> bool:
        """
        Save the path preference for future use.

        Args:
            path: Path to save

        Returns:
            True if saved successfully
        """
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(path)

            return True
        except OSError as e:
            print(f"Warning: Could not save path preference: {e}")
            return False

    def load_path_preference(self, default_path: str) -> str:
        """
        Load the saved path preference.

        Args:
            default_path: Default path to return if no preference is saved

        Returns:
            Saved path or default path
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, encoding="utf-8") as f:
                    saved_path = f.read().strip()
                    if saved_path:
                        return saved_path
        except OSError as e:
            print(f"Warning: Could not load path preference: {e}")

        return default_path

    def save_last_directory(self, directory: str) -> bool:
        """
        Save the last used directory for file browser.

        Args:
            directory: Directory path to save

        Returns:
            True if saved successfully
        """
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(exist_ok=True)

            with open(self.last_directory_file, "w", encoding="utf-8") as f:
                f.write(directory)

            return True
        except OSError as e:
            print(f"Warning: Could not save last directory: {e}")
            return False

    def load_last_directory(self, default_directory: str) -> str:
        """
        Load the last used directory for file browser.

        Args:
            default_directory: Default directory to return if no preference is saved

        Returns:
            Saved directory or default directory
        """
        try:
            if self.last_directory_file.exists():
                with open(self.last_directory_file, encoding="utf-8") as f:
                    saved_directory = f.read().strip()
                    if saved_directory and Path(saved_directory).exists():
                        return saved_directory
        except OSError as e:
            print(f"Warning: Could not load last directory: {e}")

        return default_directory

    def save_timer_preferences(self, main_wait: str, get_ready_delay: str) -> bool:
        """
        Save timer preferences for future use.

        Args:
            main_wait: Main wait time value
            get_ready_delay: Get ready delay value

        Returns:
            True if saved successfully
        """
        try:
            import json

            # Create config directory if it doesn't exist
            self.config_dir.mkdir(exist_ok=True)

            timer_settings = {
                "main_wait": main_wait,
                "get_ready_delay": get_ready_delay,
            }

            with open(self.timer_config_file, "w", encoding="utf-8") as f:
                json.dump(timer_settings, f, indent=2)

            return True
        except OSError as e:
            print(f"Warning: Could not save timer preferences: {e}")
            return False

    def load_timer_preferences(
        self, default_main_wait: str = "500", default_get_ready_delay: str = "3"
    ) -> tuple[str, str]:
        """
        Load the saved timer preferences.

        Args:
            default_main_wait: Default main wait time if no preference is saved
            default_get_ready_delay: Default get ready delay if no preference is saved

        Returns:
            Tuple of (main_wait, get_ready_delay)
        """
        try:
            import json

            if self.timer_config_file.exists():
                with open(self.timer_config_file, encoding="utf-8") as f:
                    timer_settings = json.load(f)
                    main_wait = timer_settings.get("main_wait", default_main_wait)
                    get_ready_delay = timer_settings.get(
                        "get_ready_delay", default_get_ready_delay
                    )
                    return main_wait, get_ready_delay
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load timer preferences: {e}")

        return default_main_wait, default_get_ready_delay
