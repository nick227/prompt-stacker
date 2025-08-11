"""
Cursor Automation System - UI Session Manager

This module provides a comprehensive GUI for the Cursor automation system.
Features include coordinate capture, timer configuration, real-time countdown,
and process visualization with a beautiful Monokai dark theme.

Key Components:
- Coordinate capture system for input, submit, and accept targets
- Configurable timing controls (start delay, main wait, cooldown, get ready)
- Real-time countdown with pause/resume functionality
- Process visualization with emoji indicators
- Persistent settings storage
- Responsive UI with fixed window sizing

Author: Automation System
Version: 2.0
"""

import time
from typing import Dict, Tuple, Optional, Any

import customtkinter as ctk
from pynput import mouse
import pyautogui

from settings_store import load_coords, save_coords

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

Coords = Dict[str, Tuple[int, int]]

# =============================================================================
# CONSTANTS - UI CONFIGURATION
# =============================================================================

# Target Labels for UI Display
LABELS = {
    "input": "Input",
    "submit": "Submit", 
    "accept": "Accept",
}

# Layout Constants - Enhanced Monokai Spacing
WINDOW_WIDTH = 840
WINDOW_HEIGHT = 580
WINDOW_MARGIN = 20
CARD_RADIUS = 12
SECTION_RADIUS = 12
PADDING = 16
GUTTER = 12
BUTTON_WIDTH = 100
ENTRY_WIDTH = 120

# Monokai Dark Theme Color Palette
COLOR_BG = "#272822"                    # Main background
COLOR_SURFACE = "#3E3D32"               # Surface elements
COLOR_SURFACE_ALT = "#2F2F2F"           # Alternative surface
COLOR_BORDER = "#75715E"                # Borders and dividers
COLOR_PRIMARY = "#F92672"               # Primary actions (pink/red)
COLOR_PRIMARY_HOVER = "#FD5FF0"         # Primary hover state
COLOR_TEXT = "#F8F8F2"                  # Primary text
WHITE_COLOR_TEXT = "#FFFFFF"            # White text for contrast
COLOR_TEXT_MUTED = "#75715E"            # Muted/secondary text
COLOR_ACCENT = "#A6E22E"                # Accent actions (green)
COLOR_WARNING = "#E6DB74"               # Warning actions (yellow)
COLOR_ERROR = "#F92672"                 # Error/destructive actions (red)
COLOR_SUCCESS = "#A6E22E"               # Success states (green)

# Typography Configuration
FONT_H1 = ("Segoe UI Variable", 28, "bold")    # Large headings
FONT_H2 = ("Segoe UI", 13, "bold")             # Section headings
FONT_BODY = ("Segoe UI", 12)                   # Body text

# =============================================================================
# MAIN UI CLASS
# =============================================================================

