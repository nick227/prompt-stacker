"""
Prompt List Area Builder

This module provides the builder for the prompt list area of the automation system UI,
including the prompt list container and frame.
"""

import customtkinter as ctk

try:
    from ..config import (
        PADDING,
    )
    from .base_builder import BaseUIBuilder
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path

    # Add src directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from config import (
        PADDING,
    )
    from ui_builders.base_builder import BaseUIBuilder


class PromptListBuilder(BaseUIBuilder):
    """
    Builder for the prompt list area of the UI.

    Handles the construction of the prompt list container and frame.
    """

    def build_prompt_list_area(self, parent: ctk.CTkFrame) -> None:
        """Build the prompt list area."""
        # Create prompt list container (no padding for top alignment)
        self.ui.prompt_list_container = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        self.ui.prompt_list_container.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(5, PADDING),
            pady=(0, PADDING),
        )

        # No title - removed as requested

        # Inline prompt editor service will be initialized here after UI is built
        self.ui.prompt_list_frame = ctk.CTkFrame(
            self.ui.prompt_list_container,
            fg_color="transparent",
        )
        self.ui.prompt_list_frame.pack(fill="both", expand=True, pady=(0, 0))
