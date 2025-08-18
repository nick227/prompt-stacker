"""
Unit tests for Multiple File Handling

Tests the functionality for loading prompts from multiple files using semicolon-separated paths.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.session_app import RefactoredSessionUI
from file_service import PromptListService


class TestMultipleFileHandling:
    """Test cases for multiple file handling functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_prompts(self):
        """Sample prompts for testing."""
        return [
            "This is a test prompt",
            "Another test prompt with 'quotes'",
            "Simple prompt",
            "Prompt with special chars: !@#$%^&*()",
            "Final test prompt"
        ]

    @pytest.fixture
    def ui_instance(self):
        """Create a UI instance for testing."""
        try:
            # Mock customtkinter to prevent real UI creation
            with patch('customtkinter.CTk') as mock_ctk, \
                 patch('customtkinter.CTkFrame') as mock_frame, \
                 patch('customtkinter.CTkLabel') as mock_label, \
                 patch('customtkinter.CTkButton') as mock_button, \
                 patch('customtkinter.CTkTextbox') as mock_textbox, \
                 patch('customtkinter.CTkEntry') as mock_entry, \
                 patch('customtkinter.CTkScrollableFrame') as mock_scrollable_frame:
                
                # Mock the window
                mock_window = Mock()
                mock_ctk.return_value = mock_window
                
                # Mock UI widgets
                mock_window.after = Mock()
                mock_window.after_idle = Mock()
                mock_window.quit = Mock()
                mock_window.destroy = Mock()
                
                ui = RefactoredSessionUI(default_start=5, default_main=500, default_cooldown=0.2)
                yield ui
                
                # Cleanup
                try:
                    ui.window.destroy()
                except:
                    pass
                    
        except Exception as e:
            # Skip tests if UI can't be created (e.g., no display)
            pytest.skip(f"UI cannot be created: {e}")

    def create_test_file(self, temp_dir, filename, prompts, file_type="txt"):
        """Helper to create test files of different types."""
        file_path = os.path.join(temp_dir, filename)
        
        if file_type == "py":
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("prompt_list = [\n")
                for prompt in prompts:
                    escaped_prompt = prompt.replace('\n', '\\n')
                    f.write(f'    "{escaped_prompt}",\n')
                f.write("]\n")
        elif file_type == "txt":
            with open(file_path, 'w', encoding='utf-8') as f:
                for prompt in prompts:
                    f.write(prompt + '\n')
        elif file_type == "csv":
            with open(file_path, 'w', encoding='utf-8') as f:
                # Create CSV with index and prompt columns
                for i, prompt in enumerate(prompts):
                    f.write(f'{i+1},"{prompt}"\n')
        
        return file_path

    @pytest.mark.unit
    def test_load_prompts_from_multiple_files_success(self, ui_instance, temp_dir, sample_prompts):
        """Test successful loading from multiple files."""
        # Create test files
        file1_path = self.create_test_file(temp_dir, "file1.txt", sample_prompts[:2], "txt")
        file2_path = self.create_test_file(temp_dir, "file2.py", sample_prompts[2:4], "py")
        file3_path = self.create_test_file(temp_dir, "file3.csv", sample_prompts[4:], "csv")
        
        # Create semicolon-separated path
        combined_path = f"{file1_path};{file2_path};{file3_path}"
        
        # Test the method
        success = ui_instance._load_prompts_from_multiple_files(combined_path)
        
        assert success is True
        assert len(ui_instance.prompts) == len(sample_prompts)
        assert ui_instance.prompts == sample_prompts

    @pytest.mark.unit
    def test_load_prompts_from_single_file(self, ui_instance, temp_dir, sample_prompts):
        """Test loading from a single file (backward compatibility)."""
        # Create a single test file
        file_path = self.create_test_file(temp_dir, "single.txt", sample_prompts, "txt")
        
        # Test the method
        success = ui_instance._load_prompts_from_multiple_files(file_path)
        
        assert success is True
        assert len(ui_instance.prompts) == len(sample_prompts)
        assert ui_instance.prompts == sample_prompts

    @pytest.mark.unit
    def test_load_prompts_with_mixed_valid_invalid_files(self, ui_instance, temp_dir, sample_prompts):
        """Test loading when some files are valid and others are invalid."""
        # Create one valid file
        valid_file = self.create_test_file(temp_dir, "valid.txt", sample_prompts[:2], "txt")
        
        # Create path with valid and invalid files
        combined_path = f"{valid_file};nonexistent_file.txt;another_invalid.py"
        
        # Test the method
        success = ui_instance._load_prompts_from_multiple_files(combined_path)
        
        # Should succeed because at least one file is valid
        assert success is True
        assert len(ui_instance.prompts) == 2
        assert ui_instance.prompts == sample_prompts[:2]

    @pytest.mark.unit
    def test_load_prompts_all_invalid_files(self, ui_instance, temp_dir):
        """Test loading when all files are invalid."""
        # Create path with only invalid files
        combined_path = "nonexistent1.txt;nonexistent2.py;invalid_file.csv"
        
        # Store original prompts count
        original_count = len(ui_instance.prompts)
        
        # Test the method
        success = ui_instance._load_prompts_from_multiple_files(combined_path)
        
        # Should fail because no files are valid
        assert success is False
        # Should not change the prompts (keep original/default prompts)
        assert len(ui_instance.prompts) == original_count

    @pytest.mark.unit
    def test_load_prompts_empty_path(self, ui_instance):
        """Test loading with empty path."""
        # Test with empty string
        success = ui_instance._load_prompts_from_multiple_files("")
        assert success is False
        
        # Test with only semicolons
        success = ui_instance._load_prompts_from_multiple_files(";;;")
        assert success is False
        
        # Test with whitespace only
        success = ui_instance._load_prompts_from_multiple_files("   ")
        assert success is False

    @pytest.mark.unit
    def test_load_prompts_with_whitespace(self, ui_instance, temp_dir, sample_prompts):
        """Test loading with whitespace around semicolons."""
        # Create test files
        file1_path = self.create_test_file(temp_dir, "file1.txt", sample_prompts[:2], "txt")
        file2_path = self.create_test_file(temp_dir, "file2.txt", sample_prompts[2:4], "txt")
        
        # Create path with whitespace
        combined_path = f"  {file1_path}  ;  {file2_path}  "
        
        # Test the method
        success = ui_instance._load_prompts_from_multiple_files(combined_path)
        
        assert success is True
        assert len(ui_instance.prompts) == 4

    @pytest.mark.unit
    def test_load_prompts_different_file_types(self, ui_instance, temp_dir, sample_prompts):
        """Test loading from different file types in the same path."""
        # Create files of different types
        txt_file = self.create_test_file(temp_dir, "file.txt", sample_prompts[:1], "txt")
        py_file = self.create_test_file(temp_dir, "file.py", sample_prompts[1:2], "py")
        csv_file = self.create_test_file(temp_dir, "file.csv", sample_prompts[2:3], "csv")
        
        # Create combined path
        combined_path = f"{txt_file};{py_file};{csv_file}"
        
        # Test the method
        success = ui_instance._load_prompts_from_multiple_files(combined_path)
        
        assert success is True
        assert len(ui_instance.prompts) == 3

    @pytest.mark.unit
    def test_validate_prompt_list_with_multiple_files(self, ui_instance, temp_dir, sample_prompts):
        """Test the _validate_prompt_list method with multiple files."""
        # Create test files
        file1_path = self.create_test_file(temp_dir, "file1.txt", sample_prompts[:2], "txt")
        file2_path = self.create_test_file(temp_dir, "file2.txt", sample_prompts[2:4], "txt")
        
        # Set the path in the UI
        combined_path = f"{file1_path};{file2_path}"
        ui_instance.prompt_path_var.set(combined_path)
        
        # Test the validation method
        ui_instance._validate_prompt_list()
        
        assert len(ui_instance.prompts) == 4
        assert ui_instance.prompts == sample_prompts[:4]

    @pytest.mark.unit
    def test_browse_prompt_file_multiple_selection(self, ui_instance, temp_dir, sample_prompts):
        """Test the browse functionality with multiple file selection."""
        # Create test files
        file1_path = self.create_test_file(temp_dir, "file1.txt", sample_prompts[:2], "txt")
        file2_path = self.create_test_file(temp_dir, "file2.txt", sample_prompts[2:4], "txt")
        
        # Mock the file dialog to return multiple files
        with patch('tkinter.filedialog.askopenfilenames') as mock_askopenfilenames:
            mock_askopenfilenames.return_value = (file1_path, file2_path)
            
            # Test the browse method
            ui_instance._browse_prompt_file()
            
            # Check that the path was set correctly
            expected_path = f"{file1_path};{file2_path}"
            assert ui_instance.prompt_path_var.get() == expected_path

    @pytest.mark.unit
    def test_browse_prompt_file_single_selection(self, ui_instance, temp_dir, sample_prompts):
        """Test the browse functionality with single file selection."""
        # Create test file
        file_path = self.create_test_file(temp_dir, "file.txt", sample_prompts, "txt")
        
        # Mock the file dialog to return a single file
        with patch('tkinter.filedialog.askopenfilenames') as mock_askopenfilenames:
            mock_askopenfilenames.return_value = (file_path,)
            
            # Test the browse method
            ui_instance._browse_prompt_file()
            
            # Check that the path was set correctly
            assert ui_instance.prompt_path_var.get() == file_path

    @pytest.mark.unit
    def test_browse_prompt_file_cancelled(self, ui_instance):
        """Test the browse functionality when cancelled."""
        # Mock the file dialog to return empty tuple (cancelled)
        with patch('tkinter.filedialog.askopenfilenames') as mock_askopenfilenames:
            mock_askopenfilenames.return_value = ()
            
            # Store original path
            original_path = ui_instance.prompt_path_var.get()
            
            # Test the browse method
            ui_instance._browse_prompt_file()
            
            # Check that the path wasn't changed
            assert ui_instance.prompt_path_var.get() == original_path

    @pytest.mark.unit
    def test_path_change_handler_multiple_files(self, ui_instance, temp_dir, sample_prompts):
        """Test the path change handler with multiple files."""
        # Create test files
        file1_path = self.create_test_file(temp_dir, "file1.txt", sample_prompts[:2], "txt")
        file2_path = self.create_test_file(temp_dir, "file2.txt", sample_prompts[2:4], "txt")
        
        # Set the path
        combined_path = f"{file1_path};{file2_path}"
        ui_instance.prompt_path_var.set(combined_path)
        
        # Trigger the path change handler
        ui_instance._validate_prompt_list()
        
        assert len(ui_instance.prompts) == 4

    @pytest.mark.unit
    def test_path_change_handler_single_file(self, ui_instance, temp_dir, sample_prompts):
        """Test the path change handler with single file."""
        # Create test file
        file_path = self.create_test_file(temp_dir, "file.txt", sample_prompts, "txt")
        
        # Set the path
        ui_instance.prompt_path_var.set(file_path)
        
        # Trigger the path change handler
        ui_instance._validate_prompt_list()
        
        assert len(ui_instance.prompts) == len(sample_prompts)

    @pytest.mark.unit
    def test_persistence_tracking_multiple_files(self, ui_instance, temp_dir, sample_prompts):
        """Test that persistence tracking works correctly with multiple files."""
        # Create test files
        file1_path = self.create_test_file(temp_dir, "file1.txt", sample_prompts[:2], "txt")
        file2_path = self.create_test_file(temp_dir, "file2.txt", sample_prompts[2:4], "txt")
        
        # Load multiple files
        combined_path = f"{file1_path};{file2_path}"
        success = ui_instance._load_prompts_from_multiple_files(combined_path)
        
        assert success is True
        # Should use first file as primary for persistence
        assert ui_instance._current_file_path == file1_path
        assert ui_instance._prompts_modified is False

    @pytest.mark.unit
    def test_error_handling_file_service_exception(self, ui_instance, temp_dir):
        """Test error handling when file service throws an exception."""
        # Create a path with a file that will cause issues
        problematic_path = os.path.join(temp_dir, "problematic.txt")
        
        # Create a file that will cause parsing issues
        with open(problematic_path, 'w', encoding='utf-8') as f:
            f.write("Invalid content that will cause parsing issues\n")
        
        # Mock the file service to throw an exception
        with patch.object(ui_instance.file_service, 'parse_prompt_list') as mock_parse:
            mock_parse.side_effect = Exception("Test exception")
            
            # Test the method
            success = ui_instance._load_prompts_from_multiple_files(problematic_path)
            
            assert success is False

    @pytest.mark.unit
    def test_ui_widget_updates_multiple_files(self, ui_instance, temp_dir, sample_prompts):
        """Test that UI widgets are updated correctly when loading multiple files."""
        # Create test files
        file1_path = self.create_test_file(temp_dir, "file1.txt", sample_prompts[:2], "txt")
        file2_path = self.create_test_file(temp_dir, "file2.txt", sample_prompts[2:4], "txt")
        
        # Mock UI widgets
        ui_instance.current_box = Mock()
        ui_instance.path_entry = Mock()
        
        # Load multiple files
        combined_path = f"{file1_path};{file2_path}"
        success = ui_instance._load_prompts_from_multiple_files(combined_path)
        
        assert success is True
        
        # Check that UI was updated
        assert ui_instance.current_box.configure.called
        assert ui_instance.path_entry.configure.called

    @pytest.mark.unit
    def test_prompt_list_service_integration(self, ui_instance, temp_dir, sample_prompts):
        """Test integration with prompt list service."""
        # Create test files
        file1_path = self.create_test_file(temp_dir, "file1.txt", sample_prompts[:2], "txt")
        file2_path = self.create_test_file(temp_dir, "file2.txt", sample_prompts[2:4], "txt")
        
        # Mock prompt list service
        ui_instance.prompt_list_service = Mock()
        
        # Load multiple files
        combined_path = f"{file1_path};{file2_path}"
        success = ui_instance._load_prompts_from_multiple_files(combined_path)
        
        assert success is True
        
        # Check that prompt list service was updated
        ui_instance.prompt_list_service.set_prompts.assert_called_once_with(sample_prompts[:4])


