import os
import time
from typing import Optional

from pywinauto.application import Application

DEFAULT_TITLE = os.environ.get("CURSOR_TARGET_TITLE", "Cursor")

class CursorWindow:
    def __init__(self, title_pattern: Optional[str] = None):
        self.title_pattern = title_pattern or f".*{DEFAULT_TITLE}.*"
        self.app = Application(backend='uia')
        self.window = None

    def connect(self) -> bool:
        try:
            self.app.connect(title_re=self.title_pattern, timeout=5)
            self.window = self.app.top_window()
            return True
        except Exception:
            self.window = None
            return False

    def _click_center(self) -> None:
        if not self.window:
            return
        rect = self.window.rectangle()
        cx = rect.left + (rect.width() // 2)
        cy = rect.top + (rect.height() // 2)
        try:
            self.window.click_input(coords=(cx, cy))
        except Exception:
            pass

    def ensure_focus(self, attempts: int = 5, delay_seconds: float = 0.3) -> bool:
        for _ in range(attempts):
            if self.window is None:
                if not self.connect():
                    time.sleep(delay_seconds)
                    continue
            try:
                self.window.set_focus()
                self._click_center()
                time.sleep(delay_seconds)
                # Consider success after actions; some wrappers don't expose has_focus reliably
                return True
            except Exception:
                # Reset window and retry connect on next iteration
                self.window = None
                time.sleep(delay_seconds)
        return False

    def rect(self):
        if self.window is None:
            return None
        return self.window.rectangle()
