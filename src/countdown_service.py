"""
Countdown Service

This module provides countdown functionality for the Cursor automation system.
Handles timer logic, countdown display, and user controls during countdown periods.

Author: Automation System
Version: 2.0 - Simplified Thread Management
"""

import logging
import threading
import time
import tkinter
from typing import Any, Callable, Dict, Optional

# Set up logger
logger = logging.getLogger(__name__)

# Handle imports for both testing and normal usage
try:
    from .config import (
        BTN_PAUSE,
        BTN_RESUME,
        BUTTON_BG,
        BUTTON_HOVER,
        COLOR_ACCENT,
        COLOR_PRIMARY,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        COUNTDOWN_TICK,
        WAIT_TICK,
    )
except ImportError:
    # Fallback for testing
    try:
        from config import (
            BTN_PAUSE,
            BTN_RESUME,
            BUTTON_BG,
            BUTTON_HOVER,
            COLOR_ACCENT,
            COLOR_PRIMARY,
            COLOR_TEXT,
            COLOR_TEXT_MUTED,
            COUNTDOWN_TICK,
            WAIT_TICK,
        )
    except ImportError:
        # Mock values for testing - these should match the actual config values
        COUNTDOWN_TICK = 0.1
        WAIT_TICK = 0.05
        BTN_PAUSE = "Pause"
        BTN_RESUME = "Resume"
        COLOR_TEXT = "#F8F8F2"
        COLOR_TEXT_MUTED = "#75715E"
        COLOR_PRIMARY = "#F92672"
        COLOR_ACCENT = "#A6E22E"
        BUTTON_BG = "#2F2F2F"
        BUTTON_HOVER = "#1f1f1f"

# =============================================================================
# COUNTDOWN SERVICE
# =============================================================================


