"""
Session App - Main UI Application Orchestrator

The main application class that orchestrates all UI components and services.
This is the entry point for the refactored UI system.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import customtkinter as ctk

# Configure logging
logger = logging.getLogger(__name__)

# Import with fallback for standalone execution
try:
    from ..config import (
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_TEXT,
        CARD_RADIUS,
        COLOR_BG,
        COLOR_SURFACE,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
        WINDOW_MARGIN,
    )
except ImportError:
    # Fallback values if config is not available
    BUTTON_BG = "#2B2B2B"
    BUTTON_HOVER = "#3B3B3B"
    BUTTON_TEXT = "#FFFFFF"
    CARD_RADIUS = 8
    COLOR_BG = "#1E1E1E"
    COLOR_SURFACE = "#2B2B2B"
    COLOR_TEXT = "#FFFFFF"
    COLOR_TEXT_MUTED = "#888888"
    FONT_BODY = ("Segoe UI", 10)
    GUTTER = 20
    PADDING = 10
    SECTION_RADIUS = 12
    WINDOW_MARGIN = 20

try:
    from ..coordinate_service import CoordinateCaptureService
    from ..countdown_service import CountdownService
    from ..file_service import PromptListService as FilePromptService
    from ..inline_prompt_editor_service import InlinePromptEditorService
    from ..ui_builders.configuration_builder import ConfigurationBuilder
    from ..ui_builders.content_builder import ContentBuilder
    from ..ui_builders.control_builder import ControlBuilder
    from ..ui_builders.prompt_list_builder import PromptListBuilder
    from ..window_service import WindowService
    from .prompt_io import PromptIO
    from .session_controller import SessionController
    from .state_manager import UIStateManager
except ImportError:
    # Fallback for standalone execution
    import sys
    from pathlib import Path

    # Add src directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from coordinate_service import CoordinateCaptureService
    from countdown_service import CountdownService
    from file_service import PromptListService as FilePromptService
    from inline_prompt_editor_service import InlinePromptEditorService
    from ui.prompt_io import PromptIO
    from ui.session_controller import SessionController
    from ui.state_manager import UIStateManager
    from ui_builders.configuration_builder import ConfigurationBuilder
    from ui_builders.content_builder import ContentBuilder
    from ui_builders.control_builder import ControlBuilder
    from ui_builders.prompt_list_builder import PromptListBuilder
    from window_service import WindowService

try:
    from ..memory_pool import cleanup_memory_pools
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


class SessionUI:
    """
    Refactored session UI using service-oriented architecture.
    This class orchestrates various services to provide a clean, maintainable
    interface for the automation system.
    """

    def __init__(self, default_start: int = 5):
        """
        Initialize the refactored session UI.
        Args:
            default_start: Default start delay
        """
        # Store default values
        self._default_start = default_start

        # Initialize main window
        self.window = ctk.CTk()
        self.window.title("Prompt Stacker")
        self.window.geometry("1000x800")
        self.window.minsize(800, 600)

        # Store base title for dynamic updates
        self._base_title = "Prompt Stacker"

        # Initialize services
        self.window_service = WindowService(self.window)
        self.coordinate_service = CoordinateCaptureService()

        # Initialize config service
        try:
            from ..config_service import ConfigService
            self.config_service = ConfigService()
        except ImportError:
            # Fallback if config service not available
            self.config_service = None

        # Initialize state
        self._prompts = []  # Private prompts list
        self.prompt_count = 0
        self.current_prompt_index = 0

        # Initialize UI variables
        self.prompt_path_var = ctk.StringVar()
        self.main_wait_var = ctk.StringVar()
        self.get_ready_delay_var = ctk.StringVar()

        # Set up trace for prompt path changes to update window title
        self.prompt_path_var.trace_add("write", self._on_prompt_path_changed)

        # Build interface
        self._build_interface()

        # Initialize services that depend on UI
        self.file_service = FilePromptService()

        # Initialize UI-dependent services AFTER UI is built
        self._initialize_ui_services()

        # Initialize controllers and managers
        self._initialize_controllers()

        # Load timer preferences
        self._load_timer_preferences()

        # Set up timer change tracking
        self._setup_timer_change_tracking()

        # Load initial prompt list
        self.prompt_io.load_last_prompt_file()

        # Update window title with current path
        self._update_window_title()

        # Update start button state AFTER everything is initialized
        self.state_manager.update_start_state()

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

        # Countdown section removed - only using control timer

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
        self.section_content.grid_columnconfigure(0, weight=1)  # Left column
        # (prompt list)
        self.section_content.grid_columnconfigure(1, weight=1)  # Right column
        # (configuration)
        self.section_content.grid_rowconfigure(0, weight=1)

    def _initialize_ui_services(self) -> None:
        """Initialize UI-dependent services."""
        # Initialize countdown service (using control timer label)
        ui_widgets = {}
        if hasattr(self, "control_timer_label"):
            ui_widgets["time_label"] = self.control_timer_label  # Use control
            # timer as main display
        if hasattr(self, "pause_btn"):
            ui_widgets["pause_btn"] = self.pause_btn
        if hasattr(self, "current_box"):
            ui_widgets["current_box"] = self.current_box
        if hasattr(self, "next_box"):
            ui_widgets["next_box"] = self.next_box
        # Progress bar removed - no longer needed

        # Always create countdown service, even if some widgets are missing
        self.countdown_service = CountdownService(ui_widgets)

        # Update countdown service with widget references
        if hasattr(self, "control_timer_label") and self.control_timer_label:
            self.countdown_service.time_label = self.control_timer_label  # Wire
            # control timer as main display
        if hasattr(self, "pause_btn") and self.pause_btn:
            self.countdown_service.pause_btn = self.pause_btn
        if hasattr(self, "current_box") and self.current_box:
            self.countdown_service.current_box = self.current_box
        if hasattr(self, "next_box") and self.next_box:
            self.countdown_service.next_box = self.next_box

        # Initialize inline prompt editor service (with safe widget access)
        if hasattr(self, "prompt_list_frame"):
            self.prompt_list_service = InlinePromptEditorService(
                self.prompt_list_frame,
                on_prompt_click=self._on_prompt_click,
                on_prompts_changed=self._on_prompts_changed,
            )

            # CRITICAL FIX: Pass next_box reference to prompt list service
            # This allows the service to update the "Next:" textarea when
            # prompts are modified
            if hasattr(self, "next_box") and self.next_box:
                self.prompt_list_service.next_box = self.next_box

    def _initialize_controllers(self) -> None:
        """Initialize controllers and managers."""
        # Initialize controllers
        self.session_controller = SessionController(self)
        self.prompt_io = PromptIO(self)
        self.state_manager = UIStateManager(self)

        # Load initial prompt list
        self.prompt_io.validate_prompt_list()

        # CRITICAL FIX: Start periodic UI health check to detect stuck states
        self.state_manager.start_ui_health_check()

    def _toggle_settings(self) -> None:
        """Toggle the settings column visibility."""
        self.settings_collapsed = not self.settings_collapsed

        if self.settings_collapsed:
            # Hide settings column, expand prompt list
            self.section_content.grid_columnconfigure(0, weight=1)  # Prompt
            # list takes full width
            self.section_content.grid_columnconfigure(1, weight=0)  # Settings
            # column hidden

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

    def _load_timer_preferences(self) -> None:
        """Load timer preferences from config service."""
        if hasattr(self, "config_service"):
            main_wait, get_ready_delay = self.config_service.load_timer_preferences()
            self.main_wait_var.set(main_wait)
            self.get_ready_delay_var.set(get_ready_delay)
        else:
            # Fallback to defaults if config service not available
            self.main_wait_var.set(str(self._default_start))
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

        # Update start button state when timer values change
        if hasattr(self, "state_manager"):
            self.state_manager.update_start_state()

    def _on_prompt_click(self, index: int) -> None:
        """Handle prompt list click."""
        self.state_manager.on_prompt_click(index)

    def _on_prompts_changed(self, prompts: List[str]) -> None:
        """Handle prompts changed event from inline editor."""
        self.prompt_io.on_prompts_changed(prompts)

        # Update start button state when prompts change
        if hasattr(self, "state_manager"):
            self.state_manager.update_start_state()

    def wait_for_start(self) -> None:
        """Wait for user to start the automation."""
        # Start the mainloop - automation will be triggered by start button
        self.window.mainloop()

    def get_coords(self) -> Coords:
        """Get current coordinates."""
        return self.coordinate_service.get_coordinates()

    def get_timers(self) -> Tuple[int, int, float, float]:
        """Get current timer values."""
        return (
            self._default_start,  # Use constructor parameter
            int(float(self.main_wait_var.get())),
            self._default_start,  # Use constructor parameter
            float(self.get_ready_delay_var.get()),
        )

    def _update_window_title(self) -> None:
        """Update window title to show current valid path."""
        try:
            current_path = self.prompt_path_var.get().strip()

            if not current_path:
                # No path set - use base title
                self.window.title(self._base_title)
                return

            # Split multiple paths if present
            paths = [path.strip() for path in current_path.split(";") if path.strip()]

            if not paths:
                # No valid paths - use base title
                self.window.title(self._base_title)
                return

            # Use the first valid path for the title
            primary_path = paths[0]

            # Convert to Path object for better handling
            from pathlib import Path
            path_obj = Path(primary_path)

            if path_obj.exists() and path_obj.is_file():
                # File exists - show filename and parent directory
                filename = path_obj.name
                parent_dir = path_obj.parent.name

                if len(paths) > 1:
                    # Multiple files - show count
                    title = f"{self._base_title} - {filename} (+{len(paths)-1} more) - {parent_dir}"
                else:
                    # Single file
                    title = f"{self._base_title} - {filename} - {parent_dir}"
            elif len(paths) > 1:
                title = f"{self._base_title} - {primary_path} (+{len(paths)-1} more)"
            else:
                title = f"{self._base_title} - {primary_path}"

            self.window.title(title)

        except Exception as e:
            # Fallback to base title on error
            logger.warning(f"Error updating window title: {e}")
            self.window.title(self._base_title)

    def _on_prompt_path_changed(self, *args) -> None:
        """Handle prompt path variable changes to update window title."""
        try:
            # Debounce the update to avoid too frequent title changes
            if hasattr(self, "_title_update_timer"):
                self.window.after_cancel(self._title_update_timer)

            # Schedule title update after a short delay
            self._title_update_timer = self.window.after(500, self._update_window_title)
        except Exception as e:
            logger.warning(f"Error handling prompt path change: {e}")

    @property
    def prompts(self) -> List[str]:
        """Get prompts with thread safety."""
        return self._prompts.copy()  # Return a copy to prevent modification

    @prompts.setter
    def prompts(self, value: List[str]) -> None:
        """Set prompts with thread safety."""
        if not self.session_controller.are_prompts_locked():
            self._prompts = value.copy() if value else []
            self.prompt_count = len(self._prompts)

            # Update start button state when prompts are set
            if hasattr(self, "state_manager"):
                self.state_manager.update_start_state()
        else:
            print("Warning: Cannot modify prompts during automation")

    def get_prompts_safe(self) -> List[str]:
        """Get prompts with thread safety."""
        return self._prompts.copy()  # Return a copy to prevent modification

    def get_current_prompt(self) -> Optional[str]:
        """Get current prompt text."""
        return self.state_manager.get_current_prompt()

    def get_next_prompt(self) -> Optional[str]:
        """Get next prompt text."""
        return self.state_manager.get_next_prompt()

    def advance_prompt_index(self) -> None:
        """Advance to next prompt."""
        self.state_manager.advance_prompt_index()

    def set_prompt_index(self, index: int) -> bool:
        """Set prompt index."""
        return self.state_manager.set_prompt_index(index)

    def update_prompt_index_from_automation(self, index: int) -> None:
        """Update prompt index from automation (thread-safe)."""
        self.state_manager.update_prompt_index_from_automation(index)

    def refresh_automation_display(self) -> None:
        """Refresh the automation display state after a cycle completes."""
        self.state_manager.refresh_automation_display()

    def detect_and_fix_stuck_ui(self) -> bool:
        """Detect and fix stuck UI state."""
        return self.state_manager.detect_and_fix_stuck_ui()

    def countdown(
        self,
        seconds: float,
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
        if (self.prompt_io.is_prompts_modified() and
            self.prompt_io.get_current_file_path()):
            try:
                success = self.file_service.save_prompts(
                    self.prompt_io.get_current_file_path(),
                    self.prompts,
                )
                if success:
                    print(
                        f"Saved modified prompts to: "
                        f"{self.prompt_io.get_current_file_path()}",
                    )
                else:
                    print(
                        f"Failed to save modified prompts to: "
                        f"{self.prompt_io.get_current_file_path()}",
                    )
            except Exception as e:
                print(f"Error saving prompts on exit: {e}")

    def save_prompts_manually(self, file_path: Optional[str] = None) -> bool:
        """Manually save prompts to a file."""
        return self.prompt_io.save_prompts_manually(file_path)

    def is_prompts_modified(self) -> bool:
        """Check if prompts have been modified since last save."""
        return self.prompt_io.is_prompts_modified()

    def get_current_file_path(self) -> str:
        """Get the current file path."""
        return self.prompt_io.get_current_file_path()

    def _browse_prompt_file(self) -> None:
        """Open file browser to select one or more prompt files."""
        self.prompt_io.browse_prompt_file()

    # Removed duplicate validation - use prompt_io.validate_prompt_list() directly

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

        # Update start button state when coordinates change
        if hasattr(self, "state_manager"):
            self.state_manager.update_start_state()

    def _on_key_up(self) -> None:
        """Handle up key."""
        if (hasattr(self, "session_controller") and
            not self.session_controller.is_started()):
            new_index = max(0, self.current_prompt_index - 1)
            if new_index != self.current_prompt_index:
                self.current_prompt_index = new_index
                if hasattr(self, "prompt_list_service"):
                    self.prompt_list_service.set_current_prompt_index(new_index)

    def _on_key_down(self) -> None:
        """Handle down key."""
        if (hasattr(self, "session_controller") and
            not self.session_controller.is_started()):
            new_index = min(len(self.prompts) - 1, self.current_prompt_index + 1)
            if new_index != self.current_prompt_index:
                self.current_prompt_index = new_index
                if hasattr(self, "prompt_list_service"):
                    self.prompt_list_service.set_current_prompt_index(new_index)

    def _on_key_enter(self) -> None:
        """Handle enter key."""
        if (hasattr(self, "session_controller") and
            not self.session_controller.is_started()):
            self._on_prompt_click(self.current_prompt_index)

    def _on_start(self) -> None:
        """Handle start button click."""
        if hasattr(self, "session_controller"):
            if not self.session_controller.is_started():
                if self.session_controller.start_automation():
                    self.state_manager.update_start_button_to_stop()
            else:
                self.session_controller.stop_automation()
                self.state_manager.reset_start_button()

    def _on_stop(self) -> None:
        """Handle stop button click."""
        if hasattr(self, "session_controller"):
            self.session_controller.stop_automation()
            self.state_manager.reset_start_button()

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if hasattr(self, "session_controller"):
            self.session_controller.cancel_automation()

    def _on_next(self) -> None:
        """Handle next button click."""
        if hasattr(self, "session_controller"):
            self.session_controller.next_prompt()

    def _toggle_pause(self) -> None:
        """Handle pause/resume button click."""
        if hasattr(self, "session_controller"):
            self.session_controller.toggle_pause()

    def _update_path_entry_border(self, color: str = None) -> None:
        """Update path entry border color based on modification state or directly."""
        self.prompt_io._update_path_entry_border(color)

    # --- Backward-compatibility forwarders for tests & builders ---
    def _update_preview(self, text: str) -> None:
        """Backward-compatibility: forward to prompt_io._update_preview."""
        self.prompt_io._update_preview(text)

    def _load_prompts_from_multiple_files(self, path_input: str) -> bool:
        """Backward-compatibility: forward to
        prompt_io._load_prompts_from_multiple_files."""
        return self.prompt_io._load_prompts_from_multiple_files(path_input)

    def _load_prompts_from_file(self, file_path: str) -> bool:
        """Backward-compatibility: forward to prompt_io._load_prompts_from_file."""
        return self.prompt_io._load_prompts_from_file(file_path)

    @property
    def _current_file_path(self) -> str:
        """Backward-compatibility: expose current file path."""
        return self.prompt_io.get_current_file_path()

    @property
    def _prompts_modified(self) -> bool:
        """Backward-compatibility: expose prompts modified state."""
        return self.prompt_io.is_prompts_modified()
