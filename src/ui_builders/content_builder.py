"""
Content Area Builder

This module provides the builder for the content area of the automation system UI,
including current and next prompt display boxes.
"""

import customtkinter as ctk

try:
    from ..config import (
        COLOR_SURFACE,
        COLOR_SURFACE_ALT,
        COLOR_TEXT,
        FONT_BODY,
        FONT_H2,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
    )
    from .base_builder import BaseUIBuilder
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path

    # Add src directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from config import (
        COLOR_SURFACE,
        COLOR_SURFACE_ALT,
        COLOR_TEXT,
        FONT_BODY,
        FONT_H2,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
    )
    from ui_builders.base_builder import BaseUIBuilder


class ContentBuilder(BaseUIBuilder):
    """
    Builder for the content area of the UI.

    Handles the construction of current and next prompt display boxes.
    """

    def build_content_area(self, parent=None) -> None:
        """Build the content area with current and next prompt boxes."""
        # Use provided parent or fall back to main_container
        if parent is None:
            parent = self.ui.main_container

        # Content frame
        self.ui.content_frame = ctk.CTkFrame(
            parent,
            fg_color=COLOR_SURFACE,
            corner_radius=SECTION_RADIUS,
        )
        self.ui.content_frame.pack(
            fill="both",
            expand=True,
            padx=0,
            pady=(10, PADDING),
        )

        # Content grid
        content_grid = ctk.CTkFrame(self.ui.content_frame, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=PADDING, pady=PADDING)

        # Build current prompt box
        self._build_current_prompt_box(content_grid)

        # Build next prompt box
        self._build_next_prompt_box(content_grid)

        # Configure grid weights
        content_grid.grid_columnconfigure(0, weight=1)
        content_grid.grid_columnconfigure(1, weight=1)
        content_grid.grid_rowconfigure(0, weight=1)

    def _build_current_prompt_box(self, parent: ctk.CTkFrame) -> None:
        """Build the current prompt display box."""
        # Current prompt frame
        current_frame = ctk.CTkFrame(parent, fg_color="transparent")
        current_frame.grid(row=0, column=0, sticky="nsew", padx=(0, GUTTER // 2))

        # Current prompt header
        current_header = ctk.CTkFrame(current_frame, fg_color="transparent")
        current_header.pack(fill="x", pady=(0, GUTTER // 2))

        ctk.CTkLabel(
            current_header,
            text="Current Prompt:",
            font=FONT_H2,
            text_color=COLOR_TEXT,
        ).pack(side="left")

        # Current prompt box with better styling
        self.ui.current_box = ctk.CTkTextbox(
            current_frame,
            height=40,
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            fg_color=COLOR_SURFACE_ALT,
            corner_radius=8,
        )
        self.ui.current_box.pack(fill="both", expand=True)

    def _build_next_prompt_box(self, parent: ctk.CTkFrame) -> None:
        """Build the next prompt display box."""
        # Next prompt frame
        next_frame = ctk.CTkFrame(parent, fg_color="transparent")
        next_frame.grid(row=0, column=1, sticky="nsew", padx=(GUTTER // 2, 0))

        # Next prompt header
        next_header = ctk.CTkFrame(next_frame, fg_color="transparent")
        next_header.pack(fill="x", pady=(0, GUTTER // 2))

        ctk.CTkLabel(
            next_header,
            text="Next Prompt:",
            font=FONT_H2,
            text_color=COLOR_TEXT,
        ).pack(side="left")

        # Next prompt box with better styling
        self.ui.next_box = ctk.CTkTextbox(
            next_frame,
            height=40,
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            fg_color=COLOR_SURFACE_ALT,
            corner_radius=8,
        )
        self.ui.next_box.pack(fill="both", expand=True)
