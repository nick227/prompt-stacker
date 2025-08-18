"""
Coordinate Capture Service

This module provides coordinate capture functionality for the Cursor automation system.
Handles mouse click detection, coordinate storage, and coordinate management.

Author: Automation System
Version: 1.0
"""

from typing import Callable, Dict, List, Optional, Tuple

from pynput import mouse

# Handle imports for both testing and normal usage
try:
    from .config import CAPTURE_DELAY
    from .settings_store import load_coords, save_coords
except ImportError:
    # Fallback for testing
    try:
        from config import CAPTURE_DELAY
        from settings_store import load_coords, save_coords
    except ImportError:
        # Mock values for testing
        def load_coords():
            return {}

        def save_coords(coords):
            pass

        CAPTURE_DELAY = 0.12

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

Coords = Dict[str, Tuple[int, int]]

# =============================================================================
# CONSTANTS
# =============================================================================

# Import constants from centralized config
try:
    from .config import LABELS, TARGET_KEYS
except ImportError:
    # Fallback for testing
    try:
        from config import LABELS, TARGET_KEYS
    except ImportError:
        # Mock values for testing
        TARGET_KEYS = ["input", "submit", "accept"]
        LABELS = {
            "input": "Input",
            "submit": "Submit",
            "accept": "Accept",
        }

# =============================================================================
# COORDINATE CAPTURE SERVICE
# =============================================================================


