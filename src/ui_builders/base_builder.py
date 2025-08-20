"""
Base UI Builder

This module provides the base class for all UI builders in the automation system.
"""

from typing import Any

import customtkinter as ctk

try:
    from ..config import (
        COLOR_TEXT,
        FONT_BODY,
        FONT_H1,
        FONT_H2,
        GUTTER,
        PADDING,
    )
except ImportError:
    # Fallback values if config is not available
    COLOR_TEXT = "#FFFFFF"
    FONT_BODY = ("Segoe UI", 10)
    FONT_H1 = ("Segoe UI", 16, "bold")
    FONT_H2 = ("Segoe UI", 14, "bold")
    GUTTER = 20
    PADDING = 10


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
