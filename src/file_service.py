"""
File Service for Prompt List Management

This module orchestrates dedicated services for prompt list file operations:
- PathService: Path resolution and validation
- ParserService: File format parsing
- WriterService: File format writing
- ConfigService: User preferences

Author: Automation System
Version: 3.0
"""

import os
from typing import List, Tuple, Union

try:
    from .config_service import ConfigService
    from .parser_service import ParserService
    from .path_service import PathService
    from .writer_service import WriterService
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    # Add src directory to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

    from config_service import ConfigService
    from parser_service import ParserService
    from path_service import PathService
    from writer_service import WriterService


class PromptListService:
    """Orchestrator service for managing prompt list files with multiple
    format support."""

    def __init__(self):
        """Initialize the prompt list service with dedicated sub-services."""
        self.path_service = PathService()
        self.parser_service = ParserService()
        self.writer_service = WriterService()
        self.config_service = ConfigService()
        self.default_path = self.path_service.default_path

    def resolve_path(self, path: str) -> str:
        """Resolve a path to an absolute path."""
        return self.path_service.resolve_path(path)

    def validate_file_exists(self, path: str) -> Tuple[bool, str]:
        """Validate that a file exists and is readable."""
        return self.path_service.validate_file_exists(path)

    def parse_prompt_list(self, path: str) -> Tuple[bool, Union[List[str], str]]:
        """
        Parse a prompt list file based on file type.

        Priority order:
        1. .py files: Import the array variable (default behavior)
        2. .txt files: Parse as line-separated prompts
        3. .csv files: Parse as comma-separated prompts

        Args:
            path: Path to the prompt list file

        Returns:
            Tuple of (success, prompts_list_or_error_message)
        """
        try:
            resolved_path = self.path_service.resolve_path(path)

            # Validate file exists and is readable
            is_valid, error_msg = self.path_service.validate_file_exists(resolved_path)
            if not is_valid:
                return False, error_msg

            # Get file extension
            file_ext = self.path_service.get_file_extension(resolved_path)

            # Read file content
            with open(resolved_path, encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                return True, []

            # Parse based on file type
            if file_ext == "py":
                return self.parser_service.parse_python_file(resolved_path, content)
            if file_ext == "txt":
                return self.parser_service.parse_text_file(content)
            if file_ext == "csv":
                return self.parser_service.parse_csv_file(content)
            # For unknown extensions, return error
            return False, "Unsupported file format"

        except OSError as e:
            return False, f"Error reading file: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error parsing file: {str(e)}"

    def get_prompt_preview(self, prompts: List[str], max_length: int = 100) -> str:
        """
        Get a preview of the first prompt for display.

        Args:
            prompts: List of prompts
            max_length: Maximum length for preview

        Returns:
            Preview string
        """
        if not prompts:
            return "No prompts available"

        first_prompt = prompts[0]
        if len(first_prompt) <= max_length:
            return first_prompt

        return first_prompt[:max_length] + "..."

    def save_path_preference(self, path: str) -> bool:
        """Save the path preference for future use."""
        return self.config_service.save_path_preference(path)

    def load_path_preference(self) -> str:
        """Load the saved path preference."""
        return self.config_service.load_path_preference(self.default_path)

    def get_default_prompt_list_path(self) -> str:
        """Get the default prompt list path."""
        return self.path_service.get_default_path()

    def save_prompts(self, file_path: str, prompts: List[str]) -> bool:
        """
        Save prompts to a file in the appropriate format.

        Args:
            file_path: Path to save the file
            prompts: List of prompts to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.path_service.validate_file_path(file_path):
                return False

            # Create directory if needed
            if not self.path_service.create_directory_if_needed(file_path):
                return False

            file_ext = self.path_service.get_file_extension(file_path)

            if file_ext == "py":
                return self.writer_service.save_python_file(file_path, prompts)
            if file_ext == "txt":
                return self.writer_service.save_text_file(file_path, prompts)
            if file_ext == "csv":
                return self.writer_service.save_csv_file(file_path, prompts)
            return False

        except (OSError, PermissionError) as e:
            print(f"Permission error saving prompts: {e}")
            return False
        except Exception as e:
            print(f"Error saving prompts: {e}")
            return False

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return self.writer_service.get_supported_formats()

    # Convenience methods for backward compatibility with tests
    def _get_file_extension(self, file_path: str) -> str:
        """Get file extension from path (for backward compatibility)."""
        return self.path_service.get_file_extension(file_path)

    def _validate_file_path(self, file_path: str) -> bool:
        """Validate file path (for backward compatibility)."""
        return self.path_service.validate_file_path(file_path)

    def _create_directory_if_needed(self, file_path: str) -> bool:
        """Create directory for file if it doesn't exist (for backward
        compatibility)."""
        return self.path_service.create_directory_if_needed(file_path)