class CoordinateCaptureService:
    """
    Service for capturing and managing screen coordinates.

    Handles mouse click detection, coordinate storage, and coordinate management
    for automation targets (input, submit, accept).
    """

    def __init__(self):
        """Initialize the coordinate capture service."""
        self.coords: Coords = {}
        self.capture_active = False
        self.capture_key: Optional[str] = None
        self.listener: Optional[mouse.Listener] = None
        self.on_coord_captured: Optional[Callable[[str, Tuple[int, int]], None]] = None

        # Load existing coordinates
        self._load_coordinates()

        # Ensure any existing listeners are cleaned up
        self.stop_capture()

    def _load_coordinates(self) -> None:
        """Load coordinates from persistent storage."""
        try:
            coords = load_coords()
            self.coords = coords if coords is not None else {}
        except Exception as e:
            print(f"Failed to load coordinates: {e}")
            self.coords = {}

    def save_coordinates(self) -> None:
        """Save coordinates to persistent storage."""
        try:
            save_coords(self.coords)
        except Exception as e:
            print(f"Failed to save coordinates: {e}")

    def get_coordinates(self) -> Coords:
        """
        Get current coordinates.

        Returns:
            Dictionary of target coordinates
        """
        return self.coords.copy()

    def set_coordinate(self, key: str, coord: Tuple[int, int]) -> None:
        """
        Set a coordinate for a specific target.

        Args:
            key: Target key (input, submit, accept)
            coord: Coordinate tuple (x, y)
        """
        self.coords[key] = coord
        self.save_coordinates()

    def has_coordinate(self, key: str) -> bool:
        """
        Check if a coordinate exists for the given key.

        Args:
            key: Target key to check

        Returns:
            True if coordinate exists
        """
        return key in self.coords

    def get_coordinate(self, key: str) -> Optional[Tuple[int, int]]:
        """
        Get coordinate for a specific target.

        Args:
            key: Target key

        Returns:
            Coordinate tuple or None if not found
        """
        return self.coords.get(key)

    def get_coordinate_text(self, key: str) -> str:
        """
        Get formatted text representation of coordinate.

        Args:
            key: Target key

        Returns:
            Formatted coordinate string or "Not set"
        """
        coord = self.coords.get(key)
        if coord:
            return f"{coord[0]}, {coord[1]}"
        return "Not set"

    def clear_coordinate(self, key: str) -> None:
        """
        Clear a specific coordinate.

        Args:
            key: Target key to clear
        """
        if key in self.coords:
            del self.coords[key]
            self.save_coordinates()

    def remove_coordinate(self, key: str) -> bool:
        """
        Remove a coordinate and return success status.

        Args:
            key: Target key to remove

        Returns:
            True if coordinate was removed
        """
        if key in self.coords:
            del self.coords[key]
            self.save_coordinates()
            return True
        return False

    def start_capture(self, key: str) -> bool:
        """
        Start capturing coordinates for a specific target.

        Args:
            key: Target key to capture for

        Returns:
            True if capture started successfully
        """
        if self.capture_active:
            return False

        if key not in TARGET_KEYS:
            return False

        try:
            self.capture_key = key
            self.capture_active = True

            # Start mouse listener
            self.listener = mouse.Listener(on_click=self._on_click)
            self.listener.start()

            return True

        except Exception as e:
            print(f"Failed to start capture: {e}")
            self.capture_active = False
            self.capture_key = None
            return False

    def stop_capture(self) -> None:
        """Stop coordinate capture."""
        self.capture_active = False
        self.capture_key = None

        if self.listener:
            try:
                self.listener.stop()
            except Exception as e:
                print(f"Error stopping mouse listener: {e}")
            finally:
                self.listener = None

    def is_capturing(self) -> bool:
        """
        Check if coordinate capture is active.

        Returns:
            True if capture is active
        """
        return self.capture_active

    def get_capture_key(self) -> Optional[str]:
        """
        Get the current capture key.

        Returns:
            Current capture key or None
        """
        return self.capture_key

    def set_callback(self, callback: Callable[[str, Tuple[int, int]], None]) -> None:
        """
        Set callback for when coordinates are captured.

        Args:
            callback: Function to call with captured coordinates
        """
        self.on_coord_captured = callback

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """
        Handle mouse click events.

        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button
            pressed: Whether button was pressed
        """
        if not self.capture_active or not pressed:
            return

        if button != mouse.Button.left:
            return

        try:
            # Store key and callback BEFORE stop_capture() clears them
            captured_key = self.capture_key
            captured_callback = self.on_coord_captured

            # Stop capture
            self.stop_capture()

            if captured_key:
                coord = (x, y)
                self.set_coordinate(captured_key, coord)

                # Call callback if provided
                if captured_callback:
                    try:
                        captured_callback(captured_key, coord)
                    except Exception as e:
                        print(f"Error in coordinate callback: {e}")

                print(f"Captured coordinate for {captured_key}: {coord}")

        except Exception as e:
            print(f"Error handling click: {e}")
            self.stop_capture()

    def get_target_keys(self) -> List[str]:
        """
        Get list of available target keys.

        Returns:
            List of target keys
        """
        return list(TARGET_KEYS)

    def get_target_label(self, key: str) -> str:
        """
        Get display label for a target key.

        Args:
            key: Target key

        Returns:
            Display label
        """
        return LABELS.get(key, key.title())

    def validate_coordinates(self) -> Dict[str, bool]:
        """
        Validate all coordinates.

        Returns:
            Dictionary mapping target keys to validation status
        """
        validation = {}
        for key in TARGET_KEYS:
            validation[key] = self.validate_coordinate(key)
        return validation

    def validate_coordinate(self, key: str) -> bool:
        """
        Validate a specific coordinate.

        Args:
            key: Target key to validate

        Returns:
            True if coordinate is valid
        """
        if key not in TARGET_KEYS:
            return False

        coord = self.get_coordinate(key)
        if not coord:
            return False

        # Basic validation - coordinates should be positive
        try:
            x, y = coord
            return x >= 0 and y >= 0
        except (ValueError, TypeError):
            # Handle invalid coordinate format (wrong length, not a tuple, etc.)
            return False

    def get_missing_coordinates(self) -> List[str]:
        """
        Get list of missing coordinates.

        Returns:
            List of target keys that don't have valid coordinates
        """
        missing = []
        for key in TARGET_KEYS:
            if not self.validate_coordinate(key):
                missing.append(key)
        return missing
