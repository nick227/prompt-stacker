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

# Global thread registry to track all countdown threads
_countdown_threads = set()
_thread_registry_lock = threading.Lock()

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

def _kill_all_countdown_threads():
    """Kill all countdown threads globally."""
    global _countdown_threads
    with _thread_registry_lock:
        threads_to_kill = _countdown_threads.copy()
        thread_count = len(threads_to_kill)
        logger.warning(f"KILLING ALL THREADS: Found {thread_count} countdown threads to kill")
        _countdown_threads.clear()
    
    if thread_count == 0:
        logger.info("No countdown threads found to kill")
        return
    
    for i, thread in enumerate(threads_to_kill, 1):
        if thread.is_alive():
            thread_name = getattr(thread, 'name', 'Unknown')
            thread_ident = getattr(thread, 'ident', 'Unknown')
            logger.warning(f"Killing thread {i}/{thread_count}: {thread_name} (ID: {thread_ident})")
            # Set a flag to make the thread exit
            if hasattr(thread, '_force_exit'):
                thread._force_exit = True
                logger.info(f"   Set force_exit flag on thread {thread_name}")
            # Wait a moment for graceful exit
            thread.join(timeout=0.1)
            if thread.is_alive():
                logger.error(f"FAILED to kill thread: {thread_name} (ID: {thread_ident})")
            else:
                logger.info(f"Successfully killed thread: {thread_name}")
        else:
            thread_name = getattr(thread, 'name', 'Unknown')
            logger.info(f"Thread {thread_name} was already dead")
    
    logger.info(f"Thread cleanup completed - killed {thread_count} threads")

