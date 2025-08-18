"""
Base UI Builder

This module provides the base class for all UI builders in the automation system.
"""

from typing import Any

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
        FONT_H2,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
        WINDOW_MARGIN,
    )
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
        FONT_H2,
        GUTTER,
        PADDING,
        SECTION_RADIUS,
        WINDOW_MARGIN,
    )


class BaseUIBuilder:
    """
    Base class for UI builders.

    Provides common functionality and access to the main UI instance
    for building different sections of the interface.
    """

    def __init__(self, ui_instance: Any):
        """
        Initialize the base builder.

        Args:
            ui_instance: Reference to the main UI instance
        """
        self.ui = ui_instance
        self.window = ui_instance.window if hasattr(ui_instance, "window") else None

    def _section_title(self, parent: ctk.CTkFrame, text: str) -> None:
        """
        Create a section title.

        Args:
            parent: Parent widget
            text: Title text
        """
        ctk.CTkLabel(
            parent,
            text=text,
            font=FONT_H2,
            text_color=COLOR_TEXT,
        ).pack(anchor="w")
