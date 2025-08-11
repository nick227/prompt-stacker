import customtkinter as ctk
from typing import Optional, Dict, Any

# Visual design system (compact, high-contrast, dark-themed)
WINDOW_SIZE = "600x480"
TITLE = "Session"
WRAPLENGTH = 520

# Typography
FONT_H1 = ("Segoe UI Variable", 30, "bold")
FONT_H2 = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_BODY_MUTED = ("Segoe UI", 11)

# Palette
COLOR_BG = "#0F1115"
COLOR_SURFACE = "#171A21"
COLOR_SURFACE_ALT = "#1E232C"
COLOR_BORDER = "#2A2F3A"
COLOR_PRIMARY = "#4F8CFF"
COLOR_PRIMARY_HOVER = "#3C73D6"
COLOR_ACCENT = "#9BDBFF"
COLOR_TEXT = "#E6EAF2"
COLOR_TEXT_MUTED = "#A7B0BF"
COLOR_WARNING = "#FFB020"
COLOR_DANGER = "#FF5D5D"

THEME = "blue"
MODE = "dark"

# Track a singleton hidden root to host toplevels across the app
_hidden_root: Optional[ctk.CTk] = None


def _ensure_root() -> ctk.CTk:
    global _hidden_root
    if _hidden_root is None:
        ctk.set_appearance_mode(MODE)
        ctk.set_default_color_theme(THEME)
        _hidden_root = ctk.CTk()
        # Hide root; we'll use only Toplevels
        try:
            _hidden_root.withdraw()
        except Exception:
            pass
    return _hidden_root


def _label(parent, text: str, font, color=COLOR_TEXT, wrap: Optional[int] = None, justify="left", padx=0, pady=0, anchor="w"):
    kwargs = {
        "text": text,
        "font": ctk.CTkFont(*font),
        "text_color": color,
        "justify": justify,
    }
    if wrap is not None:
        kwargs["wraplength"] = wrap
    lbl = ctk.CTkLabel(parent, **kwargs)
    lbl.pack(padx=padx, pady=pady, anchor=anchor)
    return lbl


def _button(parent, text: str, command, color_fg, color_hover, color_text=COLOR_TEXT, width=84):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        fg_color=color_fg,
        hover_color=color_hover,
        text_color=color_text,
        corner_radius=8,
        height=34,
    )


def _build_countdown_ui(win, cb, text: Optional[str] = None, next_text: Optional[str] = None, last_text: Optional[str] = None):
    # Window + background
    win.geometry(WINDOW_SIZE)
    win.title(TITLE)
    try:
        win.configure(fg_color=COLOR_BG)
    except Exception:
        pass

    # Card container
    card = ctk.CTkFrame(win, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
    card.pack(fill="both", expand=True, padx=14, pady=14)

    # Header: time and progress
    header = ctk.CTkFrame(card, fg_color=COLOR_SURFACE_ALT, corner_radius=10)
    header.pack(fill="x", padx=10, pady=(10, 8))

    time_row = ctk.CTkFrame(header, fg_color="transparent")
    time_row.pack(fill="x", padx=12, pady=(10, 6))

    time_label = ctk.CTkLabel(time_row, text="", font=ctk.CTkFont(*FONT_H1), text_color=COLOR_TEXT)
    time_label.pack(side="left")
    _label(time_row, "sec", FONT_BODY_MUTED, COLOR_TEXT_MUTED, padx=8, anchor="w")

    progress = ctk.CTkProgressBar(header, height=8, corner_radius=6, fg_color=COLOR_BORDER, progress_color=COLOR_PRIMARY)
    progress.pack(fill="x", padx=12, pady=(0, 12))
    progress.set(1.0)

    # Content area (scrollable)
    content = ctk.CTkScrollableFrame(card, width=WRAPLENGTH, height=180, fg_color=COLOR_SURFACE)
    content.pack(fill="both", expand=True, padx=10, pady=(0, 6))

    if text:
        _label(content, "Current", FONT_H2, COLOR_ACCENT, padx=2, pady=(6, 2))
        _label(content, text, FONT_BODY, COLOR_TEXT, wrap=WRAPLENGTH - 24, padx=8, pady=(0, 4))

    if next_text:
        _label(content, "Next", FONT_H2, COLOR_TEXT_MUTED, padx=2, pady=(8, 2))
        _label(content, next_text, FONT_BODY_MUTED, COLOR_TEXT_MUTED, wrap=WRAPLENGTH - 36, padx=16, pady=(0, 2))

    # Footer controls
    footer = ctk.CTkFrame(card, fg_color="transparent")
    footer.pack(pady=8)

    pause_btn = _button(footer, "Pause", cb["toggle_pause"], "#1F2430", "#2B3240", width=86)
    pause_btn.pack(side="left", padx=5)

    next_btn = _button(footer, "Next", cb["skip"], COLOR_PRIMARY, "#3C73D6", width=74)
    next_btn.pack(side="left", padx=5)

    if last_text:
        retry_btn = _button(footer, "Retry", cb["retry"], "#FFB020", "#E89A12", width=74)
        retry_btn.pack(side="left", padx=5)
    else:
        retry_btn = None

    cancel_btn = _button(footer, "Cancel", cb["cancel"], "#FF5D5D", "#E05050", width=82)
    cancel_btn.pack(side="left", padx=5)

    return time_label, pause_btn, retry_btn, progress


def show_countdown(seconds: int, text: Optional[str] = None, next_text: Optional[str] = None, last_text: Optional[str] = None) -> Dict[str, Any]:
    root = _ensure_root()
    win = ctk.CTkToplevel(root)

    paused = cancelled = skipped = retried = False
    total = max(1, int(seconds))

    def close_win():
        try:
            win.destroy()
        except Exception:
            pass

    def toggle_pause():
        nonlocal paused
        paused = not paused
        pause_btn.configure(text="Resume" if paused else "Pause")

    def skip():
        nonlocal skipped
        skipped = True
        close_win()

    def cancel():
        nonlocal cancelled
        cancelled = True
        close_win()

    def retry():
        nonlocal retried
        retried = True
        close_win()

    time_label, pause_btn, _retry_btn, progress = _build_countdown_ui(win, {
        "toggle_pause": toggle_pause,
        "skip": skip,
        "cancel": cancel,
        "retry": retry
    }, text, next_text, last_text)

    def update():
        nonlocal seconds
        if cancelled or skipped or retried or seconds <= 0:
            close_win()
        else:
            if not paused:
                time_label.configure(text=str(seconds))
                pct = max(0.0, min(1.0, seconds / total))
                progress.set(pct)
                seconds -= 1
            win.after(1000, update)

    time_label.configure(text=str(seconds))
    progress.set(1.0)
    update()

    # Run a nested event loop for this toplevel, not a full root mainloop
    win.grab_set()
    root.wait_window(win)

    return {"cancelled": cancelled, "skipped": skipped, "retried": retried}