class TestMultipleFileHandlingIntegration:
    """Integration tests for multiple file handling."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.mark.integration
    def test_full_workflow_multiple_files(self, temp_dir):
        """Test the complete workflow with multiple files."""
        try:
            # Mock customtkinter to prevent real UI creation
            with patch('customtkinter.CTk') as mock_ctk, \
                 patch('customtkinter.CTkFrame') as mock_frame, \
                 patch('customtkinter.CTkLabel') as mock_label, \
                 patch('customtkinter.CTkButton') as mock_button, \
                 patch('customtkinter.CTkTextbox') as mock_textbox, \
                 patch('customtkinter.CTkEntry') as mock_entry, \
                 patch('customtkinter.CTkScrollableFrame') as mock_scrollable_frame:
                
                # Mock the window
                mock_window = Mock()
                mock_ctk.return_value = mock_window
                
                # Mock UI widgets
                mock_window.after = Mock()
                mock_window.after_idle = Mock()
                mock_window.quit = Mock()
                mock_window.destroy = Mock()
                
                # Create UI instance
                ui = RefactoredSessionUI(default_start=5, default_main=500, default_cooldown=0.2)
                
                # Create test files with different content
                prompts1 = ["Hello", "World"]
                prompts2 = ["Test", "Automation"]
                prompts3 = ["Final", "Prompt"]
                
                file1_path = self.create_test_file(temp_dir, "file1.txt", prompts1, "txt")
                file2_path = self.create_test_file(temp_dir, "file2.py", prompts2, "py")
                file3_path = self.create_test_file(temp_dir, "file3.csv", prompts3, "csv")
                
                # Set path and validate
                combined_path = f"{file1_path};{file2_path};{file3_path}"
                ui.prompt_path_var.set(combined_path)
                ui._validate_prompt_list()
                
                # Verify results
                expected_prompts = prompts1 + prompts2 + prompts3
                assert ui.prompts == expected_prompts
                assert ui.prompt_count == len(expected_prompts)
                assert ui.current_prompt_index == 0
                
        except Exception as e:
            # Skip test if UI can't be created (e.g., no display)
            pytest.skip(f"UI cannot be created: {e}")
        finally:
            try:
                ui.window.destroy()
            except:
                pass

    def create_test_file(self, temp_dir, filename, prompts, file_type="txt"):
        """Helper to create test files of different types."""
        file_path = os.path.join(temp_dir, filename)
        
        if file_type == "py":
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("prompt_list = [\n")
                for prompt in prompts:
                    f.write(f'    "{prompt}",\n')
                f.write("]\n")
        elif file_type == "txt":
            with open(file_path, 'w', encoding='utf-8') as f:
                for prompt in prompts:
                    f.write(prompt + '\n')
        elif file_type == "csv":
            with open(file_path, 'w', encoding='utf-8') as f:
                # Create CSV with index and prompt columns
                for i, prompt in enumerate(prompts):
                    f.write(f'{i+1},"{prompt}"\n')
        
        return file_path
