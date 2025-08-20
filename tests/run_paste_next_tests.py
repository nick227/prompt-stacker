#!/usr/bin/env python3
"""
Dedicated test runner for Paste Operations and Next Button tests.

This script runs the specific tests for:
1. perform_paste_operation() functionality
2. Next button behavior
3. Cancel button behavior
4. Integration tests

Usage:
    python tests/run_paste_next_tests.py
"""

import subprocess
import sys
from pathlib import Path


def run_paste_next_tests():
    """Run the dedicated paste and next button tests."""

    # Get the tests directory
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent

    # Add project root to Python path
    sys.path.insert(0, str(project_root))

    print("🧪 Running Paste Operations and Next Button Tests")
    print("=" * 60)

    # Test file to run
    test_file = tests_dir / "test_paste_and_next_operations.py"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    # Run the tests with pytest
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
        "--durations=10",  # Show top 10 slowest tests
        "-x",  # Stop on first failure
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test_classes():
    """Run specific test classes for focused testing."""

    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    test_file = tests_dir / "test_paste_and_next_operations.py"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    # Test classes to run
    test_classes = [
        "TestPasteOperations",
        "TestNextButtonFunctionality",
        "TestCancelButtonFunctionality",
        "TestPasteIntegration",
        "TestNextButtonIntegration",
    ]

    print("🧪 Running Specific Test Classes")
    print("=" * 60)

    all_passed = True

    for test_class in test_classes:
        print(f"\n📋 Running {test_class}...")

        cmd = [
            sys.executable, "-m", "pytest",
            f"{test_file}::{test_class}",
            "-v",
            "--tb=short",
            "--color=yes",
            "-x",
        ]

        try:
            result = subprocess.run(cmd, cwd=project_root, check=False)
            if result.returncode == 0:
                print(f"✅ {test_class} - PASSED")
            else:
                print(f"❌ {test_class} - FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_class} - ERROR: {e}")
            all_passed = False

    return all_passed

def run_quick_smoke_tests():
    """Run a quick smoke test of the most critical functionality."""

    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    test_file = tests_dir / "test_paste_and_next_operations.py"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    print("🚀 Running Quick Smoke Tests")
    print("=" * 60)

    # Quick smoke tests - most critical functionality
    smoke_tests = [
        "TestPasteOperations::test_perform_paste_operation_success",
        "TestNextButtonFunctionality::test_next_prompt_advances_index",
        "TestCancelButtonFunctionality::test_cancel_automation_stops_controller",
    ]

    all_passed = True

    for test_name in smoke_tests:
        print(f"\n🔍 Running {test_name}...")

        cmd = [
            sys.executable, "-m", "pytest",
            f"{test_file}::{test_name}",
            "-v",
            "--tb=short",
            "--color=yes",
            "-x",
        ]

        try:
            result = subprocess.run(cmd, cwd=project_root, check=False)
            if result.returncode == 0:
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
            all_passed = False

    return all_passed

def main():
    """Main function to run tests based on command line arguments."""

    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()

        if test_type == "smoke":
            success = run_quick_smoke_tests()
        elif test_type == "classes":
            success = run_specific_test_classes()
        elif test_type == "all":
            success = run_paste_next_tests()
        else:
            print("Usage: python run_paste_next_tests.py [smoke|classes|all]")
            print("  smoke   - Run quick smoke tests")
            print("  classes - Run specific test classes")
            print("  all     - Run all paste/next tests (default)")
            return False
    else:
        # Default: run all tests
        success = run_paste_next_tests()

    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests PASSED!")
        return True
    print("💥 Some tests FAILED!")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
