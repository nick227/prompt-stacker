"""
Centralized Automation Controller

This module provides a unified, reliable automation controller that replaces
the fragmented automation architecture. It centralizes all automation state,
event handling, and coordination between UI, countdown, and automation logic.

Key Features:
- Single source of truth for automation state
- Unified event handling (start/stop/pause/next)
- Reliable countdown integration
- Thread-safe operations
- Simplified debugging and maintenance

Author: Automation System
Version: 3.0 - Centralized Architecture
"""

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import pyautogui

logger = logging.getLogger(__name__)


class AutomationState(Enum):
    """Automation state enumeration."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"


class CountdownPhase(Enum):
    """Countdown phase enumeration."""
    START_DELAY = "start_delay"
    GET_READY = "get_ready"
    MAIN_WAIT = "main_wait"
    COOLDOWN = "cooldown"


@dataclass
class AutomationConfig:
    """Automation configuration."""
    start_delay: float = 5.0
    get_ready_delay: float = 2.0
    main_wait: float = 399.0
    cooldown: float = 0.2

    # Validation settings
    validate_coordinates: bool = True
    validate_prompts: bool = True
    validate_timers: bool = True

    # Safety settings
    max_retries: int = 3
    operation_timeout: float = 10.0
    countdown_timeout_buffer: float = 60.0


@dataclass
class AutomationContext:
    """Current automation context."""
    prompts: List[str]
    coordinates: Dict[str, Tuple[int, int]]
    timers: List[float]
    current_prompt_index: int = 0
    current_phase: CountdownPhase = CountdownPhase.START_DELAY

    def get_current_prompt(self) -> Optional[str]:
        """Get current prompt text."""
        if 0 <= self.current_prompt_index < len(self.prompts):
            return self.prompts[self.current_prompt_index]
        return None

    def get_next_prompt(self) -> Optional[str]:
        """Get next prompt text."""
        next_index = self.current_prompt_index + 1
        if 0 <= next_index < len(self.prompts):
            return self.prompts[next_index]
        return None

    def has_more_prompts(self) -> bool:
        """Check if there are more prompts to process."""
        return self.current_prompt_index < len(self.prompts) - 1

    def advance_prompt(self) -> bool:
        """Advance to next prompt."""
        if self.has_more_prompts():
            self.current_prompt_index += 1
            return True
        return False


class AutomationController:
    """
    Centralized automation controller that manages the complete automation lifecycle.

    This controller is the single source of truth for automation state and coordinates
    all automation activities including UI updates, countdown management, and
    prompt processing.
    """

    def __init__(self, ui_session, config: Optional[AutomationConfig] = None):
        """
        Initialize the automation controller.

        Args:
            ui_session: Reference to the main UI session
        """
        self.ui = ui_session
        self.config = config or AutomationConfig()

        # State management
        self._state = AutomationState.IDLE
        self._state_lock = threading.RLock()
        self._context: Optional[AutomationContext] = None

        # Thread management
        self._automation_thread: Optional[threading.Thread] = None
        self._stop_requested = threading.Event()
        self._pause_requested = threading.Event()

        # Event callbacks
        self._state_callbacks: List[Callable[[AutomationState], None]] = []
        self._progress_callbacks: List[Callable[[int, int], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []

        # Configuration tracking
        self._last_config_snapshot = None
        self._config_change_detected = False

        # Next button tracking
        self._next_button_pressed = False

        # Integration with existing services
        self._countdown_service = None
        self._setup_countdown_integration()

        logger.info("AutomationController initialized")

    # =============================================================================
    # PUBLIC API - AUTOMATION CONTROL
    # =============================================================================

    def start_automation(self) -> bool:
        """
        Start the automation process.

        Returns:
            True if automation started successfully, False otherwise
        """
        with self._state_lock:
            if self._state != AutomationState.IDLE:
                logger.warning(f"Cannot start automation - current state: "
                             f"{self._state}")
                return False

            # Validate prerequisites
            if not self._validate_prerequisites():
                return False

            # Initialize automation context
            self._context = self._create_automation_context()
            if not self._context:
                return False

            # Update state
            self._set_state(AutomationState.STARTING)

            # Clear stop/pause flags
            self._stop_requested.clear()
            self._pause_requested.clear()

            # Update Next button state (disabled when starting)
            self._update_next_button_state()

            # Start automation thread
            self._automation_thread = threading.Thread(
                target=self._automation_main_loop,
                name="AutomationController",
                daemon=True,
            )
            self._automation_thread.start()

            logger.info("Automation started successfully")
            return True

    def stop_automation(self) -> None:
        """Stop the automation process."""
        with self._state_lock:
            if self._state in [AutomationState.IDLE, AutomationState.STOPPING]:
                return

            logger.info("Stopping automation...")
            self._set_state(AutomationState.STOPPING)

            # Signal stop to automation thread
            self._stop_requested.set()

            # Clear pause if set
            if self._pause_requested.is_set():
                self._pause_requested.clear()
                self._update_countdown_pause_state(False)

            # Stop countdown if active
            self._stop_countdown()

            # Wait for automation thread to finish
            if self._automation_thread and self._automation_thread.is_alive():
                self._automation_thread.join(timeout=5.0)
                if self._automation_thread.is_alive():
                    logger.warning("Automation thread did not stop gracefully")

            # Reset state
            self._automation_thread = None
            self._context = None
            self._set_state(AutomationState.IDLE)

            # Update Next button state (disabled when stopped)
            self._update_next_button_state()

            logger.info("Automation stopped")

    def pause_automation(self) -> None:
        """Pause the automation process."""
        with self._state_lock:
            if self._state != AutomationState.RUNNING:
                logger.warning(f"Cannot pause automation - current state: "
                             f"{self._state}")
                return

            logger.info("Pausing automation...")
            self._pause_requested.set()
            self._set_state(AutomationState.PAUSED)
            self._update_countdown_pause_state(True)

    def resume_automation(self) -> None:
        """Resume the automation process."""
        with self._state_lock:
            if self._state != AutomationState.PAUSED:
                logger.warning(f"Cannot resume automation - current state: "
                             f"{self._state}")
                return

            logger.info("Resuming automation...")
            self._pause_requested.clear()
            self._set_state(AutomationState.RUNNING)
            self._update_countdown_pause_state(False)

    def toggle_pause(self) -> None:
        """Toggle pause/resume state."""
        with self._state_lock:
            if self._state == AutomationState.RUNNING:
                self.pause_automation()
            elif self._state == AutomationState.PAUSED:
                self.resume_automation()
            else:
                logger.warning(f"Cannot toggle pause - current state: {self._state}")

    def next_prompt(self) -> bool:
        """
        Advance to next prompt and restart automation cycle.

        This method will advance the prompt index and restart the automation
        cycle to begin processing the next prompt immediately.

        Returns:
            True if advanced successfully, False otherwise
        """
        with self._state_lock:
            if not self._context:
                logger.warning("Cannot advance prompt - no active automation context")
                return False

            if not self._context.has_more_prompts():
                logger.warning("Cannot advance prompt - already at last prompt")
                return False

            # CRITICAL: Stop current countdown to trigger next cycle
            if self._countdown_service and self._countdown_service.is_active():
                logger.info("Stopping current countdown to trigger next cycle")
                self._next_button_pressed = True  # Mark that Next button was pressed
                self._countdown_service.stop()

            # Don't advance prompt here - let the automation loop handle it
            # This ensures the Ready countdown runs for the next prompt
            logger.info("Next button pressed - will advance to next prompt after current cycle")

            # Temporarily disable Next button for 2 seconds to prevent rapid clicking
            self._temporarily_disable_next_button()

            return True

            return False

    # =============================================================================
    # PUBLIC API - STATE ACCESS
    # =============================================================================

    def get_state(self) -> AutomationState:
        """Get current automation state."""
        with self._state_lock:
            return self._state

    def is_running(self) -> bool:
        """Check if automation is running."""
        return self.get_state() in [AutomationState.RUNNING, AutomationState.PAUSED]

    def is_paused(self) -> bool:
        """Check if automation is paused."""
        return self.get_state() == AutomationState.PAUSED

    def get_current_prompt_index(self) -> int:
        """Get current prompt index."""
        with self._state_lock:
            return self._context.current_prompt_index if self._context else 0

    def get_total_prompts(self) -> int:
        """Get total number of prompts."""
        with self._state_lock:
            return len(self._context.prompts) if self._context else 0

    def get_progress(self) -> Tuple[int, int]:
        """Get automation progress as (current, total)."""
        with self._state_lock:
            if self._context:
                return (self._context.current_prompt_index + 1,
                       len(self._context.prompts))
            return (0, 0)

    # =============================================================================
    # PUBLIC API - EVENT CALLBACKS
    # =============================================================================

    def add_state_callback(self, callback: Callable[[AutomationState], None]) -> None:
        """Add callback for state changes."""
        self._state_callbacks.append(callback)

    def add_progress_callback(self, callback: Callable[[int, int], None]) -> None:
        """Add callback for progress updates."""
        self._progress_callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for error notifications."""
        self._error_callbacks.append(callback)

    # =============================================================================
    # PRIVATE IMPLEMENTATION - AUTOMATION LOOP
    # =============================================================================

    def _automation_main_loop(self) -> None:
        """Main automation loop - runs in separate thread."""
        try:
            logger.info("=== AUTOMATION MAIN LOOP STARTED ===")
            self._set_state(AutomationState.RUNNING)

            # Start delay countdown
            if not self._run_countdown_phase(CountdownPhase.START_DELAY):
                return

            # Process all prompts
            while (self._context and
                   self._context.current_prompt_index < len(self._context.prompts)):
                if self._stop_requested.is_set():
                    logger.info("Automation stopped by user request")
                    return

                # Check for configuration changes
                if self._check_configuration_changes():
                    logger.info("Configuration changes detected - continuing with updated values")

                prompt_index = self._context.current_prompt_index
                logger.info(f"=== PROCESSING PROMPT {prompt_index + 1}/"
                          f"{len(self._context.prompts)} ===")

                # Get ready countdown
                if not self._run_countdown_phase(CountdownPhase.GET_READY):
                    # Check if cancelled by Next button - restart cycle
                    if self._next_button_pressed:
                        logger.info("Get ready countdown cancelled by Next button - restarting cycle")
                        continue  # Restart the loop for the new prompt
                    return

                # Execute automation steps for current prompt
                automation_success = self._execute_prompt_automation()
                if not automation_success:
                    logger.warning("Automation step failed, but continuing to next prompt")
                    # Don't return - continue to next prompt instead of breaking the loop

                # Main wait countdown
                if not self._run_countdown_phase(CountdownPhase.MAIN_WAIT):
                    # Check if cancelled by Next button - restart cycle
                    if self._next_button_pressed:
                        logger.info("Main wait countdown cancelled by Next button - restarting cycle")
                        continue  # Restart the loop for the new prompt
                    logger.warning("Main wait countdown failed, but continuing to next prompt")
                    # Don't return - continue to next prompt instead of breaking the loop

                # Accept button click
                accept_success = self._click_accept_button()
                if not accept_success:
                    logger.warning("Accept button click failed, but continuing to next prompt")
                    # Don't return - continue to next prompt instead of breaking the loop

                # Cooldown countdown
                if not self._run_countdown_phase(CountdownPhase.COOLDOWN):
                    # Check if cancelled by Next button - restart cycle
                    if self._next_button_pressed:
                        logger.info("Cooldown countdown cancelled by Next button - restarting cycle")
                        continue  # Restart the loop for the new prompt
                    logger.warning("Cooldown countdown failed, but continuing to next prompt")
                    # Don't return - continue to next prompt instead of breaking the loop

                # Advance to next prompt (handle Next button press)
                if self._next_button_pressed:
                    # Next button was pressed - advance to next prompt
                    if self._context.has_more_prompts():
                        old_index = self._context.current_prompt_index
                        self._context.advance_prompt()
                        new_index = self._context.current_prompt_index
                        self._update_ui_for_current_prompt()
                        self._notify_progress_callbacks(
                            self._context.current_prompt_index,
                            len(self._context.prompts),
                        )
                        logger.info(f"Advanced from prompt {old_index + 1} to {new_index + 1} via Next button")
                        self._next_button_pressed = False  # Reset the flag
                    else:
                        logger.info("All prompts completed")
                        break
                elif self._context.has_more_prompts():
                    # Normal advancement (not via Next button)
                    self._context.advance_prompt()
                    self._update_ui_for_current_prompt()
                    self._notify_progress_callbacks(
                        self._context.current_prompt_index,
                        len(self._context.prompts),
                    )
                    logger.info(f"Advanced to prompt "
                              f"{self._context.current_prompt_index + 1}")
                else:
                    logger.info("All prompts completed")
                    break

            # Automation completed successfully
            self._set_state(AutomationState.COMPLETED)
            
            # Update Next button state (disabled when completed)
            self._update_next_button_state()
            
            logger.info("=== AUTOMATION COMPLETED SUCCESSFULLY ===")

        except Exception as e:
            logger.error(f"Automation failed with error: {e}")
            self._set_state(AutomationState.FAILED)
            
            # Update Next button state (disabled when failed)
            self._update_next_button_state()
            
            self._notify_error_callbacks(str(e))

        finally:
            # Cleanup
            with self._state_lock:
                if self._state not in [AutomationState.STOPPING]:
                    self._set_state(AutomationState.IDLE)
                self._context = None
                self._automation_thread = None

    def _run_countdown_phase(self, phase: CountdownPhase) -> bool:
        """
        Run a countdown phase and handle pause/resume.

        Args:
            phase: The countdown phase to run

        Returns:
            True if countdown completed successfully, False if cancelled/stopped
        """
        if not self._context:
            return False

        # Determine countdown duration and text
        duration, text = self._get_countdown_config(phase)
        if duration <= 0:
            return True  # Skip zero-duration countdowns

        logger.info(f"Starting {phase.value} countdown for {duration}s: {text}")

        # Update context
        self._context.current_phase = phase

        # Update Next button state based on current phase
        self._update_next_button_state()

        # Run countdown with integrated pause handling
        result = self._run_countdown_with_pause_handling(duration, text)

        if result.get("cancelled"):
            logger.info(f"{phase.value} countdown was cancelled")
            # Check if it was cancelled by Next button
            if self._next_button_pressed:
                logger.info("Countdown cancelled by Next button - will restart cycle")
                self._next_button_pressed = False  # Reset flag
                return True  # Allow continuation to restart cycle
            return False

        logger.info(f"{phase.value} countdown completed successfully")
        return True

    def _run_countdown_with_pause_handling(self, duration: float,
                                         text: str) -> Dict[str, Any]:
        """
        Run countdown with integrated pause handling.

        This method coordinates with the CountdownService to provide unified
        pause/resume behavior that doesn't cause race conditions.
        """
        if not self._countdown_service:
            logger.warning("No countdown service available - using simple delay")
            time.sleep(duration)
            return {"cancelled": False, "paused": False}

        # Start countdown
        result = self._countdown_service.start_countdown(
            seconds=duration,
            text=self._context.get_current_prompt() if self._context else None,
            next_text=self._context.get_next_prompt() if self._context else None,
            last_text=text,
        )

        # Wait for countdown to actually complete if it was paused
        if result.get("paused"):
            logger.info("Countdown was paused - waiting for actual completion")
            while self._countdown_service.is_active():
                if self._stop_requested.is_set():
                    result["cancelled"] = True
                    break
                time.sleep(0.1)
            logger.info("Countdown resumed and completed")

        return result

    def _get_countdown_config(self, phase: CountdownPhase) -> Tuple[float, str]:
        """Get countdown duration and text for a phase with real-time UI values."""
        if not self._context:
            return 0.0, ""

        current_index = self._context.current_prompt_index
        total_prompts = len(self._context.prompts)

        # Get real-time values from UI
        try:
            if phase == CountdownPhase.START_DELAY:
                # Use UI get ready delay for start delay, or config default
                start_delay = (float(self.ui.get_ready_delay_var.get()) if hasattr(self.ui, "get_ready_delay_var")
                              else self.config.start_delay)
                return start_delay, "About to start!"

            if phase == CountdownPhase.GET_READY:
                # Use UI get ready delay
                get_ready_delay = (float(self.ui.get_ready_delay_var.get()) if hasattr(self.ui, "get_ready_delay_var")
                                 else self.config.get_ready_delay)
                return get_ready_delay, f"Starting {current_index + 1} of {total_prompts}"

            if phase == CountdownPhase.MAIN_WAIT:
                # Use UI main wait
                main_wait = (float(self.ui.main_wait_var.get()) if hasattr(self.ui, "main_wait_var")
                           else self.config.main_wait)
                return main_wait, self._context.get_current_prompt() or ""

            if phase == CountdownPhase.COOLDOWN:
                # Use UI cooldown if available, otherwise config default
                cooldown = (float(self.ui.get_ready_delay_var.get()) * 0.1 if hasattr(self.ui, "get_ready_delay_var")
                          else self.config.cooldown)
                return cooldown, "Waiting..."
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error getting UI timer values, using config defaults: {e}")
            # Fallback to config values
            if phase == CountdownPhase.START_DELAY:
                return self.config.start_delay, "About to start!"
            if phase == CountdownPhase.GET_READY:
                return self.config.get_ready_delay, f"Starting {current_index + 1} of {total_prompts}"
            if phase == CountdownPhase.MAIN_WAIT:
                return self.config.main_wait, self._context.get_current_prompt() or ""
            if phase == CountdownPhase.COOLDOWN:
                return self.config.cooldown, "Waiting..."

        return 0.0, ""

    # =============================================================================
    # PRIVATE IMPLEMENTATION - AUTOMATION STEPS
    # =============================================================================

    def _execute_prompt_automation(self) -> bool:
        """Execute automation steps for the current prompt with optimized flow."""
        if not self._context:
            return False

        current_prompt = self._context.get_current_prompt()
        if not current_prompt:
            logger.error("No current prompt to process")
            return False

        try:
            # Import automation functions
            try:
                from .automator import (
                    click_button_or_fallback,
                    click_with_timeout,
                    paste_text_safely,
                    perform_paste_operation,
                )
                from .dpi import enable_windows_dpi_awareness
                from .win_focus import CursorWindow
            except ImportError:
                # Fallback for standalone execution
                from automator import (
                    click_button_or_fallback,
                    click_with_timeout,
                    paste_text_safely,
                    perform_paste_operation,
                )
                from dpi import enable_windows_dpi_awareness
                from win_focus import CursorWindow

            # Enable DPI awareness
            enable_windows_dpi_awareness()

            # Get window and real-time coordinates
            win = CursorWindow()
            coords = self.ui.get_coords()  # Get fresh coordinates from UI

            # OPTIMIZED FLOW:
            # 1. Copy text to clipboard (prepare for paste)
            logger.info(f"Copying text to clipboard: {current_prompt[:50]}...")
            clipboard_success = paste_text_safely(current_prompt)
            if not clipboard_success:
                logger.warning("Failed to copy text to clipboard, but continuing")
                # Don't return False - allow the automation to continue

            # 2. Click Accept button first (if coordinates exist)
            if "accept" in coords:
                logger.info(f"Clicking Accept button at {coords['accept']}")
                accept_success = click_button_or_fallback(win, coords["accept"],
                                               r"^(Accept|Continue|Proceed)$")
                if not accept_success:
                    logger.warning("Failed to click Accept button, but continuing")
                time.sleep(0.1)  # Brief delay after accept

            # 3. Click input field with focus validation
            logger.info(f"Clicking input field at {coords['input']}")
            click_success = click_with_timeout(coords["input"])
            if not click_success:
                logger.warning("Failed to click input field, but continuing")
                # Don't return False - allow the automation to continue

            # 4. Optimized focus delay (reduced from 0.2s to 0.1s)
            time.sleep(0.1)  # Reduced focus delay

            # 5. Clear input field and paste text
            logger.info(f"Clearing input field and pasting text: {current_prompt[:50]}...")
            try:
                # Clear existing content
                pyautogui.hotkey("ctrl", "a")
                time.sleep(0.05)  # Brief delay for clear

                # Paste new text
                paste_success = perform_paste_operation(current_prompt)
                if not paste_success:
                    logger.warning("Failed to paste text, but continuing with automation")
                else:
                    logger.info("Paste operation completed successfully")
            except Exception as e:
                logger.warning(f"Error during paste operation: {e}")

            # 6. Brief validation delay (reduced from 0.5s to 0.2s)
            time.sleep(0.2)  # Reduced validation delay

            # 7. Click submit button
            logger.info(f"Clicking submit button at {coords['submit']}")
            submit_success = click_button_or_fallback(win, coords["submit"],
                                           r"^(Send|Submit|Enter|Run)$")
            if not submit_success:
                logger.warning("Failed to click submit button, but continuing with automation")
                # Don't return False - allow the automation to continue
                # The user can manually submit if needed

            return True

        except Exception as e:
            logger.error(f"Error during prompt automation: {e}")
            return False

    def _click_accept_button(self) -> bool:
        """Click the accept button with timeout protection (now handled in main flow)."""
        # This method is now redundant since accept button is clicked in _execute_prompt_automation
        # Keeping for backward compatibility but it's a no-op
        logger.info("Accept button click handled in main automation flow")
        return True

    # =============================================================================
    # PRIVATE IMPLEMENTATION - STATE MANAGEMENT
    # =============================================================================

    def _set_state(self, new_state: AutomationState) -> None:
        """Set automation state and notify callbacks."""
        old_state = self._state
        self._state = new_state

        if old_state != new_state:
            logger.info(f"Automation state changed: {old_state.value} -> "
                       f"{new_state.value}")

            self._notify_state_callbacks(new_state)

    def _notify_state_callbacks(self, state: AutomationState) -> None:
        """Notify all state change callbacks."""

        for callback in self._state_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")

    def _notify_progress_callbacks(self, current: int, total: int) -> None:
        """Notify all progress callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(current, total)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def _notify_error_callbacks(self, error_message: str) -> None:
        """Notify all error callbacks."""
        for callback in self._error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    # =============================================================================
    # PRIVATE IMPLEMENTATION - VALIDATION & SETUP
    # =============================================================================

    def _validate_prerequisites(self) -> bool:
        """Validate all prerequisites for starting automation."""
        if not self.ui:
            logger.error("No UI session available")
            return False

        # Validate coordinates
        if self.config.validate_coordinates:
            coords_validation = self.ui.coordinate_service.validate_coordinates()
            if not all(coords_validation.values()):
                logger.error("Missing required coordinates")
                return False

        # Validate prompts
        if self.config.validate_prompts:
            prompts = self.ui.get_prompts_safe()
            if not prompts:
                logger.error("No prompts available")
                return False

        # Validate timers
        if self.config.validate_timers and not self._validate_timers():
            logger.error("Invalid timer values")
            return False

        return True

    def _validate_timers(self) -> bool:
        """Validate timer values with enhanced error handling."""
        try:
            if not hasattr(self.ui, "main_wait_var") or not hasattr(self.ui, "get_ready_delay_var"):
                logger.warning("Timer variables not available")
                return False

            main_wait_str = self.ui.main_wait_var.get().strip()
            get_ready_str = self.ui.get_ready_delay_var.get().strip()

            # Handle empty strings
            if not main_wait_str or not get_ready_str:
                logger.warning("Empty timer values detected")
                return False

            main_wait = float(main_wait_str)
            get_ready = float(get_ready_str)

            # Validate reasonable ranges
            if main_wait < 0 or get_ready < 0:
                logger.warning("Negative timer values detected")
                return False

            if main_wait > 3600 or get_ready > 3600:  # More than 1 hour
                logger.warning("Unreasonably large timer values detected")
                return False

            return True
        except ValueError as e:
            logger.warning(f"Invalid timer values: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating timers: {e}")
            return False

    def _create_automation_context(self) -> Optional[AutomationContext]:
        """Create automation context from current UI state."""
        try:
            prompts = self.ui.get_prompts_safe()
            coordinates = self.ui.get_coords()
            timers = self.ui.get_timers()

            # Store configuration snapshot for change detection
            self._last_config_snapshot = {
                "coordinates": coordinates.copy(),
                "timers": timers,
                "prompts_count": len(prompts),
            }

            return AutomationContext(
                prompts=prompts,
                coordinates=coordinates,
                timers=timers,
                current_prompt_index=self.ui.current_prompt_index,
            )
        except Exception as e:
            logger.error(f"Failed to create automation context: {e}")
            return None

    def _check_configuration_changes(self) -> bool:
        """Check if configuration has changed since last snapshot."""
        if not self._last_config_snapshot:
            return False

        try:
            current_coords = self.ui.get_coords()
            current_timers = self.ui.get_timers()
            current_prompts = self.ui.get_prompts_safe()

            # Check for changes
            coords_changed = current_coords != self._last_config_snapshot["coordinates"]
            timers_changed = current_timers != self._last_config_snapshot["timers"]
            prompts_changed = len(current_prompts) != self._last_config_snapshot["prompts_count"]

            if coords_changed or timers_changed or prompts_changed:
                logger.info("Configuration changes detected during automation")
                self._config_change_detected = True
                return True

            return False
        except Exception as e:
            logger.warning(f"Error checking configuration changes: {e}")
            return False

    # =============================================================================
    # PRIVATE IMPLEMENTATION - COUNTDOWN INTEGRATION
    # =============================================================================

    def _setup_countdown_integration(self) -> None:
        """Set up integration with existing countdown service."""
        if hasattr(self.ui, "countdown_service"):
            self._countdown_service = self.ui.countdown_service
            # Set up callback for UI state updates
            self._countdown_service.on_pause_state_changed = (
                self._on_countdown_pause_changed
            )

    def _on_countdown_pause_changed(self, is_paused: bool) -> None:
        """Handle countdown pause state changes."""
        try:
            # Update automation state to match countdown pause state
            with self._state_lock:
                if is_paused and self._state == AutomationState.RUNNING:
                    self._set_state(AutomationState.PAUSED)
                elif not is_paused and self._state == AutomationState.PAUSED:
                    self._set_state(AutomationState.RUNNING)

            # Update UI
            self._update_ui_for_current_prompt()

        except Exception as e:
            logger.error(f"Error handling countdown pause change: {e}")

    def _update_countdown_pause_state(self, paused: bool) -> None:
        """Update countdown service pause state."""
        if self._countdown_service and self._countdown_service.is_active():
            current_paused = self._countdown_service.is_paused()
            if current_paused != paused:
                self._countdown_service.toggle_pause()

    def _stop_countdown(self) -> None:
        """Stop the countdown service if active."""
        if self._countdown_service and self._countdown_service.is_active():
            self._countdown_service.stop()

    # =============================================================================
    # PRIVATE IMPLEMENTATION - UI INTEGRATION
    # =============================================================================

    def _update_ui_for_current_prompt(self) -> None:
        """Update UI elements for the current prompt."""
        try:
            if hasattr(self.ui, "session_controller"):
                self.ui.session_controller._update_textareas_for_current_prompt()
        except Exception as e:
            logger.error(f"Error updating UI: {e}")

    def _update_next_button_state(self) -> None:
        """Update Next button state based on current automation phase."""
        try:
            if hasattr(self.ui, "state_manager"):
                self.ui.state_manager.update_next_button_state()
        except Exception as e:
            logger.error(f"Error updating Next button state: {e}")

    def _temporarily_disable_next_button(self) -> None:
        """Temporarily disable Next button for 2 seconds to prevent rapid clicking."""
        try:
            if hasattr(self.ui, "state_manager"):
                self.ui.state_manager.disable_next_button_temporarily()
        except Exception as e:
            logger.error(f"Error temporarily disabling Next button: {e}")
