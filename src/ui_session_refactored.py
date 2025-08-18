"""
Cursor Automation System - Refactored UI Session Manager

This module provides a refactored GUI for the Cursor automation system using
service-oriented architecture for better maintainability and testability.

Key Services:
- UI Theme Service: Colors, fonts, layout constants
- Coordinate Capture Service: Mouse click detection, coordinate management
- Countdown Service: Timer logic, countdown display
- Window Service: Window positioning, focus, DPI awareness
- Prompt List Service: Prompt list UI, highlighting, navigation
- Event Service: Button events, keyboard navigation

Author: Automation System
Version: 3.0
"""

import logging
import sys
import tkinter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

import customtkinter as ctk

# Configure logging
logger = logging.getLogger(__name__)

# Import with fallback for standalone execution
try:
    from .config import (
        BTN_START,
        BTN_STOP,
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_START_ACTIVE,
        BUTTON_START_ACTIVE_HOVER,
        BUTTON_START_INACTIVE,
        BUTTON_STOP_ACTIVE,
        BUTTON_STOP_ACTIVE_HOVER,
        BUTTON_TEXT,
        CARD_RADIUS,
        COLOR_BG,
        COLOR_BORDER,
        COLOR_MODIFIED,
        COLOR_SUCCESS,
        COLOR_SURFACE,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
        WINDOW_MARGIN,
    )
    from .coordinate_service import CoordinateCaptureService
    from .countdown_service import CountdownService
    from .file_service import PromptListService as FilePromptService
    from .inline_prompt_editor_service import InlinePromptEditorService
    from .memory_pool import cleanup_memory_pools
    from .ui_builders.configuration_builder import ConfigurationBuilder
    from .ui_builders.content_builder import ContentBuilder
    from .ui_builders.control_builder import ControlBuilder
    from .ui_builders.prompt_list_builder import PromptListBuilder
    from .window_service import WindowService
except ImportError:
    # Fallback for when running as script
    # Add src directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent))

    from config import (
        BTN_START,
        BTN_STOP,
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_START_ACTIVE,
        BUTTON_START_ACTIVE_HOVER,
        BUTTON_START_INACTIVE,
        BUTTON_STOP_ACTIVE,
        BUTTON_STOP_ACTIVE_HOVER,
        BUTTON_TEXT,
        CARD_RADIUS,
        COLOR_BG,
        COLOR_BORDER,
        COLOR_MODIFIED,
        COLOR_SUCCESS,
        COLOR_SURFACE,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
        WINDOW_MARGIN,
    )
    from coordinate_service import CoordinateCaptureService
    from countdown_service import CountdownService
    from file_service import PromptListService as FilePromptService
    from inline_prompt_editor_service import InlinePromptEditorService
    from ui_builders.configuration_builder import ConfigurationBuilder
    from ui_builders.content_builder import ContentBuilder
    from ui_builders.control_builder import ControlBuilder
    from ui_builders.prompt_list_builder import PromptListBuilder
    from window_service import WindowService

    try:
        from memory_pool import cleanup_memory_pools
    except ImportError:
        # Fallback if memory pool module not available
        def cleanup_memory_pools():
            pass

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

Coords = Dict[str, Tuple[int, int]]

# =============================================================================
# REFACTORED SESSION UI
# =============================================================================


