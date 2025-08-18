import atexit
import logging
import sys
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Dict, List, Optional, Tuple, Any

import pyautogui
import pyperclip

try:
    from .dpi import enable_windows_dpi_awareness
    from .ui_session_refactored import RefactoredSessionUI as SessionUI
    from .win_focus import CursorWindow
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    # Add src directory to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

    from dpi import enable_windows_dpi_awareness
    from ui_session_refactored import RefactoredSessionUI as SessionUI
    from win_focus import CursorWindow

# Configure logging
import os
from pathlib import Path

# Create logs directory in user's home directory
log_dir = Path.home() / "prompt_stacker_logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "automation.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Import config for defaults
try:
    from .config import config
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from config import config

# Defaults from config (can be edited in UI)
DEFAULT_START_DELAY = config.automation.default_start_delay
DEFAULT_MAIN_WAIT = config.automation.default_main_wait
DEFAULT_COOLDOWN = config.automation.default_cooldown

# Automation timing constants from config
FOCUS_DELAY = config.automation.focus_delay
CLIPBOARD_RETRY_ATTEMPTS = config.automation.clipboard_retry_attempts
CLIPBOARD_RETRY_DELAY = config.automation.clipboard_retry_delay
GET_READY_DELAY = (
    config.automation.default_get_ready_delay
)  # Default get ready pause before each cycle

# Timeout constants for preventing hangs
OPERATION_TIMEOUT = 10.0  # 10 seconds timeout for any operation
CLIPBOARD_TIMEOUT = 5.0  # 5 seconds timeout for clipboard operations
CLICK_TIMEOUT = 3.0  # 3 seconds timeout for click operations

pyautogui.PAUSE = config.automation.pyautogui_pause
pyautogui.FAILSAFE = config.automation.pyautogui_failsafe

# =============================================================================
# THREAD POOL MANAGEMENT
# =============================================================================


class AutomationThreadPool:
    """
    Thread pool manager for automation operations.

    Provides per-session thread pools with proper cleanup and error handling.
    """

    def __init__(self, max_workers: int = 4, thread_name_prefix: str = "Automation"):
        """
        Initialize the thread pool manager.

        Args:
            max_workers: Maximum number of worker threads
            thread_name_prefix: Prefix for thread names
        """
        self.max_workers = max_workers
        self.thread_name_prefix = thread_name_prefix
        self.executor: Optional[ThreadPoolExecutor] = None
        self.active_futures: List[Future] = []
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()

    def start(self) -> None:
        """Start the thread pool executor."""
        if self.executor is None or self.executor._shutdown:
            with self._lock:
                self.executor = ThreadPoolExecutor(
                    max_workers=self.max_workers,
                    thread_name_prefix=self.thread_name_prefix,
                )
                self.active_futures.clear()
                self._shutdown_event.clear()
                logger.info(
                    f"Started automation thread pool with {self.max_workers} workers",
                )

    def submit(self, func, *args, **kwargs) -> Future:
        """
        Submit a task to the thread pool.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Future object for the submitted task
        """
        if self.executor is None or self.executor._shutdown:
            self.start()

        future = self.executor.submit(func, *args, **kwargs)

        with self._lock:
            self.active_futures.append(future)

        # Add callback to remove future from active list when done
        future.add_done_callback(self._remove_future)

        return future

    def _remove_future(self, future: Future) -> None:
        """Remove completed future from active list."""
        with self._lock:
            if future in self.active_futures:
                self.active_futures.remove(future)

    def cancel_all_futures(self) -> None:
        """Cancel all active futures."""
        with self._lock:
            for future in self.active_futures[
                :
            ]:  # Copy list to avoid modification during iteration
                if not future.done():
                    future.cancel()
                    logger.info("Cancelled pending automation operation")

    def shutdown(self, timeout: float = 10.0) -> None:
        """
        Shutdown the thread pool with proper cleanup.

        Args:
            timeout: Maximum time to wait for shutdown
        """
        if self.executor is None:
            return

        logger.info("Shutting down automation thread pool...")

        # Cancel all pending operations
        self.cancel_all_futures()

        # Signal shutdown
        self._shutdown_event.set()

        try:
            # Shutdown executor (ThreadPoolExecutor.shutdown doesn't accept timeout parameter)
            self.executor.shutdown(wait=True)
            logger.info("Automation thread pool shutdown complete")
        except Exception as e:
            logger.warning(f"Error during thread pool shutdown: {e}")
        finally:
            self.executor = None
            self.active_futures.clear()

    def is_shutdown(self) -> bool:
        """Check if thread pool is shutdown."""
        return self.executor is None or self.executor._shutdown

    def get_active_count(self) -> int:
        """Get number of active futures."""
        with self._lock:
            return len([f for f in self.active_futures if not f.done()])


