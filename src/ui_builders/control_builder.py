"""
Control Area Builder

This module provides the builder for the control area of the automation system UI,
including start, stop, pause, and next buttons.
"""

import customtkinter as ctk

try:
    from ..config import (
        BTN_CANCEL,
        BTN_NEXT,
        BTN_PAUSE,
        BTN_START,
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_START_ACTIVE,
        BUTTON_START_ACTIVE_HOVER,
        BUTTON_TEXT,
        BUTTON_WIDTH,
        COLOR_ACCENT,
        COLOR_SURFACE,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
        WHITE_COLOR_TEXT,
    )
    from .base_builder import BaseUIBuilder
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path

    # Add src directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from config import (
        BTN_CANCEL,
        BTN_NEXT,
        BTN_PAUSE,
        BTN_START,
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_START_ACTIVE,
        BUTTON_START_ACTIVE_HOVER,
        BUTTON_TEXT,
        BUTTON_WIDTH,
        COLOR_ACCENT,
        COLOR_SURFACE,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
        WHITE_COLOR_TEXT,
    )
    from ui_builders.base_builder import BaseUIBuilder


class ControlBuilder(BaseUIBuilder):
    """
    Builder for the control area of the UI.

    Handles the construction of control buttons (start, stop, pause, next).
    """

    def build_control_section(self, parent=None) -> None:
        """Build the control section with all control buttons."""
        # Use provided parent or fall back to main_container
        if parent is None:
            parent = self.ui.main_container

        # Control frame
        self.ui.control_frame = ctk.CTkFrame(
            parent,
            fg_color=COLOR_SURFACE,
            corner_radius=SECTION_RADIUS,
        )
        self.ui.control_frame.pack(fill="x", padx=PADDING, pady=(GUTTER // 2, GUTTER))

        # Control buttons frame
        buttons_frame = ctk.CTkFrame(self.ui.control_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=PADDING, pady=PADDING)

        # Build control buttons
        self._build_control_buttons(buttons_frame)

    def _build_control_buttons(self, parent: ctk.CTkFrame) -> None:
        """Build the control buttons with integrated countdown timer."""
        # Left side: Control buttons
        buttons_left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_left_frame.pack(side="left", fill="x", expand=True)

        # Special Start/Stop button
        self.ui.start_btn = ctk.CTkButton(
            buttons_left_frame,
            text=BTN_START,
            width=BUTTON_WIDTH,
            height=36,
            corner_radius=8,
            fg_color=BUTTON_START_ACTIVE,
            hover_color=BUTTON_START_ACTIVE_HOVER,
            text_color=WHITE_COLOR_TEXT,
            font=FONT_BODY,
            command=self.ui._on_start,
        )
        self.ui.start_btn.pack(side="left", padx=(0, GUTTER // 2))

        # Standard Cancel button (dark gray with green hover)
        self.ui.cancel_btn = ctk.CTkButton(
            buttons_left_frame,
            text=BTN_CANCEL,
            width=BUTTON_WIDTH,
            height=36,
            corner_radius=8,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            font=FONT_BODY,
            command=self.ui._on_cancel,
        )
        self.ui.cancel_btn.pack(side="left", padx=(0, GUTTER // 2))

        # Standard Pause button (dark gray with green hover)
        self.ui.pause_btn = ctk.CTkButton(
            buttons_left_frame,
            text=BTN_PAUSE,
            width=BUTTON_WIDTH,
            height=36,
            corner_radius=8,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            font=FONT_BODY,
            command=self.ui._toggle_pause,
        )
        self.ui.pause_btn.pack(side="left", padx=(0, GUTTER // 2))

        # Standard Next button (dark gray with green hover)
        self.ui.next_btn = ctk.CTkButton(
            buttons_left_frame,
            text=BTN_NEXT,
            width=BUTTON_WIDTH,
            height=36,
            corner_radius=8,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            font=FONT_BODY,
            command=self.ui._on_next,
        )
        self.ui.next_btn.pack(side="left", padx=(0, GUTTER // 2))

        # Right side: Countdown timer only
        countdown_frame = ctk.CTkFrame(parent, fg_color="transparent")
        countdown_frame.pack(side="right", padx=(GUTTER, 0))

        # Countdown timer with seconds label
        timer_frame = ctk.CTkFrame(countdown_frame, fg_color="transparent")
        timer_frame.pack(side="bottom", anchor="e")

        # SIMPLE FIX: Create a compact timer display for control section
        # This avoids conflicts with the main countdown display
        self.ui.control_timer_label = ctk.CTkLabel(
            timer_frame,
            text="0",
            font=("Segoe UI Variable", 20, "bold"),
            text_color=COLOR_ACCENT,
        )
        self.ui.control_timer_label.pack(side="left")

        # Seconds label
        ctk.CTkLabel(
            timer_frame,
            text="s",
            font=("Segoe UI Variable", 16, "bold"),
            text_color=COLOR_TEXT_MUTED,
        ).pack(side="left", padx=(2, 0))
