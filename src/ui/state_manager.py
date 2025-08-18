"""
UI State Manager - UI State Updates and Health Checks

Handles UI state management including button states, display updates,
health checks, and UI synchronization.
"""

import logging
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
        Detect and fix stuck UI state where display shows "Waiting..." but automation has moved on.
        
        Returns:
            True if stuck state was detected and fixed, False otherwise
        """
        try:
            # SIMPLIFIED: Only check if countdown is inactive but UI shows "Waiting..."
            if hasattr(self.ui, "countdown_service") and not self.ui.countdown_service.is_active():
                if hasattr(self.ui, "current_box") and self.ui.current_box:
                    try:
                        current_content = self.ui.current_box.get("1.0", "end-1c").strip()
                        if current_content == "Waiting...":
                            print("Detected stuck UI state - fixing...")
                            # Simple fix: update to show current prompt
                            current_text = self.ui.prompts[self.ui.current_prompt_index] if self.ui.prompts and self.ui.current_prompt_index < len(self.ui.prompts) else ""
                            self.ui.current_box.configure(state="normal")
                            self.ui.current_box.delete("1.0", "end")
                            self.ui.current_box.insert("end", current_text)
                            self.ui.current_box.configure(state="disabled")
                            
                            print("Stuck UI state fixed successfully")
                            return True
                    except Exception as e:
                        print(f"Error checking current box content: {e}")
            
            # CRITICAL FIX: Check for orphaned countdown threads
            if hasattr(self.ui, "countdown_service"):
                try:
                    thread_status = self.ui.countdown_service.get_thread_status()
                    if thread_status["thread_alive"] and not thread_status["countdown_active"]:
                        print("Detected orphaned countdown thread - forcing cleanup")
                        self.ui.countdown_service.force_reset()
                        return True
                except Exception as e:
                    print(f"Error checking thread status: {e}")
            
            return False
        except Exception as e:
            print(f"Error in detect_and_fix_stuck_ui: {e}")
            return False
    
    def start_ui_health_check(self) -> None:
        """Start periodic UI health check to detect and fix stuck states."""
        def health_check():
            try:
                # Check for stuck UI state every 2 seconds
                if self.detect_and_fix_stuck_ui():
                    print("Periodic health check detected and fixed stuck UI state")
            except Exception as e:
                print(f"Error in periodic health check: {e}")
            finally:
                # Schedule next health check
                if hasattr(self.ui, 'window_service') and self.ui.window_service.window:
                    self.ui.window_service.window.after(2000, health_check)  # 2 seconds
        
        # Start the health check
        if hasattr(self.ui, 'window_service') and self.ui.window_service.window:
            self.ui.window_service.window.after(2000, health_check)
    
    def on_prompt_click(self, index: int) -> None:
        """Handle prompt list click."""
        if hasattr(self.ui, "session_controller") and not self.ui.session_controller.is_started():
            self.ui.current_prompt_index = index
            if hasattr(self.ui, "prompt_list_service"):
                self.ui.prompt_list_service.set_current_prompt_index(index)
    
    def advance_prompt_index(self) -> None:
        """Advance to next prompt."""
        if self.ui.current_prompt_index < len(self.ui.prompts) - 1:
            self.ui.current_prompt_index += 1
            if hasattr(self.ui, "prompt_list_service"):
                self.ui.prompt_list_service.set_current_prompt_index(self.ui.current_prompt_index)
            print(f"Automation: Advanced to prompt {self.ui.current_prompt_index + 1}")
    
    def set_prompt_index(self, index: int) -> bool:
        """Set prompt index."""
        if 0 <= index < len(self.ui.prompts):
            self.ui.current_prompt_index = index
            if hasattr(self.ui, "prompt_list_service"):
                self.ui.prompt_list_service.set_current_prompt_index(index)
            return True
        return False
    
    def update_prompt_index_from_automation(self, index: int) -> None:
        """Update prompt index from automation (thread-safe)."""
        self.ui.current_prompt_index = index
        if hasattr(self.ui, "prompt_list_service"):
            self.ui.prompt_list_service.set_current_prompt_index(index)
    
    def get_current_prompt(self) -> Optional[str]:
        """Get current prompt text."""
        if hasattr(self.ui, "prompt_list_service"):
            return self.ui.prompt_list_service.get_current_prompt()
        return None
    
    def get_next_prompt(self) -> Optional[str]:
        """Get next prompt text."""
        if hasattr(self.ui, "prompt_list_service"):
            return self.ui.prompt_list_service.get_next_prompt()
        return None
    
    def _timers_valid(self) -> bool:
        """Validate timer values."""
        try:
            main_wait = float(self.ui.main_wait_var.get())
            get_ready = float(self.ui.get_ready_delay_var.get())
            return all(val >= 0 for val in [main_wait, get_ready])
        except ValueError:
            return False
    
    def _on_start(self) -> None:
        """Handle start button click."""
        if hasattr(self.ui, "session_controller"):
            if not self.ui.session_controller.is_started():
                if self.ui.session_controller.start_automation():
                    self.update_start_button_to_stop()
            else:
                self.ui.session_controller.stop_automation()
                self.reset_start_button()
    
    def _on_stop(self) -> None:
        """Handle stop button click."""
        if hasattr(self.ui, "session_controller"):
            self.ui.session_controller.stop_automation()
            self.reset_start_button()
