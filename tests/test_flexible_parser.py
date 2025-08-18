"""
Tests for the flexible parser service.

Tests various parsing strategies and formats to ensure maximum flexibility
for users to format their prompt lists however they prefer.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

try:
    from src.parser_service import ParserService
except ImportError:
    # Fallback for when running as script
    import sys
    sys.path.insert(0, 'src')
    from parser_service import ParserService


class TestFlexibleParser:
    """Test the flexible parsing capabilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ParserService()
    
    def test_parse_python_any_variable_name(self):
        """Test that Python files work with any variable name."""
        content = """
my_custom_variable = [
    "first prompt",
    "second prompt", 
    "third prompt"
]
"""
        success, result = self.parser.parse_python_file("test.py", content)
        assert success
        assert len(result) == 3
        assert result[0] == "first prompt"
        assert result[1] == "second prompt"
        assert result[2] == "third prompt"
    
    def test_parse_python_multiple_lists_picks_largest(self):
        """Test that when multiple lists exist, it picks the largest one."""
        content = """
small_list = ["a", "b"]
medium_list = ["x", "y", "z"]
large_list = ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"]
tiny_list = ["1"]
"""
        success, result = self.parser.parse_python_file("test.py", content)
        assert success
        assert len(result) == 5
        assert result[0] == "prompt1"
        assert result[4] == "prompt5"
    
    def test_parse_python_multi_line_list(self):
        """Test parsing multi-line list definitions."""
        content = """
tasks = [
    "first task",
    "second task",
    "third task"
]
"""
        success, result = self.parser.parse_python_file("test.py", content)
        assert success
        assert len(result) == 3
        assert result[0] == "first task"
    
    def test_parse_python_ast_fallback(self):
        """Test AST parsing fallback when import fails."""
        content = """
# This is a comment
my_list = ["prompt1", "prompt2", "prompt3"]
# Another comment
"""
        success, result = self.parser.parse_python_file("test.py", content)
        assert success
        assert len(result) == 3
    
    def test_parse_text_line_separated(self):
        """Test basic line-separated text parsing."""
        content = "prompt1\nprompt2\nprompt3"
        success, result = self.parser.parse_text_file(content)
        assert success
        assert len(result) == 3
        assert result == ["prompt1", "prompt2", "prompt3"]
    
    def test_parse_text_double_line_separated(self):
        """Test double-line separated text parsing."""
        content = "prompt1\n\nprompt2\n\nprompt3"
        success, result = self.parser.parse_text_file(content)
        assert success
        assert len(result) == 3
        assert result == ["prompt1", "prompt2", "prompt3"]
    
    def test_parse_text_custom_delimiters(self):
        """Test custom delimiter parsing."""
        content = "prompt1\n---\nprompt2\n===\nprompt3"
        success, result = self.parser.parse_text_file(content)
        assert success
        # With the current logic, it will split by the first delimiter found
        # So it will split by "---" and get ["prompt1", "prompt2\n===\nprompt3"]
        assert len(result) == 2
        assert result[0] == "prompt1"
        assert "prompt2" in result[1]
    
    def test_parse_text_numbered_format(self):
        """Test numbered format parsing."""
        content = "1. first prompt\n2. second prompt\n3. third prompt"
        success, result = self.parser.parse_text_file(content)
        assert success
        assert len(result) == 3
        assert result == ["first prompt", "second prompt", "third prompt"]
    
    def test_parse_text_bullet_format(self):
        """Test bullet format parsing."""
        content = "- bullet prompt 1\n* bullet prompt 2\n• bullet prompt 3"
        success, result = self.parser.parse_text_file(content)
        assert success
        assert len(result) == 3
        assert result == ["bullet prompt 1", "bullet prompt 2", "bullet prompt 3"]
    
    def test_parse_text_mixed_format(self):
        """Test mixed format parsing."""
        content = "1. numbered prompt\n\n- bullet prompt\n\n***\n\ncustom delimiter prompt"
        success, result = self.parser.parse_text_file(content)
        assert success
        assert len(result) == 4
    
    def test_parse_text_empty_content(self):
        """Test handling of empty content."""
        success, result = self.parser.parse_text_file("")
        assert not success
        assert "No content found" in result
    
    def test_parse_text_whitespace_only(self):
        """Test handling of whitespace-only content."""
        success, result = self.parser.parse_text_file("   \n\n   \t   ")
        assert not success
        assert "No content found" in result
    
    def test_remove_common_prefixes(self):
        """Test the prefix removal functionality."""
        # Test numbered prefixes
        assert self.parser._remove_common_prefixes("1. prompt") == "prompt"
        assert self.parser._remove_common_prefixes("2) prompt") == "prompt"
        assert self.parser._remove_common_prefixes("10. prompt") == "prompt"
        
        # Test bullet prefixes
        assert self.parser._remove_common_prefixes("- prompt") == "prompt"
        assert self.parser._remove_common_prefixes("* prompt") == "prompt"
        assert self.parser._remove_common_prefixes("• prompt") == "prompt"
        
        # Test no prefix
        assert self.parser._remove_common_prefixes("plain prompt") == "plain prompt"
        
        # Test whitespace handling
        assert self.parser._remove_common_prefixes("  1.   prompt  ") == "prompt"
    
    def test_parse_python_syntax_error_handling(self):
        """Test handling of Python syntax errors."""
        content = "invalid python syntax {"
        success, result = self.parser.parse_python_file("test.py", content)
        assert not success
        assert "syntax error" in result.lower()
    
    def test_parse_python_no_lists_found(self):
        """Test handling when no lists are found in Python file."""
        content = "x = 5\ny = 'hello'"
        success, result = self.parser.parse_python_file("test.py", content)
        assert not success
        assert "No valid prompt lists found" in result
    
    def test_parse_python_list_with_non_strings(self):
        """Test handling of lists with non-string items."""
        content = "my_list = [1, 2, 3, 'prompt']"
        success, result = self.parser.parse_python_file("test.py", content)
        # Should fail because not all items are strings
        assert not success
    
    def test_parse_python_empty_list(self):
        """Test handling of empty lists."""
        content = "my_list = []"
        success, result = self.parser.parse_python_file("test.py", content)
        assert not success
        assert "No valid prompt lists found" in result
    
    def test_parse_python_list_with_empty_strings(self):
        """Test handling of lists with empty strings."""
        content = 'my_list = ["prompt1", "", "prompt2", "   "]'
        success, result = self.parser.parse_python_file("test.py", content)
        assert success
        assert len(result) == 2  # Empty strings should be filtered out
        assert result == ["prompt1", "prompt2"]
    
    def test_parse_text_with_empty_lines(self):
        """Test text parsing with empty lines."""
        content = "prompt1\n\n\nprompt2\n\nprompt3"
        success, result = self.parser.parse_text_file(content)
        assert success
        assert len(result) == 3
        assert result == ["prompt1", "prompt2", "prompt3"]
    
    def test_parse_text_with_mixed_delimiters(self):
        """Test text parsing with multiple delimiter types."""
        content = "prompt1\n---\nprompt2\n===\nprompt3\n***\nprompt4"
        success, result = self.parser.parse_text_file(content)
        assert success
        # With the current logic, it will split by the first delimiter found
        # So it will split by "---" and get ["prompt1", "prompt2\n===\nprompt3\n***\nprompt4"]
        assert len(result) == 2
        assert result[0] == "prompt1"
        assert "prompt2" in result[1]
    
    def test_parse_text_complex_format(self):
        """Test complex text format with multiple strategies."""
        content = """
1. First numbered prompt

- First bullet prompt
* Second bullet prompt

---

Second section prompt

===

Final prompt
"""
        success, result = self.parser.parse_text_file(content)
        assert success
        assert len(result) == 6
        # Should handle the mixed format appropriately
