"""
Inline Prompt Editor Service

This module provides inline prompt editing functionality for the main
automation dialog.
Allows users to edit prompts directly in the prompt list with real-time
updates and throttling.

Author: Automation System
Version: 1.0
"""

import threading
import tkinter
from typing import Callable, Dict, List, Optional

import customtkinter as ctk

try:
    from .config import (
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_TEXT,
        COLOR_ACCENT,
        COLOR_ERROR,
        COLOR_SURFACE,
        COLOR_SURFACE_ALT,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
    )
    from .memory_pool import get_dict, get_list, return_dict, return_list
    from .performance_profiler import profile
except ImportError:
    # Fallback for when running as script
    from config import (
        BUTTON_BG,
        BUTTON_HOVER,
        BUTTON_TEXT,
        COLOR_ACCENT,
        COLOR_ERROR,
        COLOR_SURFACE,
        COLOR_SURFACE_ALT,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        FONT_BODY,
    )

    try:
        from memory_pool import get_dict, get_list, return_dict, return_list
        from performance_profiler import profile
    except ImportError:
        # Fallback if memory pool is not available
        get_list = list
        def return_list(x): pass
        get_dict = dict
        def return_dict(x): pass
        def profile(func_name=None):
            def decorator(f):
                return f
            return decorator

    # Fallback values if config is not available
    PROMPT_STATE_CURRENT = "current"
    PROMPT_STATE_NORMAL = "normal"

    def get_prompt_row_colors(state):
        if state == "current":  # Use string literal instead of constant
            return "#2B2B2B", "#FFFFFF"
        return "#1E1E1E", "#CCCCCC"

# =============================================================================
# INLINE PROMPT EDITOR SERVICE
# =============================================================================