class CountdownService:
    """
    Service for managing countdown timers and user controls.

    Simplified thread management: One thread per service instance.
    Handles timer logic, countdown display, pause/resume functionality,
    and user interaction during countdown periods.
    """

    def __init__(self, ui_widgets: Dict[str, Any]):
        """
        SIMPLIFIED: Initialize the countdown service with minimal complexity.
        """
        self.ui_widgets = ui_widgets

        # SIMPLIFIED: Single lock for all state
        self._lock = threading.Lock()

        # SIMPLIFIED: Basic state variables
        self._active = False
        self._paused = False
        self._cancelled = False
        self._thread = None
        self._completion_event = threading.Event()  # Keep only essential event

        # UI widget references
        self.time_label = ui_widgets.get("time_label")
        self.pause_btn = ui_widgets.get("pause_btn")
        self.current_box = ui_widgets.get("current_box")
        self.next_box = ui_widgets.get("next_box")

        # Callback for countdown completion
        self.on_countdown_complete: Optional[Callable[[Dict[str, Any]], None]] = None

        # Add callback for UI state updates when pause state changes
        self.on_pause_state_changed: Optional[Callable[[bool], None]] = None

    @property
    def countdown_active(self) -> bool:
        """Thread-safe access to active state."""
        with self._lock:
            return self._active

    @countdown_active.setter
    def countdown_active(self, value: bool) -> None:
        """Thread-safe setter for active state."""
        with self._lock:
            self._active = value

    @property
    def paused(self) -> bool:
        """Thread-safe access to paused state."""
        with self._lock:
            return self._paused

    @paused.setter
    def paused(self, value: bool) -> None:
        """Thread-safe setter for paused state."""
        with self._lock:
            self._paused = value

    @property
    def cancelled(self) -> bool:
        """Thread-safe access to cancelled state."""
        with self._lock:
            return self._cancelled

    @cancelled.setter
    def cancelled(self, value: bool) -> None:
        """Thread-safe setter for cancelled state."""
        with self._lock:
            self._cancelled = value

    def start_countdown(
        self,
        seconds: float,
        text: Optional[str] = None,
        next_text: Optional[str] = None,
        last_text: Optional[str] = None,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Start countdown with user controls.

        Args:
            seconds: Duration in seconds
            text: Current text to display
            next_text: Next text to display
            last_text: Previous text
            on_complete: Callback function when countdown completes

        Returns:
            Dictionary containing final state
        """
        logger.info(f"Starting countdown for {seconds} seconds")

        # Preserve pause state when transitioning between countdowns
        was_paused = self._paused

        # Stop any existing countdown
        self.stop()

        # Reset state but preserve pause state if it was set
        with self._lock:
            self._active = True
            self._paused = was_paused  # Preserve pause state across countdown
            # transitions
            self._cancelled = False
            self.on_countdown_complete = on_complete

        # Clear completion event
        self._completion_event.clear()

        # Start countdown thread
        self._thread = threading.Thread(
            target=self._countdown_loop,
            args=(seconds, text, next_text, last_text),
            daemon=True,
            name="CountdownThread",
        )
        self._thread.start()

        # Wait for completion
        self._completion_event.wait(timeout=seconds + 10)

        # Get final state
        result = self._get_final_state()
        logger.info(f"Countdown completed with result: {result}")
        return result

    def stop(self) -> None:
        """SIMPLIFIED: Stop the countdown immediately."""
        with self._lock:
            self._active = False
            self._cancelled = True
            # Don't clear pause state when stopping - preserve it for transitions

        self._completion_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

    def toggle_pause(self) -> None:
        """Toggle pause/resume state."""
        if not self.countdown_active:
            logger.warning("Cannot toggle pause - countdown not active")
            return

        with self._lock:
            self._paused = not self._paused

        # Update UI
        try:
            if self.pause_btn:
                if self.paused:
                    self.pause_btn.configure(
                        text=BTN_RESUME,
                        fg_color=COLOR_PRIMARY,
                        hover_color=COLOR_PRIMARY,
                    )
                else:
                    self.pause_btn.configure(
                        text=BTN_PAUSE,
                        fg_color=BUTTON_BG,
                        hover_color=BUTTON_HOVER,
                    )
        except (AttributeError, tkinter.TclError) as e:
            logger.error(f"Error updating pause button: {e}")

        # Trigger UI state update callback when pause state changes
        if self.on_pause_state_changed:
            try:
                self.on_pause_state_changed(self._paused)
                logger.info(f"Triggered UI state update callback - paused: "
                          f"{self._paused}")
            except Exception as e:
                logger.error(f"Error in pause state change callback: {e}")

    def cancel(self) -> None:
        """Cancel the countdown."""
        self.stop()

    def is_active(self) -> bool:
        """Check if countdown is active."""
        return self.countdown_active

    def is_paused(self) -> bool:
        """Check if countdown is paused."""
        return self.paused

    def is_cancelled(self) -> bool:
        """Check if countdown is cancelled."""
        return self.cancelled

    def force_reset(self) -> None:
        """SIMPLIFIED: Basic reset - stop the countdown and reset state."""
        logger.info("Resetting countdown service")
        with self._lock:
            self._active = False
            self._cancelled = False
            self._paused = False
        self._completion_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

    def force_complete(self) -> None:
        """SIMPLIFIED: Basic completion - just signal completion."""
        logger.info("Completing countdown")
        with self._lock:
            self._active = False
        self._completion_event.set()

    def _get_final_state(self) -> Dict[str, Any]:
        """Get the final state of the countdown."""
        with self._lock:
            return {
                "cancelled": self._cancelled,
                "paused": self._paused,
            }

    def _update_display(
        self,
        remaining: float,
        total: float,
        text: Optional[str],
        next_text: Optional[str],
    ) -> None:
        """
        Update the countdown display with current values.

        Args:
            remaining: Remaining time in seconds
            total: Total countdown time in seconds
            text: Current prompt text
            next_text: Next prompt text
        """
        try:
            # Validate inputs
            if not isinstance(remaining, (int, float)) or remaining < 0:
                logger.warning(f"Invalid remaining time: {remaining}")
                remaining = 0.0

            if not isinstance(total, (int, float)) or total <= 0:
                logger.warning(f"Invalid total time: {total}")
                total = 1.0

            # Update time display
            if self.time_label:
                try:
                    # Show paused indicator when paused
                    if self.paused:
                        display_text = f"*{int(round(remaining))}"
                    else:
                        display_text = str(int(round(remaining)))
                    self.time_label.configure(text=display_text)
                except AttributeError:
                    pass  # No time_label to update

            # Progress bar removed - no longer needed

            # Update pause button
            if self.pause_btn:
                try:
                    if self.paused:
                        self.pause_btn.configure(
                            text=BTN_RESUME,
                            fg_color=COLOR_PRIMARY,
                            hover_color=COLOR_PRIMARY,
                        )
                    else:
                        self.pause_btn.configure(
                            text=BTN_PAUSE,
                            fg_color=BUTTON_BG,
                            hover_color=BUTTON_HOVER,
                        )
                except AttributeError:
                    pass  # No pause button to update

            # Update text boxes
            if self.current_box:
                try:
                    safe_text = str(text) if text is not None else ""
                    self._set_textbox(self.current_box, safe_text)
                except AttributeError:
                    pass  # No current_box to update

            if self.next_box:
                try:
                    safe_next_text = str(next_text) if next_text is not None else ""
                    next_text_with_prefix = f"{safe_next_text}"
                    self._set_textbox(self.next_box, next_text_with_prefix)
                except AttributeError:
                    pass  # No next_box to update
        except Exception as e:
            logger.warning(f"Error updating display: {e}")

    def _set_textbox(self, textbox, text: str) -> None:
        """Set text in a textbox widget."""
        if hasattr(textbox, "delete") and hasattr(textbox, "insert"):
            textbox.delete("1.0", tkinter.END)
            textbox.insert("1.0", text)
        elif hasattr(textbox, "configure"):
            textbox.configure(text=text)

    def _schedule_ui_update(self, remaining: float, total: float,
                          text: Optional[str], next_text: Optional[str]) -> None:
        """Update UI display directly."""
        self._update_display(remaining, total, text, next_text)

    def _countdown_loop(
        self,
        seconds: float,
        text: Optional[str],
        next_text: Optional[str],
        last_text: Optional[str],
    ) -> None:
        """
        Main countdown loop executed in separate thread.

        Args:
            seconds: Duration in seconds
            text: Current text to display
            next_text: Next text to display
            last_text: Previous text
        """
        try:
            # Initialize countdown
            total = max(0.0, float(seconds))
            remaining = total
            start_time = time.time()
            pause_start_time = None  # Track when pause started
            total_pause_time = 0.0   # Track total time spent paused

            logger.info(f"Countdown loop started for {total}s")

            # Update initial display
            self._update_display(remaining, total, text, next_text)

            # SIMPLIFIED: Main countdown loop
            while (
                remaining > 0
                and self.countdown_active
                and not self.cancelled
            ):
                # Handle pause state - Don't decrement time when paused
                if self.paused:
                    # Track pause start time
                    if pause_start_time is None:
                        pause_start_time = time.time()

                    # Update display to show paused state
                    self._schedule_ui_update(remaining, total, text, next_text)
                    time.sleep(WAIT_TICK)
                    continue
                # Not paused - update total pause time if we were paused
                if pause_start_time is not None:
                    total_pause_time += time.time() - pause_start_time
                    pause_start_time = None

                # Check for timeout based on ACTUAL countdown time (excluding
                # pause time)
                actual_elapsed = time.time() - start_time - total_pause_time
                if actual_elapsed > total + 60:  # Allow 1 minute extra for safety
                    logger.error("Countdown timeout reached")
                    break

                # Update display
                self._schedule_ui_update(remaining, total, text, next_text)

                # Proper pause/resume logic - always wait full second
                time.sleep(1.0)
                remaining -= 1.0

            # Countdown completed
            with self._lock:
                self._active = False

            # Final display update
            self._update_display(0.0, total, text, next_text)

            # Call completion callback
            if self.on_countdown_complete:
                try:
                    final_state = self._get_final_state()
                    self.on_countdown_complete(final_state)
                except Exception as e:
                    logger.error(f"Error in completion callback: {e}")

            # Signal completion
            self._completion_event.set()

        except Exception as e:
            logger.error(f"Error in countdown loop: {e}")
            self._completion_event.set()
