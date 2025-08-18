"""
Configuration Area Builder

This module provides the builder for the configuration area of the automation system UI,
including targets (coordinates) and timers sections.
"""

import customtkinter as ctk

try:
    from ..config import (
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_TEXT,
        COLOR_BG,
        COLOR_BORDER,
        COLOR_ERROR,
        COLOR_SUCCESS,
        COLOR_SURFACE,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        FONT_H1,
        GUTTER,
        LABELS,
        PADDING,
        SECTION_RADIUS,
        TARGET_KEYS,
        WINDOW_MARGIN,
    )
    from .base_builder import BaseUIBuilder
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path

    # Add src directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from config import (
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_TEXT,
        COLOR_BG,
        COLOR_BORDER,
        COLOR_ERROR,
        COLOR_SUCCESS,
        COLOR_SURFACE,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        FONT_H1,
        GUTTER,
        LABELS,
        PADDING,
        SECTION_RADIUS,
        TARGET_KEYS,
        WINDOW_MARGIN,
    )
    from ui_builders.base_builder import BaseUIBuilder


class ConfigurationBuilder(BaseUIBuilder):
    """
    Builder for the configuration area of the UI.

    Handles the construction of targets and timers sections.
    """

    def build_configuration_area(self, parent: ctk.CTkFrame) -> None:
        """Build the configuration area."""
        # Create configuration container
        self.ui.config_container = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        self.ui.config_container.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=PADDING,
            pady=(10, PADDING),
        )

        # Build prompt path section
        self._build_prompt_path_section(self.ui.config_container)

        # Build targets and timers section
        self._build_targets_timers_section(self.ui.config_container)

    def _build_prompt_path_section(self, parent: ctk.CTkFrame) -> None:
        """Build the prompt path input section."""
        # No title - removed as requested

        # Initialize config service for path preferences
        try:
            from ..config_service import ConfigService
        except ImportError:
            from config_service import ConfigService
        self.ui.config_service = ConfigService()

        # Path input frame
        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x", pady=(2, 0))

        # Path entry
        self.ui.path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.ui.prompt_path_var,
            placeholder_text="Enter path(s) separated by semicolons (;)",
            border_color=COLOR_BORDER,
        )
        self.ui.path_entry.pack(side="left", fill="x", expand=True, padx=(0, GUTTER))

        # Bind path change event for real-time validation
        self.ui.prompt_path_var.trace_add("write", self._on_path_changed)

        # Info icon button
        self.ui.info_btn = ctk.CTkButton(
            path_frame,
            text="ℹ",
            width=30,
            height=30,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            font=("Segoe UI", 14, "bold"),
            command=self._show_info_dialog,
        )
        self.ui.info_btn.pack(side="right", padx=(GUTTER, 0))

        # Browse file button (standard styling)
        self.ui.browse_file_btn = ctk.CTkButton(
            path_frame,
            text="Browse Files",
            width=80,
            height=30,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            font=FONT_BODY,
            command=self.ui._browse_prompt_file,
        )
        self.ui.browse_file_btn.pack(side="right", padx=(GUTTER, 0))

    def _show_info_dialog(self) -> None:
        """Show information dialog about the app and prompt list formats."""
        # Create dialog window
        dialog = ctk.CTkToplevel(self.ui.window)
        dialog.title("Prompt Stacker - Information")
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLOR_BG)

        # Make dialog modal
        dialog.transient(self.ui.window)
        dialog.grab_set()

        # Center dialog on parent window
        dialog.update_idletasks()
        x = self.ui.window.winfo_x() + (self.ui.window.winfo_width() // 2) - (600 // 2)
        y = self.ui.window.winfo_y() + (self.ui.window.winfo_height() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")

        # Main container
        main_frame = ctk.CTkFrame(
            dialog,
            fg_color=COLOR_SURFACE,
            corner_radius=CARD_RADIUS,
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Prompt Stacker - Automation Tool",
            font=FONT_H1,
            text_color=COLOR_TEXT,
        )
        title_label.pack(pady=(20, 10))

        # Scrollable text area
        text_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # Create text widget with scrollbar
        text_widget = ctk.CTkTextbox(
            text_frame,
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            fg_color="transparent",
            wrap="word",
        )
        text_widget.pack(fill="both", expand=True)

        # Information content
        info_text = """
Welcome to Prompt Stacker!

This automation tool helps you automate repetitive text input tasks by cycling through a list of prompts and automatically pasting them into target applications.

HOW TO USE:
1. Set up your target coordinates by clicking "Capture" buttons
2. Configure your timing preferences
3. Load or create a prompt list file
4. Click "Start" to begin automation

PROMPT LIST FILE FORMATS:

Python Files (.py):
• Create a Python file with a list variable
• Example:
  prompt_list = [
      "Your first prompt here",
      "Your second prompt here",
      "Your third prompt here"
  ]
• Variable name can be anything (prompt_list, prompts, etc.)

Text Files (.txt):
• One prompt per line
• Example:
  First prompt
  Second prompt
  Third prompt

CSV Files (.csv):
• Comma-separated values
• Example:
  "First prompt","Second prompt","Third prompt"

CREATING YOUR OWN PROMPT FILES:
• Use the "Browse Files" button to select one or more existing files
• Multiple files can be selected and will be combined into one prompt list
• File paths are separated by semicolons (;) in the input field
• Create new files in the prompt_lists/ directory
• The app will automatically load prompt_list.py on startup
• You can edit prompts directly in the app using the prompt list editor

AUTOMATION CONTROLS:
• Start/Stop: Begin or end automation
• Pause/Resume: Temporarily stop automation
• Next: Immediately start next prompt automation (when running)

TIPS:
• Test your coordinates before starting automation
• Use the prompt list editor to modify prompts on the fly
• Save your coordinate settings for future use
• The app remembers your last used prompt file
• Toggle settings panel with the ⚙ button or Ctrl+S for more prompt list space
        """

        # Insert text
        text_widget.insert("1.0", info_text)
        text_widget.configure(state="disabled")  # Make read-only

        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            width=100,
            height=35,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            font=FONT_BODY,
            command=dialog.destroy,
        )
        close_btn.pack(pady=(0, 20))

        # Focus on dialog
        dialog.focus_set()

    def _on_path_changed(self, *_args) -> None:
        """Handle path input changes for real-time validation."""
        path_input = self.ui.prompt_path_var.get().strip()

        # If path is empty, show default border and load default prompts
        if not path_input:
            self.ui._update_path_entry_border(COLOR_BORDER)  # Default border color
            # Load default prompts without setting a path
            self.ui._load_default_prompts()
            return

        # Path has content, validate it (support multiple files)
        try:
            # Check if this is a multiple file path (contains semicolon)
            if ";" in path_input:
                # Use the multiple file loading method
                success = self.ui._load_prompts_from_multiple_files(path_input)
                if success:
                    self.ui._update_path_entry_border(COLOR_SUCCESS)
                else:
                    self.ui._update_path_entry_border(COLOR_ERROR)
            else:
                # Single file validation
                success, result = self.ui.file_service.parse_prompt_list(path_input)

                if success and isinstance(result, list):
                    self.ui.prompts = result
                    self.ui.prompt_count = len(result)
                    self.ui.current_prompt_index = 0

                    # Update inline prompt editor service
                    if hasattr(self.ui, "prompt_list_service"):
                        self.ui.prompt_list_service.set_prompts(result)

                    # Update UI with success border color
                    self.ui._update_path_entry_border(COLOR_SUCCESS)
                    self.ui._update_preview(result[0] if result else "")

                else:
                    self.ui._update_path_entry_border(COLOR_ERROR)
                    self.ui._update_preview("")

        except Exception:
            self.ui._update_path_entry_border(COLOR_ERROR)
            self.ui._update_preview("")

    def _build_targets_timers_section(self, parent: ctk.CTkFrame) -> None:
        """Build the targets and timers section."""
        # No title - removed as requested

        # Targets frame
        targets_frame = ctk.CTkFrame(parent, fg_color="transparent")
        targets_frame.pack(fill="x", pady=(10, 5))

        # Build target buttons
        for key in TARGET_KEYS:
            self._build_compact_target_row(targets_frame, key)

        # Timers frame
        timers_frame = ctk.CTkFrame(parent, fg_color="transparent")
        timers_frame.pack(fill="x", pady=(5, 0))

        # Build timer inputs
        self._build_compact_timers_section(timers_frame)

    def _build_compact_target_row(self, parent: ctk.CTkFrame, key: str) -> None:
        """Build a compact target row."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=1)

        # Configure grid columns for proper alignment
        row_frame.grid_columnconfigure(0, weight=0)  # Label (fixed width)
        row_frame.grid_columnconfigure(1, weight=0)  # Coordinates (fixed width)
        row_frame.grid_columnconfigure(2, weight=1)  # Spacer (expands)
        row_frame.grid_columnconfigure(3, weight=0)  # Button (fixed width)

        # Label
        label = ctk.CTkLabel(
            row_frame,
            text=LABELS[key],
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            width=60,
            anchor="w",
        )
        label.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")

        # Coordinate display
        coord_label = ctk.CTkLabel(
            row_frame,
            text=self.ui.coordinate_service.get_coordinate_text(key),
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
            width=70,
        )
        coord_label.grid(row=0, column=1, padx=(0, 5), pady=2, sticky="w")

        # Capture button (standard styling) - properly aligned
        capture_btn = ctk.CTkButton(
            row_frame,
            text="Capture",
            width=70,
            height=30,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            font=FONT_BODY,
            command=lambda k=key: self.ui._start_capture(k),
        )
        capture_btn.grid(row=0, column=3, padx=(0, 0), pady=2, sticky="e")

        # Store references
        setattr(self.ui, f"{key}_coord_label", coord_label)
        setattr(self.ui, f"{key}_capture_btn", capture_btn)

    def _build_compact_timers_section(self, parent: ctk.CTkFrame) -> None:
        """Build the compact timers section."""
        # Create timer entries (removed Start Delay and Cooldown)
        self._create_timer_entry(parent, "Main Wait", self.ui.main_wait_var)
        self._create_timer_entry(parent, "Get Ready", self.ui.get_ready_delay_var)

    def _create_timer_entry(
        self,
        parent: ctk.CTkFrame,
        label: str,
        var: ctk.StringVar,
    ) -> None:
        """Create a timer entry field."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=1)

        # Configure grid columns for proper alignment (exactly like capture buttons)
        row_frame.grid_columnconfigure(0, weight=0)  # Label (fixed width)
        row_frame.grid_columnconfigure(1, weight=1)  # Spacer (expands)
        row_frame.grid_columnconfigure(2, weight=0)  # Entry (fixed width)

        # Label
        ctk.CTkLabel(
            row_frame,
            text=label,
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            width=60,
            anchor="w",
        ).grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")

        # Entry
        ctk.CTkEntry(
            row_frame,
            textvariable=var,
            width=80,
            placeholder_text="0",
        ).grid(row=0, column=2, padx=(0, 0), pady=2, sticky="e")