class InlinePromptEditorService:
    """
    Service for inline prompt editing in the main dialog.

    Provides real-time editing capabilities with:
    - Inline text input fields
    - Throttled updates (1 second delay)
    - Clickable navigation
    - Visual state management
    - Real-time prompt list updates
    """

    def __init__(
        self,
        parent_widget: ctk.CTkFrame,
        on_prompt_click: Optional[Callable[[int], None]] = None,
        on_prompts_changed: Optional[Callable[[List[str]], None]] = None,
    ):
        """
        Initialize the inline prompt editor service.

        Args:
            parent_widget: Parent widget to contain the prompt list
            on_prompt_click: Callback function when a prompt is clicked
            on_prompts_changed: Callback function when prompts are modified
        """
        self.parent = parent_widget
        self.on_prompt_click = on_prompt_click
        self.on_prompts_changed = on_prompts_changed

        # Prompt data
        self.prompts: List[str] = get_list()  # Use memory pool
        self.current_prompt_index = 0
        self.prompt_count = 0

        # UI components
        self.prompt_frame: Optional[ctk.CTkScrollableFrame] = None
        self.prompt_rows: Dict[int, ctk.CTkFrame] = get_dict()  # Use memory pool
        self.prompt_labels: Dict[int, ctk.CTkLabel] = get_dict()  # Use memory pool
        self.prompt_entries: Dict[int, ctk.CTkEntry] = get_dict()  # Use memory pool

        # Editing state
        self.is_automation_running = False
        self.editing_index: Optional[int] = None
        self.throttle_timer: Optional[threading.Timer] = None
        self.last_edit_time = 0
        self.throttle_delay = 1.0  # 1 second throttle

        # New prompt state management
        self.new_prompt_index: Optional[int] = None
        self.is_processing_deletion = False

        # Build UI
        self._build_prompt_list_ui()

    def _build_prompt_list_ui(self) -> None:
        """Build the prompt list UI components."""
        # Create toolbar frame
        self.toolbar_frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent",
            height=40,
        )
        self.toolbar_frame.pack(fill="x", padx=2, pady=(2, 0))

        # Add prompt button
        self.add_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="+ Add Prompt",
            width=100,
            height=30,
            font=FONT_BODY,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
            command=self._add_new_prompt,
        )
        self.add_btn.pack(side="left", padx=(0, 0))

        # Prompt count label
        self.count_label = ctk.CTkLabel(
            self.toolbar_frame,
            text="0 prompts",
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
        )
        self.count_label.pack(side="right")

        # Create scrollable frame for prompts
        self.prompt_frame = ctk.CTkScrollableFrame(
            self.parent,
            height=200,
            fg_color="transparent",
        )
        self.prompt_frame.pack(fill="both", expand=True, padx=2, pady=2)

    @profile("set_prompts")
    def set_prompts(self, prompts: List[str]) -> None:
        """
        Set the list of prompts to display.

        Args:
            prompts: List of prompt strings
        """
        # Return current prompts list to pool if it's from the pool
        if hasattr(self, "prompts") and self.prompts:
            return_list(self.prompts)

        # Use memory pool for new prompts list
        self.prompts = get_list()
        self.prompts.extend(prompts)  # Add prompts to pooled list
        self.prompt_count = len(prompts)

        # Preserve current prompt index if it's still valid, otherwise reset to 0
        if self.current_prompt_index >= len(prompts):
            self.current_prompt_index = 0

        # Clear existing rows
        self._clear_prompt_list()

        # Build new prompt rows
        if prompts:
            self._build_dynamic_prompt_list()

        # Update count label
        self._update_count_label()

    def _add_new_prompt(self) -> None:
        """Add a new empty prompt to the list."""
        new_prompt = "New prompt"
        self.add_prompt(new_prompt)

        # Update count label
        self._update_count_label()

        # Focus on the new prompt entry and mark it as new
        if self.prompt_count > 0:
            new_index = self.prompt_count - 1
            self.new_prompt_index = new_index
            if new_index in self.prompt_entries:
                self.prompt_entries[new_index].focus_set()
                self.prompt_entries[new_index].select_range(0, len(new_prompt))

    def _update_count_label(self) -> None:
        """Update the prompt count label."""
        if hasattr(self, "count_label"):
            count = len(self.prompts)
            if count == 1:
                self.count_label.configure(text="1 prompt")
            else:
                self.count_label.configure(text=f"{count} prompts")

    @profile("clear_prompt_list")
    def _clear_prompt_list(self) -> None:
        """Clear all prompt rows from the UI."""
        # Properly destroy all widgets to prevent memory leaks
        for row in self.prompt_rows.values():
            try:
                row.destroy()
            except (AttributeError, tkinter.TclError):
                pass

        # Return dictionaries to memory pool instead of clearing
        return_dict(self.prompt_rows)
        return_dict(self.prompt_labels)
        return_dict(self.prompt_entries)

        # Get fresh dictionaries from pool
        self.prompt_rows = get_dict()
        self.prompt_labels = get_dict()
        self.prompt_entries = get_dict()

        # Force garbage collection for widget cleanup
        import gc

        gc.collect()

    @profile("build_dynamic_prompt_list")
    def _build_dynamic_prompt_list(self) -> None:
        """Build the dynamic prompt list UI."""
        if not self.prompts or not self.prompt_frame:
            return

        for index, prompt in enumerate(self.prompts):
            self._create_prompt_row(index, prompt)

    def _create_prompt_row(self, index: int, prompt: str) -> None:
        """
        Create a single prompt row with inline editing capability.

        Args:
            index: Prompt index
            prompt: Prompt text
        """
        if not self.prompt_frame:
            return

        # Create row frame
        row = ctk.CTkFrame(
            self.prompt_frame,
            fg_color=COLOR_SURFACE,
            corner_radius=6,
            height=40,
        )
        row.pack(fill="x", padx=2, pady=1)

        # Create number label
        number_label = ctk.CTkLabel(
            row,
            text=f"{index + 1}",
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            width=30,
        )
        number_label.pack(side="left", padx=(10, 5))

        # Create editable text entry
        entry = ctk.CTkEntry(
            row,
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            fg_color=COLOR_SURFACE_ALT,
            border_width=1,
            border_color=COLOR_TEXT_MUTED,
            height=30,
        )

        # Set the initial value
        entry.insert(0, prompt)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Create action buttons frame
        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.pack(side="right", padx=(0, 10))

        # Move up button (only if not first)
        if index > 0:
            up_btn = ctk.CTkButton(
                action_frame,
                text="↑",
                width=25,
                height=25,
                font=FONT_BODY,
                fg_color=COLOR_SURFACE_ALT,
                hover_color=COLOR_ACCENT,
                command=lambda idx=index: self.move_prompt_up(idx),
            )
            up_btn.pack(side="left", padx=(0, 2))

        # Move down button (only if not last)
        if index < len(self.prompts) - 1:
            down_btn = ctk.CTkButton(
                action_frame,
                text="↓",
                width=25,
                height=25,
                font=FONT_BODY,
                fg_color=COLOR_SURFACE_ALT,
                hover_color=COLOR_ACCENT,
                command=lambda idx=index: self.move_prompt_down(idx),
            )
            down_btn.pack(side="left", padx=(0, 2))

        # Delete button
        delete_btn = ctk.CTkButton(
            action_frame,
            text="×",
            width=25,
            height=25,
            font=FONT_BODY,
            fg_color=COLOR_ERROR,
            hover_color="#D32F2F",
            command=lambda idx=index: self.remove_prompt(idx),
        )
        delete_btn.pack(side="left", padx=(0, 2))

        # Store references
        self.prompt_rows[index] = row
        self.prompt_labels[index] = number_label
        self.prompt_entries[index] = entry

        # Bind events
        self._bind_row_events(row, entry, index)

        # Apply initial styling
        self._apply_row_highlighting(index)

    def _bind_row_events(
        self,
        row: ctk.CTkFrame,
        entry: ctk.CTkEntry,
        index: int,
    ) -> None:
        """
        Bind events to a prompt row and entry.

        Args:
            row: The row frame
            entry: The text entry widget
            index: Prompt index
        """
        # Click event for navigation (but not on the entry itself)
        row.bind("<Button-1>", lambda e, idx=index: self._on_prompt_row_click(idx))
        self.prompt_labels[index].bind(
            "<Button-1>",
            lambda e, idx=index: self._on_prompt_row_click(idx),
        )

        # Entry events for editing
        entry.bind(
            "<KeyRelease>",
            lambda e, idx=index: self._on_prompt_text_changed(idx),
        )
        entry.bind("<FocusIn>", lambda _e, idx=index: self._on_entry_focus_in(idx))
        entry.bind("<FocusOut>", lambda _e, idx=index: self._on_entry_focus_out(idx))
        entry.bind("<Return>", lambda _e, idx=index: self._on_entry_return(idx))
        entry.bind("<Escape>", lambda _e, idx=index: self._on_entry_escape(idx))

        # Prevent row click when clicking on entry
        entry.bind("<Button-1>", lambda e: e.widget.focus_set())

    def _on_prompt_row_click(self, target_index: int) -> None:
        """
        Handle click on a prompt row for navigation.

        Args:
            target_index: Target prompt index
        """
        if self.is_automation_running:
            # During automation, clicking jumps to that prompt
            if self.on_prompt_click:
                self.on_prompt_click(target_index)
        else:
            # Outside automation, clicking selects the prompt
            self.set_current_prompt_index(target_index)

    def _on_prompt_text_changed(self, index: int) -> None:
        """
        Handle text changes in prompt entries with throttling.

        Args:
            index: Prompt index
        """
        if index not in self.prompt_entries:
            return

        entry = self.prompt_entries[index]
        new_text = entry.get()

        # Update the prompt in our list
        if index < len(self.prompts):
            self.prompts[index] = new_text

        # Throttle the callback to avoid too many updates
        self._throttle_prompt_update()

    @profile("throttle_prompt_update")
    def _throttle_prompt_update(self) -> None:
        """Throttle prompt updates to avoid excessive callbacks."""
        # Cancel existing timer if it exists and ensure proper cleanup
        if self.throttle_timer:
            self.throttle_timer.cancel()
            try:
                self.throttle_timer.join(timeout=0.1)  # Wait for cleanup with timeout
            except Exception:
                pass  # Ignore join errors
            self.throttle_timer = None

        # Create new timer
        self.throttle_timer = threading.Timer(
            self.throttle_delay,
            self._trigger_prompt_update,
        )
        self.throttle_timer.start()

    def _trigger_prompt_update(self) -> None:
        """Trigger the prompt update callback after throttling."""
        if self.on_prompts_changed:
            self.on_prompts_changed(self.prompts)  # Direct reference - no copy needed

    def _on_entry_focus_in(self, index: int) -> None:
        """
        Handle entry focus in event.

        Args:
            index: Prompt index
        """
        self.editing_index = index
        # Highlight the editing row
        self._apply_editing_highlight(index)

    def _on_entry_focus_out(self, index: int) -> None:
        """
        Handle entry focus out event.

        Args:
            index: Prompt index
        """
        self.editing_index = None

        # Handle new prompt focus out - save and deselect
        if index == self.new_prompt_index:
            self._save_new_prompt(index)

        # Remove editing highlight
        self._apply_row_highlighting(index)

    def _on_entry_return(self, index: int) -> None:
        """
        Handle Return key press in entry.

        Args:
            index: Prompt index
        """
        if index == self.new_prompt_index:
            # Save the new prompt and move focus to next entry or add another
            self._save_new_prompt(index)
            if index + 1 < self.prompt_count:
                # Focus on next entry
                if index + 1 in self.prompt_entries:
                    self.prompt_entries[index + 1].focus_set()
            else:
                # Add another new prompt
                self._add_new_prompt()

    def _on_entry_escape(self, index: int) -> None:
        """
        Handle Escape key press in entry.

        Args:
            index: Prompt index
        """
        if index == self.new_prompt_index:
            # Cancel the new prompt
            self.remove_prompt(index)

    def _apply_editing_highlight(self, index: int) -> None:
        """
        Apply editing highlight to a row.

        Args:
            index: Prompt index
        """
        if index not in self.prompt_rows:
            return

        row = self.prompt_rows[index]
        row.configure(fg_color=COLOR_ACCENT)

        # Update text colors
        if index in self.prompt_labels:
            self.prompt_labels[index].configure(text_color=COLOR_TEXT)
        if index in self.prompt_entries:
            self.prompt_entries[index].configure(text_color=COLOR_TEXT)

    def _apply_row_highlighting(self, index: int) -> None:
        """
        Apply appropriate highlighting to a prompt row.

        Args:
            index: Prompt index
        """
        if index not in self.prompt_rows:
            return

        row = self.prompt_rows[index]

        # Determine the state based on automation status and current index
        is_current_item = (index == self.current_prompt_index)

        # Apply colors based on state
        if self.is_automation_running and is_current_item:
            # Current item during automation - highlight it
            bg_color, text_color = "#2B2B2B", "#FFFFFF"  # Dark gray background, white text
        else:
            # Normal state - all items have transparent/normal styling
            bg_color, text_color = "transparent", "#CCCCCC"  # Transparent background, light gray text

        # Apply the colors
        row.configure(fg_color=bg_color)

        # Update text colors for labels and entries
        if index in self.prompt_labels:
            self.prompt_labels[index].configure(text_color=text_color)
        if index in self.prompt_entries:
            self.prompt_entries[index].configure(text_color=text_color)

    def set_current_prompt_index(self, index: int) -> None:
        """
        Set the current prompt index and update UI accordingly.

        Args:
            index: New current prompt index
        """
        if 0 <= index < len(self.prompts):
            self.current_prompt_index = index
            self._update_prompt_list_ui()

            # CRITICAL FIX: Refresh next prompt display when current index changes
            self.refresh_next_prompt_display()

    def set_automation_running(self, running: bool) -> None:
        """
        Set automation running state and update highlighting.

        Args:
            running: Whether automation is running
        """

        self.is_automation_running = running
        self._update_all_highlighting()

    def _update_all_highlighting(self) -> None:
        """Update highlighting for all prompt rows."""
        for index in range(self.prompt_count):
            self._apply_row_highlighting(index)

    def get_prompts(self) -> List[str]:
        """
        Get the current list of prompts.

        Returns:
            List of prompt strings
        """
        return self.prompts  # Direct return - caller can copy if needed

    def add_prompt(self, prompt: str, index: Optional[int] = None) -> None:
        """
        Add a new prompt to the list with subtle visual update.

        Args:
            prompt: Prompt text to add
            index: Optional index to insert at (None for end)
        """
        if index is None:
            index = len(self.prompts)

        self.prompts.insert(index, prompt)
        self.prompt_count = len(self.prompts)

        # Use consistent rebuild approach for all operations
        self._rebuild_prompt_list_ui()

        # Update count label
        self._update_count_label()

        # Trigger update callback (only if not a new prompt that needs saving)
        if self.on_prompts_changed and prompt != "New prompt":
            self.on_prompts_changed(self.prompts)  # Direct reference - no copy needed

    def get_next_prompt(self) -> Optional[str]:
        """
        Get the next prompt text - delegated to centralized controller.
        """
        # Try to get from centralized controller first
        if hasattr(self, "ui") and hasattr(self.ui, "session_controller"):
            return (self.ui.session_controller.controller._context.get_next_prompt()
                   if self.ui.session_controller.controller._context else None)

        # Fallback to local logic
        if self.current_prompt_index < len(self.prompts) - 1:
            return self.prompts[self.current_prompt_index + 1]
        return None

    def refresh_next_prompt_display(self) -> None:
        """
        Refresh the next prompt display - delegated to centralized controller.
        This should be called when prompts are modified to update the 'Next:' textarea.
        """
        try:
            # Try to use centralized controller first
            if hasattr(self, "ui") and hasattr(self.ui, "session_controller"):
                self.ui.session_controller._update_textareas_for_current_prompt()
                return

            # Fallback to local logic
            next_prompt = self.get_next_prompt()
            if hasattr(self, "next_box") and self.next_box:
                next_text_with_prefix = f"Next: {next_prompt}" if next_prompt else ""
                self.next_box.configure(state="normal")
                self.next_box.delete("1.0", "end")
                self.next_box.insert("end", next_text_with_prefix)
                self.next_box.configure(state="disabled")
        except Exception as e:
            print(f"Error refreshing next prompt display: {e}")

    def remove_prompt(self, index: int) -> None:
        """
        Remove a prompt from the list with robust error handling.

        Args:
            index: Index of prompt to remove
        """
        # Prevent concurrent deletions
        if self.is_processing_deletion:
            return

        # Validate index
        if not (0 <= index < len(self.prompts)):
            return

        self.is_processing_deletion = True

        try:
            # Clear new prompt state if this is the new prompt being deleted
            if index == self.new_prompt_index:
                self.new_prompt_index = None

            # Remove from data
            self.prompts.pop(index)
            self.prompt_count = len(self.prompts)

            # Adjust current index if needed
            if self.current_prompt_index >= self.prompt_count:
                self.current_prompt_index = max(0, self.prompt_count - 1)

            # Rebuild the entire UI to ensure consistency
            self._rebuild_prompt_list_ui()

            # Update count label
            self._update_count_label()

            # Trigger update callback
            if self.on_prompts_changed:
                self.on_prompts_changed(
                    self.prompts,
                )  # Direct reference - no copy needed

            # CRITICAL FIX: Refresh next prompt display when a prompt is deleted
            # This ensures the "Next:" textarea shows the correct next prompt
            self.refresh_next_prompt_display()

        except Exception as e:
            # Log error and attempt recovery
            print(f"Error during prompt deletion: {e}")
            # Attempt to restore UI consistency
            self._rebuild_prompt_list_ui()
        finally:
            self.is_processing_deletion = False

    def clear_prompts(self) -> None:
        """Clear all prompts from the list."""
        self.prompts.clear()
        self.prompt_count = 0
        self.current_prompt_index = 0

        self._clear_prompt_list()

        # Update count label
        self._update_count_label()

        # Trigger update callback
        if self.on_prompts_changed:
            self.on_prompts_changed(self.prompts)  # Direct reference - no copy needed

        # CRITICAL FIX: Refresh next prompt display when prompts are cleared
        self.refresh_next_prompt_display()

    def sort_prompts(self, reverse: bool = False) -> None:
        """
        Sort prompts alphabetically.

        Args:
            reverse: Whether to sort in reverse order
        """
        if len(self.prompts) <= 1:
            return

        # Store current prompt text to find new index
        current_prompt_text = ""
        if 0 <= self.current_prompt_index < len(self.prompts):
            current_prompt_text = self.prompts[self.current_prompt_index]

        # Sort the prompts
        self.prompts.sort(reverse=reverse)

        # Find the new index of the current prompt
        if current_prompt_text:
            try:
                self.current_prompt_index = self.prompts.index(current_prompt_text)
            except ValueError:
                self.current_prompt_index = 0
        else:
            self.current_prompt_index = 0

        # Use consistent rebuild approach
        self._rebuild_prompt_list_ui()

        # Update count label
        self._update_count_label()

        # Trigger update callback
        if self.on_prompts_changed:
            self.on_prompts_changed(
                self.prompts,
            )  # Direct reference - no copy needed

        # CRITICAL FIX: Refresh next prompt display when prompts are sorted
        self.refresh_next_prompt_display()

    def _update_prompt_list_ui(self) -> None:
        """Update the prompt list UI elements directly without rebuilding."""
        if not self.prompts:
            return

        # Update each row's content and number label
        for index, prompt in enumerate(self.prompts):
            if index in self.prompt_entries:
                # Update entry text only if it changed
                entry = self.prompt_entries[index]
                current_text = entry.get()
                if current_text != prompt:
                    entry.delete(0, "end")
                    entry.insert(0, prompt)

            if index in self.prompt_labels:
                # Update number label only if it changed
                current_number = self.prompt_labels[index].cget("text")
                new_number = f"{index + 1}"
                if current_number != new_number:
                    self.prompt_labels[index].configure(text=new_number)

        # Update highlighting for all rows
        self._update_all_highlighting()

    def _rebuild_prompt_list_ui(self) -> None:
        """
        Rebuild the entire prompt list UI to ensure data and UI consistency.
        This is more reliable than trying to manually shift indices.
        """
        try:
            # Clear existing UI elements
            self._clear_prompt_list()

            # Rebuild all rows
            for index, prompt in enumerate(self.prompts):
                self._create_prompt_row(index, prompt)

            # Update highlighting
            self._update_all_highlighting()
        except Exception as e:
            print(f"Error during UI rebuild: {e}")
            # Fallback: try to clear and rebuild again
            try:
                self._clear_prompt_list()
                for index, prompt in enumerate(self.prompts):
                    self._create_prompt_row(index, prompt)
                self._update_all_highlighting()
            except Exception as e2:
                print(f"Critical error during UI rebuild fallback: {e2}")

    def move_prompt_up(self, index: int) -> None:
        """
        Move a prompt up in the list.

        Args:
            index: Index of prompt to move up
        """
        if index > 0 and index < len(self.prompts):
            # Swap prompts in the data
            self.prompts[index], self.prompts[index - 1] = (
                self.prompts[index - 1],
                self.prompts[index],
            )

            # Update current index if needed
            if self.current_prompt_index == index:
                self.current_prompt_index = index - 1
            elif self.current_prompt_index == index - 1:
                self.current_prompt_index = index

            # Use consistent rebuild approach
            self._rebuild_prompt_list_ui()

            # Update count label
            self._update_count_label()

            # Trigger update callback
            if self.on_prompts_changed:
                self.on_prompts_changed(
                    self.prompts,
                )  # Direct reference - no copy needed

            # CRITICAL FIX: Refresh next prompt display when a prompt is moved
            self.refresh_next_prompt_display()

    def move_prompt_down(self, index: int) -> None:
        """
        Move a prompt down in the list.

        Args:
            index: Index of prompt to move down
        """
        if index >= 0 and index < len(self.prompts) - 1:
            # Swap prompts in the data
            self.prompts[index], self.prompts[index + 1] = (
                self.prompts[index + 1],
                self.prompts[index],
            )

            # Update current index if needed
            if self.current_prompt_index == index:
                self.current_prompt_index = index + 1
            elif self.current_prompt_index == index + 1:
                self.current_prompt_index = index

            # Use consistent rebuild approach
            self._rebuild_prompt_list_ui()

            # Update count label
            self._update_count_label()

            # Trigger update callback
            if self.on_prompts_changed:
                self.on_prompts_changed(
                    self.prompts,
                )  # Direct reference - no copy needed

            # CRITICAL FIX: Refresh next prompt display when a prompt is moved
            self.refresh_next_prompt_display()

    def _save_new_prompt(self, index: int) -> None:
        """
        Save a new prompt and clear the new prompt state.

        Args:
            index: Index of the new prompt
        """
        if index == self.new_prompt_index and index in self.prompt_entries:
            # Get the current text from the entry
            entry = self.prompt_entries[index]
            current_text = entry.get().strip()

            # If the text is empty or just the default, remove the prompt
            if not current_text or current_text == "New prompt":
                self.remove_prompt(index)
            else:
                # Update the prompt in our data
                if index < len(self.prompts):
                    self.prompts[index] = current_text

                # Clear the new prompt state
                self.new_prompt_index = None

                # Trigger update callback
                if self.on_prompts_changed:
                    self.on_prompts_changed(
                        self.prompts,
                    )  # Direct reference - no copy needed

                # CRITICAL FIX: Refresh next prompt display when a new prompt is saved
                self.refresh_next_prompt_display()

    def destroy(self) -> None:
        """Clean up resources."""
        # Cancel any pending throttle timer and ensure proper cleanup
        if self.throttle_timer:
            self.throttle_timer.cancel()
            try:
                self.throttle_timer.join(timeout=0.1)  # Wait for cleanup with timeout
            except Exception:
                pass  # Ignore join errors
            self.throttle_timer = None

        # Clear UI components
        self._clear_prompt_list()

        # Return all pooled objects
        if hasattr(self, "prompts"):
            return_list(self.prompts)
        if hasattr(self, "prompt_rows"):
            return_dict(self.prompt_rows)
        if hasattr(self, "prompt_labels"):
            return_dict(self.prompt_labels)
        if hasattr(self, "prompt_entries"):
            return_dict(self.prompt_entries)
