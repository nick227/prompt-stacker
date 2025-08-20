"""
Window Management Service

This module provides window management functionality for the Cursor automation system.
Handles window positioning, focus, DPI awareness, and window state management.

Author: Automation System
Version: 1.0
"""

import ctypes
from typing import Optional, Tuple

import customtkinter as ctk

try:
    from .config import WINDOW_HEIGHT, WINDOW_MARGIN, WINDOW_WIDTH
except ImportError:
    # Fallback for when running as script
    from config import WINDOW_HEIGHT, WINDOW_MARGIN, WINDOW_WIDTH

# =============================================================================
# DPI AWARENESS CONSTANTS
# =============================================================================

# Windows DPI awareness constants
PROCESS_PER_MONITOR_DPI_AWARE = 2
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_DPI_UNAWARE = 0

# =============================================================================
# WINDOW MANAGEMENT SERVICE
# =============================================================================


class WindowService:
    """
    Service for managing window positioning, focus, and DPI awareness.

    Handles window positioning, focus management, DPI scaling, and window state
    for the automation UI.
    """

    def __init__(self, window: ctk.CTk):
        """
        Initialize the window service.

        Args:
            window: The main window to manage
        """
        self.window = window
        self.original_position: Optional[Tuple[int, int]] = None
        self.is_topmost = False

        # Enable DPI awareness
        self._enable_dpi_awareness()

        # Configure window properties
        self._configure_window()

    def _enable_dpi_awareness(self) -> None:
        """Enable Windows DPI awareness for consistent scaling."""
        try:
            # Try to set per-monitor DPI awareness (Windows 8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
        except (AttributeError, OSError):
            try:
                # Fallback to system DPI awareness (Windows 8+)
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                # Fallback for older Windows versions
                pass

        print("DPI awareness enabled")

    def _configure_window(self) -> None:
        """Configure window properties and appearance."""
        # Set window size and position
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.window.resizable(False, False)

        # Center window on screen
        self.center_window()

        # Set window title
        self.window.title("Cursor Automation System")

        # Configure window icon (if available)
        try:
            self.window.iconbitmap("icon.ico")
        except Exception:
            pass  # Icon not available

    def center_window(self) -> None:
        """Center the window on the screen."""
        try:
            # Get screen dimensions
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()

            # Calculate center position
            x = (screen_width - WINDOW_WIDTH) // 2
            y = (screen_height - WINDOW_HEIGHT) // 2

            # Position window
            self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        except Exception as e:
            print(f"Failed to center window: {e}")

    def bring_to_front(self) -> None:
        """Bring window to front and focus."""
        try:
            # Lift window to top
            self.window.lift()

            # Focus window
            self.window.focus_force()

            # Ensure window is visible
            self.window.deiconify()

            print("Window brought to front")

        except Exception as e:
            print(f"Failed to bring window to front: {e}")

    def set_topmost(self, topmost: bool = True) -> None:
        """
        Set window topmost state.

        Args:
            topmost: Whether window should be topmost
        """
        try:
            self.window.attributes("-topmost", topmost)
            self.is_topmost = topmost

            if topmost:
                print("Window set to topmost")
            else:
                print("Window topmost state removed")

        except Exception as e:
            print(f"Failed to set topmost state: {e}")

    def minimize(self) -> None:
        """Minimize the window."""
        try:
            # Store current position
            self.original_position = self.window.geometry()

            # Minimize window
            self.window.iconify()

            print("Window minimized")

        except Exception as e:
            print(f"Failed to minimize window: {e}")

    def restore(self) -> None:
        """Restore the window from minimized state."""
        try:
            # Restore window
            self.window.deiconify()

            # Restore original position if available
            if self.original_position:
                self.window.geometry(self.original_position)
                self.original_position = None

            # Bring to front
            self.bring_to_front()

            print("Window restored")

        except Exception as e:
            print(f"Failed to restore window: {e}")

    def position_away_from_coords(self, coords: dict) -> None:
        """
        Position window away from specified coordinates.

        Args:
            coords: Dictionary of coordinates to avoid
        """
        try:
            # Get screen dimensions
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()

            # Find a safe position away from coordinates
            safe_x, safe_y = self._find_safe_position(
                coords,
                screen_width,
                screen_height,
            )

            # Move window to safe position
            self.window.geometry(f"+{safe_x}+{safe_y}")

            print(f"Window positioned at safe location ({safe_x}, {safe_y})")

        except Exception as e:
            print(f"Failed to position window: {e}")

    def _find_safe_position(
        self,
        coords: dict,
        screen_width: int,
        screen_height: int,
    ) -> Tuple[int, int]:
        """
        Find a safe position away from the specified coordinates.

        Args:
            coords: Dictionary of coordinates to avoid
            screen_width: Screen width
            screen_height: Screen height

        Returns:
            Tuple of (x, y) coordinates for safe position
        """
        # Define safe zones (corners and edges)
        safe_zones = [
            (WINDOW_MARGIN, WINDOW_MARGIN),  # Top-left
            (screen_width - WINDOW_WIDTH - WINDOW_MARGIN, WINDOW_MARGIN),  # Top-right
            (
                WINDOW_MARGIN,
                screen_height - WINDOW_HEIGHT - WINDOW_MARGIN,
            ),  # Bottom-left
            (
                screen_width - WINDOW_WIDTH - WINDOW_MARGIN,
                screen_height - WINDOW_HEIGHT - WINDOW_MARGIN,
            ),  # Bottom-right
        ]

        # Check each safe zone
        for x, y in safe_zones:
            if self._is_position_safe(x, y, coords):
                return x, y

        # If no safe zone found, use center
        return (screen_width - WINDOW_WIDTH) // 2, (screen_height - WINDOW_HEIGHT) // 2

    def _is_position_safe(self, x: int, y: int, coords: dict) -> bool:
        """
        Check if a position is safe (away from coordinates).

        Args:
            x: X coordinate to check
            y: Y coordinate to check
            coords: Dictionary of coordinates to avoid

        Returns:
            True if position is safe, False otherwise
        """

        # Define what constitutes "covering" a coordinate
        def covers(coord_x: int, coord_y: int) -> bool:
            return (
                x <= coord_x <= x + WINDOW_WIDTH and y <= coord_y <= y + WINDOW_HEIGHT
            )

        # Check if window would cover any coordinate
        for coord in coords.values():
            if coord and covers(coord[0], coord[1]):
                return False

        return True

    def get_window_position(self) -> Tuple[int, int]:
        """
        Get current window position.

        Returns:
            Tuple of (x, y) coordinates
        """
        try:
            geometry = self.window.geometry()
            # Parse geometry string "WxH+X+Y"
            parts = geometry.split("+")
            if len(parts) >= 3:
                return int(parts[1]), int(parts[2])
        except Exception as e:
            print(f"Failed to get window position: {e}")

        return (0, 0)

    def get_window_size(self) -> Tuple[int, int]:
        """
        Get current window size.

        Returns:
            Tuple of (width, height)
        """
        try:
            geometry = self.window.geometry()
            # Parse geometry string "WxH+X+Y"
            size_part = geometry.split("+")[0]
            width, height = size_part.split("x")
            return int(width), int(height)
        except Exception as e:
            print(f"Failed to get window size: {e}")

        return (WINDOW_WIDTH, WINDOW_HEIGHT)

    def is_visible(self) -> bool:
        """
        Check if window is currently visible.

        Returns:
            True if window is visible, False otherwise
        """
        try:
            return self.window.state() != "iconic"
        except Exception:
            return True

    def close(self) -> None:
        """Close the window."""
        try:
            self.window.quit()
            self.window.destroy()
            print("Window closed")
        except Exception as e:
            print(f"Failed to close window: {e}")