# Global thread pool manager (singleton)
_thread_pool_manager = AutomationThreadPool(
    max_workers=4,
    thread_name_prefix="Automation",
)


# Register cleanup function
def cleanup_thread_pool():
    """Cleanup thread pool on exit."""
    _thread_pool_manager.shutdown(timeout=15.0)


atexit.register(cleanup_thread_pool)


def run_with_timeout(func, timeout: float, *args, **kwargs):
    """
    Run a function with timeout protection using the thread pool manager.

    Args:
        func: Function to execute
        timeout: Timeout in seconds
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result or None if timeout/error
    """
    try:
        future = _thread_pool_manager.submit(func, *args, **kwargs)
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        logger.error(f"Operation timed out after {timeout} seconds: {func.__name__}")
        # Cancel the future to free up the thread
        future.cancel()
        return None
    except Exception as e:
        logger.error(f"Operation failed: {func.__name__} - {e}")
        return None


def get_thread_pool_status() -> Dict[str, any]:
    """
    Get thread pool status information.

    Returns:
        Dictionary with thread pool status
    """
    return {
        "active_operations": _thread_pool_manager.get_active_count(),
        "max_workers": _thread_pool_manager.max_workers,
        "is_shutdown": _thread_pool_manager.is_shutdown(),
    }


def cleanup_automation_resources() -> None:
    """Cleanup automation resources (call between automation sessions)."""
    _thread_pool_manager.shutdown(timeout=5.0)
    _thread_pool_manager.start()


def paste_text_safely(text: str) -> bool:
    """Safely copy text to clipboard with verification and timeout protection."""
    if text is None or text == "":
        return False

    def clipboard_operation():
        for attempt in range(CLIPBOARD_RETRY_ATTEMPTS):
            try:
                pyperclip.copy(text)
                time.sleep(CLIPBOARD_RETRY_DELAY)
                clipboard_text = pyperclip.paste().strip()
                expected_text = text.strip()

                # More flexible comparison - check if the text is contained
                if clipboard_text == expected_text or expected_text in clipboard_text:
                    return True
                logger.warning(
                    f"Clipboard verification failed on attempt {attempt + 1}. Expected: '{expected_text[:50]}...', Got: '{clipboard_text[:50]}...'",
                )

            except Exception as e:
                logger.warning(
                    f"Clipboard operation failed on attempt {attempt + 1}: {e}",
                )
                if attempt == CLIPBOARD_RETRY_ATTEMPTS - 1:  # Last attempt
                    logger.error(
                        f"Clipboard copy failed after {CLIPBOARD_RETRY_ATTEMPTS} attempts: {e}",
                    )
                    return False
                continue

        return False

    # Run clipboard operation with timeout
    result = run_with_timeout(clipboard_operation, CLIPBOARD_TIMEOUT)
    return result if result is not None else False


def click_with_timeout(coords: Tuple[int, int], timeout: float = CLICK_TIMEOUT) -> bool:
    """Click with timeout protection."""

    def click_operation():
        try:
            pyautogui.click(*coords)
            return True
        except Exception as e:
            logger.error(f"Click operation failed: {e}")
            return False

    return run_with_timeout(click_operation, timeout) or False


def right_click_with_timeout(timeout: float = CLICK_TIMEOUT) -> bool:
    """Right click with timeout protection."""

    def right_click_operation():
        try:
            pyautogui.rightClick()
            return True
        except Exception as e:
            logger.error(f"Right click operation failed: {e}")
            return False

    return run_with_timeout(right_click_operation, timeout) or False


def hotkey_with_timeout(*keys, timeout: float = CLICK_TIMEOUT) -> bool:
    """Execute hotkey with timeout protection."""

    def hotkey_operation():
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            logger.error(f"Hotkey operation failed: {e}")
            return False

    return run_with_timeout(hotkey_operation, timeout) or False


