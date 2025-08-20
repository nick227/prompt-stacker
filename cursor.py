"""Cursor automation launcher.

This script launches the refactored UI session manager with enhanced error handling
and performance monitoring.

The application uses a service-oriented architecture with modular components:
- UI Session Manager: Main GUI interface
- Coordinate Service: Mouse click detection and management
- Countdown Service: Timer logic and display
- Window Service: Window positioning and focus
- File Service: Prompt list management
- Event Service: Button events and keyboard navigation

"""

import os
import sys
import traceback
from pathlib import Path

from src.config import config
from src.error_handler import handle_error, log_info
from src.performance import (
    cleanup_memory,
    start_performance_monitoring,
    stop_performance_monitoring,
)


def validate_environment() -> dict:
    """Validate the runtime environment before starting."""
    issues = []
    warnings = []

    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8 or higher required")

    # Check required directories
    required_dirs = ["src", "prompt_lists", "data"]
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            issues.append(f"Required directory '{dir_name}' not found")

    # Check for write permissions
    try:
        test_file = Path("data/test_write.tmp")
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        warnings.append(f"Write permission issues: {e}")

    # Check for display (for GUI)
    try:
        import tkinter
        root = tkinter.Tk()
        root.destroy()
    except Exception as e:
        issues.append(f"GUI display not available: {e}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
    }





def main():
    """Main entry point with enhanced error handling and performance monitoring."""
    try:
        # Environment validation
        env_check = validate_environment()
        if not env_check["valid"]:
            print("❌ Environment validation failed:")
            for issue in env_check["issues"]:
                print(f"  - {issue}")
            return 1

        if env_check["warnings"]:
            print("⚠️  Environment warnings:")
            for warning in env_check["warnings"]:
                print(f"  - {warning}")

        # Validate configuration
        validation = config.validate_config()
        if not validation["valid"]:
            print("❌ Configuration validation failed:")
            for error in validation["errors"]:
                print(f"  - {error}")
            return 1

        # Start performance monitoring
        start_performance_monitoring()
        log_info("Application started with performance monitoring")

        # UI initialization with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                from src.ui import SessionUI
                ui = SessionUI(default_start=5)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                log_info(f"UI initialization attempt {attempt + 1} failed: {e}")
                import time
                time.sleep(1)  # Brief delay before retry

        # Wait for UI to be ready
        ui.wait_for_start()

        return 0

    except KeyboardInterrupt:
        log_info("Application interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Critical error during startup: {e}")
        print("Full traceback:")
        traceback.print_exc()
        handle_error(e, context="Main application", show_ui=True)
        return 1
    finally:
        # Cleanup
        stop_performance_monitoring()
        cleanup_memory()
        log_info("Application shutdown complete")

if __name__ == "__main__":
    sys.exit(main())
