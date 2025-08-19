#!/usr/bin/env python3
"""
Test Runner for Cursor Automation System

This script runs the complete test suite with proper configuration and reporting.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for Cursor Automation System")
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests",
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests",
    )
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Include slow tests",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Include UI tests",
    )
    parser.add_argument(
        "--automation",
        action="store_true",
        help="Include automation tests",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--test-file",
        type=str,
        help="Run specific test file",
    )
    parser.add_argument(
        "--test-function",
        type=str,
        help="Run specific test function",
    )

    args = parser.parse_args()

    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test selection
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    else:
        # Default: run all tests except slow ones
        cmd.extend(["-m", "not slow"])

    # Add specific test filters
    if args.slow:
        cmd.extend(["-m", "slow"])
    if args.ui:
        cmd.extend(["-m", "ui"])
    if args.automation:
        cmd.extend(["-m", "automation"])

    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
        ])

    # Add verbose output
    if args.verbose:
        cmd.append("-v")

    # Add specific test file or function
    if args.test_file:
        cmd.append(f"tests/{args.test_file}")
    elif args.test_function:
        cmd.extend(["-k", args.test_function])
    else:
        cmd.append("tests/")

    # Add pytest options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
    ])

    print(f"Running tests with command: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
