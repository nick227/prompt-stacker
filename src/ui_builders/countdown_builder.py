"""
Countdown Area Builder

This module provides the builder for the countdown area of the automation system UI,
including timer display and progress bar.
"""

import customtkinter as ctk

try:
    from ..config import (
        COLOR_ACCENT,
        COLOR_SURFACE,
        COLOR_SURFACE_ALT,
        COLOR_TEXT_MUTED,
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
        COLOR_ACCENT,
        COLOR_SURFACE,
        COLOR_SURFACE_ALT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
        FONT_H2,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
    )
    from ui_builders.base_builder import BaseUIBuilder


class CountdownBuilder(BaseUIBuilder):
    """
    Builder for the countdown area of the UI.

    Handles the construction of timer display and progress bar.
    """

    def build_countdown_section(self) -> None:
        """Build the countdown section with timer display and progress bar."""
        # Countdown frame
        self.ui.countdown_frame = ctk.CTkFrame(
            self.ui.main_container,
            fg_color=COLOR_SURFACE,
            corner_radius=SECTION_RADIUS,
        )
        self.ui.countdown_frame.pack(fill="x", padx=PADDING, pady=(GUTTER, GUTTER // 2))

        # Countdown header
        self._build_countdown_header()

        # Progress bar
        self._build_progress_bar()

        # Add some bottom padding to ensure visibility
        bottom_padding = ctk.CTkFrame(
            self.ui.countdown_frame,
            fg_color="transparent",
            height=8,
        )
        bottom_padding.pack(fill="x", pady=(0, PADDING))

    def _build_countdown_header(self) -> None:
        """Build the countdown header."""
        header_frame = ctk.CTkFrame(self.ui.countdown_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=PADDING, pady=(PADDING, GUTTER))

        # Time label with better styling and spacing
        time_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        time_frame.pack(side="left")

        # Label with better spacing
        ctk.CTkLabel(
            time_frame,
            text="Time Remaining:",
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 4))

        # Time display with larger, more prominent styling
        self.ui.time_label = ctk.CTkLabel(
            time_frame,
            text="0",
            font=("Segoe UI Variable", 32, "bold"),  # Larger font for better visibility
            text_color=COLOR_ACCENT,
        )
        self.ui.time_label.pack(anchor="w")

        # Status label with better positioning and styling
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.pack(side="right", fill="x", expand=True)

        self.ui.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready to Start Automation!",
            font=FONT_H2,
            text_color=COLOR_TEXT_MUTED,
            anchor="e",
        )
        self.ui.status_label.pack(side="right", pady=(0, 4))

    def _build_progress_bar(self) -> None:
        """Build the progress bar."""
        # Progress bar container for better styling
        progress_container = ctk.CTkFrame(
            self.ui.countdown_frame,
            fg_color="transparent",
        )
        progress_container.pack(fill="x", padx=PADDING, pady=(0, PADDING))

        # Progress bar with improved styling - thicker and more prominent
        self.ui.progress = ctk.CTkProgressBar(
            progress_container,
            progress_color=COLOR_ACCENT,
            fg_color=COLOR_SURFACE_ALT,
            height=16,  # Thicker for better visibility
            corner_radius=8,  # More rounded corners
        )
        self.ui.progress.pack(fill="x", pady=(GUTTER, 0))
        self.ui.progress.set(0.0)
