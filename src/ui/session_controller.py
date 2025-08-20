"""
Session Controller - Automation Lifecycle Management

This file now serves as a compatibility layer that imports the new centralized
automation controller. The old SessionController has been replaced with the
new AutomationController for better reliability and maintainability.

Author: Automation System
Version: 3.0 - Centralized Architecture
"""

# Import the new centralized automation controller
try:
    from ..automation_integration import SessionController
except ImportError:
    # Fallback for standalone execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from automation_integration import SessionController

# Re-export for backward compatibility
__all__ = ["SessionController"]
