#!/usr/bin/env python3
"""
Build Script

Simple script to build the automation application.
Usage: python build.py [command] [options]
"""

import sys
import os
from pathlib import Path

# Add build_tools to path
sys.path.insert(0, str(Path(__file__).parent / "build_tools"))

from build_manager import BuildManager


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("🚀 Prompt Stacker Build System")
        print()
        print("Usage: python build.py <command> [options]")
        print()
        print("Commands:")
        print("  build              Build production executable")
        print("  build-dev          Build development executable (faster)")
        print("  clean              Clean all build artifacts")
        print("  install-deps       Install build dependencies")
        print("  validate           Validate build environment")
        print("  info               Show build information")
        print("  package            Package for distribution")
        print("  test               Run tests")
        print("  build-with-tests   Run tests then build")
        print()
        print("Options:")
        print("  --no-clean         Don't clean build directories")
        print("  --installer        Include installer in package")
        print()
        print("Examples:")
        print("  python build.py build")
        print("  python build.py build-dev --no-clean")
        print("  python build.py build-with-tests")
        print("  python build.py package --installer")
        return 1
    
    # Extract command and arguments
    command = sys.argv[1]
    args = sys.argv[2:]
    
    # Parse arguments
    no_clean = "--no-clean" in args
    installer = "--installer" in args
    
    # Remove parsed arguments
    args = [arg for arg in args if arg not in ["--no-clean", "--installer"]]
    
    manager = BuildManager()
    
    try:
        if command == "build":
            success = manager.build_production(clean=not no_clean)
        elif command == "build-dev":
            success = manager.build_development(clean=not no_clean)
        elif command == "clean":
            manager.clean_all()
            success = True
        elif command == "install-deps":
            success = manager.install_dependencies()
        elif command == "validate":
            success = manager.validate_environment()
        elif command == "info":
            info = manager.get_build_info()
            print("📋 Build Information:")
            for key, value in info.items():
                print(f"   {key}: {value}")
            success = True
        elif command == "package":
            success = manager.package_for_distribution(include_installer=installer)
        elif command == "test":
            success = manager.run_tests()
        elif command == "build-with-tests":
            success = manager.build_with_tests(clean=not no_clean)
        else:
            print(f"❌ Unknown command: {command}")
            print("Run 'python build.py' for help")
            success = False
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Build interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