def _log_thread_registry_status():
    """Log the current status of all threads in the global registry."""
    global _countdown_threads
    with _thread_registry_lock:
        thread_count = len(_countdown_threads)
        logger.info(f"THREAD REGISTRY STATUS: {thread_count} threads registered")
        
        if thread_count > 0:
            for i, thread in enumerate(_countdown_threads, 1):
                thread_name = getattr(thread, 'name', 'Unknown')
                thread_ident = getattr(thread, 'ident', 'Unknown')
                is_alive = thread.is_alive()
                force_exit = getattr(thread, '_force_exit', False)
                status = "ALIVE" if is_alive else "DEAD"
                force_status = "FORCE_EXIT" if force_exit else "NORMAL"
                logger.info(f"   {i}. {thread_name} (ID: {thread_ident}) - {status} - {force_status}")
        else:
            logger.info("   No threads registered")

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
        logger.info(f"STARTING COUNTDOWN: {seconds} seconds (Generation: {self._generation_id + 1})")

        # CRITICAL FIX: Kill ALL countdown threads globally before starting new one
        logger.info("Cleaning up existing threads before starting new countdown...")
        _log_thread_registry_status()  # Log before cleanup
        _kill_all_countdown_threads()
        _log_thread_registry_status()  # Log after cleanup
        
        # Wait a moment to ensure all threads are dead
        time.sleep(0.1)

        # Reset state for new countdown
        self._reset_state()

        # Store callback
        self.on_countdown_complete = on_complete

        # CRITICAL FIX: Reset completion event for new countdown
        self._completion_event.clear()
        self._completion_result = None

        # Increment generation ID to invalidate any old threads
        self._generation_id += 1
        local_generation = self._generation_id
        logger.info(f"New generation ID: {local_generation}")

        # Set countdown as active
        with self._state_lock:
            self._countdown_active = True
            self._paused = False
            self._cancelled = False

        # Start countdown thread
        def _thread_target():
            thread_name = f"CountdownThread#{local_generation}"
            logger.info(f"THREAD STARTED: {thread_name} (ID: {threading.current_thread().ident})")
            try:
                self._countdown_loop(seconds, text, next_text, last_text, local_generation)
            except Exception as e:
                logger.error(f"THREAD ERROR in {thread_name}: {e}")
            finally:
                logger.info(f"THREAD ENDED: {thread_name}")

        self.countdown_thread = threading.Thread(
            target=_thread_target,
            daemon=True,
            name=f"CountdownThread#{local_generation}",
        )
        
        # CRITICAL FIX: Register thread globally
        with _thread_registry_lock:
            _countdown_threads.add(self.countdown_thread)
            current_thread_count = len(_countdown_threads)
            logger.info(f"REGISTERED THREAD: {self.countdown_thread.name} (Total threads: {current_thread_count})")
        
        # Add force exit flag
        self.countdown_thread._force_exit = False
        
        logger.info(f"STARTING THREAD: {self.countdown_thread.name}")
        self.countdown_thread.start()

        # CRITICAL FIX: Wait for completion event instead of thread join
        # This ensures proper synchronization
        logger.info(f"WAITING for countdown completion (timeout: {seconds + 10}s)...")
        
        # Wait for completion with timeout, but handle paused state
        wait_start_time = time.time()
        timeout_reached = False
        while not self._completion_event.is_set():
            # Check if we should timeout
            if time.time() - wait_start_time > seconds + 10:
                # Only timeout if not paused - if paused, keep waiting
                if not self.paused:
                    logger.warning(f"COUNTDOWN TIMEOUT: {self.countdown_thread.name}")
                    timeout_reached = True
                    break
                else:
                    logger.info(f"Countdown paused - extending timeout for {self.countdown_thread.name}")
                    # Reset timeout for paused countdown
                    wait_start_time = time.time()
            
            # Wait a short time before checking again
            if self._completion_event.wait(timeout=0.1):
                break
        
        if timeout_reached:
            result = self._get_final_state()
        else:
            # Countdown completed normally
            result = self._completion_result or self._get_final_state()
            # Log completion
            if self.countdown_thread and hasattr(self.countdown_thread, 'name'):
                logger.info(f"COUNTDOWN COMPLETED: {self.countdown_thread.name}")
            else:
                logger.info("COUNTDOWN COMPLETED: Unknown thread")

        # CRITICAL FIX: Unregister thread from global registry
        with _thread_registry_lock:
            _countdown_threads.discard(self.countdown_thread)
            remaining_threads = len(_countdown_threads)
            logger.info(f"UNREGISTERED THREAD: {self.countdown_thread.name} (Remaining threads: {remaining_threads})")

        return result

    def force_reset(self) -> None:
        """Force reset the countdown service state."""
        logger.info("FORCE RESETTING countdown service")
        
        # CRITICAL FIX: Kill all countdown threads globally
        _kill_all_countdown_threads()
        
        # Reset all state
        with self._state_lock:
            self._countdown_active = False
            self._paused = False
            self._cancelled = False
        
        # Clear completion event
        self._completion_event.clear()
        self._completion_result = None
        
        # Reset thread reference
        self.countdown_thread = None
        
        logger.info("FORCE RESET COMPLETED")

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
        seconds: float,
        text: Optional[str],
        next_text: Optional[str],
        last_text: Optional[str],
        local_generation: int,
    ) -> None:
        """
        Main countdown loop running in separate thread.

        Args:
            seconds: Total countdown duration
            text: Current text to display
            next_text: Next text to display
            last_text: Previous text
            local_generation: Generation ID for this thread
        """
        thread_name = f"CountdownThread#{local_generation}"
        logger.info(f"COUNTDOWN LOOP STARTED: {thread_name} for {seconds}s")
        
        try:
            # Initialize countdown
            total = max(0.0, float(seconds))
            remaining = float(total)
            start_time = time.time()
            max_duration = total + 60  # Allow 60 seconds extra for safety

            # Update UI immediately
            self._update_display(remaining, total, text, next_text)

            # Initialize tick_count before any pause checks
            tick_count = 0

            # CRITICAL FIX: Check pause state immediately when thread starts
            # This prevents the countdown from running even briefly when resuming from pause
            if self.paused:
                logger.info(f"PAUSED at {remaining:.1f}s remaining (tick {tick_count})")
                pause_start = time.time()
                while self.paused and self.countdown_active and not self.cancelled:
                    # CRITICAL FIX: Check force exit flag
                    if hasattr(self.countdown_thread, '_force_exit') and self.countdown_thread._force_exit:
                        logger.info(f"FORCE EXIT requested during pause")
                        return
                    
                    time.sleep(WAIT_TICK)  # 0.05 seconds for responsive pause
                    if self._stop_event.is_set():
                        logger.info(f"STOP event set during pause")
                        break
                    # Prevent infinite pause
                    if time.time() - pause_start > 300:  # 5 minutes max pause
                        logger.warning(f"PAUSE TIMEOUT - forcing resume")
                        break

            # Main countdown loop
            while (
                remaining > 0
                and self.countdown_active
                and not self.cancelled
                and not self._stop_event.is_set()
            ):
                tick_count += 1
                
                # If a newer generation started, exit silently
                with self._state_lock:
                    if local_generation != self._generation_id:
                        logger.info(f"SUPERSEDED by newer generation {self._generation_id} - exiting")
                        return

                # Check for timeout
                if time.time() - start_time > max_duration:
                    logger.error(f"TIMEOUT reached after {max_duration}s")
                    break
                    
                # CRITICAL FIX: Check force exit flag
                if hasattr(self.countdown_thread, '_force_exit') and self.countdown_thread._force_exit:
                    logger.info(f"FORCE EXIT requested during countdown (tick {tick_count})")
                    return
                    
                # CRITICAL FIX: Actually pause the countdown timer
                # When paused, don't decrement remaining time
                if self.paused:
                    if tick_count % 20 == 0:  # Log every 20 ticks when paused (every 1 second)
                        logger.info(f"PAUSED at {remaining:.1f}s remaining (tick {tick_count})")
                    time.sleep(WAIT_TICK)  # 0.05 seconds for responsive pause
                    continue

                # Update display
                self._schedule_ui_update(remaining, total, text, next_text)

                # Wait for next tick
                time.sleep(1.0)

                # Decrement remaining time
                remaining -= 1.0
                
                # Log progress every 10 seconds
                if tick_count % 10 == 0:
                    logger.info(f"Progress: {remaining:.1f}s remaining (tick {tick_count})")

            # Countdown completed
            self.countdown_active = False
            elapsed_time = time.time() - start_time
            logger.info(f"COUNTDOWN LOOP COMPLETED after {elapsed_time:.2f}s (tick {tick_count})")

            # CRITICAL FIX: Don't complete countdown if it was paused
            # This prevents automation from continuing when paused
            if self.paused:
                logger.info(f"COMPLETED while PAUSED - not triggering completion")
                # Don't call completion callback or set completion event
                return

            # SIMPLIFIED FIX: Single, immediate UI reset after countdown completion
            # This eliminates the race condition by doing one clean reset
            try:
                # Reset UI to final state immediately
                self._update_display(0.0, total, text, next_text)
            except Exception as e:
                logger.warning(f"Error in final UI update: {e}")

            # Call completion callback if provided
            if self.on_countdown_complete:
                try:
                    logger.info(f"Calling completion callback...")
                    final_state = self._get_final_state()
                    self.on_countdown_complete(final_state)
                    # Store result for synchronization
                    self._completion_result = final_state
                    logger.info(f"Completion callback executed successfully")
                except Exception as e:
                    logger.error(f"Error in completion callback: {e}")
                    self._completion_result = self._get_final_state()
            else:
                logger.info(f"No completion callback provided - storing result only")
                # Store result for synchronization even without callback
                self._completion_result = self._get_final_state()

            # Signal completion event to unblock any waiting threads
            self._completion_event.set()
            logger.info(f"Completion event signaled")

        except Exception as e:
            logger.error(f"Error in countdown loop: {e}")
            # Ensure completion event is set even on error
            self._completion_event.set()
            logger.info(f"Completion event signaled after error")

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
        logger.info(f"TOGGLE PAUSE called - countdown_active: {self.countdown_active}")
        
        if not self.countdown_active:
            logger.warning("Cannot toggle pause - countdown not active")
            return

        with self._state_lock:
            old_paused = self._paused
            self._paused = not self._paused
            new_paused = self._paused
        
        logger.info(f"PAUSE STATE CHANGED: {old_paused} -> {new_paused}")

        try:
            if self.pause_btn:
                if self.paused:
                    self.pause_btn.configure(
                        text=BTN_RESUME,
                        fg_color=COLOR_PRIMARY,
                        hover_color=COLOR_PRIMARY,
                    )
                    logger.info("Pause button updated to RESUME")
                else:
                    self.pause_btn.configure(
                        text=BTN_PAUSE,
                        fg_color=BUTTON_BG,
                        hover_color=BUTTON_HOVER,
                    )
                    logger.info("Pause button updated to PAUSE")
        except (AttributeError, tkinter.TclError) as e:
            logger.error(f"Error updating pause button: {e}")

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

    def cleanup_orphaned_threads(self) -> bool:
        """
        Detect and cleanup any orphaned countdown threads.
        
        Returns:
            True if orphaned threads were found and cleaned up, False otherwise
        """
        try:
            # Check if there's a thread running but countdown is not active
            if self.countdown_thread and self.countdown_thread.is_alive():
                if not self.countdown_active:
                    logger.warning("Detected orphaned countdown thread - forcing cleanup")
                    self.force_reset()
                    return True
                else:
                    logger.info("Countdown thread is running normally")
            else:
                logger.info("No countdown threads running")
            
            return False
        except Exception as e:
            logger.warning(f"Error checking for orphaned threads: {e}")
            return False

    def get_thread_status(self) -> Dict[str, Any]:
        """Get detailed thread status for debugging."""
        thread = self.countdown_thread
        return {
            "countdown_active": self.countdown_active,
            "thread_exists": thread is not None,
            "thread_alive": thread.is_alive() if thread else False,
            "thread_name": getattr(thread, "name", None) if thread else None,
            "thread_ident": getattr(thread, "ident", None) if thread else None,
            "paused": self.paused,
            "cancelled": self.cancelled,
            "stop_event_set": self._stop_event.is_set(),
            "generation_id": self._generation_id,
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
        thread_name = getattr(self.countdown_thread, 'name', 'Unknown') if self.countdown_thread else 'Unknown'
        logger.info(f"STOPPING COUNTDOWN: {thread_name}")
        
        # CRITICAL FIX: Set stop event first to signal threads to stop
        self._stop_event.set()
        
        # Set cancelled state
        with self._state_lock:
            self._cancelled = True
            self._countdown_active = False
        
        # CRITICAL FIX: Wait for thread to actually stop
        if self.countdown_thread and self.countdown_thread.is_alive():
            logger.info(f"Waiting for {thread_name} to stop...")
            self.countdown_thread.join(timeout=2.0)  # Increased timeout
            if self.countdown_thread.is_alive():
                logger.warning(f"did not stop within timeout")
            else:
                logger.info(f"stopped successfully")
        else:
            logger.info(f"was not running")
        
        # CRITICAL FIX: Unregister thread from global registry
        with _thread_registry_lock:
            _countdown_threads.discard(self.countdown_thread)
            remaining_threads = len(_countdown_threads)
            logger.info(f"UNREGISTERED THREAD: {thread_name} (Remaining threads: {remaining_threads})")
        
        # Signal completion event to unblock any waiting threads
        self._completion_event.set()
        
        # Reset thread reference
        self.countdown_thread = None
        
        logger.info(f"STOP COMPLETED: {thread_name}")