def press_key_with_timeout(key: str, timeout: float = CLICK_TIMEOUT) -> bool:
    """Press a single key with timeout protection."""

    def press_operation():
        try:
            pyautogui.press(key)
            return True
        except Exception as e:
            logger.error(f"Key press operation failed: {e}")
            return False

    return run_with_timeout(press_operation, timeout) or False


def click_button_or_fallback(
    win: CursorWindow,
    coords: Tuple[int, int],
    pattern: str,
) -> bool:
    """Click button with fallback and timeout protection."""
    
    logger.info(f"Attempting to click button at coordinates {coords} with pattern '{pattern}'")

    def button_operation():
        try:
            if win.window is None and not win.connect():
                logger.info("Window connection failed, falling back to coordinate click")
                return click_with_timeout(coords)
            
            logger.info("Searching for button with pattern: " + pattern)
            btn = win.window.child_window(control_type="Button", title_re=pattern)
            
            if btn.exists():
                logger.info(f"Found button '{btn.window_text()}' - attempting to click")
                try:
                    btn.invoke()
                    logger.info("Button invoke() successful")
                    return True
                except Exception as e:
                    logger.warning(f"Button invoke() failed: {e}, trying click_input()")
                    try:
                        btn.click_input()
                        logger.info("Button click_input() successful")
                        return True
                    except Exception as e2:
                        logger.warning(f"Button click_input() failed: {e2}")
                        pass
            else:
                logger.warning(f"No button found matching pattern '{pattern}'")
        except Exception as e:
            logger.warning(f"Button search/click failed: {e}")
            pass
            
        logger.info("Falling back to coordinate-based click")
        return click_with_timeout(coords)

    result = run_with_timeout(button_operation, CLICK_TIMEOUT)
    logger.info(f"Button click operation result: {result}")
    return result or False


def perform_paste_operation(text: str) -> bool:
    """Perform paste operation with multiple fallback methods and timeout protection."""
    logger.info("Selecting all text and pasting")

    # Select all with timeout
    if not hotkey_with_timeout("ctrl", "a"):
        logger.warning("Select all operation failed")
        return False

    time.sleep(0.1)  # small delay to ensure selection

    # Try multiple paste methods with timeout protection
    paste_success = False

    # Method 1: Ctrl+V
    if hotkey_with_timeout("ctrl", "v"):
        time.sleep(0.1)
        logger.info("Ctrl+V paste operation completed")
        paste_success = True
    else:
        logger.warning("Ctrl+V paste failed, trying alternative method")

        # Method 2: Right-click paste
        if right_click_with_timeout(timeout=1.0):
            time.sleep(0.1)
            if press_key_with_timeout("v", timeout=1.0):  # paste option
                time.sleep(0.1)
                logger.info("Right-click paste method completed")
                paste_success = True

        # Method 3: Direct text input
        if not paste_success:
            logger.warning("All paste methods failed, trying direct text input")

            def write_operation():
                try:
                    pyautogui.write(text)
                    return True
                except Exception as e:
                    logger.error(f"Direct text input failed: {e}")
                    return False

            if run_with_timeout(write_operation, 5.0):
                logger.info("Direct text input completed")
                paste_success = True

    return paste_success


