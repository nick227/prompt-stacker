import os
import time
from typing import Dict, Tuple, Optional

import pyautogui
from pywinauto.application import Application

Selection = Dict[str, Tuple[int, int]]

DEFAULT_TITLE = os.environ.get("CURSOR_TARGET_TITLE", "Cursor")
DEFAULT_PATTERN = f".*{DEFAULT_TITLE}.*"

PROMPTS = [
    ("input", "Hover over the INPUT field. Capturing in 3 seconds..."),
    ("submit", "Hover over the SUBMIT button. Capturing in 3 seconds..."),
    ("accept", "Hover over the ACCEPT button. Capturing in 3 seconds..."),
]


def _try_find_uia_points(title_pattern: str = DEFAULT_PATTERN) -> Optional[Selection]:
    """Try to locate elements via UIA and return their clickable points.
    Returns None if not found.
    """
    try:
        app = Application(backend='uia').connect(title_re=title_pattern, timeout=3)
        win = app.top_window()

        selection: Selection = {}

        # Input/editor surface
        try:
            editor = win.child_window(control_type='Edit')
            if editor.exists():
                r = editor.rectangle()
                selection["input"] = (r.left + r.width() // 2, r.top + r.height() // 2)
            else:
                doc = win.child_window(control_type='Document')
                if doc.exists():
                    r = doc.rectangle()
                    selection["input"] = (r.left + r.width() // 2, r.top + r.height() // 2)
        except Exception:
            pass

        # Submit button
        try:
            submit = win.child_window(control_type='Button', title_re='^(Send|Submit|Enter|Run)$')
            if submit.exists():
                r = submit.rectangle()
                selection["submit"] = (r.left + r.width() // 2, r.top + r.height() // 2)
        except Exception:
            pass

        # Accept button
        try:
            accept = win.child_window(control_type='Button', title_re='^(Accept|Continue|Proceed)$')
            if accept.exists():
                r = accept.rectangle()
                selection["accept"] = (r.left + r.width() // 2, r.top + r.height() // 2)
        except Exception:
            pass

        if len(selection) == 3:
            return selection
        return None
    except Exception:
        return None


def interactive_coordinate_selection(title_pattern: str = DEFAULT_PATTERN) -> Selection:
    """Ask the user to hover specific controls and capture positions.
    Prefers UIA detection; falls back to timed screen capture.
    """
    uia_points = _try_find_uia_points(title_pattern)
    if uia_points is not None:
        print("Found UI elements via UIA; using their clickable points.")
        return uia_points

    print("UIA elements not found. Falling back to hover capture.")
    captured: Selection = {}
    for key, msg in PROMPTS:
        print(msg)
        time.sleep(3)
        pos = pyautogui.position()
        captured[key] = (pos.x, pos.y)
        print(f"Captured {key}: {captured[key]}")
    return captured
