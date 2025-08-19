"""
Session Controller - Automation Lifecycle Management

Handles the automation session lifecycle including start, stop, cancel, next operations,
and manages the automation thread state.
"""

import logging
import threading
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

# Import with fallback for standalone execution
try:
    from ..automator import run_automation_with_ui, run_single_prompt_automation
except ImportError:
    try:
        # Try absolute import
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from automator import run_automation_with_ui, run_single_prompt_automation
    except ImportError:
        # Fallback if automator not available
        def run_automation_with_ui(ui):
            logger.error("Automation function not available")
        
        def run_single_prompt_automation(ui, index):
            logger.error("Single prompt automation function not available")


class SessionController:
    """
    Controls the automation session lifecycle and state management.
    """
    
    def __init__(self, ui):
        """
        Initialize the session controller.
        
        Args:
            ui: Reference to the main UI session
        """
        self.ui = ui
        self._started = False
        self._automation_lock = threading.RLock()
        self._prompts_locked = False
        self._automation_thread = None  # Track the automation thread
        self._stop_requested = False  # Flag to request stop
        
    def start_automation(self) -> bool:
        """
        Start the automation process.
        
        Returns:
            True if automation started successfully, False otherwise
        """
        with self._automation_lock:
            if self._started:
                logger.warning("Automation already started")
                return False
            
            # CRITICAL FIX: Ensure any existing countdown is stopped before starting
            if hasattr(self.ui, "countdown_service"):
                self.ui.countdown_service.force_reset()
                
            # Validate configuration before starting
            if not self._validate_start_prerequisites():
                return False
                
            # Lock prompt list during automation
            self._prompts_locked = True
            self._started = True
            
            # Update UI state
            if hasattr(self.ui, "prompt_list_service"):
                self.ui.prompt_list_service.set_automation_running(True)
                
            # Start automation thread
            self._start_automation_thread()
            return True
    
    def stop_automation(self) -> None:
        """Stop the automation process."""
        with self._automation_lock:
            # CRITICAL FIX: Stop the automation thread if it's running
            if self._automation_thread and self._automation_thread.is_alive():
                logger.info("Automation stopped via stop button")
                self._stop_requested = True  # Signal the thread to stop
            
            self._reset_automation_state()
            self._stop_countdown_if_active()
            self._automation_thread = None
            self._stop_requested = False
    
    def cancel_automation(self) -> None:
        """Cancel the automation process and close application."""
        with self._automation_lock:
            self._reset_automation_state()
            self._cancel_countdown_if_active()
        
        # Close the application
        if hasattr(self.ui, "window"):
            self.ui.window.quit()
    
    def next_prompt(self) -> None:
        """Advance to next prompt and start automation cycle if running."""
        with self._automation_lock:
            if not self._started:
                # If automation is not running, just advance UI position
                if self.ui.current_prompt_index < len(self.ui.prompts) - 1:
                    self.ui.current_prompt_index += 1
                    if hasattr(self.ui, "prompt_list_service"):
                        self.ui.prompt_list_service.set_current_prompt_index(
                            self.ui.current_prompt_index
                        )
                    print(f"Advanced to prompt {self.ui.current_prompt_index + 1}")
                return
            
            # If automation is running, advance to next prompt and start automation cycle
            if self.ui.current_prompt_index < len(self.ui.prompts) - 1:
                # Stop countdown and advance index together
                self._stop_countdown_if_active()
                
                # Advance to next prompt
                self.ui.current_prompt_index += 1
                if hasattr(self.ui, "prompt_list_service"):
                    self.ui.prompt_list_service.set_current_prompt_index(
                        self.ui.current_prompt_index
                    )
                print(f"Next button: Advanced to prompt {self.ui.current_prompt_index + 1}")
                
                # CRITICAL FIX: Only start automation cycle if NOT paused
                if hasattr(self.ui, "countdown_service") and not self.ui.countdown_service.is_paused():
                    # Start automation cycle for the new prompt
                    self._start_prompt_automation()
                else:
                    print("Next button: Automation paused - not starting new cycle")
            else:
                print("Next button: Already at last prompt")
    
    def toggle_pause(self) -> None:
        """Toggle pause state of countdown."""
        if hasattr(self.ui, "countdown_service") and self.ui.countdown_service.is_active():
            self.ui.countdown_service.toggle_pause()
    
    def is_started(self) -> bool:
        """Check if automation is started."""
        return self._started
    
    def are_prompts_locked(self) -> bool:
        """Check if prompts are locked during automation."""
        return self._prompts_locked
    
    def is_stop_requested(self) -> bool:
        """Check if stop was requested."""
        return self._stop_requested
    
    def _validate_start_prerequisites(self) -> bool:
        """Validate prerequisites before starting automation."""
        # Check coordinates
        coords_validation = self.ui.coordinate_service.validate_coordinates()
        if not all(coords_validation.values()):
            logger.error("Missing required coordinates")
            return False
        
        # Check timers
        if not self._timers_valid():
            logger.error("Invalid timer values")
            return False
        
        # Check prompts
        if len(self.ui.prompts) == 0:
            logger.error("No prompts available")
            return False
        
        return True
    
    def _timers_valid(self) -> bool:
        """Validate timer values."""
        try:
            main_wait = float(self.ui.main_wait_var.get())
            get_ready = float(self.ui.get_ready_delay_var.get())
            return all(val >= 0 for val in [main_wait, get_ready])
        except ValueError:
            return False
    
    def _start_automation_thread(self) -> None:
        """Start the automation thread."""
        try:
            logger.info("Starting automation process...")
            
            # Save coordinates
            self.ui.coordinate_service.save_coordinates()
            
            # Run automation in a separate thread
            self._automation_thread = threading.Thread(
                target=run_automation_with_ui,
                args=(self.ui,),
                name="AutomationThread"
            )
            self._automation_thread.daemon = True
            self._automation_thread.start()
            
            logger.info("Automation thread started successfully")
            
        except Exception:
            logger.exception("Error starting automation")
            self._reset_automation_state()
    
    def _start_prompt_automation(self) -> None:
        """Start automation cycle for the current prompt."""
        try:
            # Run single prompt automation in a separate thread
            automation_thread = threading.Thread(
                target=run_single_prompt_automation,
                args=(self.ui, self.ui.current_prompt_index)
            )
            automation_thread.daemon = True
            automation_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting prompt automation: {e}")
    
    def _reset_automation_state(self) -> None:
        """Reset automation state to initial values."""
        self._started = False
        if hasattr(self.ui, "prompt_list_service"):
            self.ui.prompt_list_service.set_automation_running(False)
        self.ui.current_prompt_index = 0
        if hasattr(self.ui, "prompt_list_service"):
            self.ui.prompt_list_service.set_current_prompt_index(0)
        
        # Unlock prompt list when automation stops
        self._prompts_locked = False
    
    def _stop_countdown_if_active(self) -> None:
        """Stop countdown service if it's currently active."""
        if hasattr(self.ui, "countdown_service") and self.ui.countdown_service.is_active():
            self.ui.countdown_service.stop()
    
    def _cancel_countdown_if_active(self) -> None:
        """Cancel countdown service if it's currently active."""
        if hasattr(self.ui, "countdown_service") and self.ui.countdown_service.is_active():
            self.ui.countdown_service.cancel()
