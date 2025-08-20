"""
Automation Integration Module

This module provides integration between the new AutomationController
and the existing UI system. It replaces the fragmented SessionController
with a unified interface while maintaining compatibility.

Author: Automation System
Version: 3.0 - Centralized Integration
"""

import logging

try:
    from .automation_controller import AutomationController, AutomationState
except ImportError:
    # Fallback for standalone execution
    from automation_controller import AutomationController, AutomationState

logger = logging.getLogger(__name__)


class AutomationIntegration:
    """
    Integration adapter that replaces SessionController with AutomationController.

    This class provides a compatible interface for the existing UI while using
    the new centralized automation controller underneath.
    """

    def __init__(self, ui_session):
        """
        Initialize the integration layer.

        Args:
            ui_session: The UI session instance to integrate with
        """
        self.ui = ui_session
        self.controller = AutomationController(ui_session)
        self._setup_callbacks()

    def _setup_callbacks(self):
        """Set up callbacks from the automation controller to update UI state."""
        self.controller.add_state_callback(self._on_automation_state_changed)
        self.controller.add_progress_callback(self._on_automation_progress_changed)

    def _on_automation_state_changed(self, state: AutomationState):
        """Handle automation state changes by updating UI."""
        if state == AutomationState.RUNNING:
            self.ui.state_manager.update_start_state()
            # Update prompt list service automation state
            if hasattr(self.ui, "prompt_list_service"):
                self.ui.prompt_list_service.set_automation_running(True)
        elif state in [AutomationState.PAUSED, AutomationState.STOPPING, AutomationState.COMPLETED, AutomationState.FAILED]:
            self.ui.state_manager.update_start_state()
            # Update prompt list service automation state
            if hasattr(self.ui, "prompt_list_service"):
                self.ui.prompt_list_service.set_automation_running(False)

    def _on_automation_progress_changed(self, current_index: int, total: int):
        """Handle automation progress changes by updating UI."""
        self._update_textareas_for_current_prompt()

    def start_automation(self) -> bool:
        """
        Start the automation process.

        Returns:
            True if automation started successfully, False otherwise
        """
        return self.controller.start_automation()

    def stop_automation(self) -> bool:
        """
        Stop the automation process.

        Returns:
            True if automation stopped successfully, False otherwise
        """
        return self.controller.stop_automation()

    def pause_automation(self) -> bool:
        """
        Pause the automation process.

        Returns:
            True if automation paused successfully, False otherwise
        """
        return self.controller.pause_automation()

    def resume_automation(self) -> bool:
        """
        Resume the automation process.

        Returns:
            True if automation resumed successfully, False otherwise
        """
        return self.controller.resume_automation()

    def toggle_pause(self) -> bool:
        """
        Toggle the pause state of the automation.

        Returns:
            True if pause state toggled successfully, False otherwise
        """
        return self.controller.toggle_pause()

    def next_prompt(self) -> bool:
        """
        Advance to the next prompt.

        Returns:
            True if advanced successfully, False otherwise
        """
        return self.controller.next_prompt()

    def is_running(self) -> bool:
        """
        Check if automation is currently running.

        Returns:
            True if automation is running, False otherwise
        """
        return self.controller.is_running()

    def is_paused(self) -> bool:
        """
        Check if automation is currently paused.

        Returns:
            True if automation is paused, False otherwise
        """
        return self.controller.is_paused()

    def is_started(self) -> bool:
        """
        Check if automation has been started (running or paused).

        Returns:
            True if automation is running or paused, False if stopped
        """
        return self.controller.is_running() or self.controller.is_paused()

    def are_prompts_locked(self) -> bool:
        """
        Check if prompts are locked (cannot be modified during automation).

        Returns:
            True if prompts are locked, False if they can be modified
        """
        return self.controller.is_running()

    def get_current_prompt_index(self) -> int:
        """
        Get the current prompt index.

        Returns:
            Current prompt index
        """
        return self.controller.get_current_prompt_index()

    def get_total_prompts(self) -> int:
        """
        Get the total number of prompts.

        Returns:
            Total number of prompts
        """
        return self.controller.get_total_prompts()

    def get_progress(self) -> tuple[int, int]:
        """
        Get the current progress as (current, total).

        Returns:
            Tuple of (current_index, total_prompts)
        """
        return self.controller.get_progress()

    def _update_textareas_for_current_prompt(self):
        """
        Update the UI textareas to reflect the current prompt.

        This method updates both the current and next prompt textareas,
        as well as the prompt list selection.
        """
        try:
            current_index = self.controller.get_current_prompt_index()

            # Update current prompt textarea
            if (hasattr(self.ui, "prompt_list_service") and
                hasattr(self.ui.prompt_list_service, "prompts") and
                self.ui.prompt_list_service.prompts and
                0 <= current_index < len(self.ui.prompt_list_service.prompts)):
                current_prompt = self.ui.prompt_list_service.prompts[current_index]
                if hasattr(self.ui, "current_box") and self.ui.current_box:
                    self.ui.current_box.configure(state="normal")
                    self.ui.current_box.delete("1.0", "end")
                    self.ui.current_box.insert("end", f"{current_prompt}")
                    self.ui.current_box.configure(state="disabled")

            # Update next prompt textarea
            next_prompt = self.controller._context.get_next_prompt()
            if hasattr(self.ui, "next_box") and self.ui.next_box:
                next_text = f"{next_prompt}" if next_prompt else ""
                self.ui.next_box.configure(state="normal")
                self.ui.next_box.delete("1.0", "end")
                self.ui.next_box.insert("end", next_text)
                self.ui.next_box.configure(state="disabled")

            # Update prompt list selection - use the InlinePromptEditorService method
            if (hasattr(self.ui, "prompt_list_service") and
                hasattr(self.ui.prompt_list_service, "set_current_prompt_index")):
                self.ui.prompt_list_service.set_current_prompt_index(current_index)

        except Exception as e:
            logger.error(f"Error updating textareas: {e}")


