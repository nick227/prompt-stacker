import logging
import sys
import threading
import time
from typing import List, Tuple

import pyautogui
import pyperclip

try:
    from .dpi import enable_windows_dpi_awareness
    from .ui import RefactoredSessionUI as SessionUI
    from .win_focus import CursorWindow
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    # Add src directory to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

    from dpi import enable_windows_dpi_awareness
    from ui import RefactoredSessionUI as SessionUI
    from win_focus import CursorWindow

# Configure logging
import os
from pathlib import Path

# Create logs directory in user's home directory
log_dir = Path.home() / "prompt_stacker_logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "automation.log"

# Create a custom stream handler that handles Unicode properly
class UnicodeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Write with error handling for Unicode
            stream.buffer.write(msg.encode("utf-8"))
            stream.buffer.write(b"\n")
            self.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        UnicodeStreamHandler(),
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
# SIMPLIFIED THREAD MANAGEMENT
# =============================================================================

def run_with_timeout(func, timeout: float, *args, **kwargs):
    """
    Run a function with timeout protection using a simple thread.

    Args:
        func: Function to execute
        timeout: Timeout in seconds
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result or None if timeout/error
    """
    result = None
    exception = None

    def target():
        nonlocal result, exception
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            exception = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        logger.error(f"Operation timed out after {timeout} seconds: {func.__name__}")
        return None

    if exception:
        logger.error(f"Operation failed: {func.__name__} - {exception}")
        return None

    return result


# Thread pool functions removed - simplified architecture


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


# Simplified timeout functions - inline where needed


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

            else:
                logger.warning(f"No button found matching pattern '{pattern}'")
        except Exception as e:
            logger.warning(f"Button search/click failed: {e}")

        logger.info("Falling back to coordinate-based click")
        return click_with_timeout(coords)

    result = run_with_timeout(button_operation, CLICK_TIMEOUT)
    logger.info(f"Button click operation result: {result}")
    return result or False


def perform_paste_operation(text: str) -> bool:
    """Perform paste operation with multiple fallback methods and timeout protection."""
    logger.info("Selecting all text and pasting")

    # Select all and paste (simplified)
    try:
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)
        logger.info("Ctrl+V paste operation completed")
        return True
    except Exception as e:
        logger.warning(f"Ctrl+V paste failed: {e}, trying direct text input")
        try:
            pyautogui.write(text)
            logger.info("Direct text input completed")
            return True
        except Exception as e2:
            logger.error(f"Direct text input failed: {e2}")
            return False




def sanitize_text_for_logging(text: str) -> str:
    """Sanitize text for logging by replacing problematic Unicode characters."""
    if not text:
        return text

    # Replace problematic Unicode characters
    replacements = {
        "\u2011": "-",  # Non-breaking hyphen
        "\u2013": "-",  # En dash
        "\u2014": "-",  # Em dash
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
    }

    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)

    return text


