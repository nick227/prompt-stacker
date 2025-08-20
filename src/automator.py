import logging
import sys
import threading
import time
from typing import List, Tuple

import pyautogui
import pyperclip

try:
    from .ui import SessionUI
except ImportError:
    # Fallback for standalone execution
    from ui import SessionUI

try:
    from .dpi import enable_windows_dpi_awareness
    from .win_focus import CursorWindow
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    # Add src directory to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

    from dpi import enable_windows_dpi_awareness
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
                    logger.info(f"Clipboard copy successful: '{expected_text[:50]}...'")
                    return True
                logger.warning(
                    f"Clipboard verification failed on attempt {attempt + 1}. "
                    f"Expected: '{expected_text[:50]}...', "
                    f"Got: '{clipboard_text[:50]}...'",
                )

            except Exception as e:
                logger.warning(
                    f"Clipboard operation failed on attempt {attempt + 1}: {e}",
                )
                if attempt == CLIPBOARD_RETRY_ATTEMPTS - 1:  # Last attempt
                    logger.error(
                        f"Clipboard copy failed after {CLIPBOARD_RETRY_ATTEMPTS} "
                        f"attempts: {e}",
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

    logger.info(f"Attempting to click button at coordinates {coords} "
               f"with pattern '{pattern}'")

    def button_operation():
        try:
            # CRITICAL FIX: Add timeout protection for window connection
            if win.window is None:
                logger.info("Window is None, attempting to connect...")
                try:
                    if not win.connect():
                        logger.info("Window connection failed, falling back to "
                                  "coordinate click")
                        return click_with_timeout(coords)
                except Exception as e:
                    logger.warning(f"Window connection failed with exception: {e}, "
                                 f"falling back to coordinate click")

            logger.info("Searching for button with pattern: " + pattern)
            try:
                btn = win.window.child_window(control_type="Button", title_re=pattern)
            except Exception as e:
                logger.warning(f"Button search failed: {e}, falling back to "
                             f"coordinate click")
                return click_with_timeout(coords)

            # CRITICAL FIX: Add timeout protection for button existence check
            try:
                if btn.exists():
                    logger.info(f"Found button '{btn.window_text()}' - "
                              f"attempting to click")
                    try:
                        btn.invoke()
                        logger.info("Button invoke() successful")
                        return True
                    except Exception as e:
                        logger.warning(f"Button invoke() failed: {e}, trying "
                                     f"click_input()")
                        try:
                            btn.click_input()
                            logger.info("Button click_input() successful")
                            return True
                        except Exception as e2:
                            logger.warning(f"Button click_input() failed: {e2}")
                else:
                    logger.warning(f"No button found matching pattern '{pattern}'")
            except Exception as e:
                logger.warning(f"Button existence check failed: {e}, falling "
                             f"back to coordinate click")
                return click_with_timeout(coords)

        except Exception as e:
            logger.warning(f"Button search/click failed: {e}")

        logger.info("Falling back to coordinate-based click")
        return click_with_timeout(coords)

    # CRITICAL FIX: Increase timeout for button operations that might hang
    result = run_with_timeout(button_operation, CLICK_TIMEOUT * 2)  # Double the timeout
    logger.info(f"Button click operation result: {result}")
    return result or False


def perform_paste_operation(text: str) -> bool:
    """Perform paste operation with multiple fallback methods and timeout protection."""
    logger.info("Selecting all text and pasting")

    # Select all and paste (simplified)
    try:
        # Clear any existing selection first
        pyautogui.click()  # Ensure focus
        time.sleep(0.1)

        # Select all text
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.3)  # Increased delay for better reliability

        # Paste from clipboard
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)  # Increased delay for better reliability

        logger.info("Ctrl+V paste operation completed")
        return True
    except Exception as e:
        logger.warning(f"Ctrl+V paste failed: {e}, trying direct text input")
        try:
            # Clear and type directly
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.1)
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
    """
    DEPRECATED: This function has been replaced by the centralized
    AutomationController.

    This function is kept for backward compatibility but should not be used.
    The new AutomationController provides better reliability and maintainability.

    Args:
        ui: UI session instance
        prompt_index: Index of prompt to process

    Returns:
        True if automation completed successfully, False otherwise
    """
    logger.warning("DEPRECATED: run_single_prompt_automation() is deprecated. "
                  "Use AutomationController instead.")

    # Import the new controller
    try:
        from .automation_controller import AutomationController
        controller = AutomationController(ui)
        # Set the current prompt index and start automation
        controller._context.current_prompt_index = prompt_index
        return controller.start_automation()
    except ImportError:
        logger.error("AutomationController not available - automation failed")
        return False


def run_automation_with_ui(ui) -> bool:
    """
    DEPRECATED: This function has been replaced by the centralized
    AutomationController.

    This function is kept for backward compatibility but should not be used.
    The new AutomationController provides better reliability and maintainability.

    Args:
        ui: UI session instance

    Returns:
        True if automation completed successfully, False otherwise
    """
    logger.warning("DEPRECATED: run_automation_with_ui() is deprecated. "
                  "Use AutomationController instead.")

    # Import the new controller
    try:
        from .automation_controller import AutomationController
        controller = AutomationController(ui)
        return controller.start_automation()
    except ImportError:
        logger.error("AutomationController not available - automation failed")
        return False


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
