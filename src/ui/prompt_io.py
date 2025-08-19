"""
Prompt I/O - Prompt Loading, Saving, and Path UI Management

Handles prompt list loading from files, saving to files, path validation,
and UI updates related to prompt management.
"""

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Import with fallback for standalone execution
try:
    from ..config import (
        COLOR_BORDER,
        COLOR_ERROR,
        COLOR_MODIFIED,
        COLOR_SUCCESS,
    )
    from ..file_service import PromptListService as FilePromptService
except ImportError:
    try:
        from config import (
            COLOR_BORDER,
            COLOR_ERROR,
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
        """Validate and load the prompt list from one or more files with enhanced error handling."""
        try:
            path_input = self.ui.prompt_path_var.get().strip()

            # Basic path validation
            if not path_input:
                self._current_file_path = ""
                self._prompts_modified = False
                self._update_path_entry_border()
                self._load_default_prompts()
                return
            # Allow legitimate Windows paths but block dangerous patterns
            dangerous_patterns = ["..", "*", "?", '"', "<", ">", "|"]
            if any(pattern in path_input for pattern in dangerous_patterns):
                logger.warning(f"Potentially unsafe path detected: {path_input}")
                self._show_error_border("Invalid path characters detected")
                return

            # Split paths by semicolon and handle multiple files
            if self._load_prompts_from_multiple_files(path_input):
                # Successfully loaded - save path preference
                if hasattr(self.ui, "config_service"):
                    try:
                        self.ui.config_service.save_path_preference(path_input)
                    except Exception as e:
                        logger.warning(f"Failed to save path preference: {e}")
            else:
                # Failed to load - show error border
                self._current_file_path = ""
                self._prompts_modified = False
                self._update_path_entry_border()
                self._update_preview("")
        except Exception as e:
            logger.error(f"Error in validate_prompt_list: {e}")
            self._show_error_border(f"Error: {str(e)}")

    def browse_prompt_file(self) -> None:
        """Open file browser to select one or more prompt files with enhanced error handling."""
        try:
            from tkinter import filedialog

            # Get initial directory
            initial_dir = self._get_initial_directory()
            if not initial_dir or not Path(initial_dir).exists():
                initial_dir = str(Path.cwd())
                logger.warning(f"Initial directory not found, using current directory: {initial_dir}")

            # Validate initial directory
            if not Path(initial_dir).is_dir():
                logger.warning(f"Initial directory is not a valid directory: {initial_dir}")
                initial_dir = str(Path.cwd())

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
                # BULLETPROOF IMPROVEMENT: Validate selected files
                valid_paths = []
                for file_path in file_paths:
                    try:
                        if Path(file_path).exists() and Path(file_path).is_file():
                            valid_paths.append(file_path)
                        else:
                            logger.warning(f"Selected file does not exist or is not a file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Error validating file path {file_path}: {e}")

                if not valid_paths:
                    logger.error("No valid files selected")
                    return

                # Join multiple paths with semicolons
                combined_paths = ";".join(valid_paths)

                # Update the path input
                self.ui.prompt_path_var.set(combined_paths)

                # Save preferences with error handling
                try:
                    self._save_file_preferences(valid_paths)
                except Exception as e:
                    logger.warning(f"Failed to save file preferences: {e}")

                # Validate and load the prompt list
                self.validate_prompt_list()
        except Exception as e:
            logger.error(f"Error in browse_prompt_file: {e}")
            self._show_error_border(f"Error browsing files: {str(e)}")

    def load_last_prompt_file(self) -> None:
        """Load the last used prompt file with enhanced error handling."""
        try:
            if hasattr(self.ui, "config_service"):
                try:
                    last_file = self.ui.config_service.load_path_preference("")
                    if last_file and Path(last_file).exists():
                        # BULLETPROOF IMPROVEMENT: Validate file before loading
                        if Path(last_file).is_file():
                            self.ui.prompt_path_var.set(last_file)
                            if self._load_prompts_from_file(last_file):
                                logger.info(f"Successfully loaded last prompt file: {last_file}")
                                return
                            logger.warning(f"Failed to load last prompt file: {last_file}")
                        else:
                            logger.warning(f"Last prompt file is not a valid file: {last_file}")
                    else:
                        logger.info("No last prompt file found or file does not exist")
                except Exception as e:
                    logger.warning(f"Error loading last prompt file: {e}")

            # Try to load default prompts directly
            self._load_default_prompts()
        except Exception as e:
            logger.error(f"Error in load_last_prompt_file: {e}")
            self._load_default_prompts()

    def save_prompts_manually(self, file_path: Optional[str] = None) -> bool:
        """
        Manually save prompts to a file with enhanced error handling.
        
        Args:
            file_path: Optional file path to save to. If None, uses current file path.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            # BULLETPROOF IMPROVEMENT: Validate prompts
            if not self.ui.prompts:
                logger.warning("No prompts to save")
                return False

            # BULLETPROOF IMPROVEMENT: Validate prompt content
            valid_prompts = []
            for i, prompt in enumerate(self.ui.prompts):
                if prompt and isinstance(prompt, str) and prompt.strip():
                    valid_prompts.append(prompt.strip())
                else:
                    logger.warning(f"Invalid prompt at index {i}: {prompt}")

            if not valid_prompts:
                logger.warning("No valid prompts to save")
                return False

            target_path = file_path or self._current_file_path
            if not target_path:
                logger.warning("No file path specified for saving")
                return False

            # BULLETPROOF IMPROVEMENT: Validate target path
            try:
                target_path_obj = Path(target_path)
                if target_path_obj.exists() and not target_path_obj.is_file():
                    logger.error(f"Target path exists but is not a file: {target_path}")
                    return False

                # Ensure parent directory exists
                target_path_obj.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Error validating target path {target_path}: {e}")
                return False

            # BULLETPROOF IMPROVEMENT: Save with backup
            try:
                # Create backup if file exists
                if Path(target_path).exists():
                    backup_path = f"{target_path}.backup"
                    import shutil
                    shutil.copy2(target_path, backup_path)
                    logger.info(f"Created backup: {backup_path}")

                success = self.file_service.save_prompts(target_path, valid_prompts)
                if success:
                    logger.info(f"Successfully saved {len(valid_prompts)} prompts to {target_path}")
                    self._current_file_path = target_path
                    self._prompts_modified = False
                    self._update_path_entry_border()
                    return True
                logger.error(f"Failed to save prompts to {target_path}")
                return False
            except Exception as e:
                logger.error(f"Error saving prompts: {e}")
                return False
        except Exception as e:
            logger.error(f"Error in save_prompts_manually: {e}")
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
        """Load prompts from multiple files with enhanced error handling."""
        try:
            # BULLETPROOF IMPROVEMENT: Validate path input
            if not path_input or not isinstance(path_input, str):
                logger.error("Invalid path input")
                return False

            # Split paths by semicolon
            file_paths = [path.strip() for path in path_input.split(";") if path.strip()]

            if not file_paths:
                logger.error("No valid file paths found")
                return False

            # BULLETPROOF IMPROVEMENT: Validate each file path
            valid_paths = []
            for file_path in file_paths:
                try:
                    if Path(file_path).exists() and Path(file_path).is_file():
                        valid_paths.append(file_path)
                    else:
                        logger.warning(f"File does not exist or is not a file: {file_path}")
                except Exception as e:
                    logger.warning(f"Error validating file path {file_path}: {e}")

            if not valid_paths:
                logger.error("No valid files found")
                return False

            # Load prompts from each valid file
            all_prompts = []
            successful_files = 0

            for file_path in valid_paths:
                try:
                    prompts = self._load_prompts_from_file(file_path)
                    if prompts:
                        all_prompts.extend(prompts)
                        successful_files += 1
                        logger.info(f"Successfully loaded {len(prompts)} prompts from {file_path}")
                    else:
                        logger.warning(f"No prompts loaded from {file_path}")
                except Exception as e:
                    logger.error(f"Error loading prompts from {file_path}: {e}")

            if successful_files == 0:
                logger.error("Failed to load prompts from any files")
                return False

            # BULLETPROOF IMPROVEMENT: Validate loaded prompts
            valid_prompts = []
            for i, prompt in enumerate(all_prompts):
                if prompt and isinstance(prompt, str) and prompt.strip():
                    valid_prompts.append(prompt.strip())
                else:
                    logger.warning(f"Invalid prompt at index {i}: {prompt}")

            if not valid_prompts:
                logger.error("No valid prompts loaded from any files")
                return False

            # Update UI with loaded prompts
            self.ui.prompts = valid_prompts
            self.ui.current_prompt_index = 0
            self._current_file_path = path_input
            self._prompts_modified = False

            # Update UI components
            self._update_path_entry_border(COLOR_SUCCESS)
            self._update_preview(f"Loaded {len(valid_prompts)} prompts from {successful_files} files")

            # Update prompt list service if available
            if hasattr(self.ui, "prompt_list_service"):
                try:
                    self.ui.prompt_list_service.set_prompts(valid_prompts)
                    self.ui.prompt_list_service.set_current_prompt_index(0)
                except Exception as e:
                    logger.warning(f"Error updating prompt list service: {e}")

            logger.info(f"Successfully loaded {len(valid_prompts)} prompts from {successful_files} files")
            return True

        except Exception as e:
            logger.error(f"Error in _load_prompts_from_multiple_files: {e}")
            return False

    def _load_prompts_from_file(self, file_path: str) -> List[str]:
        """Load prompts from a single file and return the list."""
        try:
            success, result = self.file_service.parse_prompt_list(file_path)

            if success and isinstance(result, list):
                return result
            logger.warning(f"Failed to load prompts from {file_path}: {result}")
            return []

        except Exception as e:
            logger.error(f"Error loading prompts from file {file_path}: {e}")
            return []

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

    def _show_error_border(self, message: str) -> None:
        """Show error border with message."""
        try:
            self._update_path_entry_border(COLOR_ERROR)
            logger.error(f"File loading error: {message}")
        except Exception as e:
            logger.error(f"Error showing error border: {e}")