def run_single_prompt_automation(ui: SessionUI, prompt_index: int) -> bool:
    """Run automation for a single prompt with enhanced error handling and timeout protection."""
    logger.info(f"Starting single prompt automation for index {prompt_index}")

    # Validate UI parameter
    if ui is None:
        logger.error("UI parameter is None")
        return False

    # Validate prompt index
    if prompt_index >= len(ui.prompts):
        logger.error(f"Invalid prompt index: {prompt_index}")
        return False

    enable_windows_dpi_awareness()
    logger.info("DPI awareness enabled")

    win = CursorWindow()

    # CRITICAL FIX: Capture initial state to prevent race conditions
    initial_prompts = ui.get_prompts_safe()
    initial_coords = ui.get_coords()
    initial_timers = ui.get_timers()

    if not initial_prompts:
        logger.error("No prompts available from UI")
        return False

    if prompt_index >= len(initial_prompts):
        logger.error(
            f"Prompt index {prompt_index} out of range for {len(initial_prompts)} prompts"
        )
        return False

    logger.info(f"Processing single prompt {prompt_index + 1}/{len(initial_prompts)}")

    # Get the text for this prompt
    text = initial_prompts[prompt_index]
    logger.info(
        f"Processing prompt {prompt_index + 1}/{len(initial_prompts)}: {text[:50]}..."
    )

    # Get ready pause with dialog to front
    logger.info(f"Starting get ready countdown for {initial_timers[3]} seconds")
    ui.bring_to_front()
    result = ui.countdown(
        initial_timers[3],  # get_ready_delay
        f"Starting {prompt_index + 1} of {len(initial_prompts)}",
        text,
        None,
    )
    logger.info(f"Get ready countdown result: {result}")
    if result.get("cancelled"):
        logger.info("Single prompt automation cancelled during get ready countdown")
        return False

    # Check for pause state during countdown execution
    if result.get("paused"):
        logger.info("Single prompt automation paused during get ready countdown")
        # Wait for countdown to complete (which will happen when resumed)
        while ui.countdown_service.is_active() and ui.countdown_service.is_paused():
            time.sleep(0.05)  # More responsive checking
        logger.info("Single prompt automation resumed after get ready countdown")

    # Process automation with timeout protection
    logger.info(f"Copying text to clipboard: {text[:50]}...")
    clipboard_success = paste_text_safely(text)
    if not clipboard_success:
        logger.error("Failed to copy text to clipboard")
        return False
    logger.info("Text successfully copied to clipboard")

    # Check for required coordinates
    if (
        "input" not in initial_coords
        or "submit" not in initial_coords
        or "accept" not in initial_coords
    ):
        logger.error("Missing required coordinates: input, submit, or accept")
        return False

    logger.info(f"Clicking input field at {initial_coords['input']}")
    if not click_with_timeout(initial_coords["input"]):
        logger.error("Failed to click input field")
        return False

    time.sleep(FOCUS_DELAY)  # minimal delay for focus

    # Perform paste operation with timeout protection
    if not perform_paste_operation(text):
        logger.error("All paste methods failed")
        return False

    logger.info(f"Clicking submit button at {initial_coords['submit']}")
    if not click_button_or_fallback(
        win,
        initial_coords["submit"],
        r"^(Send|Submit|Enter|Run)$",
    ):
        logger.error("Failed to click submit button")
        return False

    next_text = (
        initial_prompts[prompt_index + 1]
        if prompt_index + 1 < len(initial_prompts)
        else None
    )
    logger.info(f"Starting main wait countdown for {initial_timers[1]} seconds")
    result = ui.countdown(initial_timers[1], text, next_text, None)  # main_wait
    logger.info(f"Main wait countdown result: {result}")
    if result.get("cancelled"):
        logger.info("Single prompt automation cancelled during main wait countdown")
        return False

    # Check for pause state during countdown execution
    if result.get("paused"):
        logger.info("Single prompt automation paused during main wait countdown")
        # Wait for countdown to complete (which will happen when resumed)
        while ui.countdown_service.is_active() and ui.countdown_service.is_paused():
            time.sleep(0.05)  # More responsive checking
        logger.info("Single prompt automation resumed after main wait countdown")

    if not click_button_or_fallback(
        win,
        initial_coords["accept"],
        r"^(Accept|Continue|Proceed)$",
    ):
        logger.error("Failed to click accept button")
        return False

    if ui.countdown(int(initial_timers[2]), "Waiting...", next_text, None).get(
        "cancelled"
    ):  # cooldown
        return False

    logger.info(
        f"Single prompt automation completed successfully for prompt {prompt_index + 1}",
    )
    return True


