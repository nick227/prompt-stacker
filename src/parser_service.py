"""
Parser Service for File Format Parsing

This module handles parsing of different file formats including:
- Python files with variable arrays
- Text files with line-separated prompts
- CSV files with comma-separated prompts

Author: Automation System
Version: 1.0
"""

import ast
import sys
from typing import List, Optional, Tuple, Union


class ParserService:
    """Service for parsing different file formats into prompt lists."""

    def parse_python_file(
        self,
        file_path: str,
        content: str,
    ) -> Tuple[bool, Union[List[str], str]]:
        """
        Parse a Python file using multiple flexible strategies.

        Supports multiple formats:
        1. Direct list assignment: prompts = ["prompt1", "prompt2"]
        2. Multi-line list: prompts = ["prompt1", "prompt2"]
        3. List comprehension: prompts = [f"prompt{i}" for i in range(10)]
        4. Any variable name that contains a list of strings
        5. Multiple lists in the same file (uses the largest one)
        """
        try:
            # Strategy 1: Try to import and find any list variable
            # Skip dynamic imports in PyInstaller environment
            if getattr(sys, "frozen", False):
                # Running as executable - skip dynamic imports
                return self._parse_python_content_ast(content)

            import importlib.util

            spec = importlib.util.spec_from_file_location("prompt_module", file_path)
            if spec is None or spec.loader is None:
                return False, "Could not load Python module"

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all list variables (any variable name that contains a list)
            list_variables = []
            all_vars = [var for var in dir(module) if not var.startswith("_")]

            for var_name in all_vars:
                try:
                    value = getattr(module, var_name)
                    if isinstance(value, list) and len(value) > 0:
                        # Check if it's a list of strings or can be converted to strings
                        if all(
                            isinstance(item, str) or hasattr(item, "__str__")
                            for item in value
                        ):
                            list_variables.append((var_name, value))
                except Exception:
                    continue

            # Sort by list length (prefer larger lists)
            list_variables.sort(key=lambda x: len(x[1]), reverse=True)

            if list_variables:
                var_name, prompts = list_variables[0]
                # Convert all items to strings and filter out empty ones
                result = [str(item).strip() for item in prompts if str(item).strip()]
                if result:
                    print(
                        f"Found prompts in variable: {var_name} ({len(result)} items)",
                    )
                    return True, result

            # Strategy 2: Parse the content directly using AST
            return self._parse_python_content_ast(content)

        except ImportError as e:
            return False, f"Error importing Python file: {str(e)}"
        except Exception:
            # If import fails, try AST parsing as fallback
            return self._parse_python_content_ast(content)

    def _parse_python_content_ast(
        self,
        content: str,
    ) -> Tuple[bool, Union[List[str], str]]:
        """
        Parse Python content using AST to find list literals.
        This is a fallback when import fails or no suitable variables found.
        """
        try:
            import ast

            # Parse the Python code
            tree = ast.parse(content)

            # Find all list literals in the code
            list_literals = []

            for node in ast.walk(tree):
                if isinstance(node, ast.List):
                    # Check if this list contains string literals
                    string_items = []
                    for item in node.elts:
                        if isinstance(item, ast.Constant) and isinstance(
                            item.value,
                            str,
                        ):
                            string_items.append(item.value)
                        elif hasattr(
                            item,
                            "s",
                        ):  # Handle ast.Str for older Python versions
                            string_items.append(item.s)
                        else:
                            # Skip non-string items
                            break
                    else:
                        # All items were strings
                        if string_items:
                            list_literals.append(string_items)

            # Sort by length and return the largest list
            if list_literals:
                list_literals.sort(key=len, reverse=True)
                largest_list = list_literals[0]
                # Filter out empty strings
                result = [item.strip() for item in largest_list if item.strip()]
                if result:
                    print(f"Found prompts using AST parsing ({len(result)} items)")
                    return True, result

            return False, "No valid prompt lists found in Python file"

        except SyntaxError as e:
            return False, f"Python syntax error: {str(e)}"
        except Exception as e:
            return False, f"Error parsing Python content: {str(e)}"

    def parse_text_file(self, content: str) -> Tuple[bool, Union[List[str], str]]:
        """
        Parse a text file using multiple flexible strategies.

        Supports multiple formats:
        1. Line-separated: Each line is a prompt
        2. Double-line separated: Prompts separated by blank lines
        3. Custom delimiter: Prompts separated by "---" or "==="
        4. Numbered format: "1. prompt", "2. prompt"
        5. Bullet format: "- prompt", "* prompt"
        """
        try:
            if not content.strip():
                return False, "No content found in text file"

            # Strategy 1: Try double-line separation first (for multi-line prompts)
            if "\n\n" in content:
                sections = content.split("\n\n")
                prompts = []
                for section in sections:
                    cleaned_section = section.strip()
                    if cleaned_section:
                        # Remove common prefixes
                        cleaned_section = self._remove_common_prefixes(cleaned_section)
                        if cleaned_section:
                            prompts.append(cleaned_section)
                if prompts:
                    return True, prompts

            # Strategy 2: Try custom delimiters (only if double-line separation didn't work)
            if "\n\n" not in content:
                delimiters = ["---", "===", "***", "###"]
                for delimiter in delimiters:
                    if delimiter in content:
                        sections = content.split(delimiter)
                        prompts = []
                        for section in sections:
                            cleaned_section = section.strip()
                            if cleaned_section:
                                cleaned_section = self._remove_common_prefixes(
                                    cleaned_section
                                )
                                if cleaned_section:
                                    prompts.append(cleaned_section)
                        if prompts:
                            return True, prompts

            # Strategy 3: Line-separated (default)
            lines = []
            for line in content.split("\n"):
                cleaned_line = line.strip()
                if cleaned_line:
                    cleaned_line = self._remove_common_prefixes(cleaned_line)
                    if cleaned_line:
                        lines.append(cleaned_line)

            if lines:
                return True, lines

            return False, "No valid prompts found in text file"

        except Exception as e:
            return False, f"Error parsing text file: {str(e)}"

    def _remove_common_prefixes(self, text: str) -> str:
        """Remove common numbering and bullet prefixes from text."""
        text = text.strip()

        # Remove numbered prefixes: "1.", "2.", "1)", "2)", etc.
        import re

        text = re.sub(r"^\d+[\.\)]\s*", "", text)

        # Remove bullet prefixes: "- ", "* ", "• ", etc.
        text = re.sub(r"^[\-\*•]\s*", "", text)

        return text.strip()

    def parse_csv_file(self, content: str) -> Tuple[bool, Union[List[str], str]]:
        """Parse a CSV file as comma-separated prompts."""
        try:
            lines = content.strip().split("\n")
            if not lines:
                return False, "No valid prompts found in CSV file"

            # Check if first line is header
            if lines[0].strip().lower() in ["index,prompt", "prompt", "prompts"]:
                lines = lines[1:]  # Skip header
            elif "," in lines[0] and not lines[0].strip().startswith('"'):
                # If first line contains comma but doesn't start with quote, it might be a header
                # Check if second line also contains comma (indicating data)
                if len(lines) > 1 and "," in lines[1]:
                    lines = lines[1:]  # Skip header

            prompts = []
            for line in lines:
                cleaned_line = line.strip()
                if not cleaned_line:
                    continue

                # Handle CSV with index and prompt columns
                if "," in line:
                    # Split by comma
                    parts = line.split(",", 1)  # Split only on first comma
                    if len(parts) >= 2:
                        # Has index and prompt columns
                        prompt_part = parts[1].strip()

                        # Handle quoted prompt
                        if prompt_part.startswith('"'):
                            # Find the closing quote, handling escaped quotes
                            i = 1
                            while i < len(prompt_part):
                                if prompt_part[i] == '"':
                                    if (
                                        i + 1 < len(prompt_part)
                                        and prompt_part[i + 1] == '"'
                                    ):
                                        # Escaped quote, skip next character
                                        i += 2
                                    else:
                                        # End quote found
                                        prompt = prompt_part[1:i]
                                        # Handle escaped quotes
                                        prompt = prompt.replace('""', '"')
                                        break
                                else:
                                    i += 1
                            else:
                                # No closing quote found
                                continue
                        else:
                            # Unquoted prompt
                            prompt = prompt_part
                    else:
                        # Single column
                        prompt = parts[0].strip()
                else:
                    # Single column without comma
                    prompt = line.strip()

                if prompt:
                    prompts.append(prompt)

            if prompts:
                return True, prompts
            return False, "No valid prompts found in CSV file"
        except Exception as e:
            return False, f"Error parsing CSV file: {str(e)}"

    def parse_unknown_file(self, content: str) -> Tuple[bool, Union[List[str], str]]:
        """Parse unknown file type by trying all methods in order."""
        # Try Python array first (most common for automation)
        prompts = self._try_parse_python_array(content)
        if prompts:
            return True, prompts

        # Try line-separated
        prompts = self._try_parse_line_separated(content)
        if prompts:
            return True, prompts

        # Try comma-separated
        prompts = self._try_parse_comma_separated(content)
        if prompts:
            return True, prompts

        return (
            False,
            "Unable to parse file. Expected Python array, line-separated, or comma-separated format.",
        )

    def _try_parse_python_array(self, content: str) -> Optional[List[str]]:
        """Try to parse content as a Python array."""
        try:
            # Try to evaluate as Python literal
            parsed = ast.literal_eval(content)

            if isinstance(parsed, list):
                # Convert all items to strings and filter out empty ones
                prompts = [str(item).strip() for item in parsed if str(item).strip()]
                return prompts if prompts else None

            return None
        except (ValueError, SyntaxError):
            return None

    def _try_parse_line_separated(self, content: str) -> Optional[List[str]]:
        """Try to parse content as line-separated prompts."""
        try:
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            return lines if lines else None
        except (AttributeError, TypeError):
            return None

    def _try_parse_comma_separated(self, content: str) -> Optional[List[str]]:
        """Try to parse content as comma-separated prompts."""
        try:
            # Split by commas and clean up
            items = [item.strip() for item in content.split(",") if item.strip()]
            return items if items else None
        except (AttributeError, TypeError):
            return None
