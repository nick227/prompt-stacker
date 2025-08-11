"""Cursor automation launcher.

This script delegates to the modular pipeline defined in:
- dpi.py (DPI awareness)
- win_focus.py (window focus)
- coord_selector.py (pre-run coordinate/UIA selection)
- ui_countdown.py (countdown UI)
- automator.py (main automation)

"""

from automator import run_automation
from prompt_lists.prompt_list import prompt_list


if __name__ == "__main__":
    run_automation(prompt_list)
