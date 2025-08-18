"""
Countdown Service

This module provides countdown functionality for the Cursor automation system.
Handles timer logic, countdown display, and user controls during countdown periods.

Author: Automation System
Version: 1.0
"""

import logging
import threading
import time
import tkinter
from typing import Any, Callable, Dict, Optional

import customtkinter as ctk

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

    Handles timer logic, countdown display, pause/resume functionality,
    and user interaction during countdown periods.
    """

    def __init__(self, ui_widgets: Dict[str, Any]):
        """
        Initialize the countdown service.

        Args:
            ui_widgets: Dictionary containing UI widgets needed for countdown
        """
        self.ui_widgets = ui_widgets
        self._state_lock = threading.Lock()  # Thread safety lock

        # Thread-safe state variables
        self._countdown_active = False
        self._paused = False
        self._cancelled = False
        self.countdown_thread = None
        self._stop_event = threading.Event()

        # UI widget references
        self.time_label = ui_widgets.get("time_label")
        self.progress = ui_widgets.get("progress")
        self.pause_btn = ui_widgets.get("pause_btn")
        self.current_box = ui_widgets.get("current_box")
        self.next_box = ui_widgets.get("next_box")

        # Callback for countdown completion
        self.on_countdown_complete: Optional[Callable[[Dict[str, Any]], None]] = None

        # CRITICAL FIX: Add completion event for better synchronization
        self._completion_event = threading.Event()
        self._completion_result: Optional[Dict[str, Any]] = None

        # CRITICAL FIX: Generation token to invalidate older threads
        self._generation_id: int = 0

    @property
    def countdown_active(self) -> bool:
        """Thread-safe access to countdown_active."""
        with self._state_lock:
            return self._countdown_active

    @countdown_active.setter
    def countdown_active(self, value: bool) -> None:
        """Thread-safe setter for countdown_active."""
        with self._state_lock:
            self._countdown_active = value

    @property
    def paused(self) -> bool:
        """Thread-safe access to paused."""
        with self._state_lock:
            return self._paused

    @paused.setter
    def paused(self, value: bool) -> None:
        """Thread-safe setter for paused."""
        with self._state_lock:
            self._paused = value

    @property
    def cancelled(self) -> bool:
        """Thread-safe access to cancelled."""
        with self._state_lock:
            return self._cancelled

    @cancelled.setter
    def cancelled(self, value: bool) -> None:
        """Thread-safe setter for cancelled."""
        with self._state_lock:
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

        # CRITICAL FIX: Stop any existing countdown before starting new one
        # This prevents multiple threads from running simultaneously
        if self.countdown_active:
            logger.warning("Stopping existing countdown before starting new one")
            self.stop()
            # Wait a moment for the thread to actually stop
            time.sleep(0.1)

        # CRITICAL FIX: Ensure no threads are running
        if self.countdown_thread and self.countdown_thread.is_alive():
            logger.warning("Force stopping existing countdown thread")
            self._stop_event.set()
            self.countdown_thread.join(timeout=1.0)
            if self.countdown_thread.is_alive():
                logger.error("Failed to stop existing countdown thread")

        # Reset state for new countdown
        self._reset_state()

        # Store callback
        self.on_countdown_complete = on_complete

        # CRITICAL FIX: Reset completion event for new countdown
        self._completion_event.clear()
        self._completion_result = None

        # Initialize countdown
        total = max(0.0, float(seconds))
        remaining = float(total)

        # Update UI immediately
        self._update_display(remaining, total, text, next_text)

        # Start countdown in separate thread to prevent UI blocking
        # CRITICAL: Set active state AFTER pause state is restored
        self.countdown_active = True

        # Increment generation and capture local copy for this thread
        with self._state_lock:
            self._generation_id += 1
            local_generation = self._generation_id

        def _thread_target():
            self._countdown_loop(remaining, total, text, next_text, last_text, local_generation)

        self.countdown_thread = threading.Thread(
            target=_thread_target,
            daemon=True,
        )
        self.countdown_thread.start()

        # Wait for countdown to complete but with timeout to prevent blocking
        try:
            # CRITICAL FIX: Wait for completion event instead of thread join
            # This ensures proper synchronization
            if self._completion_event.wait(timeout=total + 10):
                # Countdown completed normally
                result = self._completion_result or self._get_final_state()
            else:
                # Timeout occurred
                logger.warning("Countdown timeout - forcing completion")
                result = self._get_final_state()
        except Exception as e:
            logger.error(f"Error waiting for countdown completion: {e}")
            result = self._get_final_state()

        # Return final state
        return result

    def force_reset(self) -> None:
        """Force reset the countdown service state - useful for debugging hanging issues."""
        logger.info("Force resetting countdown service state")
        with self._state_lock:
            self._countdown_active = False
            self._paused = False
            self._cancelled = False
            # Bump generation so any existing threads exit quickly
            self._generation_id += 1
        self._stop_event.set()
        
        # CRITICAL FIX: Signal completion event to unblock any waiting threads
        self._completion_event.set()
        
        # Wait for any running thread to finish
        if self.countdown_thread and self.countdown_thread.is_alive():
            logger.info("Waiting for countdown thread to finish...")
            self.countdown_thread.join(timeout=5.0)
            if self.countdown_thread.is_alive():
                logger.warning("Countdown thread did not finish within timeout")
        
        self.countdown_thread = None
        logger.info("Countdown service state reset complete")

    def force_complete(self) -> None:
        """
        Force complete the countdown immediately, even if paused.
        This is useful when the countdown reaches zero but is stuck in paused state.
        """
        logger.info("Force completing countdown")
        
        with self._state_lock:
            self._countdown_active = False
            self._paused = False
            self._cancelled = False
        
        # Signal completion event to unblock any waiting threads
        self._completion_event.set()
        
        # Call completion callback if provided
        if self.on_countdown_complete:
            try:
                final_state = self._get_final_state()
                self.on_countdown_complete(final_state)
                self._completion_result = final_state
            except Exception as e:
                logger.error(f"Error in force complete callback: {e}")
                self._completion_result = self._get_final_state()
        else:
            self._completion_result = self._get_final_state()
        
        logger.info("Countdown force completed")

    def _reset_state(self) -> None:
        """Reset all control state flags."""
        with self._state_lock:
            self._paused = False
            self._cancelled = False
        self._stop_event.clear()

    def _update_display(
        self,
        remaining: float,
        total: float,
        text: Optional[str],
        next_text: Optional[str],
    ) -> None:
        """Update countdown display elements with error handling."""
        try:
            # Update time display
            if self.time_label:
                self.time_label.configure(text=str(int(round(remaining))))

            # Update progress bar
            if self.progress:
                if total > 0:
                    # Calculate progress as remaining time / total time
                    # Progress should decrease from 1.0 to 0.0 as time counts down
                    progress_value = remaining / total
                else:
                    progress_value = 0.0
                self.progress.set(progress_value)

            # Update pause button
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

            # Update text boxes
            if self.current_box:
                self._set_textbox(self.current_box, text or "")

            if self.next_box:
                next_text_with_prefix = f"Next: {next_text}" if next_text else ""
                self._set_textbox(self.next_box, next_text_with_prefix)

        except (AttributeError, tkinter.TclError) as e:
            print(f"Error updating countdown display: {e}")
            # Graceful fallback

    def _set_textbox(self, box: ctk.CTkTextbox, text: str) -> None:
        """
        Safely update a text box with new content.

        Args:
            box: The text box widget to update
            text: The text content to display
        """
        try:
            if box is None:
                return
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("end", str(text))
            box.configure(state="disabled")
        except (AttributeError, tkinter.TclError) as e:
            print(f"Error updating textbox: {e}")
            # Graceful fallback if text update fails

    def _schedule_ui_update(
        self,
        remaining: float,
        total: float,
        text: Optional[str],
        next_text: Optional[str],
    ) -> None:
        """Schedule UI update on main thread with proper variable capture."""
        try:
            if self.time_label and hasattr(self.time_label, "after"):
                # CRITICAL FIX: Use immediate execution instead of scheduling
                # This prevents race conditions where UI updates are delayed
                def update_ui():
                    try:
                        self._update_display(remaining, total, text, next_text)
                    except Exception as e:
                        logger.warning(f"Error in UI update: {e}")
                
                # Execute immediately on main thread
                self.time_label.after_idle(update_ui)
        except Exception as e:
            logger.warning(f"Error scheduling UI update: {e}")
            # Fallback: try direct update
            try:
                self._update_display(remaining, total, text, next_text)
            except Exception as e2:
                logger.warning(f"Fallback UI update also failed: {e2}")

    def _countdown_loop(
        self,
        remaining: float,
        total: float,
        text: Optional[str],
        next_text: Optional[str],
        last_text: Optional[str],
        local_generation: int,
    ) -> None:
        """
        Main countdown loop running in separate thread.

        Args:
            remaining: Remaining time in seconds
            text: Current text to display
            next_text: Next text to display
            last_text: Previous text
            local_generation: Generation id captured at start; if mismatched, exit
        """
        start_time = time.time()
        max_duration = total + 60  # Allow 60 seconds extra for safety
        
        try:
            # Abort immediately if superseded by a newer countdown
            with self._state_lock:
                if local_generation != self._generation_id:
                    logger.info("Countdown thread superseded by newer generation - exiting early")
                    return

            # CRITICAL FIX: Check pause state immediately when thread starts
            # This prevents the countdown from running even briefly when resuming from pause
            if self.paused:
                logger.info(
                    "Countdown thread started in paused state - waiting for resume"
                )
                pause_start = time.time()
                while self.paused and self.countdown_active and not self.cancelled:
                    time.sleep(WAIT_TICK)  # 0.05 seconds for responsive pause
                    if self._stop_event.is_set():
                        break
                    # Prevent infinite pause
                    if time.time() - pause_start > 300:  # 5 minutes max pause
                        logger.warning("Pause timeout reached - forcing resume")
                        break
                    # Check for generation change during pause
                    with self._state_lock:
                        if local_generation != self._generation_id:
                            logger.info("Countdown thread superseded during pause - exiting")
                            return
                logger.info("Countdown thread resumed from pause state")

            while (
                remaining > 0
                and self.countdown_active
                and not self.cancelled
                and not self._stop_event.is_set()
            ):
                # If a newer generation started, exit silently
                with self._state_lock:
                    if local_generation != self._generation_id:
                        logger.info("Countdown loop detected newer generation - exiting")
                        return

                # Check for timeout
                if time.time() - start_time > max_duration:
                    logger.error(f"Countdown timeout reached after {max_duration} seconds")
                    break
                    
                # CRITICAL FIX: Actually pause the countdown timer
                # When paused, don't decrement remaining time and don't update UI
                if self.paused:
                    time.sleep(WAIT_TICK)  # 0.05 seconds for responsive pause
                    continue

                # Schedule UI update on main thread with proper variable capture
                self._schedule_ui_update(remaining, total, text, next_text)

                # Use smaller tick for more responsive pause checking
                tick_duration = min(
                    COUNTDOWN_TICK,
                    0.05,
                )  # Use 0.05 seconds max for responsiveness
                time.sleep(tick_duration)
                
                # CRITICAL FIX: Only decrement remaining time when not paused
                remaining -= tick_duration

                # Check for stop event
                if self._stop_event.is_set():
                    break

            # If superseded, do not finalize or fire callbacks
            with self._state_lock:
                if local_generation != self._generation_id:
                    logger.info("Countdown finalize skipped due to newer generation")
                    return

            # Countdown completed
            self.countdown_active = False
            logger.info(f"Countdown loop completed after {time.time() - start_time:.2f} seconds")

            # SIMPLIFIED FIX: Single, immediate UI reset after countdown completion
            # This eliminates the race condition by doing one clean reset
            try:
                # Reset UI to final state immediately
                self._update_display(0, total, text, next_text)
                
                # Ensure time display shows 0
                if self.time_label:
                    self.time_label.configure(text="0")
                
                # Ensure progress bar shows 0
                if self.progress:
                    self.progress.set(0.0)
                    
                logger.info("UI reset completed after countdown")
            except Exception as e:
                logger.warning(f"UI reset after countdown completion failed: {e}")

            # Call completion callback if provided
            if self.on_countdown_complete:
                try:
                    final_state = self._get_final_state()
                    self.on_countdown_complete(final_state)
                    # Store result for synchronization
                    self._completion_result = final_state
                except Exception as e:
                    logger.error(f"Error in countdown completion callback: {e}")
                    self._completion_result = self._get_final_state()
            else:
                # Store result for synchronization
                self._completion_result = self._get_final_state()

            # CRITICAL FIX: Signal completion event for proper synchronization
            self._completion_event.set()

        except Exception as e:
            logger.error(f"Error in countdown loop: {e}")
            self.countdown_active = False
            self.cancelled = True

    def _get_final_state(self) -> Dict[str, Any]:
        """
        Get the final state of the countdown.

        Returns:
            Dictionary containing control state
        """
        with self._state_lock:
            return {
                "cancelled": self._cancelled,
                "paused": self._paused,
            }

    def toggle_pause(self) -> None:
        """Toggle pause/resume state with immediate UI feedback."""
        if not self.countdown_active:
            return

        with self._state_lock:
            self._paused = not self._paused

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
            print(f"Error updating pause button: {e}")

    def cancel(self) -> None:
        """Cancel the countdown with immediate response."""
        with self._state_lock:
            self._cancelled = True
            self._countdown_active = False
        self._stop_event.set()

        # Stop the countdown thread if it's running
        if self.countdown_thread and self.countdown_thread.is_alive():
            try:
                self.countdown_thread.join(timeout=1.0)  # Wait up to 1 second
            except Exception as e:
                print(f"Error stopping countdown thread: {e}")

    def is_active(self) -> bool:
        """Check if countdown is currently active."""
        return self.countdown_active

    def has_running_thread(self) -> bool:
        """Check if there's actually a running countdown thread."""
        return (
            self.countdown_thread is not None 
            and self.countdown_thread.is_alive()
        )

    def get_thread_status(self) -> Dict[str, Any]:
        """Get detailed thread status for debugging."""
        return {
            "countdown_active": self.countdown_active,
            "thread_exists": self.countdown_thread is not None,
            "thread_alive": self.countdown_thread.is_alive() if self.countdown_thread else False,
            "paused": self.paused,
            "cancelled": self.cancelled,
            "stop_event_set": self._stop_event.is_set(),
        }

    def is_paused(self) -> bool:
        """
        Check if countdown is currently paused.

        Returns:
            True if countdown is paused, False otherwise
        """
        return self.paused

    def is_truly_paused(self) -> bool:
        """
        Check if countdown is truly paused (not just UI state).
        This is more reliable than is_paused() for automation logic.

        Returns:
            True if countdown is actually paused, False otherwise
        """
        with self._state_lock:
            return self._paused and self._countdown_active and not self._cancelled

    def is_cancelled(self) -> bool:
        """
        Check if countdown is currently cancelled.

        Returns:
            True if countdown is cancelled, False otherwise
        """
        return self.cancelled

    def stop(self) -> None:
        """Stop the countdown with immediate response."""
        logger.info("Stopping countdown")
        
        # CRITICAL FIX: Set stop event first to signal threads to stop
        self._stop_event.set()
        
        # Set cancelled state and bump generation
        with self._state_lock:
            self._cancelled = True
            self._countdown_active = False
            self._generation_id += 1
        
        # CRITICAL FIX: Wait for thread to actually stop
        if self.countdown_thread and self.countdown_thread.is_alive():
            logger.info("Waiting for countdown thread to stop...")
            self.countdown_thread.join(timeout=2.0)  # Increased timeout
            if self.countdown_thread.is_alive():
                logger.warning("Countdown thread did not stop within timeout")
            else:
                logger.info("Countdown thread stopped successfully")
        
        # Signal completion event to unblock any waiting threads
        self._completion_event.set()
        
        # Reset thread reference
        self.countdown_thread = None
        
        logger.info("Countdown stop completed")
