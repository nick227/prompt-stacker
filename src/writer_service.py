"""
Writer Service for File Format Writing

This module handles writing prompts to different file formats including:
- Python files with variable arrays
- Text files with line-separated prompts
- CSV files with comma-separated prompts

Author: Automation System
Version: 1.0
"""

from typing import List


class WriterService:
    """Service for writing prompt lists to different file formats."""

    def save_python_file(self, file_path: str, prompts: List[str]) -> bool:
        """Save prompts as Python file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Prompt List\n")
                f.write("prompt_list = [\n")
                for prompt in prompts:
                    # Escape quotes and newlines
                    escaped_prompt = prompt.replace('"', '\\"').replace("\n", "\\n")
                    f.write(f'    "{escaped_prompt}",\n')
                f.write("]\n")
            return True
        except Exception:
            return False

    def save_text_file(self, file_path: str, prompts: List[str]) -> bool:
        """Save prompts as text file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for prompt in prompts:
                    f.write(prompt + "\n")
            return True
        except Exception:
            return False

    def save_csv_file(self, file_path: str, prompts: List[str]) -> bool:
        """Save prompts as CSV file."""
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write("index,prompt\n")
                for i, prompt in enumerate(prompts, 1):
                    # Escape quotes in CSV
                    escaped_prompt = prompt.replace('"', '""')
                    f.write(f'{i},"{escaped_prompt}"\n')
            return True
        except Exception:
            return False

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.

        Returns:
            List of supported format extensions
        """
        return ["py", "txt", "csv"]
