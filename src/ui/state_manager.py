"""
UI State Manager - UI State Updates and Health Checks

Handles UI state management including button states, display updates,
health checks, and UI synchronization.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Import with fallback for standalone execution
try:
    from ..config import (
        BTN_START,
        BTN_STOP,
        BUTTON_START_ACTIVE,
        BUTTON_START_ACTIVE_HOVER,
        BUTTON_START_INACTIVE,
        BUTTON_STOP_ACTIVE,
        BUTTON_STOP_ACTIVE_HOVER,
        BUTTON_BG,
        BUTTON_HOVER,
    )
except ImportError:
    try:
        from config import (
            BTN_START,
            BTN_STOP,
            BUTTON_START_ACTIVE,
            BUTTON_START_ACTIVE_HOVER,
            BUTTON_START_INACTIVE,
            BUTTON_STOP_ACTIVE,
            BUTTON_STOP_ACTIVE_HOVER,
        )
    except ImportError:
        # Fallback if imports not available
        BTN_START = "Start"
        BTN_STOP = "Stop"
        BUTTON_START_ACTIVE = "#ff6600"
        BUTTON_START_ACTIVE_HOVER = "#ff8533"
        BUTTON_START_INACTIVE = "#666666"
        BUTTON_STOP_ACTIVE = "#cc0000"
        BUTTON_STOP_ACTIVE_HOVER = "#ff3333"
        BUTTON_BG = "#2B2B2B"
        BUTTON_HOVER = "#3B3B3B"


class UIStateManager:
    """
    Manages UI state updates, health checks, and display synchronization.
    """

    def __init__(self, ui):
        """
        Initialize the UI state manager.
        """
        self.ui = ui

    def update_start_state(self) -> None:
        """Update start button state based on current conditions."""
        # Don't update button if automation is running - let the button
        # handlers manage it
        if (hasattr(self.ui, "session_controller") and
            self.ui.session_controller.is_started()):
            return

        # Check if start button exists
        if not hasattr(self.ui, "start_btn"):
            return

        # Check if all required coordinates are set
        coords_validation = self.ui.coordinate_service.validate_coordinates()
        coords_valid = all(coords_validation.values())  # All coordinates must be valid
        timers_valid = self._timers_valid()
        prompts_valid = len(self.ui.prompts) > 0

        can_start = coords_valid and timers_valid and prompts_valid

        # Update start button only when not started
        if can_start:
            self.ui.start_btn.configure(
                text=BTN_START,
                fg_color=BUTTON_START_ACTIVE,
                hover_color=BUTTON_START_ACTIVE_HOVER,
                state="normal",
                command=self._on_start,
            )
        else:
            self.ui.start_btn.configure(
                text=BTN_START,
                fg_color=BUTTON_START_INACTIVE,
                hover_color=BUTTON_START_INACTIVE,
                state="disabled",
                command=self._on_start,
            )

    def reset_start_button(self) -> None:
        """Reset start button to initial state."""
        if hasattr(self.ui, "start_btn"):
            self.ui.start_btn.configure(
                text=BTN_START,
                fg_color=BUTTON_START_ACTIVE,
                hover_color=BUTTON_START_ACTIVE_HOVER,
                command=self._on_start,
            )

    def update_start_button_to_stop(self) -> None:
        """Update start button to stop state."""
        if hasattr(self.ui, "start_btn"):
            self.ui.start_btn.configure(
                text=BTN_STOP,
                fg_color=BUTTON_STOP_ACTIVE,
                hover_color=BUTTON_STOP_ACTIVE_HOVER,
                command=self._on_stop,
            )

    def refresh_automation_display(self) -> None:
        """SIMPLIFIED: Basic display refresh."""
        # Simplified - just log that refresh was requested
        logger.debug("Display refresh requested")

    def detect_and_fix_stuck_ui(self) -> bool:
        """
        SIMPLIFIED: Only handle basic button state mismatches.
        Removed complex health checks that were causing bugs.
        """
        try:
            # SIMPLIFIED: Only check for button state mismatches
            if hasattr(self.ui, "start_btn") and hasattr(self.ui, "session_controller"):
                try:
                    is_started = self.ui.session_controller.is_started()
                    current_text = self.ui.start_btn.cget("text")

                    # Fix button state mismatch
                    if is_started and current_text == "Start":
                        logger.info(
                            "Detected button state mismatch - fixing start button",
                        )
                        self.update_start_button_to_stop()
                        return True
                    if not is_started and current_text == "Stop":
                        logger.info(
                            "Detected button state mismatch - fixing start button",
                        )
                        self.reset_start_button()
                        return True
                except Exception as e:
                    logger.warning(f"Error checking button states: {e}")

            return False
        except Exception as e:
            logger.error(f"Error in detect_and_fix_stuck_ui: {e}")
            return False

    def start_ui_health_check(self) -> None:
        """SIMPLIFIED: Removed periodic health checks that were causing bugs."""
        # Health checks removed - they were causing more problems than they solved
        logger.info("UI health checks disabled - simplified approach")

    def on_prompt_click(self, index: int) -> None:
        """SIMPLIFIED: Handle prompt list click."""
        try:
            if (isinstance(index, int) and index >= 0 and
                hasattr(self.ui, "prompts") and index < len(self.ui.prompts) and
                hasattr(self.ui, "session_controller") and
                not self.ui.session_controller.is_started()):
                self.ui.current_prompt_index = index
                logger.info(f"Prompt clicked: index {index}")
        except Exception as e:
            logger.error(f"Error handling prompt click: {e}")

    def advance_prompt_index(self) -> None:
        """Advance to next prompt with validation."""
        try:
            if not hasattr(self.ui, "prompts"):
                logger.warning("No prompts available")
                return

            if self.ui.current_prompt_index < len(self.ui.prompts) - 1:
                self.ui.current_prompt_index += 1
                if hasattr(self.ui, "prompt_list_service"):
                    self.ui.prompt_list_service.set_current_prompt_index(self.ui.current_prompt_index)
                logger.info(f"Advanced to prompt {self.ui.current_prompt_index + 1}")
            else:
                logger.info("Already at last prompt")
        except Exception as e:
            logger.error(f"Error advancing prompt index: {e}")

    def set_prompt_index(self, index: int) -> bool:
        """Set prompt index with validation."""
        try:
            # BULLETPROOF IMPROVEMENT: Comprehensive validation
            if not isinstance(index, int):
                logger.warning(f"Invalid index type: {type(index)}")
                return False

            if not hasattr(self.ui, "prompts"):
                logger.warning("No prompts available")
                return False

            if 0 <= index < len(self.ui.prompts):
                self.ui.current_prompt_index = index
                if hasattr(self.ui, "prompt_list_service"):
                    self.ui.prompt_list_service.set_current_prompt_index(index)
                logger.info(f"Set prompt index to {index}")
                return True
            logger.warning(f"Index {index} out of range [0, {len(self.ui.prompts)})")
            return False
        except Exception as e:
            logger.error(f"Error setting prompt index: {e}")
            return False

    def update_prompt_index_from_automation(self, index: int) -> None:
        """Update prompt index from automation (thread-safe) with validation."""
        try:
            # BULLETPROOF IMPROVEMENT: Validate index before updating
            if not isinstance(index, int) or index < 0:
                logger.warning(f"Invalid automation index: {index}")
                return

            if hasattr(self.ui, "prompts") and index >= len(self.ui.prompts):
                logger.warning(f"Automation index {index} out of range")
                return

            self.ui.current_prompt_index = index
            if hasattr(self.ui, "prompt_list_service"):
                self.ui.prompt_list_service.set_current_prompt_index(index)
            logger.debug(f"Automation updated prompt index to {index}")
        except Exception as e:
            logger.error(f"Error updating prompt index from automation: {e}")

    def get_current_prompt(self) -> Optional[str]:
        """Get current prompt text with validation."""
        try:
            if hasattr(self.ui, "prompt_list_service"):
                return self.ui.prompt_list_service.get_current_prompt()
            if hasattr(self.ui, "prompts") and hasattr(self.ui, "current_prompt_index"):
                if (0 <= self.ui.current_prompt_index < len(self.ui.prompts)):
                    return self.ui.prompts[self.ui.current_prompt_index]
            return None
        except Exception as e:
            logger.error(f"Error getting current prompt: {e}")
            return None

    def get_next_prompt(self) -> Optional[str]:
        """Get next prompt text - delegated to centralized controller."""
        try:
            if hasattr(self.ui, "session_controller"):
                return (self.ui.session_controller.controller._context.get_next_prompt()
                       if self.ui.session_controller.controller._context else None)
            if hasattr(self.ui, "prompt_list_service"):
                return self.ui.prompt_list_service.get_next_prompt()
            if hasattr(self.ui, "prompts") and hasattr(self.ui, "current_prompt_index"):
                next_index = self.ui.current_prompt_index + 1
                if next_index < len(self.ui.prompts):
                    return self.ui.prompts[next_index]
            return None
        except Exception as e:
            logger.error(f"Error getting next prompt: {e}")
            return None

    def _timers_valid(self) -> bool:
        """Validate timer values with enhanced error handling."""
        try:
            if (not hasattr(self.ui, "main_wait_var") or
                not hasattr(self.ui, "get_ready_delay_var")):
                logger.warning("Timer variables not available")
                return False

            main_wait_str = self.ui.main_wait_var.get().strip()
            get_ready_str = self.ui.get_ready_delay_var.get().strip()

            # Handle empty strings by treating them as invalid but not warning
            if not main_wait_str or not get_ready_str:
                return False

            main_wait = float(main_wait_str)
            get_ready = float(get_ready_str)

            # BULLETPROOF IMPROVEMENT: Check for reasonable values
            if main_wait < 0 or get_ready < 0:
                logger.warning("Negative timer values detected")
                return False

            if main_wait > 3600 or get_ready > 3600:  # More than 1 hour
                logger.warning("Unreasonably large timer values detected")
                return False

            return True
        except ValueError as e:
            # Only log warning if it's not an empty string issue
            main_wait_str = self.ui.main_wait_var.get().strip() if hasattr(self.ui, "main_wait_var") else ""
            get_ready_str = self.ui.get_ready_delay_var.get().strip() if hasattr(self.ui, "get_ready_delay_var") else ""
            if main_wait_str and get_ready_str:
                logger.warning(f"Invalid timer values: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating timers: {e}")
            return False

    def _on_start(self) -> None:
        """Handle start button click - delegated to centralized controller."""
        try:
            if hasattr(self.ui, "session_controller"):
                if not self.ui.session_controller.is_started():
                    if self.ui.session_controller.start_automation():
                        self.update_start_button_to_stop()
                        logger.info("Automation started successfully")
                    else:
                        logger.warning("Failed to start automation")
                else:
                    self.ui.session_controller.stop_automation()
                    self.reset_start_button()
                    logger.info("Automation stopped")
            else:
                logger.error("Session controller not available")
        except Exception as e:
            logger.error(f"Error handling start button click: {e}")

    def _on_stop(self) -> None:
        """Handle stop button click - delegated to centralized controller."""
        try:
            if hasattr(self.ui, "session_controller"):
                self.ui.session_controller.stop_automation()
                self.reset_start_button()
                logger.info("Automation stopped via stop button")
            else:
                logger.error("Session controller not available")
        except Exception as e:
            logger.error(f"Error handling stop button click: {e}")

    def update_next_button_state(self) -> None:
        """Update Next button state based on current automation phase."""
        try:
            if not hasattr(self.ui, "next_btn"):
                return

            # Check if automation is running
            if (hasattr(self.ui, "session_controller") and 
                self.ui.session_controller.is_started()):
                
                # Enable Next button during automation (temporary disable handled by timer)
                self.ui.next_btn.configure(
                    state="normal",
                    fg_color=BUTTON_BG,
                    hover_color=BUTTON_HOVER,
                )
            else:
                # Automation not running - disable Next button
                self.ui.next_btn.configure(
                    state="disabled",
                    fg_color="#444444",
                    hover_color="#444444",
                )
        except Exception as e:
            logger.error(f"Error updating Next button state: {e}")

    def disable_next_button_temporarily(self) -> None:
        """Disable Next button for 2 seconds to prevent rapid clicking."""
        try:
            if not hasattr(self.ui, "next_btn"):
                return

            # Disable the button immediately
            self.ui.next_btn.configure(
                state="disabled",
                fg_color="#444444",  # Darker gray when disabled
                hover_color="#444444",
            )

            # Re-enable after 2 seconds if automation is still running
            def re_enable_next_button():
                if (hasattr(self.ui, "session_controller") and 
                    self.ui.session_controller.is_started()):
                    self.ui.next_btn.configure(
                        state="normal",
                        fg_color=BUTTON_BG,
                        hover_color=BUTTON_HOVER,
                    )

            # Schedule re-enable after 2 seconds
            self.ui.window.after(2000, re_enable_next_button)

        except Exception as e:
            logger.error(f"Error temporarily disabling Next button: {e}")
