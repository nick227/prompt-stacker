"""
Path Service for File Path Management

This module handles all path-related operations including:
- Path resolution and validation
- Default path management
- File existence and readability checks

Author: Automation System
Version: 1.0
"""

import os
import sys
from pathlib import Path
from typing import Tuple


class PathService:
    """Service for managing file paths and validation."""

    def __init__(self):
        """Initialize the path service."""
        self.default_path = self.get_default_path()

    def get_default_path(self) -> str:
        """Get the default prompt list path relative to the project root."""
        try:
            # PyInstaller-compatible path resolution
            if getattr(sys, "frozen", False):
                # Running as executable
                base_path = Path(getattr(sys, "_MEIPASS", ""))
                default_path = base_path / "prompt_lists" / "prompt_list.py"
            else:
                # Running as script
                current_dir = Path(__file__).parent  # src directory
                project_root = current_dir.parent  # project root
                default_path = project_root / "prompt_lists" / "prompt_list.py"

            return str(default_path.absolute())
        except (OSError, ValueError) as e:
            # Log the error for debugging but continue with fallback
            print(f"Warning: Could not resolve default path: {e}")
            return "prompt_lists/prompt_list.py"

    def resolve_path(self, path: str) -> str:
        """
        Resolve a path to an absolute path.

        Args:
            path: Relative or absolute path

        Returns:
            Absolute path string
        """
        try:
            return str(Path(path).resolve())
        except (OSError, ValueError) as e:
            # Log the error for debugging but continue with original path
            print(f"Warning: Could not resolve path '{path}': {e}")
            return path

    def validate_file_exists(self, path: str) -> Tuple[bool, str]:
        """
        Validate that a file exists and is readable.

        Args:
            path: File path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            resolved_path = self.resolve_path(path)
            if not os.path.exists(resolved_path):
                return False, f"File not found: {resolved_path}"

            if not Path(resolved_path).is_file():
                return False, f"Path is not a file: {resolved_path}"

            # Check if file is readable
            with open(resolved_path, encoding="utf-8") as f:
                f.read(1)  # Try to read first character
                f.seek(0)  # Reset to beginning

            return True, ""
        except PermissionError:
            return False, f"Permission denied: {path}"
        except UnicodeDecodeError:
            return (
                False,
                f"File is not a valid text file (binary or encoding issue): {path}",
            )
        except OSError as e:
            return False, f"Error reading file: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def get_file_extension(self, file_path: str) -> str:
        """
        Get file extension from path.

        Args:
            file_path: Path to file

        Returns:
            File extension without dot
        """
        if not file_path:
            return ""
        return Path(file_path).suffix.lower().lstrip(".")

    def validate_file_path(self, file_path: str) -> bool:
        """
        Validate file path.

        Args:
            file_path: Path to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(file_path and isinstance(file_path, str))

    def create_directory_if_needed(self, file_path: str) -> bool:
        """
        Create directory for file if it doesn't exist.

        Args:
            file_path: Path to file

        Returns:
            True if directory exists or was created, False otherwise
        """
        try:
            directory = Path(file_path).parent
            if directory.exists():
                return True
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False
        except Exception:
            return False