class RefactoredSessionUI:
    """
    Refactored session UI using service-oriented architecture.

    This class orchestrates various services to provide a clean, maintainable
    interface for the automation system.
    """

    def __init__(self, default_start: int, default_main: int, default_cooldown: float):
        """
        Initialize the refactored session UI.

        Args:
            default_start: Default start delay
            default_main: Default main wait time
            default_cooldown: Default cooldown time
        """
        # Store default values
        self._default_start = default_start
        self._default_main = default_main
        self._default_cooldown = default_cooldown

        # Initialize main window
        self.window = ctk.CTk()
        self.window.title("Prompt Stacker")
        self.window.geometry("1000x800")
        self.window.minsize(800, 600)

        # Initialize services
        self.window_service = WindowService(self.window)
        self.coordinate_service = CoordinateCaptureService()
        # Event service disabled to prevent keyboard conflicts

        # Initialize prompt persistence state
        self._prompts_modified = False
        self._current_file_path = ""
        self._original_prompts_hash = None

        # Initialize state
        self._started = False
        self._prompts = []  # Private prompts list
        self.prompt_count = 0
        self.current_prompt_index = 0

        # Initialize UI variables
        self.prompt_path_var = ctk.StringVar()
        self.main_wait_var = ctk.StringVar()
        self.get_ready_delay_var = ctk.StringVar()

        # Thread-safe state management
        import threading

        self._automation_lock = threading.RLock()
        self._prompts_locked = False

        # Build interface
        self._build_interface()

        # Initialize services that depend on UI
        self.file_service = FilePromptService()

        # Initialize remaining services after UI is built
        self._initialize_ui_services()

        # Load timer preferences
        self._load_timer_preferences()

        # Set up timer change tracking
        self._setup_timer_change_tracking()

        # Load initial prompt list
        self._load_last_prompt_file()

        # Event handlers disabled to prevent keyboard conflicts

        # Update start button state
        self._update_start_state()

    def _build_interface(self) -> None:
        """Build the main interface."""
        # Configure window appearance
        ctk.set_appearance_mode("dark")

        # Build main container
        self._build_main_container()

        # Build sections
        self._build_combined_section()

        # Use builders to construct UI components
        content_builder = ContentBuilder(self)
        content_builder.build_content_area(self.main_content_container)

        configuration_builder = ConfigurationBuilder(self)
        configuration_builder.build_configuration_area(self.section_content)

        control_builder = ControlBuilder(self)
        control_builder.build_control_section(self.main_content_container)

        prompt_list_builder = PromptListBuilder(self)
        prompt_list_builder.build_prompt_list_area(self.section_content)

    def _build_main_container(self) -> None:
        """Build the main container."""
        self.main_container = ctk.CTkFrame(
            self.window,
            fg_color=COLOR_BG,
            corner_radius=CARD_RADIUS,
        )
        self.main_container.pack(
            fill="both",
            expand=True,
            padx=WINDOW_MARGIN,
            pady=WINDOW_MARGIN,
        )

    def _build_combined_section(self) -> None:
        """Build the combined targets and timers section."""
        # Create combined section frame with flexible height
        self.combined_section = ctk.CTkFrame(
            self.main_container,
            fg_color=COLOR_SURFACE,
            corner_radius=SECTION_RADIUS,
        )
        self.combined_section.pack(
            fill="both",
            expand=True,
            padx=PADDING,
            pady=(PADDING, GUTTER),
        )

        # Initialize collapse state
        self.settings_collapsed = False

        # Create header frame for toggle button
        self.section_header = ctk.CTkFrame(
            self.combined_section,
            fg_color="transparent",
        )
        self.section_header.pack(fill="x", padx=PADDING, pady=(5, 0))

        # Add application title on the left (smaller font, shifted in)
        self.app_title = ctk.CTkLabel(
            self.section_header,
            text="Prompt Stacker",
            font=FONT_BODY,
            text_color=COLOR_TEXT,
        )
        self.app_title.pack(side="left", padx=(10, 0))

        # Create toggle button (standard styling)
        self.settings_toggle_btn = ctk.CTkButton(
            self.section_header,
            text="⚙",  # Settings gear icon
            width=30,
            height=30,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            font=("Segoe UI", 14, "bold"),
            command=self._toggle_settings,
        )
        self.settings_toggle_btn.pack(side="right")

        # Add tooltip-like label
        self.toggle_label = ctk.CTkLabel(
            self.section_header,
            text="Toggle Settings",
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
        )
        self.toggle_label.pack(side="right", padx=(0, GUTTER))

        # Create a container for the main content area
        self.main_content_container = ctk.CTkFrame(
            self.combined_section,
            fg_color="transparent",
        )
        self.main_content_container.pack(
            fill="both",
            expand=True,
            padx=PADDING,
            pady=(5, PADDING),
        )

        # Create content frame (not scrollable - only prompt list will scroll)
        self.section_content = ctk.CTkFrame(
            self.main_content_container,
            fg_color="transparent",
        )
        self.section_content.pack(
            fill="both",
            expand=True,
            padx=0,
            pady=0,
        )

        # Configure grid weights for equal column distribution
        self.section_content.grid_columnconfigure(
            0,
            weight=1,
        )  # Left column (prompt list)
        self.section_content.grid_columnconfigure(
            1,
            weight=1,
        )  # Right column (configuration)
        self.section_content.grid_rowconfigure(0, weight=1)

    def _initialize_ui_services(self) -> None:
        """Initialize UI-dependent services."""
        # Initialize countdown service (with safe widget access)
        ui_widgets = {}
        if hasattr(self, "time_label"):
            ui_widgets["time_label"] = self.time_label
        if hasattr(self, "pause_btn"):
            ui_widgets["pause_btn"] = self.pause_btn
        if hasattr(self, "current_box"):
            ui_widgets["current_box"] = self.current_box
        if hasattr(self, "next_box"):
            ui_widgets["next_box"] = self.next_box

        if ui_widgets:
            self.countdown_service = CountdownService(ui_widgets)

        # Initialize inline prompt editor service (with safe widget access)
        if hasattr(self, "prompt_list_frame"):
            self.prompt_list_service = InlinePromptEditorService(
                self.prompt_list_frame,
                on_prompt_click=self._on_prompt_click,
                on_prompts_changed=self._on_prompts_changed,
            )
            
            # CRITICAL FIX: Pass next_box reference to prompt list service
            # This allows the service to update the "Next:" textarea when prompts are modified
            if hasattr(self, "next_box") and self.next_box:
                self.prompt_list_service.next_box = self.next_box

        # Load initial prompt list
        self._validate_prompt_list()

        # CRITICAL FIX: Start periodic UI health check to detect stuck states
        self._start_ui_health_check()

    def _setup_event_handlers(self) -> None:
        """Setup event handlers."""
        # Setup keyboard navigation
        self.event_service.setup_keyboard_navigation(
            on_up=self._on_key_up,
            on_down=self._on_key_down,
            on_enter=self._on_key_enter,
        )

        # Setup coordinate capture callbacks
        self.coordinate_service.on_coord_captured = self._on_coordinate_captured

        # Setup settings toggle shortcut (Ctrl+S)
        self.event_service.setup_keyboard_shortcut(
            key="s",
            modifier="Control",
            callback=self._toggle_settings,
        )

    def _toggle_settings(self) -> None:
        """Toggle the settings column visibility."""
        self.settings_collapsed = not self.settings_collapsed

        if self.settings_collapsed:
            # Hide settings column, expand prompt list
            self.section_content.grid_columnconfigure(
                0,
                weight=1,
            )  # Prompt list takes full width
            self.section_content.grid_columnconfigure(
                1,
                weight=0,
            )  # Settings column hidden

            # Hide the settings container
            if hasattr(self, "config_container"):
                self.config_container.grid_remove()

            # Update button and label
            self.settings_toggle_btn.configure(text="⚙")
            self.toggle_label.configure(text="Show Settings")
        else:
            # Show settings column, equal distribution
            self.section_content.grid_columnconfigure(0, weight=1)  # Equal distribution
            self.section_content.grid_columnconfigure(1, weight=1)  # Equal distribution

            # Show the settings container
            if hasattr(self, "config_container"):
                self.config_container.grid()

            # Update button and label
            self.settings_toggle_btn.configure(text="⚙")
            self.toggle_label.configure(text="Hide Settings")

        # Update the grid layout
        self.section_content.update_idletasks()

    def _validate_prompt_list(self) -> None:
        """Validate and load the prompt list from one or more files."""
        path_input = self.prompt_path_var.get().strip()

        # If path is empty, show no border and use default prompts
        if not path_input:
            self._current_file_path = ""
            self._prompts_modified = False
            self._update_path_entry_border()
            # Load default prompts without setting a path
            self._load_default_prompts()
            return

        # Split paths by semicolon and handle multiple files
        if self._load_prompts_from_multiple_files(path_input):
            # Successfully loaded - save path preference
            if hasattr(self, "config_service"):
                self.config_service.save_path_preference(path_input)
        else:
            # Failed to load - show error border
            self._current_file_path = ""
            self._prompts_modified = False
            self._update_path_entry_border()
            self._update_preview("")

    def _update_preview(self, text: str) -> None:
        """Update preview text."""
        if hasattr(self, "current_box") and self.current_box:
            try:
                self.current_box.configure(state="normal")
                self.current_box.delete("1.0", "end")
                self.current_box.insert("end", str(text))
                self.current_box.configure(state="disabled")
            except (AttributeError, tkinter.TclError):
                pass

    def _start_capture(self, key: str) -> None:
        """Start coordinate capture for a target."""
        # Set callback first
        self.coordinate_service.set_callback(self._on_coordinate_captured)

        # Start capture
        self.coordinate_service.start_capture(key)

        # Minimize window
        self.window_service.minimize()

    def _on_coordinate_captured(self, key: str, coord: Tuple[int, int]) -> None:
        """Handle coordinate capture completion."""
        # Restore window
        self.window_service.restore()

        # Immediately update the coordinate display for this key
        coord_label = getattr(self, f"{key}_coord_label", None)
        if coord_label:
            new_text = self.coordinate_service.get_coordinate_text(key)
            coord_label.configure(text=new_text)
            logger.debug("Updated %s coordinate display to: %s", key, new_text)
        else:
            logger.warning("No coordinate label found for %s", key)

        logger.info("Captured coordinate for %s: %s", key, coord)

    def _update_start_state(self) -> None:
        """Update start button state."""
        # Don't update button if automation is running - let the button handlers manage it
        if self._started:
            return

        # Check if start button exists
        if not hasattr(self, "start_btn"):
            return

        # Check if all required coordinates are set
        coords_validation = self.coordinate_service.validate_coordinates()
        coords_valid = all(coords_validation.values())  # All coordinates must be valid
        timers_valid = self._timers_valid()
        prompts_valid = len(self.prompts) > 0

        can_start = coords_valid and timers_valid and prompts_valid

        # Update start button only when not started
        if can_start:
            self.start_btn.configure(
                text=BTN_START,
                fg_color=BUTTON_START_ACTIVE,
                hover_color=BUTTON_START_ACTIVE_HOVER,
                state="normal",
                command=self._on_start,
            )
        else:
            self.start_btn.configure(
                text=BTN_START,
                fg_color=BUTTON_START_INACTIVE,
                hover_color=BUTTON_START_INACTIVE,
                state="disabled",
                command=self._on_start,
            )

        # Status updates removed - no status label in countdown area

    def _timers_valid(self) -> bool:
        """Validate timer values."""
        try:
            main_wait = float(self.main_wait_var.get())
            get_ready = float(self.get_ready_delay_var.get())

            return all(val >= 0 for val in [main_wait, get_ready])
        except ValueError:
            return False

    def _on_start(self) -> None:
        """Handle start button click - begin automation session."""
        with self._automation_lock:
            if not self._started:
                # Validate configuration before starting
                coords_validation = self.coordinate_service.validate_coordinates()
                if not all(coords_validation.values()):
                    return

                if not self._timers_valid():
                    return

                if len(self.prompts) == 0:
                    return

                # CRITICAL FIX: Lock prompt list during automation
                self._prompts_locked = True

                # Save coordinates
                self.coordinate_service.save_coordinates()
                self._started = True
                if hasattr(self, "prompt_list_service"):
                    self.prompt_list_service.set_automation_running(True)

                # Update start button to stop state (keep orange theme)
                self.start_btn.configure(
                    text=BTN_STOP,
                    fg_color=BUTTON_STOP_ACTIVE,
                    hover_color=BUTTON_STOP_ACTIVE_HOVER,
                    command=self._on_stop,
                )

                # Status update removed - no status label in countdown area

                # Start automation immediately
                self._start_automation()
            else:
                # Already started, handle as stop
                self._on_stop()

    def _start_automation(self) -> None:
        """Start the automation process."""
        try:
            logger.info("Starting automation process...")

            # Validate prerequisites before starting
            coords = self.get_coords()
            prompts = self.get_prompts_safe()
            timers = self.get_timers()

            logger.debug(
                "Validation - Coords: %s, Prompts: %s, Timers: %s",
                list(coords.keys()),
                len(prompts),
                timers,
            )

            # Check if all required coordinates are present
            required_coords = ["input", "submit", "accept"]
            missing_coords = [coord for coord in required_coords if coord not in coords]

            if missing_coords:
                logger.error("Missing required coordinates: %s", missing_coords)
                logger.error("Cannot start automation without all required coordinates")
                self._reset_automation_state()
                self._reset_start_button()
                return

            if not prompts:
                logger.error("No prompts available")
                self._reset_automation_state()
                self._reset_start_button()
                return

            # Import automation function with fallback
            try:
                from .automator import run_automation_with_ui
            except ImportError:
                from automator import run_automation_with_ui

            logger.debug("Automation function imported successfully")

            # Run automation in a separate thread to avoid blocking UI
            import threading

            automation_thread = threading.Thread(
                target=run_automation_with_ui,
                args=(self,),
                name="AutomationThread",
            )
            automation_thread.daemon = True
            automation_thread.start()

            logger.info("Automation thread started successfully")

        except Exception:
            logger.exception("Error starting automation")
            import traceback

            traceback.print_exc()
            # Don't call _on_cancel here as it might cause recursion
            # Just reset the state
            self._reset_automation_state()
            self._reset_start_button()

    def _toggle_pause(self) -> None:
        """Toggle pause state - button toggles between Pause and Resume."""
        if hasattr(self, "countdown_service") and self.countdown_service.is_active():
            self.countdown_service.toggle_pause()
            # Note: Button text and styling are handled by countdown_service.toggle_pause()

    def _on_next(self) -> None:
        """Handle next button - immediately start next prompt automation."""
        with self._automation_lock:
            if not self._started:
                # If automation is not running, just advance UI position
                if self.current_prompt_index < len(self.prompts) - 1:
                    self.current_prompt_index += 1
                    self.prompt_list_service.set_current_prompt_index(
                        self.current_prompt_index,
                    )
                    print(f"Advanced to prompt {self.current_prompt_index + 1}")
                return

            # If automation is running, advance to next prompt and start automation cycle
            if self.current_prompt_index < len(self.prompts) - 1:
                # CRITICAL FIX: Atomic operation - stop countdown and advance index together
                self._stop_countdown_if_active()

                # Advance to next prompt
                self.current_prompt_index += 1
                self.prompt_list_service.set_current_prompt_index(
                    self.current_prompt_index,
                )
                print(
                    f"Next button: Advanced to prompt {self.current_prompt_index + 1}",
                )

                # Start automation cycle for the new prompt
                self._start_prompt_automation()
            else:
                print("Next button: Already at last prompt")

    def _start_prompt_automation(self) -> None:
        """Start automation cycle for the current prompt."""
        try:
            # Import automation function with fallback
            try:
                from .automator import run_single_prompt_automation
            except ImportError:
                from automator import run_single_prompt_automation

            # Run single prompt automation in a separate thread
            import threading

            automation_thread = threading.Thread(
                target=run_single_prompt_automation,
                args=(self, self.current_prompt_index),
            )
            automation_thread.daemon = True
            automation_thread.start()

        except Exception as e:
            print(f"Error starting prompt automation: {e}")

    def _on_stop(self) -> None:
        """Handle stop button - restart the flow."""
        with self._automation_lock:
            self._reset_automation_state()
            self._reset_start_button()
            self._stop_countdown_if_active()

    def _on_cancel(self) -> None:
        """Handle cancel button - end the whole automation."""
        with self._automation_lock:
            self._reset_automation_state()
            self._reset_start_button()
            self._cancel_countdown_if_active()

        # Close the application
        self.window.quit()

    def _browse_prompt_file(self) -> None:
        """Open file browser to select one or more prompt files."""
        from tkinter import filedialog

        # Get the initial directory - try last used directory first, then current file directory, then default
        initial_dir = None
        
        # Try to load last used directory
        if hasattr(self, "config_service"):
            initial_dir = self.config_service.load_last_directory("")
        
        # If no last directory or it doesn't exist, try current file directory
        if not initial_dir or not Path(initial_dir).exists():
            if self.prompt_path_var.get():
                initial_dir = str(Path(self.prompt_path_var.get().split(";")[0].strip()).parent)
            else:
                # Fallback to default prompt_list directory
                try:
                    initial_dir = str(Path(__file__).parent.parent / "prompt_lists")
                    # Ensure the directory exists
                    if not Path(initial_dir).exists():
                        initial_dir = str(Path.home())
                except Exception:
                    # Final fallback to user's home directory
                    initial_dir = str(Path.home())

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
            self.prompt_path_var.set(combined_paths)

            # Save this as the last used file(s)
            if hasattr(self, "config_service"):
                self.config_service.save_path_preference(combined_paths)
                
                # Save the directory of the first selected file as last used directory
                first_file_dir = str(Path(file_paths[0]).parent)
                self.config_service.save_last_directory(first_file_dir)

            # Validate and load the prompt list
            self._validate_prompt_list()
        else:
            # User cancelled the file dialog
            pass

    def _load_timer_preferences(self) -> None:
        """Load timer preferences from config service."""
        if hasattr(self, "config_service"):
            main_wait, get_ready_delay = self.config_service.load_timer_preferences()
            self.main_wait_var.set(main_wait)
            self.get_ready_delay_var.set(get_ready_delay)
        else:
            # Fallback to defaults if config service not available
            self.main_wait_var.set(str(self._default_main))
            self.get_ready_delay_var.set("3")

    def _save_timer_preferences(self) -> None:
        """Save timer preferences to config service."""
        if hasattr(self, "config_service"):
            self.config_service.save_timer_preferences(
                self.main_wait_var.get(),
                self.get_ready_delay_var.get(),
            )

    def _setup_timer_change_tracking(self) -> None:
        """Set up tracking for timer value changes."""
        # Bind timer variables to save preferences when they change
        self.main_wait_var.trace_add("write", self._on_timer_changed)
        self.get_ready_delay_var.trace_add("write", self._on_timer_changed)

    def _on_timer_changed(self, *_args) -> None:
        """Handle timer value changes."""
        # Save preferences when timer values change
        self._save_timer_preferences()

    def _load_last_prompt_file(self) -> None:
        """Load the last used prompt file."""
        if hasattr(self, "config_service"):
            last_file = self.config_service.load_path_preference("")
            if last_file and Path(last_file).exists():
                self.prompt_path_var.set(last_file)
                if self._load_prompts_from_file(last_file):
                    return

        # Try to load default prompts directly
        self._load_default_prompts()

    def _load_default_prompts(self) -> None:
        """Load default prompts from the bundled prompt_list.py."""
        default_path = self.file_service.get_default_prompt_list_path()

        if Path(default_path).exists():
            # Set the path and validate
            self.prompt_path_var.set(default_path)
            self._validate_prompt_list()
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
        self.prompts = default_prompts
        self.prompt_count = len(default_prompts)

        # Update the prompt list service
        if hasattr(self, "prompt_list_service"):
            self.prompt_list_service.set_prompts(default_prompts)

    def _on_prompt_click(self, index: int) -> None:
        """Handle prompt list click."""
        if not self._started:
            self.current_prompt_index = index
            self.prompt_list_service.set_current_prompt_index(index)

    def _on_prompts_changed(self, prompts: List[str]) -> None:
        """Handle prompts changed event from inline editor."""
        self.prompts = prompts
        self.prompt_count = len(prompts)

        # Check if prompts have been modified
        self._check_prompts_modified()

        # Auto-save if we have a file path and prompts are modified
        if self._prompts_modified and self._current_file_path:
            self._auto_save_prompts()

    def _check_prompts_modified(self) -> None:
        """Check if prompts have been modified since last load/save."""
        # If no file path, no need to track modifications
        if not self._current_file_path:
            self._prompts_modified = False
            return

        if not self.prompts:
            self._prompts_modified = False
            return

        # Create a simple hash of the prompts for comparison
        current_hash = hash(tuple(self.prompts))

        if self._original_prompts_hash is None:
            # First time loading - set as original
            self._original_prompts_hash = current_hash
            self._prompts_modified = False
        else:
            # Check if hash has changed
            self._prompts_modified = current_hash != self._original_prompts_hash

        # Update border color based on modification state
        self._update_path_entry_border()

    def _update_path_entry_border(self, color: str = None) -> None:
        """Update path entry border color based on modification state or directly."""
        if not hasattr(self, "path_entry"):
            return

        if color is not None:
            # Direct color update
            self.path_entry.configure(border_color=color)
        elif not self._current_file_path:
            # No file loaded - use default border
            self.path_entry.configure(border_color=COLOR_BORDER)
        elif self._prompts_modified:
            # File is modified - use blue border
            self.path_entry.configure(border_color=COLOR_MODIFIED)
        else:
            # File is unmodified - use success border
            self.path_entry.configure(border_color=COLOR_SUCCESS)

    def _auto_save_prompts(self) -> None:
        """Auto-save prompts to the current file path."""
        if not self._current_file_path or not self._prompts_modified:
            return

        try:
            success = self.file_service.save_prompts(
                self._current_file_path,
                self.prompts,
            )
            if success:
                # Update original hash after successful save
                self._original_prompts_hash = hash(tuple(self.prompts))
                self._prompts_modified = False
                self._update_path_entry_border()
                print(f"Auto-saved prompts to: {self._current_file_path}")
            else:
                print(f"Failed to auto-save prompts to: {self._current_file_path}")
        except Exception as e:
            print(f"Error auto-saving prompts: {e}")

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
                    print(
                        f"Successfully loaded {len(result)} prompts from: {file_path}",
                    )
                else:
                    failed_files.append(file_path)
                    print(f"Failed to load prompts from: {file_path}")
                    # Continue with other files even if one fails

            if all_prompts:
                # Set combined prompts
                self.prompts = all_prompts
                self.prompt_count = len(all_prompts)
                self.current_prompt_index = 0

                # Update inline prompt editor service
                self.prompt_list_service.set_prompts(all_prompts)

                # Set up persistence tracking (use first file as primary)
                self._current_file_path = loaded_files[0] if loaded_files else ""
                self._original_prompts_hash = hash(tuple(all_prompts))
                self._prompts_modified = False

                # Update UI
                self._update_path_entry_border()
                self._update_preview(all_prompts[0] if all_prompts else "")

                print(
                    f"Total prompts loaded: {len(all_prompts)} from {len(loaded_files)} files",
                )
                if failed_files:
                    print(
                        f"Failed to load {len(failed_files)} files: {', '.join(failed_files)}",
                    )
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
                self.prompts = result
                self.prompt_count = len(result)
                self.current_prompt_index = 0

                # Update inline prompt editor service
                self.prompt_list_service.set_prompts(result)

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

    def _on_key_up(self) -> None:
        """Handle up key."""
        if not self._started:
            new_index = max(0, self.current_prompt_index - 1)
            if new_index != self.current_prompt_index:
                self.current_prompt_index = new_index
                self.prompt_list_service.set_current_prompt_index(new_index)

    def _on_key_down(self) -> None:
        """Handle down key."""
        if not self._started:
            new_index = min(len(self.prompts) - 1, self.current_prompt_index + 1)
            if new_index != self.current_prompt_index:
                self.current_prompt_index = new_index
                self.prompt_list_service.set_current_prompt_index(new_index)

    def _on_key_enter(self) -> None:
        """Handle enter key."""
        if not self._started:
            self._on_prompt_click(self.current_prompt_index)

    def wait_for_start(self) -> None:
        """Wait for user to start the automation."""
        # Start the mainloop - automation will be triggered by start button
        self.window.mainloop()

    def get_coords(self) -> Coords:
        """Get current coordinates."""
        with self._automation_lock:
            return self.coordinate_service.get_coordinates()

    def get_timers(self) -> Tuple[int, int, float, float]:
        """Get current timer values."""
        with self._automation_lock:
            return (
                self._default_start,  # Use constructor parameter
                int(float(self.main_wait_var.get())),
                self._default_cooldown,  # Use constructor parameter
                float(self.get_ready_delay_var.get()),
            )

    @property
    def prompts(self) -> List[str]:
        """Get prompts with thread safety."""
        with self._automation_lock:
            return self._prompts.copy()  # Return a copy to prevent modification

    @prompts.setter
    def prompts(self, value: List[str]) -> None:
        """Set prompts with thread safety."""
        with self._automation_lock:
            if not self._prompts_locked:
                self._prompts = value.copy() if value else []
                self.prompt_count = len(self._prompts)
            else:
                print("Warning: Cannot modify prompts during automation")

    def get_prompts_safe(self) -> List[str]:
        """Get prompts with thread safety."""
        with self._automation_lock:
            return self._prompts.copy()  # Return a copy to prevent modification

    def get_current_prompt(self) -> Optional[str]:
        """Get current prompt text."""
        return self.prompt_list_service.get_current_prompt()

    def get_next_prompt(self) -> Optional[str]:
        """Get next prompt text."""
        return self.prompt_list_service.get_next_prompt()

    def advance_prompt_index(self) -> None:
        """Advance to next prompt."""
        if self.current_prompt_index < len(self.prompts) - 1:
            self.current_prompt_index += 1
            self.prompt_list_service.set_current_prompt_index(self.current_prompt_index)
            print(f"Automation: Advanced to prompt {self.current_prompt_index + 1}")

    def set_prompt_index(self, index: int) -> bool:
        """Set prompt index."""
        if 0 <= index < len(self.prompts):
            self.current_prompt_index = index
            self.prompt_list_service.set_current_prompt_index(index)
            return True
        return False

    def update_prompt_index_from_automation(self, index: int) -> None:
        """Update prompt index from automation (thread-safe)."""
        self.current_prompt_index = index
        if hasattr(self, "prompt_list_service"):
            self.prompt_list_service.set_current_prompt_index(index)

    def refresh_automation_display(self) -> None:
        """Refresh the automation display state after a cycle completes."""
        try:
            # Simple refresh - just update the prompt list service
            if hasattr(self, "prompt_list_service"):
                self.prompt_list_service.refresh_display()
        except Exception as e:
            print(f"Error refreshing automation display: {e}")

    def detect_and_fix_stuck_ui(self) -> bool:
        """
        Detect and fix stuck UI state where display shows "Waiting..." but automation has moved on.
        
        Returns:
            True if stuck state was detected and fixed, False otherwise
        """
        try:
            # SIMPLIFIED: Only check if countdown is inactive but UI shows "Waiting..."
            if hasattr(self, "countdown_service") and not self.countdown_service.is_active():
                if hasattr(self, "current_box") and self.current_box:
                    try:
                        current_content = self.current_box.get("1.0", "end-1c").strip()
                        if current_content == "Waiting...":
                            print("Detected stuck UI state - fixing...")
                            # Simple fix: update to show current prompt
                            current_text = self.prompts[self.current_prompt_index] if self.prompts and self.current_prompt_index < len(self.prompts) else ""
                            self.current_box.configure(state="normal")
                            self.current_box.delete("1.0", "end")
                            self.current_box.insert("end", current_text)
                            self.current_box.configure(state="disabled")
                            
                            print("Stuck UI state fixed successfully")
                            return True
                    except Exception as e:
                        print(f"Error checking current box content: {e}")
            
            # CRITICAL FIX: Check for orphaned countdown threads
            if hasattr(self, "countdown_service"):
                try:
                    thread_status = self.countdown_service.get_thread_status()
                    if thread_status["thread_alive"] and not thread_status["countdown_active"]:
                        print("Detected orphaned countdown thread - forcing cleanup")
                        self.countdown_service.force_reset()
                        return True
                except Exception as e:
                    print(f"Error checking thread status: {e}")
            
            return False
        except Exception as e:
            print(f"Error in detect_and_fix_stuck_ui: {e}")
            return False

    def countdown(
        self,
        seconds: int,
        text: Optional[str],
        next_text: Optional[str],
        last_text: Optional[str],
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Start countdown with user controls."""
        return self.countdown_service.start_countdown(
            seconds,
            text,
            next_text,
            last_text,
            on_complete,
        )

    def _reset_automation_state(self) -> None:
        """Reset automation state to initial values."""
        self._started = False
        if hasattr(self, "prompt_list_service"):
            self.prompt_list_service.set_automation_running(False)
        self.current_prompt_index = 0
        if hasattr(self, "prompt_list_service"):
            self.prompt_list_service.set_current_prompt_index(0)

        # CRITICAL FIX: Unlock prompt list when automation stops
        self._prompts_locked = False

    def _reset_start_button(self) -> None:
        """Reset start button to initial state."""
        if hasattr(self, "start_btn"):
            self.start_btn.configure(
                text=BTN_START,
                fg_color=BUTTON_START_ACTIVE,
                hover_color=BUTTON_START_ACTIVE_HOVER,
                command=self._on_start,
            )

    def _stop_countdown_if_active(self) -> None:
        """Stop countdown service if it's currently active."""
        if hasattr(self, "countdown_service") and self.countdown_service.is_active():
            self.countdown_service.stop()

    def _cancel_countdown_if_active(self) -> None:
        """Cancel countdown service if it's currently active."""
        if hasattr(self, "countdown_service") and self.countdown_service.is_active():
            self.countdown_service.cancel()

    def bring_to_front(self) -> None:
        """Bring window to front."""
        self.window_service.bring_to_front()

    def close(self) -> None:
        """Close the application."""
        # Save prompts if modified
        self._save_prompts_on_exit()

        # Stop services in proper order
        try:
            if hasattr(self, "event_service"):
                self.event_service.stop()
        except Exception as e:
            print(f"Error stopping event service: {e}")

        try:
            if hasattr(self, "coordinate_service"):
                self.coordinate_service.stop_capture()
        except Exception as e:
            print(f"Error stopping coordinate service: {e}")

        try:
            if hasattr(self, "countdown_service"):
                self.countdown_service.stop()
        except Exception as e:
            print(f"Error stopping countdown service: {e}")

        # Cleanup memory pools
        try:
            cleanup_memory_pools()
        except Exception:
            pass  # Ignore cleanup errors

        # Close window
        try:
            self.window_service.close()
        except Exception as e:
            print(f"Error closing window: {e}")

    def _save_prompts_on_exit(self) -> None:
        """Save prompts if they have been modified."""
        if self._prompts_modified and self._current_file_path:
            try:
                success = self.file_service.save_prompts(
                    self._current_file_path,
                    self.prompts,
                )
                if success:
                    print(f"Saved modified prompts to: {self._current_file_path}")
                else:
                    print(
                        f"Failed to save modified prompts to: {self._current_file_path}",
                    )
            except Exception as e:
                print(f"Error saving prompts on exit: {e}")

    def save_prompts_manually(self, file_path: Optional[str] = None) -> bool:
        """
        Manually save prompts to a file.

        Args:
            file_path: Optional file path to save to. If None, uses current file path.

        Returns:
            True if saved successfully, False otherwise.
        """
        if not self.prompts:
            print("No prompts to save")
            return False

        target_path = file_path or self._current_file_path
        if not target_path:
            print("No file path specified for saving")
            return False

        try:
            success = self.file_service.save_prompts(target_path, self.prompts)
            if success:
                # Update persistence tracking
                self._current_file_path = target_path
                self._original_prompts_hash = hash(tuple(self.prompts))
                self._prompts_modified = False
                self._update_path_entry_border()
                print(f"Manually saved prompts to: {target_path}")
                return True
            print(f"Failed to save prompts to: {target_path}")
            return False
        except Exception as e:
            print(f"Error saving prompts: {e}")
            return False

    def is_prompts_modified(self) -> bool:
        """Check if prompts have been modified since last save."""
        return self._prompts_modified

    def get_current_file_path(self) -> str:
        """Get the current file path."""
        return self._current_file_path or ""

    def _start_ui_health_check(self) -> None:
        """Start periodic UI health check to detect and fix stuck states."""
        def health_check():
            try:
                # Check for stuck UI state every 2 seconds
                if self.detect_and_fix_stuck_ui():
                    print("Periodic health check detected and fixed stuck UI state")
            except Exception as e:
                print(f"Error in periodic health check: {e}")
            finally:
                # Schedule next health check
                if hasattr(self, 'window_service') and self.window_service.window:
                    self.window_service.window.after(2000, health_check)  # 2 seconds
        
        # Start the health check
        if hasattr(self, 'window_service') and self.window_service.window:
            self.window_service.window.after(2000, health_check)
