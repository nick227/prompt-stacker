import sys
import ctypes
import time
import pyautogui

# Enable DPI awareness so recorded coordinates match actual screen pixels

def _enable_windows_dpi_awareness() -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

_enable_windows_dpi_awareness()

# Utility: get full virtual desktop rectangle (includes negative coords)

def get_virtual_screen_rect():
    if sys.platform.startswith("win"):
        user32 = ctypes.windll.user32
        x = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        y = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        w = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        h = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        return (x, y, w, h)
    w, h = pyautogui.size()
    return (0, 0, w, h)

print("Hover over target in 5s...")
print(f"Virtual screen (x, y, w, h): {get_virtual_screen_rect()}")

time.sleep(5)
pos = pyautogui.position()
print("Position:", pos)