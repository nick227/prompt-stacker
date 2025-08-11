import json
import os
from typing import Dict, Tuple, Optional

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'coords.json')

Coords = Dict[str, Tuple[int, int]]


def load_coords() -> Optional[Coords]:
    try:
        if not os.path.exists(SETTINGS_FILE):
            return None
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Basic validation
        if not all(k in data for k in ('input', 'submit', 'accept')):
            return None
        return {
            'input': tuple(data['input']),
            'submit': tuple(data['submit']),
            'accept': tuple(data['accept']),
        }  # type: ignore
    except Exception:
        return None


def save_coords(coords: Coords) -> None:
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(coords, f)
    except Exception:
        pass
