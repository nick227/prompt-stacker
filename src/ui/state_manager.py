"""
UI State Manager - UI State Updates and Health Checks

Handles UI state management including button states, display updates,
health checks, and UI synchronization.
"""

import logging
import time
from typing import Optional, Dict, Any, Callable

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


class UIStateManager:
    """
    Manages UI state updates, health checks, and display synchronization.
    """
    
    def __init__(self, ui):
        """
        Initialize the UI state manager.
        
        Args:
            ui: Reference to the main UI session
        """
        self.ui = ui
    
    def update_start_state(self) -> None:
        """Update start button state based on current conditions."""
        # Don't update button if automation is running - let the button handlers manage it
        if hasattr(self.ui, "session_controller") and self.ui.session_controller.is_started():
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
        """Refresh the automation display state after a cycle completes."""
        try:
            # Simple refresh - just update the prompt list service
            if hasattr(self.ui, "prompt_list_service"):
                self.ui.prompt_list_service.refresh_display()
        except Exception as e:
            print(f"Error refreshing automation display: {e}")
    
    def detect_and_fix_stuck_ui(self) -> bool:
        """
        Detect and fix stuck UI states with enhanced error handling.
        
        Returns:
            True if stuck state was detected and fixed, False otherwise
        """
        try:
                        # SIMPLIFIED: Check for stuck countdown display (using control timer)
            if hasattr(self.ui, "control_timer_label") and self.ui.control_timer_label:
                try:
                    current_text = self.ui.control_timer_label.cget("text")
                    # Only reset if we have a clearly stuck state - be very conservative
                    if current_text == "Waiting..." and hasattr(self.ui, "session_controller"):
                        if self.ui.session_controller.is_started():
                            # Check if countdown service is actually running
                            if hasattr(self.ui, "countdown_service"):
                                # Only consider stuck if showing "Waiting..." but not active for a while
                                if not self.ui.countdown_service.is_active():
                                    # Add a timestamp check to avoid false positives
                                    if not hasattr(self, '_last_waiting_check'):
                                        self._last_waiting_check = time.time()
                                        return False  # Don't reset immediately
                                    elif time.time() - self._last_waiting_check > 10:  # Only after 10+ seconds
                                        logger.info("Detected stuck countdown display during automation - resetting")
                                        self.ui.control_timer_label.configure(text="0")
                                        self._last_waiting_check = time.time()
                                        return True
                                else:
                                    self._last_waiting_check = time.time()  # Reset timer if active
                        else:
                            # Reset timer if not in "Waiting..." state
                            if hasattr(self, '_last_waiting_check'):
                                delattr(self, '_last_waiting_check')
                except Exception as e:
                    logger.warning(f"Error checking control timer label: {e}")
            
            # SIMPLIFIED: Check for orphaned threads
            if hasattr(self.ui, "countdown_service"):
                try:
                    # Check if thread is alive but countdown is not active
                    if (self.ui.countdown_service._thread and 
                        self.ui.countdown_service._thread.is_alive() and 
                        not self.ui.countdown_service.countdown_active):
                        logger.info("Detected orphaned countdown thread - forcing cleanup")
                        self.ui.countdown_service.force_reset()
                        return True
                except Exception as e:
                    logger.warning(f"Error checking thread status: {e}")
            
            # BULLETPROOF IMPROVEMENT: Check for invalid prompt index
            try:
                if (hasattr(self.ui, "current_prompt_index") and 
                    hasattr(self.ui, "prompts") and 
                    self.ui.prompts):
                    if (self.ui.current_prompt_index < 0 or 
                        self.ui.current_prompt_index >= len(self.ui.prompts)):
                        logger.warning(f"Invalid prompt index {self.ui.current_prompt_index} - resetting to 0")
                        self.ui.current_prompt_index = 0
                        if hasattr(self.ui, "prompt_list_service"):
                            self.ui.prompt_list_service.set_current_prompt_index(0)
                        return True
            except Exception as e:
                logger.warning(f"Error checking prompt index: {e}")
            
            # BULLETPROOF IMPROVEMENT: Check for stuck button states
            if hasattr(self.ui, "start_btn"):
                try:
                    if hasattr(self.ui, "session_controller"):
                        is_started = self.ui.session_controller.is_started()
                        current_text = self.ui.start_btn.cget("text")
                        
                        # Fix button state mismatch
                        if is_started and current_text == "Start":
                            logger.info("Detected button state mismatch - fixing start button")
                            self.update_start_button_to_stop()
                            return True
                        elif not is_started and current_text == "Stop":
                            logger.info("Detected button state mismatch - fixing start button")
                            self.reset_start_button()
                            return True
                except Exception as e:
                    logger.warning(f"Error checking button states: {e}")
            
            return False
        except Exception as e:
            logger.error(f"Error in detect_and_fix_stuck_ui: {e}")
            return False
    
    def start_ui_health_check(self) -> None:
        """Start periodic UI health check to detect and fix stuck states."""
        def health_check():
            try:
                # BULLETPROOF IMPROVEMENT: Enhanced health check with timeout
                start_time = time.time()
                
                # Check for stuck UI state every 2 seconds
                if self.detect_and_fix_stuck_ui():
                    logger.info("Periodic health check detected and fixed stuck UI state")
                
                # SIMPLIFIED: Check for memory leaks
                if hasattr(self.ui, "countdown_service"):
                    try:
                        # Check if thread is alive
                        if (self.ui.countdown_service._thread and 
                            self.ui.countdown_service._thread.is_alive()):
                            # Log thread info for debugging
                            logger.debug(f"Active thread: {self.ui.countdown_service._thread.name}")
                    except Exception as e:
                        logger.warning(f"Error in thread status check: {e}")
                
                # BULLETPROOF IMPROVEMENT: Performance check
                elapsed = time.time() - start_time
                if elapsed > 0.1:  # Health check taking too long
                    logger.warning(f"Health check took {elapsed:.3f}s - performance issue detected")
                
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")
            finally:
                # Schedule next health check with error handling
                try:
                    if (hasattr(self.ui, 'window_service') and 
                        self.ui.window_service.window and 
                        hasattr(self.ui.window_service.window, 'after')):
                        self.ui.window_service.window.after(5000, health_check)  # 5 seconds
                    else:
                        logger.warning("Cannot schedule next health check - window not available")
                except Exception as e:
                    logger.error(f"Failed to schedule next health check: {e}")
        
        # Start the health check with error handling
        try:
            if (hasattr(self.ui, 'window_service') and 
                self.ui.window_service.window and 
                hasattr(self.ui.window_service.window, 'after')):
                self.ui.window_service.window.after(5000, health_check)
                logger.info("UI health check started")
            else:
                logger.warning("Cannot start UI health check - window not available")
        except Exception as e:
            logger.error(f"Failed to start UI health check: {e}")
    
    def on_prompt_click(self, index: int) -> None:
        """Handle prompt list click with validation."""
        try:
            # BULLETPROOF IMPROVEMENT: Validate index
            if not isinstance(index, int) or index < 0:
                logger.warning(f"Invalid prompt index: {index}")
                return
            
            if hasattr(self.ui, "prompts") and index >= len(self.ui.prompts):
                logger.warning(f"Prompt index {index} out of range")
                return
            
            if hasattr(self.ui, "session_controller") and not self.ui.session_controller.is_started():
                self.ui.current_prompt_index = index
                if hasattr(self.ui, "prompt_list_service"):
                    self.ui.prompt_list_service.set_current_prompt_index(index)
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
            else:
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
            elif hasattr(self.ui, "prompts") and hasattr(self.ui, "current_prompt_index"):
                if (0 <= self.ui.current_prompt_index < len(self.ui.prompts)):
                    return self.ui.prompts[self.ui.current_prompt_index]
            return None
        except Exception as e:
            logger.error(f"Error getting current prompt: {e}")
            return None
    
    def get_next_prompt(self) -> Optional[str]:
        """Get next prompt text with validation."""
        try:
            if hasattr(self.ui, "prompt_list_service"):
                return self.ui.prompt_list_service.get_next_prompt()
            elif hasattr(self.ui, "prompts") and hasattr(self.ui, "current_prompt_index"):
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
            if not hasattr(self.ui, "main_wait_var") or not hasattr(self.ui, "get_ready_delay_var"):
                logger.warning("Timer variables not available")
                return False
                
            main_wait = float(self.ui.main_wait_var.get())
            get_ready = float(self.ui.get_ready_delay_var.get())
            
            # BULLETPROOF IMPROVEMENT: Check for reasonable values
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
    
    def _on_start(self) -> None:
        """Handle start button click with enhanced error handling."""
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
        """Handle stop button click with enhanced error handling."""
        try:
            if hasattr(self.ui, "session_controller"):
                self.ui.session_controller.stop_automation()
                self.reset_start_button()
                logger.info("Automation stopped via stop button")
            else:
                logger.error("Session controller not available")
        except Exception as e:
            logger.error(f"Error handling stop button click: {e}")