def create_automation_integration(ui_session):
    """
    Factory function to create AutomationIntegration.

    This replaces the creation of SessionController in the UI initialization.
    """
    return AutomationIntegration(ui_session)


class SessionController:
    """
    Compatibility shim that forwards all calls to AutomationIntegration.

    This allows existing code to continue working without changes while
    using the new centralized automation controller underneath.
    """

    def __init__(self, ui_session):
        """
        Initialize the session controller with the integration layer.

        Args:
            ui_session: The UI session instance to control
        """
        self.ui = ui_session
        self.controller = create_automation_integration(ui_session)

    def start_automation(self) -> bool:
        """Start automation - delegated to integration layer."""
        return self.controller.start_automation()

    def stop_automation(self) -> bool:
        """Stop automation - delegated to integration layer."""
        return self.controller.stop_automation()

    def next_prompt(self) -> bool:
        """Advance to next prompt - delegated to integration layer."""
        return self.controller.next_prompt()

    def cancel_automation(self) -> bool:
        """Cancel automation and close dialog - delegated to integration layer."""
        # Stop automation first
        result = self.controller.stop_automation()

        # Close the UI dialog
        try:
            if hasattr(self.ui, "close"):
                self.ui.close()
            elif hasattr(self.ui, "destroy"):
                self.ui.destroy()
            elif hasattr(self.ui, "quit"):
                self.ui.quit()
            logger.info("UI dialog closed")
        except Exception as e:
            logger.error(f"Error closing UI dialog: {e}")

        return result

    def toggle_pause(self) -> bool:
        """Toggle pause state - delegated to integration layer."""
        return self.controller.toggle_pause()

    def is_running(self) -> bool:
        """Check if running - delegated to integration layer."""
        return self.controller.is_running()

    def is_paused(self) -> bool:
        """Check if paused - delegated to integration layer."""
        return self.controller.is_paused()

    def is_started(self) -> bool:
        """Check if started - delegated to integration layer."""
        return self.controller.is_started()

    def are_prompts_locked(self) -> bool:
        """Check if prompts are locked - delegated to integration layer."""
        return self.controller.are_prompts_locked()

    def get_current_prompt_index(self) -> int:
        """Get current prompt index - delegated to integration layer."""
        return self.controller.get_current_prompt_index()

    def get_total_prompts(self) -> int:
        """Get total prompts - delegated to integration layer."""
        return self.controller.get_total_prompts()

    def get_progress(self) -> tuple[int, int]:
        """Get progress - delegated to integration layer."""
        return self.controller.get_progress()

    def _update_textareas_for_current_prompt(self):
        """Update textareas - delegated to integration layer."""
        self.controller._update_textareas_for_current_prompt()
