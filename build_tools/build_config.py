"""
Build Configuration

Centralized configuration for building the automation application.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Build output directories
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
SPEC_DIR = PROJECT_ROOT / "build_tools" / "specs"

# Application information
APP_NAME = "Prompt Stacker"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "A powerful automation system for Cursor with beautiful Monokai-themed UI"
APP_AUTHOR = "Automation System"

# Main entry point
MAIN_SCRIPT = PROJECT_ROOT / "cursor.py"

# Icon file (if available)
ICON_FILE = PROJECT_ROOT / "assets" / "icon.ico"

# Hidden imports (PyInstaller might miss these)
hiddenimports = [
    "src.automator",
    "src.ui.session_app",
    "src.ui.session_controller",
    "src.ui.prompt_io",
    "src.ui.state_manager",
    "src.inline_prompt_editor_service",
]

# Data files to include
DATA_FILES = [
    # Include prompt_lists directory for default prompts
    (PROJECT_ROOT / "prompt_lists", "prompt_lists"),
]

# Exclude patterns
EXCLUDE_PATTERNS = [
    "*.pyc",
    "__pycache__",
    "*.pyo", 
    "*.pyd",
    ".git",
    ".gitignore",
    ".pytest_cache",
    "tests",
    "docs",
    "build",
    "dist",
    "*.spec",
    "*.log",
    ".venv",
    "venv",
    "env",
    ".env",
]

# PyInstaller options
PYINSTALLER_OPTIONS = {
    "onefile": True,  # Single executable
    "windowed": True,  # No console window for GUI apps
    "clean": True,  # Clean cache before building
    "noconfirm": True,  # Overwrite output directory
    "strip": True,  # Strip debug symbols (smaller file)
    "optimize": 2,  # Python optimization level
}

# Development build options (faster, larger)
DEV_OPTIONS = {
    "onefile": False,  # Directory mode for faster builds
    "windowed": True,
    "clean": False,  # Keep cache for faster rebuilds
    "noconfirm": True,
    "strip": False,  # Keep debug info
    "optimize": 0,  # No optimization
}

def get_build_config(dev_mode: bool = False) -> Dict[str, Any]:
    """
    Get build configuration based on mode.
    
    Args:
        dev_mode: Whether to use development build options
        
    Returns:
        Build configuration dictionary
    """
    options = DEV_OPTIONS if dev_mode else PYINSTALLER_OPTIONS
    
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "app_description": APP_DESCRIPTION,
        "app_author": APP_AUTHOR,
        "main_script": str(MAIN_SCRIPT),
        "icon_file": str(ICON_FILE) if ICON_FILE.exists() else None,
        "hidden_imports": hiddenimports,
        "data_files": DATA_FILES,
        "exclude_patterns": EXCLUDE_PATTERNS,
        "pyinstaller_options": options,
        "build_dir": str(BUILD_DIR),
        "dist_dir": str(DIST_DIR),
        "spec_dir": str(SPEC_DIR),
        "project_root": str(PROJECT_ROOT),
    }

def validate_build_environment() -> Dict[str, Any]:
    """
    Validate the build environment and dependencies.
    
    Returns:
        Validation result dictionary
    """
    errors = []
    warnings = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        errors.append("Python 3.8+ required")
    
    # Check required files
    if not MAIN_SCRIPT.exists():
        errors.append(f"Main script not found: {MAIN_SCRIPT}")
    
    # Check build directories
    for directory in [BUILD_DIR, DIST_DIR, SPEC_DIR]:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            warnings.append(f"Created directory: {directory}")
    
    # Check PyInstaller
    try:
        import PyInstaller
        warnings.append(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        errors.append("PyInstaller not installed. Run: pip install pyinstaller")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
