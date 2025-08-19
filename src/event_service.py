"""
Event Handling Service

This module provides event handling functionality for the Cursor automation system.
Handles button events, keyboard navigation, and user interactions.

Author: Automation System
Version: 1.0
"""

import tkinter
from typing import Callable, Dict, Optional

from pynput import keyboard

try:
    from .config import COLOR_PRIMARY, COLOR_TEXT_MUTED
except ImportError:
    # Fallback for when running as script
    pass

# =============================================================================
# EVENT HANDLING SERVICE
# =============================================================================


class EventService:
    """
    Service for managing user events and interactions.

    Handles button events, keyboard navigation, tooltips, and user interaction
    management for the automation UI.
    """

    def __init__(self, parent_widget):
        """
        Initialize the event service.

        Args:
            parent_widget: Parent widget for event handling
        """
        self.parent = parent_widget
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.tooltip_widget: Optional[tkinter.Toplevel] = None
        self.tooltip_label: Optional[tkinter.Label] = None

        # Event callbacks
        self.on_key_up: Optional[Callable[[], None]] = None
        self.on_key_down: Optional[Callable[[], None]] = None
        self.on_key_enter: Optional[Callable[[], None]] = None

        # Modifier key tracking
        self.ctrl_pressed = False

        # Shortcut tracking
        self.shortcut_key = None
        self.shortcut_modifier = None
        self.shortcut_callback = None

        # Don't start keyboard listener immediately - start it when needed
        self._keyboard_listener_started = False

    def _start_keyboard_listener(self) -> None:
        """Start the keyboard event listener."""
        try:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self.keyboard_listener.start()
        except Exception as e:
            print(f"Failed to start keyboard listener: {e}")

    def _on_key_press(self, key) -> None:
        """
        Handle key press events.

        Args:
            key: The pressed key
        """
        try:
            # Track modifier keys
            if key == keyboard.Key.ctrl:
                self.ctrl_pressed = True
                return

            if hasattr(key, "char"):
                if key.char == "w":
                    if self.on_key_up:
                        self.on_key_up()
                elif key.char == "s":
                    # Check if Ctrl+S shortcut is configured
                    if (
                        self.shortcut_key == "s"
                        and self.shortcut_modifier == "Control"
                        and self.ctrl_pressed
                        and self.shortcut_callback
                    ):
                        self.shortcut_callback()
                        return

                    # Default s key behavior (only if Ctrl is not pressed)
                    if not self.ctrl_pressed and self.on_key_down:
                        self.on_key_down()
                elif key.char == "\r" or key.char == "\n":
                    if self.on_key_enter:
                        self.on_key_enter()
        except Exception as e:
            print(f"Error handling key press: {e}")

    def _on_key_release(self, key) -> None:
        """
        Handle key release events.

        Args:
            key: The released key
        """
        try:
            # Track modifier key releases
            if key == keyboard.Key.ctrl:
                self.ctrl_pressed = False
        except Exception as e:
            print(f"Error handling key release: {e}")

    def setup_keyboard_navigation(
        self,
        on_up: Optional[Callable[[], None]] = None,
        on_down: Optional[Callable[[], None]] = None,
        on_enter: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Setup keyboard navigation callbacks.

        Args:
            on_up: Callback for up arrow key
            on_down: Callback for down arrow key
            on_enter: Callback for enter key
        """
        self.on_key_up = on_up
        self.on_key_down = on_down
        self.on_key_enter = on_enter

        # Keyboard listener disabled to prevent hanging
        # Start keyboard listener only when navigation is set up
        # if not self._keyboard_listener_started:
        #     self._start_keyboard_listener()
        #     self._keyboard_listener_started = True

    def setup_keyboard_shortcut(
        self,
        key: str,
        modifier: str,
        callback: Callable[[], None],
    ) -> None:
        """
        Setup a keyboard shortcut with modifier.

        Args:
            key: The key to listen for (e.g., 's')
            modifier: The modifier key (e.g., 'Control', 'Alt', 'Shift')
            callback: Function to call when shortcut is pressed
        """
        # Store the shortcut callback
        self.shortcut_key = key
        self.shortcut_modifier = modifier
        self.shortcut_callback = callback

        # Keyboard listener disabled to prevent hanging
        # Start keyboard listener if not already started
        # if not self._keyboard_listener_started:
        #     self._start_keyboard_listener()
        #     self._keyboard_listener_started = True

    def add_tooltip(self, widget, text: str) -> None:
        """
        Add a tooltip to a widget.

        Args:
            widget: The widget to add tooltip to
            text: Tooltip text
        """

        def show_tooltip(event):
            # Create tooltip window
            self.tooltip_widget = tkinter.Toplevel()
            self.tooltip_widget.wm_overrideredirect(True)
            self.tooltip_widget.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            # Create tooltip label
            self.tooltip_label = tkinter.Label(
                self.tooltip_widget,
                text=text,
                justify=tkinter.LEFT,
                background="#ffffe0",
                relief=tkinter.SOLID,
                borderwidth=1,
                font=("Segoe UI", 9),
            )
            self.tooltip_label.pack()

            # Auto-hide after delay
            def delayed_hide():
                if self.tooltip_widget:
                    try:
                        self.tooltip_widget.destroy()
                        self.tooltip_widget = None
                        self.tooltip_label = None
                    except (AttributeError, tkinter.TclError):
                        pass

            self.parent.after(3000, delayed_hide)

        def hide_tooltip(event):
            if self.tooltip_widget:
                try:
                    self.tooltip_widget.destroy()
                    self.tooltip_widget = None
                    self.tooltip_label = None
                except (AttributeError, tkinter.TclError):
                    pass

        # Bind events
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def create_button_event_handler(
        self,
        callback: Callable[[], None],
        validation_callback: Optional[Callable[[], bool]] = None,
    ) -> Callable[[], None]:
        """
        Create a button event handler with optional validation.

        Args:
            callback: The main callback function
            validation_callback: Optional validation function

        Returns:
            Event handler function
        """

        def event_handler():
            try:
                # Run validation if provided
                if validation_callback and not validation_callback():
                    return

                # Execute callback
                callback()

            except Exception as e:
                print(f"Error in button event handler: {e}")

        return event_handler

    def create_toggle_button_handler(
        self,
        button_widget,
        on_text: str,
        off_text: str,
        on_callback: Optional[Callable[[], None]] = None,
        off_callback: Optional[Callable[[], None]] = None,
    ) -> Callable[[], None]:
        """
        Create a toggle button event handler.

        Args:
            button_widget: The button widget to toggle
            on_text: Text to show when button is on
            off_text: Text to show when button is off
            on_callback: Callback when button is turned on
            off_callback: Callback when button is turned off

        Returns:
            Toggle event handler function
        """
        is_on = False

        def toggle_handler():
            nonlocal is_on
            try:
                is_on = not is_on

                # Update button text
                button_widget.configure(text=on_text if is_on else off_text)

                # Execute appropriate callback
                if is_on and on_callback:
                    on_callback()
                elif not is_on and off_callback:
                    off_callback()

            except Exception as e:
                print(f"Error in toggle button handler: {e}")

        return toggle_handler

    def create_validation_handler(
        self,
        validation_func: Callable[[], bool],
        success_callback: Callable[[], None],
        error_message: str = "Validation failed",
    ) -> Callable[[], None]:
        """
        Create a validation-based event handler.

        Args:
            validation_func: Function that returns True if validation passes
            success_callback: Callback to execute if validation passes
            error_message: Message to show if validation fails

        Returns:
            Validation event handler function
        """

        def validation_handler():
            try:
                if validation_func():
                    success_callback()
                else:
                    self._show_error_feedback(error_message)
            except Exception as e:
                print(f"Error in validation handler: {e}")
                self._show_error_feedback("An error occurred")

        return validation_handler

    def _show_error_feedback(self, message: str) -> None:
        """
        Show error feedback to the user.

        Args:
            message: Error message to display
        """
        # This could be enhanced to show a proper error dialog
        print(f"Error: {message}")

    def create_debounced_handler(
        self,
        callback: Callable[[], None],
        delay_ms: int = 300,
    ) -> Callable[[], None]:
        """
        Create a debounced event handler.

        Args:
            callback: The callback function to debounce
            delay_ms: Delay in milliseconds

        Returns:
            Debounced event handler function
        """
        timer_id = None

        def debounced_handler():
            nonlocal timer_id

            # Cancel existing timer
            if timer_id:
                self.parent.after_cancel(timer_id)

            # Schedule new execution
            timer_id = self.parent.after(delay_ms, callback)

        return debounced_handler

    def create_async_handler(
        self,
        async_func: Callable[[], None],
        loading_callback: Optional[Callable[[bool], None]] = None,
    ) -> Callable[[], None]:
        """
        Create an async event handler with loading state.

        Args:
            async_func: The async function to execute
            loading_callback: Callback to show/hide loading state

        Returns:
            Async event handler function
        """

        def async_handler():
            try:
                # Show loading state
                if loading_callback:
                    loading_callback(True)

                # Execute async function
                async_func()

            except Exception as e:
                print(f"Error in async handler: {e}")
            finally:
                # Hide loading state
                if loading_callback:
                    loading_callback(False)

        return async_handler

    def bind_widget_events(self, widget, events: Dict[str, Callable]) -> None:
        """
        Bind multiple events to a widget.

        Args:
            widget: The widget to bind events to
            events: Dictionary of event names to callback functions
        """
        for event_name, callback in events.items():
            try:
                widget.bind(event_name, lambda e, cb=callback: cb())
            except Exception as e:
                print(f"Failed to bind event {event_name}: {e}")

    def create_context_menu(
        self,
        widget,
        menu_items: Dict[str, Callable[[], None]],
    ) -> None:
        """
        Create a context menu for a widget.

        Args:
            widget: The widget to add context menu to
            menu_items: Dictionary of menu item text to callback functions
        """

        def show_context_menu(event):
            try:
                # Create context menu
                context_menu = tkinter.Menu(self.parent, tearoff=0)

                # Add menu items
                for text, callback in menu_items.items():
                    context_menu.add_command(label=text, command=callback)

                # Show menu at cursor position
                context_menu.tk_popup(event.x_root, event.y_root)

            except Exception as e:
                print(f"Error showing context menu: {e}")

        # Bind right-click event
        widget.bind("<Button-3>", show_context_menu)

    def stop(self) -> None:
        """Stop the event service and cleanup resources."""
        try:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
                self._keyboard_listener_started = False

            if self.tooltip_widget:
                self.tooltip_widget.destroy()
                self.tooltip_widget = None
                self.tooltip_label = None

        except Exception as e:
            print(f"Error stopping event service: {e}")

    def disable_keyboard_listener(self) -> None:
        """Disable keyboard listener to prevent conflicts."""
        try:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
                self._keyboard_listener_started = False
                print("Keyboard listener disabled")
        except Exception as e:
            print(f"Error disabling keyboard listener: {e}")
