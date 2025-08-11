import os
import time
from typing import Dict, Tuple, Optional

import customtkinter as ctk
from pynput import mouse
from pywinauto.application import Application
from settings_store import load_coords, save_coords

Selection = Dict[str, Tuple[int, int]]

DEFAULT_TITLE = os.environ.get("CURSOR_TARGET_TITLE", "Cursor")
DEFAULT_PATTERN = f".*{DEFAULT_TITLE}.*"

LABELS = {
    "input": "Input",
    "submit": "Submit",
    "accept": "Accept",
}

COLOR_BG = "#0F1115"
COLOR_SURFACE = "#171A21"
COLOR_BORDER = "#2A2F3A"
COLOR_PRIMARY = "#4F8CFF"
COLOR_TEXT = "#E6EAF2"
COLOR_TEXT_MUTED = "#A7B0BF"


def _try_find_uia_points(title_pattern: str = DEFAULT_PATTERN) -> Optional[Selection]:
    try:
        app = Application(backend='uia').connect(title_re=title_pattern, timeout=3)
        win = app.top_window()
        points: Selection = {}
        # Input/editor
        try:
            editor = win.child_window(control_type='Edit')
            if editor.exists():
                r = editor.rectangle()
                points["input"] = (r.left + r.width() // 2, r.top + r.height() // 2)
            else:
                doc = win.child_window(control_type='Document')
                if doc.exists():
                    r = doc.rectangle()
                    points["input"] = (r.left + r.width() // 2, r.top + r.height() // 2)
        except Exception:
            pass
        # Submit
        try:
            submit = win.child_window(control_type='Button', title_re='^(Send|Submit|Enter|Run)$')
            if submit.exists():
                r = submit.rectangle()
                points["submit"] = (r.left + r.width() // 2, r.top + r.height() // 2)
        except Exception:
            pass
        # Accept
        try:
            accept = win.child_window(control_type='Button', title_re='^(Accept|Continue|Proceed)$')
            if accept.exists():
                r = accept.rectangle()
                points["accept"] = (r.left + r.width() // 2, r.top + r.height() // 2)
        except Exception:
            pass
        if len(points) == 3:
            return points
        return None
    except Exception:
        return None


class CoordSelectorUI:
    def __init__(self, title_pattern: str = DEFAULT_PATTERN):
        self.title_pattern = title_pattern
        self.root = ctk.CTk()
        self.root.title("Select Targets")
        self.root.geometry("520x420")
        try:
            self.root.configure(fg_color=COLOR_BG)
        except Exception:
            pass
        self.values: Selection = {}
        self.status_labels: Dict[str, ctk.CTkLabel] = {}
        self.capture_target: Optional[str] = None
        self.listener: Optional[mouse.Listener] = None
        self.pending_capture: Optional[Tuple[str, Tuple[int, int]]] = None
        self.keep_open_var = ctk.BooleanVar(value=False)
        self._build()
        self._load_existing()
        self.root.after(100, self._tick)

    def _build(self):
        card = ctk.CTkFrame(self.root, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 6))
        ctk.CTkLabel(header, text="Pick targets by clicking them in Cursor", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(header, text="Use Auto‑Detect or capture each: Input, Submit, Accept.", font=ctk.CTkFont("Segoe UI", 12), text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=(6, 6))

        for key in ["input", "submit", "accept"]:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=6)
            ctk.CTkLabel(row, text=LABELS[key], width=80, anchor="w", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=COLOR_TEXT).pack(side="left")
            self.status_labels[key] = ctk.CTkLabel(row, text="Not set", font=ctk.CTkFont("Segoe UI", 12), text_color=COLOR_TEXT_MUTED)
            self.status_labels[key].pack(side="left", padx=8)
            ctk.CTkButton(row, text="Capture", width=88, fg_color=COLOR_PRIMARY, hover_color="#3C73D6", command=lambda k=key: self.start_capture(k)).pack(side="right")

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=(4, 10))
        ctk.CTkButton(footer, text="Auto‑Detect", width=110, command=self.auto_detect).pack(side="left")
        ctk.CTkCheckBox(footer, text="Keep selector open", variable=self.keep_open_var).pack(side="left", padx=10)
        self.start_btn = ctk.CTkButton(footer, text="Start", width=90, state="disabled", command=self.finish)
        self.start_btn.pack(side="right")

        self.info = ctk.CTkLabel(card, text="", font=ctk.CTkFont("Segoe UI", 12), text_color=COLOR_TEXT_MUTED)
        self.info.pack(padx=10, pady=(0, 8), anchor="w")

    def _load_existing(self):
        existing = load_coords()
        if not existing:
            return
        self.values.update(existing)
        for k in ("input", "submit", "accept"):
            if k in existing:
                self._update_status(k, existing[k])
        self.info.configure(text="Loaded saved coordinates. You can recapture any.")

    def _update_status(self, key: str, value: Optional[Tuple[int, int]]):
        if value is None:
            self.status_labels[key].configure(text="Not set", text_color=COLOR_TEXT_MUTED)
        else:
            self.status_labels[key].configure(text=f"{value[0]}, {value[1]}", text_color=COLOR_TEXT)
        self._update_start_state()

    def _update_start_state(self):
        ready = all(k in self.values for k in ("input", "submit", "accept"))
        self.start_btn.configure(state="normal" if ready else "disabled")

    def _process_pending_capture(self):
        if not self.pending_capture:
            return
        key, value = self.pending_capture
        self.pending_capture = None
        self.values[key] = value
        # Restore window and update UI
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass
        self.info.configure(text="")
        self._update_status(key, value)

    def _tick(self):
        self._process_pending_capture()
        self.root.after(100, self._tick)

    def _on_click(self, x, y, button, pressed):
        # Listener thread: do not call Tk APIs here
        if pressed and self.capture_target:
            key = self.capture_target
            self.capture_target = None
            self.pending_capture = (key, (int(x), int(y)))
            try:
                if self.listener:
                    self.listener.stop()
            except Exception:
                pass
            return False
        return True

    def start_capture(self, key: str):
        # Minimize/hide window so user can click target beneath
        self.capture_target = key
        self.info.configure(text=f"Capturing {LABELS[key]}… click the target in Cursor.")
        try:
            self.root.withdraw()
        except Exception:
            pass
        time.sleep(0.12)
        # Global mouse listener for one click
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.start()

    def auto_detect(self):
        pts = _try_find_uia_points(self.title_pattern)
        if pts is None:
            self.info.configure(text="Auto‑Detect failed. Use Capture.")
            return
        self.values.update(pts)
        for k in ("input", "submit", "accept"):
            self._update_status(k, self.values.get(k))
        self.info.configure(text="Auto‑Detect set all targets.")

    def finish(self):
        # Persist
        try:
            save_coords(self.values)
        except Exception:
            pass
        if self.keep_open_var.get():
            # Minimize instead of closing
            try:
                self.root.iconify()
                # Do not block run(); allow caller to proceed
            except Exception:
                pass
            self.root.quit()
        else:
            self.root.quit()

    def run(self) -> Selection:
        self.root.mainloop()
        # Ensure listener stopped
        try:
            if self.listener:
                self.listener.stop()
        except Exception:
            pass
        # Destroy root to avoid conflicts with later CTk windows
        try:
            self.root.destroy()
        except Exception:
            pass
        return {
            "input": self.values["input"],
            "submit": self.values["submit"],
            "accept": self.values["accept"],
        }


def ui_coordinate_selection(title_pattern: str = DEFAULT_PATTERN) -> Selection:
    ui = CoordSelectorUI(title_pattern)
    return ui.run()
