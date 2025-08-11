import logging
import time
from typing import Dict, Tuple, List

import pyautogui
import pyperclip

from dpi import enable_windows_dpi_awareness
from win_focus import CursorWindow
from ui_session import SessionUI
from code_report_card import code_report_card

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Defaults (can be edited in UI)
DEFAULT_START_DELAY = 5
DEFAULT_MAIN_WAIT = 300
DEFAULT_COOLDOWN = 0.2

# Automation timing constants
FOCUS_DELAY = 0.05
CLIPBOARD_RETRY_ATTEMPTS = 3
CLIPBOARD_RETRY_DELAY = 0.2
GET_READY_DELAY = 2.0  # Default get ready pause before each cycle

pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True


def paste_text_safely(text: str) -> None:
    """Safely copy text to clipboard with verification."""
    for attempt in range(CLIPBOARD_RETRY_ATTEMPTS):
        try:
            pyperclip.copy(text)
            time.sleep(CLIPBOARD_RETRY_DELAY)
            if pyperclip.paste().strip() == text.strip():
                return
        except Exception as e:
            if attempt == CLIPBOARD_RETRY_ATTEMPTS - 1:  # Last attempt
                raise RuntimeError(f"Clipboard copy failed after {CLIPBOARD_RETRY_ATTEMPTS} attempts: {e}")
            continue
    raise RuntimeError("Clipboard copy failed - text verification failed")


def click_button_or_fallback(win: CursorWindow, coords: Tuple[int, int], pattern: str) -> None:
    try:
        if win.window is None and not win.connect():
            pyautogui.click(*coords)
            return
        btn = win.window.child_window(control_type='Button', title_re=pattern)
        if btn.exists():
            try:
                btn.invoke(); return
            except Exception:
                try:
                    btn.click_input(); return
                except Exception:
                    pass
    except Exception:
        pass
    pyautogui.click(*coords)


def run_automation(prompts: List[str]) -> None:
    """Run the automation process with the given prompts."""
    logger.info(f"Starting automation with {len(prompts)} prompts")
    
    if not isinstance(prompts, list):
        raise ValueError("Prompts must be a list of strings")
    
    # Filter out empty prompts
    prompts = [p.strip() for p in prompts if p and p.strip()]
    logger.info(f"Filtered to {len(prompts)} valid prompts")
    
    enable_windows_dpi_awareness()
    logger.info("DPI awareness enabled")

    ui = SessionUI(DEFAULT_START_DELAY, DEFAULT_MAIN_WAIT, DEFAULT_COOLDOWN)
    ui.wait_for_start()

    win = CursorWindow()

    coords: Dict[str, Tuple[int, int]] = ui.get_coords()
    start_delay, main_wait, cooldown, get_ready_delay = ui.get_timers()

    if not prompts:
        ui.info.configure(text="No prompts provided.")
        ui.close()
        return

    # Start delay countdown
    next_preview = prompts[0] if prompts else None
    result = ui.countdown(start_delay, "About to start!", next_preview, None)
    if result.get("cancelled"):
        ui.close(); return

    index = 0
    last_text = None
    while index < len(prompts):
        # Always read fresh timers/coords in case user edits them
        coords = ui.get_coords()
        start_delay, main_wait, cooldown, get_ready_delay = ui.get_timers()

        text = prompts[index]
        
        # Get ready pause with dialog to front
        ui.bring_to_front()
        ui.info.configure(text=f"Starting cycle {index + 1}/{len(prompts)}")
        result = ui.countdown(get_ready_delay, f"Starting in {index + 1}-{len(prompts)}", text, last_text)
        if result.get("cancelled"):
            ui.close(); return
        
        # Process visualization and automation
        ui.info.configure(text=f"📝 Pasting text...")
        paste_text_safely(text)

        ui.info.configure(text=f"🎯 Focusing input...")
        pyautogui.click(*coords["input"])  # focus by click
        time.sleep(FOCUS_DELAY)  # minimal delay for focus
        
        ui.info.configure(text=f"📋 Pasting content...")
        pyautogui.hotkey("ctrl", "a")  # select all
        pyautogui.hotkey("ctrl", "v")  # paste

        ui.info.configure(text=f"🚀 Submitting...")
        click_button_or_fallback(win, coords["submit"], r"^(Send|Submit|Enter|Run)$")

        next_text = prompts[index + 1] if index + 1 < len(prompts) else None
        result = ui.countdown(main_wait, text, next_text, last_text)
        if result.get("cancelled"):
            ui.close(); return
        if result.get("retried") and last_text is not None:
            index = max(0, index - 1)
            continue
        if not result.get("skipped"):
            ui.info.configure(text=f"✅ Accepting response...")
            click_button_or_fallback(win, coords["accept"], r"^(Accept|Continue|Proceed)$")
            if ui.countdown(int(cooldown), "Waiting...", next_text, last_text).get("cancelled"):
                ui.close(); return

        last_text = text
        index += 1

    logger.info("Automation completed successfully")
    ui.info.configure(text="All prompts submitted.")
    time.sleep(1)
    ui.close()


if __name__ == "__main__":
    try:
        run_automation(code_report_card)
    except KeyboardInterrupt:
        logger.info("Automation interrupted by user")
    except Exception as e:
        logger.error(f"Automation failed: {e}")
        raise