def run_single_prompt_automation(ui: SessionUI, prompt_index: int) -> bool:
    """Run automation for a single prompt with enhanced error handling and timeout protection."""
    logger.info(f"Starting single prompt automation for index {prompt_index}")

    # Validate UI parameter
    if ui is None:
        logger.error("UI parameter is None")
        return False

    # Validate prompt index after capturing prompts safely
    initial_prompts = ui.get_prompts_safe()
    if prompt_index >= len(initial_prompts):
        logger.error(
            f"Prompt index {prompt_index} out of range for {len(initial_prompts)} prompts",
        )
        return False

    enable_windows_dpi_awareness()
    logger.info("DPI awareness enabled")

    win = CursorWindow()

    # Capture initial state
    initial_prompts = ui.get_prompts_safe()
    initial_coords = ui.get_coords()
    initial_timers = ui.get_timers()

    if not initial_prompts:
        logger.error("No prompts available from UI")
        return False

    if prompt_index >= len(initial_prompts):
        logger.error(
            f"Prompt index {prompt_index} out of range for {len(initial_prompts)} prompts",
        )
        return False

    logger.info(f"Processing single prompt {prompt_index + 1}/{len(initial_prompts)}")

    # Get the text for this prompt
    text = initial_prompts[prompt_index]
    logger.info(
        f"Processing prompt {prompt_index + 1}/{len(initial_prompts)}: {sanitize_text_for_logging(text[:50])}...",
    )

    # Define last_text for single prompt automation
    last_text = None

    # Check if stop was requested
    if hasattr(ui, "session_controller") and ui.session_controller.is_stop_requested():
        logger.info("Single prompt automation stopped - stop was requested")
        return False

    # Get ready pause with dialog to front
    logger.info(f"Starting get ready countdown for {initial_timers[3]} seconds")
    ui.bring_to_front()
    result = ui.countdown(
        initial_timers[3],  # get_ready_delay
        f"Starting {prompt_index + 1} of {len(initial_prompts)}",
        text,
        last_text,
    )
    logger.info(f"Get ready countdown result: {result}")
    if result.get("cancelled"):
        logger.info("Single prompt automation cancelled during get ready countdown")
        return False

    # SIMPLIFIED: Handle pause state
    if result.get("paused"):
        logger.info("Single prompt automation paused during get ready countdown")
        while ui.countdown_service.is_active() and ui.countdown_service.is_paused():
            time.sleep(0.1)
        logger.info("Single prompt automation resumed after get ready countdown")

    # Process automation with timeout protection
    logger.info(f"Copying text to clipboard: {sanitize_text_for_logging(text[:50])}...")
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
    result = ui.countdown(initial_timers[1], text, next_text, last_text)  # main_wait
    logger.info(f"Main wait countdown result: {result}")
    if result.get("cancelled"):
        logger.info("Single prompt automation cancelled during main wait countdown")
        return False

    # SIMPLIFIED: Handle pause state
    if result.get("paused"):
        logger.info("Single prompt automation paused during main wait countdown")
        while ui.countdown_service.is_active() and ui.countdown_service.is_paused():
            time.sleep(0.1)
        logger.info("Single prompt automation resumed after main wait countdown")

    if not click_button_or_fallback(
        win,
        initial_coords["accept"],
        r"^(Accept|Continue|Proceed)$",
    ):
        logger.error("Failed to click accept button")
        return False

    cooldown_result = ui.countdown(initial_timers[2], "Waiting...", next_text, last_text)  # cooldown
    if cooldown_result.get("cancelled"):
        return False

    # SIMPLIFIED: Handle cooldown pause state
    if cooldown_result.get("paused"):
        logger.info("Single prompt automation paused during cooldown countdown")
        while ui.countdown_service.is_active() and ui.countdown_service.is_paused():
            time.sleep(0.1)
        logger.info("Single prompt automation resumed after cooldown countdown")

    logger.info(
        f"Single prompt automation completed successfully for prompt {prompt_index + 1}",
    )
    return True