def run_automation_with_ui(ui: SessionUI) -> bool:
    """Run the automation process with an existing UI instance and enhanced error handling."""
    logger.info("Starting automation with existing UI")

    # Validate UI parameter
    if ui is None:
        logger.error("UI parameter is None")
        return False

    enable_windows_dpi_awareness()
    logger.info("DPI awareness enabled")

    win = CursorWindow()

    coords: Dict[str, Tuple[int, int]] = ui.get_coords()
    start_delay, main_wait, cooldown, get_ready_delay = ui.get_timers()

    # CRITICAL FIX: Capture initial state to prevent race conditions
    initial_prompts = ui.get_prompts_safe()
    initial_coords = ui.get_coords()
    initial_timers = ui.get_timers()

    if not initial_prompts:
        logger.error("No prompts available from UI")
        return False

    logger.info(f"Using {len(initial_prompts)} prompts from UI")

    # Start delay countdown
    next_preview = initial_prompts[0] if initial_prompts else None
    result = ui.countdown(initial_timers[0], "About to start!", next_preview, None)
    if result.get("cancelled"):
        return False

    index = 0
    last_text = None
    try:
        while index < len(initial_prompts):
            # CRITICAL FIX: Use captured state to prevent race conditions
            # Validate that state hasn't changed during automation
            current_prompts = ui.get_prompts_safe()
            current_coords = ui.get_coords()
            current_timers = ui.get_timers()

            if current_prompts != initial_prompts:
                logger.error(
                    "Prompt list changed during automation! Stopping for safety."
                )
                return False

            if current_coords != initial_coords:
                logger.error(
                    "Coordinates changed during automation! Stopping for safety."
                )
                return False

            if current_timers != initial_timers:
                logger.error("Timers changed during automation! Stopping for safety.")
                return False

            # Update UI prompt index and ensure synchronization
            ui.update_prompt_index_from_automation(index)

            # CRITICAL FIX: Detect and fix stuck UI states before starting new cycle
            # This prevents the UI from being stuck on "Waiting..." from previous cycle
            try:
                if ui.detect_and_fix_stuck_ui():
                    logger.info("Stuck UI state detected and fixed before starting new cycle")
            except Exception as e:
                logger.warning(f"Error detecting stuck UI state: {e}")

            # CRITICAL FIX: Check for multiple running threads and force cleanup
            try:
                thread_status = ui.countdown_service.get_thread_status()
                if thread_status["thread_alive"] and not thread_status["countdown_active"]:
                    logger.warning("Detected orphaned countdown thread - forcing cleanup")
                    ui.countdown_service.force_reset()
                elif thread_status["thread_alive"] and thread_status["countdown_active"]:
                    logger.info("Countdown thread is running normally")
                else:
                    logger.info("No countdown threads running")
            except Exception as e:
                logger.warning(f"Error checking thread status: {e}")

            # CRITICAL FIX: Force reset countdown service before starting new cycle
            # This prevents hanging issues from previous cycles
            ui.countdown_service.force_reset()

            # Get the text AFTER ensuring we have the correct index
            text = initial_prompts[index]
            logger.info(
                f"Processing prompt {index + 1}/{len(initial_prompts)}: {text[:50]}..."
            )

            # Get ready pause with dialog to front
            logger.info(f"Starting get ready countdown for {current_timers[3]} seconds")
            ui.bring_to_front()
            result = ui.countdown(
                current_timers[3],  # get_ready_delay
                f"Starting {index + 1} of {len(initial_prompts)}",
                text,
                last_text,
            )
            logger.info(f"Get ready countdown result: {result}")
            if result.get("cancelled"):
                logger.info("Automation cancelled during get ready countdown")
                return False

            # Check for pause state during countdown execution
            if result.get("paused"):
                logger.info("Automation paused during get ready countdown")
                # Wait for countdown to complete (which will happen when resumed)
                while (
                    ui.countdown_service.is_active()
                    and ui.countdown_service.is_paused()
                ):
                    time.sleep(0.05)  # More responsive checking
                logger.info("Automation resumed after get ready countdown")

            # Process visualization and automation
            # Double-check that we're still processing the correct prompt
            current_ui_index = ui.current_prompt_index
            if current_ui_index != index:
                logger.warning(
                    f"Index mismatch detected! Automation index: {index}, UI index: {current_ui_index}",
                )
                logger.warning("Skipping this iteration to avoid wrong text paste")
                index = current_ui_index
                continue

            logger.info(f"Copying text to clipboard: {text[:50]}...")
            clipboard_success = paste_text_safely(text)
            if not clipboard_success:
                logger.error("Failed to copy text to clipboard")
                return False
            logger.info("Text successfully copied to clipboard")

            # Check for required coordinates
            if (
                "input" not in current_coords
                or "submit" not in current_coords
                or "accept" not in current_coords
            ):
                logger.error("Missing required coordinates: input, submit, or accept")
                return False

            logger.info(f"Clicking input field at {current_coords['input']}")
            if not click_with_timeout(current_coords["input"]):
                logger.error("Failed to click input field")
                return False

            time.sleep(FOCUS_DELAY)  # minimal delay for focus

            # Perform paste operation with timeout protection
            if not perform_paste_operation(text):
                logger.error("All paste methods failed")
                return False

            # Final safety check - verify we're still processing the correct prompt
            if ui.current_prompt_index != index:
                logger.error(
                    f"Critical error: Index changed during paste operation! Expected: {index}, Got: {ui.current_prompt_index}",
                )
                logger.error(
                    "This could result in wrong text being submitted. Stopping automation.",
                )
                return False

            logger.info(f"Clicking submit button at {current_coords['submit']}")
            if not click_button_or_fallback(
                win,
                current_coords["submit"],
                r"^(Send|Submit|Enter|Run)$",
            ):
                logger.error("Failed to click submit button")
                return False

            next_text = (
                initial_prompts[index + 1] if index + 1 < len(initial_prompts) else None
            )
            logger.info(f"Starting main wait countdown for {current_timers[1]} seconds")
            result = ui.countdown(
                current_timers[1], text, next_text, last_text
            )  # main_wait
            logger.info(f"Main wait countdown result: {result}")
            if result.get("cancelled"):
                logger.info("Automation cancelled during main wait countdown")
                return False

            # Check for pause state during countdown execution
            if result.get("paused"):
                logger.info("Automation paused during main wait countdown")
                # Wait for countdown to complete (which will happen when resumed)
                while (
                    ui.countdown_service.is_active()
                    and ui.countdown_service.is_paused()
                ):
                    time.sleep(0.05)  # More responsive checking
                logger.info("Automation resumed after main wait countdown")

            if not click_button_or_fallback(
                win,
                current_coords["accept"],
                r"^(Accept|Continue|Proceed)$",
            ):
                logger.error("Failed to click accept button")
                return False

            logger.info("✅ Accept button clicked successfully - starting cooldown countdown")
            
            # VERIFICATION: Check if Accept button is still visible (indicating click may have failed)
            time.sleep(0.5)  # Brief delay to allow page to update
            accept_button_still_visible = False
            try:
                if win.window and win.window.exists():
                    accept_buttons = win.window.children(control_type="Button", title_re=r"^(Accept|Continue|Proceed)$")
                    if accept_buttons:
                        accept_button_still_visible = True
                        logger.warning("Accept button is still visible after click - click may have failed")
                        # Try clicking again
                        logger.info("Attempting second Accept button click")
                        if not click_button_or_fallback(
                            win,
                            current_coords["accept"],
                            r"^(Accept|Continue|Proceed)$",
                        ):
                            logger.error("Second Accept button click also failed")
                            return False
                        logger.info("Second Accept button click successful")
                        # Check again after second click
                        time.sleep(0.3)
                        accept_buttons_after_retry = win.window.children(control_type="Button", title_re=r"^(Accept|Continue|Proceed)$")
                        if accept_buttons_after_retry:
                            logger.error("Accept button still visible after retry - automation may be stuck")
                            # Continue anyway as the automation might still work
                        else:
                            logger.info("Accept button verification successful after retry")
                    else:
                        logger.info("✅ Accept button verification successful - button no longer visible")
            except Exception as e:
                logger.warning(f"Could not verify Accept button state: {e}")
            
            # Log verification result for debugging
            if accept_button_still_visible:
                logger.warning("⚠️ Accept button verification failed - automation may have issues")
            else:
                logger.info("✅ Accept button verification passed")
            
            # Enhanced debugging for cooldown countdown
            cooldown_duration = int(current_timers[2])
            logger.info(f"Starting cooldown countdown for {cooldown_duration} seconds")
            
            # CRITICAL FIX: Add completion callback to trigger next cycle
            def on_cooldown_complete(result: Dict[str, Any]) -> None:
                """Callback when cooldown countdown completes - triggers next automation cycle."""
                try:
                    logger.info(f"Cooldown countdown completion callback triggered with result: {result}")
                    
                    # Only proceed if not cancelled
                    if not result.get("cancelled"):
                        logger.info("Cooldown completed successfully - triggering next automation cycle")
                        # The automation will continue in the main loop
                    else:
                        logger.info("Cooldown was cancelled - stopping automation")
                except Exception as e:
                    logger.error(f"Error in cooldown completion callback: {e}")
            
            cooldown_result = ui.countdown(
                cooldown_duration, 
                "Waiting...", 
                next_text, 
                last_text,
                on_complete=on_cooldown_complete
            )
            
            logger.info(f"Cooldown countdown completed with result: {cooldown_result}")
            
            if cooldown_result.get("cancelled"):
                logger.info("Automation cancelled during cooldown countdown")
                return False
                
            if cooldown_result.get("paused"):
                logger.info("Cooldown countdown was paused - waiting for completion")
                # Wait for countdown to complete (which will happen when resumed)
                wait_start = time.time()
                while (
                    ui.countdown_service.is_active() and ui.countdown_service.is_truly_paused()
                ):
                    time.sleep(0.05)  # More responsive checking
                    
                    # CRITICAL FIX: Safety timeout to prevent infinite waiting
                    if time.time() - wait_start > 60:  # 60 second timeout
                        logger.warning("Cooldown countdown stuck in paused state - forcing completion")
                        ui.countdown_service.force_complete()
                        break
                        
                logger.info("Cooldown countdown resumed and completed")

            logger.info(f"✅ Cooldown completed successfully for prompt {index + 1}")

            # SIMPLIFIED FIX: Single, clean UI update after cycle completion
            # This eliminates the race condition by doing one simple update
            try:
                # Update prompt index for next cycle
                ui.update_prompt_index_from_automation(index + 1)
                
                # Brief delay to allow UI to process the update
                time.sleep(0.05)
                
                logger.info(f"UI updated for next cycle (prompt {index + 2})")
            except Exception as e:
                logger.warning(f"UI update after cycle completion failed: {e}")

            last_text = text
            index += 1
            logger.info(
                f"Completed prompt {index}/{len(initial_prompts)}, advancing to next"
            )

        logger.info("Automation completed successfully")
        time.sleep(1)
        return True

    except Exception as e:
        logger.error(f"Error during automation: {e}")
        return False
    finally:
        # Log thread pool status for debugging
        status = get_thread_pool_status()
        logger.info(f"Thread pool status after automation: {status}")


