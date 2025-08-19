import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

# Use user's home directory for settings
SETTINGS_FILE = Path.home() / "prompt_stacker_logs" / "coords.json"

Coords = Dict[str, Tuple[int, int]]


def load_coords() -> Optional[Coords]:
    try:
        if not os.path.exists(SETTINGS_FILE):
            return None
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        # Basic validation
        if not all(k in data for k in ("input", "submit", "accept")):
            return None
        return {
            "input": tuple(data["input"]),
            "submit": tuple(data["submit"]),
            "accept": tuple(data["accept"]),
        }
    except Exception:
        return None


def save_coords(coords: Coords) -> None:
    try:
        # Ensure the directory exists
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(coords, f)
    except Exception:
        pass