def run_automation_with_ui(ui) -> bool:
    """
    Run automation with UI integration and enhanced error handling.
    
    Args:
        ui: UI session instance
        
    Returns:
        True if automation completed successfully, False otherwise
    """
    # SIMPLIFIED: Basic validation
    if ui is None:
        logger.error("UI parameter is None")
        return False

    try:
        enable_windows_dpi_awareness()
        logger.info("DPI awareness enabled")
    except Exception as e:
        logger.warning(f"Failed to enable DPI awareness: {e}")

    win = CursorWindow()

    # SIMPLIFIED: Get initial state
    initial_prompts = ui.get_prompts_safe()
    initial_coords = ui.get_coords()
    initial_timers = ui.get_timers()

    if not initial_prompts:
        logger.error("No prompts available from UI")
        return False

    logger.info(f"Using {len(initial_prompts)} prompts from UI")

    # Start delay
    result = ui.countdown(initial_timers[0], "About to start!", initial_prompts[0] if initial_prompts else None, None)
    if result.get("cancelled"):
        logger.info("Automation cancelled during start delay")
        return False

    index = 0
    last_text = None

    try:
        while index < len(initial_prompts):
            # Check if stop was requested
            if hasattr(ui, "session_controller") and ui.session_controller.is_stop_requested():
                logger.info("Automation stopped - stop was requested")
                return False

            # SIMPLIFIED: Basic state validation
            try:
                if not ui.get_prompts_safe():
                    logger.error("No prompts available during automation")
                    return False
            except Exception as e:
                logger.error(f"Failed to get prompts: {e}")
                return False



            # SIMPLIFIED: Get text
            text = initial_prompts[index]
            logger.info(f"Processing prompt {index + 1}/{len(initial_prompts)}: {sanitize_text_for_logging(text[:50])}...")

            # Define next_text before countdown
            next_text = (
                initial_prompts[index + 1] if index + 1 < len(initial_prompts) else None
            )

            # SIMPLIFIED: Get ready countdown
            logger.info(f"Starting get ready countdown for {initial_timers[3]} seconds")
            ui.bring_to_front()

            result = ui.countdown(
                initial_timers[3],  # get_ready_delay
                f"Starting {index + 1} of {len(initial_prompts)}",
                next_text,
                last_text,
            )
            if result.get("cancelled"):
                logger.info("Automation cancelled during get ready countdown")
                return False

            # SIMPLIFIED: Handle pause state
            if result.get("paused"):
                logger.info("Automation paused during get ready countdown")
                while ui.countdown_service.is_active() and ui.countdown_service.is_paused():
                    time.sleep(0.1)
                logger.info("Automation resumed after get ready countdown")

            # SIMPLIFIED: Basic index validation
            if not isinstance(ui.current_prompt_index, int) or ui.current_prompt_index != index:
                logger.warning(f"Index mismatch - using automation index {index}")
                ui.current_prompt_index = index

            logger.info(f"Copying text to clipboard: {sanitize_text_for_logging(text[:50])}...")
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

            # SIMPLIFIED: Basic final check
            if ui.current_prompt_index != index:
                logger.warning("Index changed during paste - continuing with current index")

            logger.info(f"Clicking submit button at {initial_coords['submit']}")
            if not click_button_or_fallback(
                win,
                initial_coords["submit"],
                r"^(Send|Submit|Enter|Run)$",
            ):
                logger.error("Failed to click submit button")
                return False

            logger.info(f"Starting main wait countdown for {initial_timers[1]} seconds")

            # Start the main wait countdown - simplified
            result = ui.countdown(initial_timers[1], text, next_text, last_text)  # main_wait
            logger.info(f"Main wait countdown result: {result}")
            if result.get("cancelled"):
                logger.info("Automation cancelled during main wait countdown")
                return False

            # SIMPLIFIED: Handle pause state
            if result.get("paused"):
                logger.info("Automation paused during main wait countdown")
                # Simple wait for countdown to complete
                while ui.countdown_service.is_active() and ui.countdown_service.is_paused():
                    time.sleep(0.1)
                logger.info("Automation resumed after main wait countdown")

            if not click_button_or_fallback(
                win,
                initial_coords["accept"],
                r"^(Accept|Continue|Proceed)$",
            ):
                logger.error("Failed to click accept button")
                return False

            logger.info("Accept button clicked successfully - starting cooldown countdown")

            # Enhanced debugging for cooldown countdown
            cooldown_duration = initial_timers[2]
            logger.info(f"Starting cooldown countdown for {cooldown_duration} seconds")

            # Start the cooldown countdown - simplified
            countdown_result = ui.countdown(cooldown_duration, "Waiting...", next_text, last_text)
            if countdown_result.get("cancelled"):
                logger.info("Automation cancelled during cooldown countdown")
                return False

            # SIMPLIFIED: Handle cooldown pause state
            if countdown_result.get("paused"):
                logger.info("Cooldown countdown was paused - waiting for completion")
                while ui.countdown_service.is_active() and ui.countdown_service.is_paused():
                    time.sleep(0.1)
                logger.info("Cooldown countdown resumed and completed")

            logger.info(f"Cooldown completed successfully for prompt {index + 1}")

            # SIMPLIFIED: Basic UI update
            try:
                ui.current_prompt_index = index + 1
                logger.info(f"Updated to prompt {index + 2}")
            except Exception as e:
                logger.warning(f"UI update failed: {e}")

            last_text = text
            index += 1
            logger.info(
                f"Completed prompt {index}/{len(initial_prompts)}, advancing to next",
            )

        logger.info("Automation completed successfully")
        time.sleep(1)
        return True

    except Exception as e:
        logger.error(f"Error during automation: {e}")
        return False
    finally:
        # Simple cleanup
        pass


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


# Main function removed - cursor.py handles application entry point
