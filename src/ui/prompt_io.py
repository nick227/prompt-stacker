"""
Prompt I/O - Prompt Loading, Saving, and Path UI Management

Handles prompt list loading from files, saving to files, path validation,
and UI updates related to prompt management.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Import with fallback for standalone execution
try:
    from ..config import (
        COLOR_BORDER,
        COLOR_MODIFIED,
        COLOR_SUCCESS,
    )
    from ..file_service import PromptListService as FilePromptService
except ImportError:
    try:
        from config import (
            COLOR_BORDER,
            COLOR_MODIFIED,
            COLOR_SUCCESS,
        )
        from file_service import PromptListService as FilePromptService
    except ImportError:
        # Fallback if imports not available
        COLOR_BORDER = "#404040"
        COLOR_MODIFIED = "#0066cc"
        COLOR_SUCCESS = "#00cc00"
        FilePromptService = None


class PromptIO:
    """
    Handles prompt list I/O operations including loading, saving, and path management.
    """
    
    def __init__(self, ui):
        """
        Initialize the prompt I/O handler.
        
        Args:
            ui: Reference to the main UI session
        """
        self.ui = ui
        self._prompts_modified = False
        self._current_file_path = ""
        self._original_prompts_hash = None
        # Prefer using the UI's file_service so external patches affect this loader
        if hasattr(ui, "file_service") and ui.file_service is not None:
            self.file_service = ui.file_service
        else:
            self.file_service = FilePromptService() if FilePromptService else None
    
    def validate_prompt_list(self) -> None:
        """Validate and load the prompt list from one or more files."""
        path_input = self.ui.prompt_path_var.get().strip()
        
        # If path is empty, show no border and use default prompts
        if not path_input:
            self._current_file_path = ""
            self._prompts_modified = False
            self._update_path_entry_border()
            self._load_default_prompts()
            return
        
        # Split paths by semicolon and handle multiple files
        if self._load_prompts_from_multiple_files(path_input):
            # Successfully loaded - save path preference
            if hasattr(self.ui, "config_service"):
                self.ui.config_service.save_path_preference(path_input)
        else:
            # Failed to load - show error border
            self._current_file_path = ""
            self._prompts_modified = False
            self._update_path_entry_border()
            self._update_preview("")
    
    def browse_prompt_file(self) -> None:
        """Open file browser to select one or more prompt files."""
        from tkinter import filedialog
        
        # Get the initial directory
        initial_dir = self._get_initial_directory()
        
        # Open file dialog for multiple file selection
        file_paths = filedialog.askopenfilenames(
            title="Select Prompt List Files (use Ctrl+Click for multiple)",
            initialdir=initial_dir,
            filetypes=[
                ("All files", "*.*"),
                ("Python files", "*.py"),
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
            ],
        )
        
        if file_paths:
            # Join multiple paths with semicolons
            combined_paths = ";".join(file_paths)
            
            # Update the path input
            self.ui.prompt_path_var.set(combined_paths)
            
            # Save preferences
            self._save_file_preferences(file_paths)
            
            # Validate and load the prompt list
            self.validate_prompt_list()
    
    def load_last_prompt_file(self) -> None:
        """Load the last used prompt file."""
        if hasattr(self.ui, "config_service"):
            last_file = self.ui.config_service.load_path_preference("")
            if last_file and Path(last_file).exists():
                self.ui.prompt_path_var.set(last_file)
                if self._load_prompts_from_file(last_file):
                    return
        
        # Try to load default prompts directly
        self._load_default_prompts()
    
    def save_prompts_manually(self, file_path: Optional[str] = None) -> bool:
        """
        Manually save prompts to a file.
        
        Args:
            file_path: Optional file path to save to. If None, uses current file path.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        if not self.ui.prompts:
            print("No prompts to save")
            return False
        
        target_path = file_path or self._current_file_path
        if not target_path:
            print("No file path specified for saving")
            return False
        
        try:
            success = self.file_service.save_prompts(target_path, self.ui.prompts)
            if success:
                # Update persistence tracking
                self._current_file_path = target_path
                self._original_prompts_hash = hash(tuple(self.ui.prompts))
                self._prompts_modified = False
                self._update_path_entry_border()
                print(f"Manually saved prompts to: {target_path}")
                return True
            print(f"Failed to save prompts to: {target_path}")
            return False
        except Exception as e:
            print(f"Error saving prompts: {e}")
            return False
    
    def auto_save_prompts(self) -> None:
        """Auto-save prompts to the current file path."""
        if not self._current_file_path or not self._prompts_modified:
            return
        
        try:
            success = self.file_service.save_prompts(
                self._current_file_path,
                self.ui.prompts,
            )
            if success:
                # Update original hash after successful save
                self._original_prompts_hash = hash(tuple(self.ui.prompts))
                self._prompts_modified = False
                self._update_path_entry_border()
                print(f"Auto-saved prompts to: {self._current_file_path}")
            else:
                print(f"Failed to auto-save prompts to: {self._current_file_path}")
        except Exception as e:
            print(f"Error auto-saving prompts: {e}")
    
    def check_prompts_modified(self) -> None:
        """Check if prompts have been modified since last load/save."""
        # If no file path, no need to track modifications
        if not self._current_file_path:
            self._prompts_modified = False
            return
        
        if not self.ui.prompts:
            self._prompts_modified = False
            return
        
        # Create a simple hash of the prompts for comparison
        current_hash = hash(tuple(self.ui.prompts))
        
        if self._original_prompts_hash is None:
            # First time loading - set as original
            self._original_prompts_hash = current_hash
            self._prompts_modified = False
        else:
            # Check if hash has changed
            self._prompts_modified = current_hash != self._original_prompts_hash
        
        # Update border color based on modification state
        self._update_path_entry_border()
    
    def on_prompts_changed(self, prompts: List[str]) -> None:
        """Handle prompts changed event from inline editor."""
        self.ui.prompts = prompts
        self.ui.prompt_count = len(prompts)
        
        # Check if prompts have been modified
        self.check_prompts_modified()
        
        # Auto-save if we have a file path and prompts are modified
        if self._prompts_modified and self._current_file_path:
            self.auto_save_prompts()
    
    def is_prompts_modified(self) -> bool:
        """Check if prompts have been modified since last save."""
        return self._prompts_modified
    
    def get_current_file_path(self) -> str:
        """Get the current file path."""
        return self._current_file_path or ""
    
    def _get_initial_directory(self) -> str:
        """Get the initial directory for file browser."""
        # Try to load last used directory
        if hasattr(self.ui, "config_service"):
            initial_dir = self.ui.config_service.load_last_directory("")
            if initial_dir and Path(initial_dir).exists():
                return initial_dir
        
        # If no last directory or it doesn't exist, try current file directory
        if self.ui.prompt_path_var.get():
            initial_dir = str(Path(self.ui.prompt_path_var.get().split(";")[0].strip()).parent)
            if Path(initial_dir).exists():
                return initial_dir
        
        # Fallback to default prompt_list directory
        try:
            initial_dir = str(Path(__file__).parent.parent.parent / "prompt_lists")
            if Path(initial_dir).exists():
                return initial_dir
        except Exception:
            pass
        
        # Final fallback to user's home directory
        return str(Path.home())
    
    def _save_file_preferences(self, file_paths: List[str]) -> None:
        """Save file preferences including path and directory."""
        if not hasattr(self.ui, "config_service"):
            return
        
        # Save the combined paths
        combined_paths = ";".join(file_paths)
        self.ui.config_service.save_path_preference(combined_paths)
        
        # Save the directory of the first selected file as last used directory
        first_file_dir = str(Path(file_paths[0]).parent)
        self.ui.config_service.save_last_directory(first_file_dir)
    
    def _load_prompts_from_multiple_files(self, path_input: str) -> bool:
        """Load prompts from multiple files separated by semicolons."""
        try:
            # Split paths by semicolon and clean up whitespace
            file_paths = [
                path.strip() for path in path_input.split(";") if path.strip()
            ]
            
            if not file_paths:
                return False
            
            all_prompts = []
            loaded_files = []
            failed_files = []
            
            # Load prompts from each file
            for file_path in file_paths:
                success, result = self.file_service.parse_prompt_list(file_path)
                
                if success and isinstance(result, list):
                    all_prompts.extend(result)
                    loaded_files.append(file_path)
                    print(f"Successfully loaded {len(result)} prompts from: {file_path}")
                else:
                    failed_files.append(file_path)
                    print(f"Failed to load prompts from: {file_path}")
            
            if all_prompts:
                # Set combined prompts
                self.ui.prompts = all_prompts
                self.ui.prompt_count = len(all_prompts)
                self.ui.current_prompt_index = 0
                
                # Update inline prompt editor service
                if hasattr(self.ui, "prompt_list_service"):
                    self.ui.prompt_list_service.set_prompts(all_prompts)
                
                # Set up persistence tracking (use first file as primary)
                self._current_file_path = loaded_files[0] if loaded_files else ""
                self._original_prompts_hash = hash(tuple(all_prompts))
                self._prompts_modified = False
                
                # Update UI
                self._update_path_entry_border()
                self._update_preview(all_prompts[0] if all_prompts else "")
                
                print(f"Total prompts loaded: {len(all_prompts)} from {len(loaded_files)} files")
                if failed_files:
                    print(f"Failed to load {len(failed_files)} files: {', '.join(failed_files)}")
                return True
            
            # If no prompts were loaded from any file, return False
            if failed_files:
                print(f"Failed to load any prompts from {len(failed_files)} files")
            return False
            
        except Exception as e:
            print(f"Error loading prompts from multiple files: {e}")
            return False
    
    def _load_prompts_from_file(self, file_path: str) -> bool:
        """Load prompts from a single file and set up persistence tracking."""
        try:
            success, result = self.file_service.parse_prompt_list(file_path)
            
            if success and isinstance(result, list):
                self.ui.prompts = result
                self.ui.prompt_count = len(result)
                self.ui.current_prompt_index = 0
                
                # Update inline prompt editor service
                if hasattr(self.ui, "prompt_list_service"):
                    self.ui.prompt_list_service.set_prompts(result)
                
                # Set up persistence tracking
                self._current_file_path = file_path
                self._original_prompts_hash = hash(tuple(result))
                self._prompts_modified = False
                
                # Update UI
                self._update_path_entry_border()
                self._update_preview(result[0] if result else "")
                
                return True
            return False
            
        except Exception as e:
            print(f"Error loading prompts from file: {e}")
            return False
    
    def _load_default_prompts(self) -> None:
        """Load default prompts from the bundled prompt_list.py."""
        if not self.file_service:
            self._create_default_prompts()
            return
        
        default_path = self.file_service.get_default_prompt_list_path()
        
        if Path(default_path).exists():
            # Set the path and validate
            self.ui.prompt_path_var.set(default_path)
            self.validate_prompt_list()
        else:
            # If file doesn't exist, create a basic default
            self._create_default_prompts()
    
    def _create_default_prompts(self) -> None:
        """Create a basic default prompt list if none exists."""
        default_prompts = [
            "Hello, this is a sample prompt.",
            "This is another sample prompt.",
            "You can replace these with your own prompts.",
            "Use the Browse button to load your prompt file.",
        ]
        
        # Set the prompts directly
        self.ui.prompts = default_prompts
        self.ui.prompt_count = len(default_prompts)
        
        # Update the prompt list service
        if hasattr(self.ui, "prompt_list_service"):
            self.ui.prompt_list_service.set_prompts(default_prompts)
    
    def _update_preview(self, text: str) -> None:
        """Update preview text."""
        if hasattr(self.ui, "current_box") and self.ui.current_box:
            try:
                self.ui.current_box.configure(state="normal")
                self.ui.current_box.delete("1.0", "end")
                self.ui.current_box.insert("end", str(text))
                self.ui.current_box.configure(state="disabled")
            except Exception:
                pass
    
    def _update_path_entry_border(self, color: str = None) -> None:
        """Update path entry border color based on modification state or directly."""
        if not hasattr(self.ui, "path_entry"):
            return
        
        if color is not None:
            # Direct color update
            self.ui.path_entry.configure(border_color=color)
        elif not self._current_file_path:
            # No file loaded - use default border
            self.ui.path_entry.configure(border_color=COLOR_BORDER)
        elif self._prompts_modified:
            # File is modified - use blue border
            self.ui.path_entry.configure(border_color=COLOR_MODIFIED)
        else:
            # File is unmodified - use success border
            self.ui.path_entry.configure(border_color=COLOR_SUCCESS)
