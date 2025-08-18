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

import sys
from src.error_handler import handle_error, log_info
from src.performance import start_performance_monitoring, stop_performance_monitoring, cleanup_memory
from src.config import config



def main():
    """Main entry point with enhanced error handling and performance monitoring."""
    try:
        # Validate configuration
        validation = config.validate_config()
        if not validation["valid"]:
            print("Configuration validation failed:")
            for error in validation["errors"]:
                print(f"  - {error}")
            return 1
        
        # Start performance monitoring
        start_performance_monitoring()
        log_info("Application started with performance monitoring")
        
        # Launch the UI session manager
        from src.ui_session_refactored import RefactoredSessionUI
        
        ui = RefactoredSessionUI(default_start=5, default_main=500, default_cooldown=0.2)
        ui.wait_for_start()
        
        return 0
        
    except KeyboardInterrupt:
        log_info("Application interrupted by user")
        return 0
    except Exception as e:
        handle_error(e, context="Main application", show_ui=True)
        return 1
    finally:
        # Cleanup
        stop_performance_monitoring()
        cleanup_memory()
        log_info("Application shutdown complete")

if __name__ == "__main__":
    sys.exit(main())