def run_automation(prompts: List[str]) -> bool:
    """Run the automation process with the given prompts."""
    logger.info("Starting automation with prompts from UI")

    enable_windows_dpi_awareness()
    logger.info("DPI awareness enabled")

    ui = SessionUI(DEFAULT_START_DELAY, DEFAULT_MAIN_WAIT, DEFAULT_COOLDOWN)
    ui.wait_for_start()

    # Check if automation was started
    if not ui._started:
        logger.info("Automation not started by user")
        ui.close()
        return False

    try:
        # Run automation with the existing UI
        result = run_automation_with_ui(ui)
        return result
    finally:
        # Cleanup resources
        ui.close()
        cleanup_automation_resources()


def main():
    """Main entry point for the automation system."""
    try:
        # Import error handling and performance monitoring
        try:
            from .config import config
            from .error_handler import handle_error, log_info
            from .performance import (
                cleanup_memory,
                start_performance_monitoring,
                stop_performance_monitoring,
            )
        except ImportError:
            # Fallback for when running as script
            from config import config
            from error_handler import handle_error, log_info
            from performance import (
                cleanup_memory,
                start_performance_monitoring,
                stop_performance_monitoring,
            )

        # Validate configuration
        validation = config.validate_config()
        if not validation["valid"]:
            print("Configuration validation failed:")
            for error in validation["errors"]:
                print(f"  - {error}")
            return 1

        # Start performance monitoring
        start_performance_monitoring()
        log_info("Application started with performance monitoring")

        # Run automation
        run_automation([])  # Empty list - prompts will be loaded from UI

        return 0

    except KeyboardInterrupt:
        log_info("Application interrupted by user")
        return 0
    except Exception as e:
        handle_error(e, context="Main application", show_ui=True)
        return 1
    finally:
        # Cleanup
        stop_performance_monitoring()
        cleanup_memory()
        cleanup_automation_resources()
        log_info("Application shutdown complete")


if __name__ == "__main__":
    sys.exit(main())
