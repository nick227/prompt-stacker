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
        CARD_RADIUS,
        COLOR_BG,
        COLOR_BORDER,
        COLOR_ERROR,
        COLOR_SUCCESS,
        COLOR_SURFACE,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        FONT_H1,
        FONT_H2,
        GUTTER,
        LABELS,
        PADDING,
        TARGET_KEYS,
    )
    from .base_builder import BaseUIBuilder
except ImportError:
    # Fallback values if config is not available
    BUTTON_BG = "#2B2B2B"
    BUTTON_HOVER = "#3B3B3B"
    BUTTON_TEXT = "#FFFFFF"
    CARD_RADIUS = 8
    COLOR_BG = "#1E1E1E"
    COLOR_BORDER = "#404040"
    COLOR_ERROR = "#FF4444"
    COLOR_SUCCESS = "#44FF44"
    COLOR_SURFACE = "#2B2B2B"
    COLOR_TEXT = "#FFFFFF"
    COLOR_TEXT_MUTED = "#888888"
    FONT_BODY = ("Segoe UI", 10)
    FONT_H1 = ("Segoe UI", 16, "bold")
    FONT_H2 = ("Segoe UI", 14, "bold")
    GUTTER = 20
    LABELS = {}
    PADDING = 10
    TARGET_KEYS = []

    # Fallback for BaseUIBuilder import
    try:
        from .base_builder import BaseUIBuilder
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from base_builder import BaseUIBuilder


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
            padx=(0, 0),
            pady=(0, PADDING),
        )

        # Build targets and timers section
        self._build_targets_timers_section(self.ui.config_container)





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