class SessionUI:
    """
    Main UI session manager for the Cursor automation system.
    
    This class handles all user interface components including:
    - Coordinate capture system
    - Timer configuration
    - Real-time countdown display
    - Process visualization
    - User interaction controls
    
    The UI is built with a fixed-size window to prevent layout issues
    and uses a consistent Monokai dark theme throughout.
    """
    
    def __init__(self, default_start: int, default_main: int, default_cooldown: float):
        """
        Initialize the UI session manager.
        
        Args:
            default_start: Default start delay in seconds
            default_main: Default main wait time in seconds  
            default_cooldown: Default cooldown time in seconds
        """
        self._initialize_window()
        self._initialize_state(default_start, default_main, default_cooldown)
        self._build_interface()
        self._start_event_polling()
    
    # =============================================================================
    # INITIALIZATION METHODS
    # =============================================================================
    
    def _initialize_window(self) -> None:
        """Initialize the main application window with fixed sizing and theme."""
        self.root = ctk.CTk()
        self.root.title("Cursor Session")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+20+20")
        
        try:
            # Set fixed size to prevent resizing issues
            self.root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
            self.root.maxsize(WINDOW_WIDTH, WINDOW_HEIGHT)
            self.root.resizable(False, False)  # Disable resizing
            self.root.configure(fg_color=COLOR_BG)
        except Exception:
            pass  # Graceful fallback if window configuration fails
    
    def _initialize_state(self, default_start: int, default_main: int, default_cooldown: float) -> None:
        """Initialize internal state variables and data structures."""
        # Load saved coordinates or start with empty dict
        self.coords: Coords = load_coords() or {}
        
        # UI component references
        self.status_labels: Dict[str, ctk.CTkLabel] = {}
        
        # Mouse capture system state
        self.listener: Optional[mouse.Listener] = None
        self.capture_target: Optional[str] = None
        self.pending_capture: Optional[Tuple[str, Tuple[int, int]]] = None
        self._last_geometry: Optional[str] = None
        
        # Timer configuration variables
        self.var_start = ctk.StringVar(value=str(int(default_start)))
        self.var_main = ctk.StringVar(value=str(int(default_main)))
        self.var_cooldown = ctk.StringVar(value=str(default_cooldown))
        self.var_get_ready = ctk.StringVar(value="2.0")  # Default get ready delay
        
        # Countdown control state
        self.paused = False
        self.cancelled = False
        self.skipped = False
        self.retried = False
        
        # Session state
        self._started = False
    
    def _start_event_polling(self) -> None:
        """Start the event polling loop for coordinate capture."""
        self.root.after(100, self._tick)
    
    # =============================================================================
    # UI HELPER METHODS
    # =============================================================================
    
    def _section_title(self, parent, text: str) -> None:
        """Create a section title label with consistent styling."""
        ctk.CTkLabel(
            parent, 
            text=text, 
            font=ctk.CTkFont(*FONT_H2), 
            text_color=COLOR_TEXT
        ).pack(anchor="w")
    
    def _kv_row(self, parent, key_text: str, value_text: str) -> ctk.CTkLabel:
        """Create a key-value row with consistent layout."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(GUTTER//2))
        
        # Key label (left side)
        ctk.CTkLabel(
            row, 
            text=key_text, 
            width=72, 
            anchor="w", 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT
        ).pack(side="left")
        
        # Value label (right side)
        value = ctk.CTkLabel(
            row, 
            text=value_text, 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT_MUTED
        )
        value.pack(side="left", padx=8)
        return value
    
    def _labeled_entry(self, parent, label: str, var: ctk.StringVar, row: int) -> None:
        """Create a labeled entry field with consistent styling."""
        # Label
        ctk.CTkLabel(
            parent, 
            text=label, 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT
        ).grid(row=row, column=0, sticky="w", pady=GUTTER//2, padx=(0, 6))
        
        # Entry field
        entry = ctk.CTkEntry(
            parent, 
            textvariable=var, 
            width=ENTRY_WIDTH,
            fg_color=COLOR_SURFACE,
            text_color=COLOR_TEXT,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6
        )
        entry.grid(row=row, column=1, sticky="e", pady=GUTTER//2)

    # =============================================================================
    # INTERFACE CONSTRUCTION
    # =============================================================================
    
    def _section_title(self, parent, text: str) -> None:
        """Create a section title label with consistent styling."""
        ctk.CTkLabel(
            parent, 
            text=text, 
            font=ctk.CTkFont(*FONT_H2), 
            text_color=COLOR_TEXT
        ).pack(anchor="w")
    
    def _kv_row(self, parent, key_text: str, value_text: str) -> ctk.CTkLabel:
        """Create a key-value row with consistent layout."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(GUTTER//2))
        
        # Key label (left side)
        ctk.CTkLabel(
            row, 
            text=key_text, 
            width=72, 
            anchor="w", 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT
        ).pack(side="left")
        
        # Value label (right side)
        value = ctk.CTkLabel(
            row, 
            text=value_text, 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT_MUTED
        )
        value.pack(side="left", padx=8)
        return value
    
    def _labeled_entry(self, parent, label: str, var: ctk.StringVar, row: int) -> None:
        """Create a labeled entry field with consistent styling."""
        # Label
        ctk.CTkLabel(
            parent, 
            text=label, 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT
        ).grid(row=row, column=0, sticky="w", pady=GUTTER//2, padx=(0, 6))
        
        # Entry field
        entry = ctk.CTkEntry(
            parent, 
            textvariable=var, 
            width=ENTRY_WIDTH,
            fg_color=COLOR_SURFACE,
            text_color=COLOR_TEXT,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6
        )
        entry.grid(row=row, column=1, sticky="e", pady=GUTTER//2)
    
    # =============================================================================
    # INTERFACE CONSTRUCTION
    # =============================================================================
    
    def _build_interface(self) -> None:
        """Build the complete user interface layout."""
        self._build_main_container()
        self._build_setup_section()
        self._build_control_section()
        self._build_countdown_section()
        self._update_start_state()
    
    def _build_main_container(self) -> None:
        """Create the main container with background and border."""
        self.container = ctk.CTkFrame(
            self.root, 
            fg_color=COLOR_SURFACE, 
            corner_radius=SECTION_RADIUS, 
            border_width=1, 
            border_color=COLOR_BORDER
        )
        self.container.pack(fill="both", expand=True, padx=WINDOW_MARGIN, pady=WINDOW_MARGIN)
    
    def _build_setup_section(self) -> None:
        """Build the setup section with targets and timers."""
        # Main setup frame
        setup = ctk.CTkFrame(
            self.container, 
            fg_color=COLOR_SURFACE_ALT, 
            corner_radius=SECTION_RADIUS
        )
        setup.pack(fill="x", padx=PADDING, pady=(PADDING, GUTTER))
        
        # Left side - Targets
        self._build_targets_section(setup)
        
        # Right side - Timers
        self._build_timers_section(setup)
    
    def _build_targets_section(self, parent) -> None:
        """Build the targets section for coordinate capture."""
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=PADDING, pady=PADDING)
        
        self._section_title(left, "Targets")
        
        # Create target rows for each coordinate type
        for key in ["input", "submit", "accept"]:
            self._build_target_row(left, key)
    
    def _build_target_row(self, parent, key: str) -> None:
        """Build a single target row with label, status, and capture button."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=GUTTER//2)
        
        # Target label
        ctk.CTkLabel(
            row, 
            text=LABELS[key], 
            width=72, 
            anchor="w", 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT
        ).pack(side="left")
        
        # Status label (shows coordinates or "Not set")
        self.status_labels[key] = ctk.CTkLabel(
            row,
            text=self._coord_text(self.coords.get(key)),
            font=ctk.CTkFont(*FONT_BODY),
            text_color=(COLOR_SUCCESS if key in self.coords else COLOR_TEXT_MUTED),
        )
        self.status_labels[key].pack(side="left", padx=8)
        
        # Capture button
        ctk.CTkButton(
            row,
            text="Capture",
            width=BUTTON_WIDTH,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_SUCCESS,
            text_color=COLOR_BG,
            command=lambda k=key: self._start_capture(k),
        ).pack(side="right")
    
    def _build_timers_section(self, parent) -> None:
        """Build the timers section for configuration."""
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.pack(side="right", padx=PADDING, pady=PADDING)
        
        self._section_title(right, "Timers")
        
        # Timer form with grid layout
        right_form = ctk.CTkFrame(right, fg_color="transparent")
        right_form.pack(fill="x")
        right_form.grid_columnconfigure(0, weight=1)
        right_form.grid_columnconfigure(1, weight=0)
        
        # Timer entry fields
        self._labeled_entry(right_form, "Start (sec)", self.var_start, 1)
        self._labeled_entry(right_form, "Main Wait (sec)", self.var_main, 2)
        self._labeled_entry(right_form, "Cooldown (sec)", self.var_cooldown, 3)
        self._labeled_entry(right_form, "Get Ready (sec)", self.var_get_ready, 4)
    
    def _build_control_section(self) -> None:
        """Build the control section with info and start button."""
        control = ctk.CTkFrame(self.container, fg_color="transparent")
        control.pack(fill="x", padx=PADDING, pady=(0, GUTTER))
        
        # Info label
        self.info = ctk.CTkLabel(
            control, 
            text="Set all coords and timers, then Start.", 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT_MUTED
        )
        self.info.pack(side="left")
        
        # Start button
        self.start_btn = ctk.CTkButton(
            control, 
            text="Start", 
            width=BUTTON_WIDTH, 
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=WHITE_COLOR_TEXT,
            command=self._on_start
        )
        self.start_btn.pack(side="right")
    
    def _build_countdown_section(self) -> None:
        """Build the countdown section with timer display and controls."""
        # Main countdown card
        self.card = ctk.CTkFrame(
            self.container, 
            fg_color=COLOR_SURFACE_ALT, 
            corner_radius=CARD_RADIUS
        )
        self.card.pack(fill="both", expand=True, padx=PADDING, pady=(GUTTER, PADDING))
        
        # Header with time display
        self._build_countdown_header()
        
        # Progress bar
        self._build_progress_bar()
        
        # Content area with text boxes
        self._build_content_area()
        
        # Footer with control buttons
        self._build_control_buttons()
    
    def _build_countdown_header(self) -> None:
        """Build the countdown header with time display."""
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=PADDING, pady=(PADDING, GUTTER))
        
        # Large time label
        self.time_label = ctk.CTkLabel(
            header, 
            text="", 
            font=ctk.CTkFont(*FONT_H1), 
            text_color=COLOR_ACCENT
        )
        self.time_label.pack(side="left")
        
        # "sec" label
        ctk.CTkLabel(
            header, 
            text="sec", 
            font=ctk.CTkFont(*FONT_BODY), 
            text_color=COLOR_TEXT_MUTED
        ).pack(side="left", padx=GUTTER)
    
    def _build_progress_bar(self) -> None:
        """Build the progress bar for visual countdown feedback."""
        self.progress = ctk.CTkProgressBar(
            self.card, 
            height=10, 
            corner_radius=8, 
            fg_color=COLOR_BORDER, 
            progress_color=COLOR_ACCENT
        )
        self.progress.pack(fill="x", padx=PADDING, pady=(0, GUTTER))
        self.progress.set(0.0)
    
    def _build_content_area(self) -> None:
        """Build the content area with current and next text boxes."""
        content = ctk.CTkFrame(self.card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PADDING, pady=GUTTER)
        
        # Current text box (shows active prompt)
        self.current_box = ctk.CTkTextbox(
            content,
            height=70,
            activate_scrollbars=False,
            wrap="word",
            fg_color=COLOR_SURFACE,
            text_color=COLOR_TEXT,
            corner_radius=8,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.current_box.pack(fill="x", pady=(0, GUTTER//2))
        self.current_box.configure(state="disabled")
        
        # Next text box (shows upcoming prompt)
        self.next_box = ctk.CTkTextbox(
            content,
            height=70,
            activate_scrollbars=False,
            wrap="word",
            fg_color=COLOR_SURFACE,
            text_color=COLOR_TEXT_MUTED,
            corner_radius=8,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.next_box.pack(fill="x", pady=(GUTTER//2, 0))
        self.next_box.configure(state="disabled")
    
    def _build_control_buttons(self) -> None:
        """Build the control buttons in the footer."""
        footer = ctk.CTkFrame(self.card, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=PADDING)
        
        # Pause/Resume button
        self.pause_btn = ctk.CTkButton(
            footer, 
            text="Pause", 
            width=BUTTON_WIDTH, 
            fg_color=COLOR_WARNING,
            hover_color=COLOR_ACCENT,
            text_color=COLOR_BG,
            command=self._toggle_pause
        )
        self.pause_btn.pack(side="left", padx=GUTTER)
        
        # Next button (skip current cycle)
        self.next_btn = ctk.CTkButton(
            footer, 
            text="Next", 
            width=BUTTON_WIDTH, 
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_SUCCESS,
            text_color=COLOR_BG,
            command=self._on_skip
        )
        self.next_btn.pack(side="left", padx=GUTTER)
        
        # Retry button (repeat previous cycle)
        self.retry_btn = ctk.CTkButton(
            footer, 
            text="Retry", 
            width=BUTTON_WIDTH, 
            fg_color=COLOR_WARNING,
            hover_color=COLOR_ACCENT,
            text_color=COLOR_BG,
            command=self._on_retry
        )
        self.retry_btn.pack(side="left", padx=GUTTER)
        
        # Cancel button (stop automation)
        self.cancel_btn = ctk.CTkButton(
            footer, 
            text="Cancel", 
            width=BUTTON_WIDTH, 
            fg_color=COLOR_ERROR,
            hover_color=COLOR_PRIMARY,
            text_color=COLOR_BG,
            command=self._on_cancel
        )
        self.cancel_btn.pack(side="left", padx=GUTTER)
        
        # Initially disable control buttons until session starts
        for btn in (self.pause_btn, self.next_btn, self.retry_btn, self.cancel_btn):
            btn.configure(state="disabled")
    
    # =============================================================================
    # COORDINATE CAPTURE SYSTEM
    # =============================================================================
    
    def _coord_text(self, val: Optional[Tuple[int, int]]) -> str:
        """Format coordinate tuple for display."""
        return f"{val[0]}, {val[1]}" if val else "Not set"
    
    def _start_capture(self, key: str) -> None:
        """
        Start coordinate capture for the specified target.
        
        Args:
            key: The target key ('input', 'submit', or 'accept')
        """
        self.capture_target = key
        self.info.configure(text=f"Capturing {LABELS[key]}… click target in Cursor.")
        
        # Minimize window to avoid interference during capture
        try:
            self._last_geometry = self.root.geometry()
            self.root.iconify()  # Minimize instead of hiding
        except Exception:
            pass
        
        # Small delay to ensure window is minimized
        time.sleep(0.12)
        
        # Start mouse listener for coordinate capture
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.start()
    
    def _on_click(self, x, y, button, pressed):
        """
        Handle mouse click events during coordinate capture.
        
        Args:
            x, y: Mouse coordinates
            button: Mouse button
            pressed: Whether button was pressed or released
            
        Returns:
            bool: True to continue listening, False to stop
        """
        if pressed and self.capture_target:
            key = self.capture_target
            self.capture_target = None
            self.pending_capture = (key, (int(x), int(y)))
            
            # Stop the mouse listener
            try:
                if self.listener:
                    self.listener.stop()
            except Exception:
                pass
            
            return False  # Stop listening
        return True  # Continue listening
    
    def _tick(self) -> None:
        """
        Main event polling loop for handling coordinate capture events.
        Called every 100ms to check for pending captures.
        """
        if self.pending_capture:
            key, value = self.pending_capture
            self.pending_capture = None
            
            # Update coordinates and UI
            self.coords[key] = value
            self.status_labels[key].configure(
                text=self._coord_text(value), 
                text_color=COLOR_SUCCESS
            )
            
            # Restore window from minimized state
            try:
                self.root.deiconify()
                # Restore exact previous geometry to avoid size jumps
                if self._last_geometry:
                    self.root.geometry(self._last_geometry)
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass
            
            # Update UI state
            self.info.configure(text="")
            self._update_start_state()
            
            # Only reposition during setup, not after start
            if not self._started:
                self._position_away_from_coords()
        
        # Schedule next tick
        self.root.after(100, self._tick)
    
    def _coord_text(self, val: Optional[Tuple[int, int]]) -> str:
        """Format coordinate tuple for display."""
        return f"{val[0]}, {val[1]}" if val else "Not set"
    
    def _start_capture(self, key: str) -> None:
        """
        Start coordinate capture for the specified target.
        
        Args:
            key: The target key ('input', 'submit', or 'accept')
        """
        self.capture_target = key
        self.info.configure(text=f"Capturing {LABELS[key]}… click target in Cursor.")
        
        # Minimize window to avoid interference during capture
        try:
            self._last_geometry = self.root.geometry()
            self.root.iconify()  # Minimize instead of hiding
        except Exception:
            pass
        
        # Small delay to ensure window is minimized
        time.sleep(0.12)
        
        # Start mouse listener for coordinate capture
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.start()
    
    def _on_click(self, x, y, button, pressed):
        """
        Handle mouse click events during coordinate capture.
        
        Args:
            x, y: Mouse coordinates
            button: Mouse button
            pressed: Whether button was pressed or released
            
        Returns:
            bool: True to continue listening, False to stop
        """
        if pressed and self.capture_target:
            key = self.capture_target
            self.capture_target = None
            self.pending_capture = (key, (int(x), int(y)))
            
            # Stop the mouse listener
            try:
                if self.listener:
                    self.listener.stop()
            except Exception:
                pass
            
            return False  # Stop listening
        return True  # Continue listening
    
    def _tick(self) -> None:
        """
        Main event polling loop for handling coordinate capture events.
        Called every 100ms to check for pending captures.
        """
        if self.pending_capture:
            key, value = self.pending_capture
            self.pending_capture = None
            
            # Update coordinates and UI
            self.coords[key] = value
            self.status_labels[key].configure(
                text=self._coord_text(value), 
                text_color=COLOR_SUCCESS
            )
            
            # Restore window from minimized state
            try:
                self.root.deiconify()
                # Restore exact previous geometry to avoid size jumps
                if self._last_geometry:
                    self.root.geometry(self._last_geometry)
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass
            
            # Update UI state
            self.info.configure(text="")
            self._update_start_state()
            
            # Only reposition during setup, not after start
            if not self._started:
                self._position_away_from_coords()
        
        # Schedule next tick
        self.root.after(100, self._tick)
    
    # =============================================================================
    # WINDOW MANAGEMENT
    # =============================================================================
    
    def _position_away_from_coords(self) -> None:
        """
        Position the window away from captured coordinates to avoid interference.
        Tries different screen corners until finding one that doesn't cover targets.
        """
        try:
            self.root.update_idletasks()
            
            # Use fixed window dimensions for consistency
            w, h = WINDOW_WIDTH, WINDOW_HEIGHT
            sw, sh = pyautogui.size()
            
            # Define screen corners to try
            corners = [
                (WINDOW_MARGIN, WINDOW_MARGIN),  # Top-left
                (sw - w - WINDOW_MARGIN, WINDOW_MARGIN),  # Top-right
                (WINDOW_MARGIN, sh - h - WINDOW_MARGIN),  # Bottom-left
                (sw - w - WINDOW_MARGIN, sh - h - WINDOW_MARGIN)  # Bottom-right
            ]
            
            def covers(x, y):
                """Check if window covers the given coordinates."""
                try:
                    rx = self.root.winfo_x()
                    ry = self.root.winfo_y()
                except Exception:
                    return False
                return rx <= x <= rx + w and ry <= y <= ry + h
            
            # Try each corner until finding one that doesn't cover targets
            for x, y in corners:
                self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
                covered = any(
                    key in self.coords and covers(*self.coords[key]) 
                    for key in ("input", "submit", "accept")
                )
                if not covered:
                    return  # Found a good position
                    
        except Exception:
            pass  # Graceful fallback if positioning fails
    
    def bring_to_front(self) -> None:
        """
        Bring the dialog to the front and focus it.
        Used during automation to ensure the UI is visible.
        """
        try:
            self.root.lift()
            self.root.focus_force()
            # Temporarily set topmost to ensure visibility
            self.root.attributes('-topmost', True)
            self.root.after(100, lambda: self.root.attributes('-topmost', False))
        except Exception:
            pass

    # =============================================================================
    # STATE MANAGEMENT
    # =============================================================================
    
    def _position_away_from_coords(self) -> None:
        """
        Position the window away from captured coordinates to avoid interference.
        Tries different screen corners until finding one that doesn't cover targets.
        """
        try:
            self.root.update_idletasks()
            
            # Use fixed window dimensions for consistency
            w, h = WINDOW_WIDTH, WINDOW_HEIGHT
            sw, sh = pyautogui.size()
            
            # Define screen corners to try
            corners = [
                (WINDOW_MARGIN, WINDOW_MARGIN),  # Top-left
                (sw - w - WINDOW_MARGIN, WINDOW_MARGIN),  # Top-right
                (WINDOW_MARGIN, sh - h - WINDOW_MARGIN),  # Bottom-left
                (sw - w - WINDOW_MARGIN, sh - h - WINDOW_MARGIN)  # Bottom-right
            ]
            
            def covers(x, y):
                """Check if window covers the given coordinates."""
                try:
                    rx = self.root.winfo_x()
                    ry = self.root.winfo_y()
                except Exception:
                    return False
                return rx <= x <= rx + w and ry <= y <= ry + h
            
            # Try each corner until finding one that doesn't cover targets
            for x, y in corners:
                self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
                covered = any(
                    key in self.coords and covers(*self.coords[key]) 
                    for key in ("input", "submit", "accept")
                )
                if not covered:
                    return  # Found a good position
                    
        except Exception:
            pass  # Graceful fallback if positioning fails
    
    def bring_to_front(self) -> None:
        """
        Bring the dialog to the front and focus it.
        Used during automation to ensure the UI is visible.
        """
        try:
            self.root.lift()
            self.root.focus_force()
            # Temporarily set topmost to ensure visibility
            self.root.attributes('-topmost', True)
            self.root.after(100, lambda: self.root.attributes('-topmost', False))
        except Exception:
            pass
    
    # =============================================================================
    # STATE MANAGEMENT
    # =============================================================================
    
    def _update_start_state(self) -> None:
        """Update the start button state based on configuration completeness."""
        ready = (
            all(k in self.coords for k in ("input", "submit", "accept")) and 
            self._timers_valid()
        )
        self.start_btn.configure(
            state="normal" if ready and not self._started else "disabled"
        )
    
    def _timers_valid(self) -> bool:
        """
        Validate that all timer values are valid numbers.
        
        Returns:
            bool: True if all timers are valid, False otherwise
        """
        try:
            int(float(self.var_start.get()))
            int(float(self.var_main.get()))
            float(self.var_cooldown.get())
            float(self.var_get_ready.get())
            return True
        except Exception:
            return False
    
    # =============================================================================
    # SESSION CONTROLS
    # =============================================================================
    
    def _on_start(self) -> None:
        """Handle start button click - begin automation session."""
        save_coords(self.coords)
        self._started = True
        
        # Enable control buttons
        for btn in (self.pause_btn, self.next_btn, self.retry_btn, self.cancel_btn):
            btn.configure(state="normal")
        
        # Disable start button
        self.start_btn.configure(state="disabled")
        
        # Don't reposition window after start to maintain consistent size
    
    def _toggle_pause(self) -> None:
        """Toggle pause/resume state during countdown."""
        self.paused = not self.paused
        self.pause_btn.configure(text="Resume" if self.paused else "Pause")
    
    def _on_skip(self) -> None:
        """Handle skip button - skip current cycle."""
        self.skipped = True
    
    def _on_retry(self) -> None:
        """Handle retry button - repeat previous cycle."""
        self.retried = True
    
    def _on_cancel(self) -> None:
        """Handle cancel button - stop automation entirely."""
        self.cancelled = True

    # =============================================================================
    # PUBLIC API METHODS
    # =============================================================================
    
    def _on_start(self) -> None:
        """Handle start button click - begin automation session."""
        save_coords(self.coords)
        self._started = True
        
        # Enable control buttons
        for btn in (self.pause_btn, self.next_btn, self.retry_btn, self.cancel_btn):
            btn.configure(state="normal")
        
        # Disable start button
        self.start_btn.configure(state="disabled")
        
        # Don't reposition window after start to maintain consistent size
    
    def _toggle_pause(self) -> None:
        """Toggle pause/resume state during countdown."""
        self.paused = not self.paused
        self.pause_btn.configure(text="Resume" if self.paused else "Pause")
    
    def _on_skip(self) -> None:
        """Handle skip button - skip current cycle."""
        self.skipped = True
    
    def _on_retry(self) -> None:
        """Handle retry button - repeat previous cycle."""
        self.retried = True
    
    def _on_cancel(self) -> None:
        """Handle cancel button - stop automation entirely."""
        self.cancelled = True
    
    # =============================================================================
    # PUBLIC API METHODS
    # =============================================================================
    
    def wait_for_start(self) -> None:
        """
        Wait for the user to click the start button.
        This method blocks until the session begins.
        """
        while not self._started:
            self.root.update()
            time.sleep(0.05)
    
    def get_coords(self) -> Coords:
        """
        Get the current coordinate configuration.
        
        Returns:
            Dict containing coordinate tuples for 'input', 'submit', 'accept'
        """
        return dict(self.coords)
    
    def get_timers(self) -> Tuple[int, int, float, float]:
        """
        Get the current timer configuration.
        
        Returns:
            Tuple of (start_delay, main_wait, cooldown, get_ready_delay)
        """
        start = int(float(self.var_start.get()))
        main = int(float(self.var_main.get()))
        cooldown = float(self.var_cooldown.get())
        get_ready = float(self.var_get_ready.get())
        return start, main, cooldown, get_ready
    
    def _set_textbox(self, box: ctk.CTkTextbox, text: str) -> None:
        """
        Safely update a text box with new content.
        
        Args:
            box: The text box widget to update
            text: The text content to display
        """
        try:
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("end", text)
            box.configure(state="disabled")
        except Exception:
            pass  # Graceful fallback if text update fails
    
    def countdown(self, seconds: int, text: Optional[str], next_text: Optional[str], last_text: Optional[str]) -> Dict[str, Any]:
        """
        Display a countdown timer with user controls.
        
        Args:
            seconds: Duration of countdown in seconds
            text: Text to display in current box
            next_text: Text to display in next box
            last_text: Previous text (for retry functionality)
            
        Returns:
            Dict containing control state: {'cancelled': bool, 'skipped': bool, 'retried': bool}
        """
        # Reset control state
        self.paused = False
        self.cancelled = False
        self.skipped = False
        self.retried = False
        
        # Initialize countdown
        total = max(0.0, float(seconds))
        remaining = float(total)
        
        # Update text boxes
        self._set_textbox(self.current_box, text or "")
        self._set_textbox(self.next_box, (f"Next: {next_text}" if next_text else ""))
        
        # Update time display and progress
        self.time_label.configure(text=str(int(round(remaining))))
        self.progress.set(1.0 if total > 0 else 0.0)
        self.pause_btn.configure(text="Pause")
        
        # Countdown loop
        prev = time.monotonic()
        tick = 0.1  # Update frequency
        
        while True:
            # Check for user control actions
            if self.cancelled or self.skipped or self.retried or remaining <= 0.0:
                break
            
            # Update timer
            now = time.monotonic()
            dt = now - prev
            prev = now
            
            if not self.paused:
                remaining = max(0.0, remaining - dt)
                self.time_label.configure(text=str(int(round(remaining))))
                
                # Update progress bar
                pct = (remaining / total) if total > 0 else 0.0
                self.progress.set(max(0.0, min(1.0, pct)))
            
            # Process UI events
            self.root.update()
            time.sleep(tick)
        
        return {
            "cancelled": self.cancelled, 
            "skipped": self.skipped, 
            "retried": self.retried
        }
    
    def close(self) -> None:
        """Safely close the UI window."""
        try:
            self.root.destroy()
        except Exception:
            pass
