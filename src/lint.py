#!/usr/bin/env python3
"""
Linting script for the Cursor Automation System.
Runs Ruff to check code quality and formatting.
"""

import subprocess
import sys
from pathlib import Path


def run_ruff_check():
    """Run Ruff check on the src directory."""
    print("🔍 Running Ruff linting check...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            ["ruff", "check", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ No linting issues found!")
            return True
        else:
            print("⚠️  Linting issues found:")
            print(result.stdout)
            return False
            
    except FileNotFoundError:
        print("❌ Ruff not found. Please install it with: pip install ruff")
        return False
    except Exception as e:
        print(f"❌ Error running Ruff: {e}")
        return False


def run_ruff_format():
    """Run Ruff format on the src directory."""
    print("\n🎨 Running Ruff formatting...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            ["ruff", "format", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ Code formatting completed!")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("❌ Formatting issues found:")
            print(result.stdout)
            return False
            
    except FileNotFoundError:
        print("❌ Ruff not found. Please install it with: pip install ruff")
        return False
    except Exception as e:
        print(f"❌ Error running Ruff format: {e}")
        return False


def main():
    """Main function to run linting and formatting."""
    print("🚀 Cursor Automation System - Code Quality Check")
    print("=" * 50)
    
    # Run formatting first
    format_success = run_ruff_format()
    
    # Run linting
    lint_success = run_ruff_check()
    
    # Summary
    print("\n📊 Summary:")
    print("=" * 50)
    if format_success and lint_success:
        print("✅ All checks passed! Code is clean and well-formatted.")
        sys.exit(0)
    else:
        print("⚠️  Some issues found. Please review and fix the above issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
