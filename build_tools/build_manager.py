"""
Build Manager

Unified interface for managing different build operations.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from .pyinstaller_builder import PyInstallerBuilder
    from .build_config import get_build_config, validate_build_environment
except ImportError:
    # Fallback for when running as script
    from pyinstaller_builder import PyInstallerBuilder
    from build_config import get_build_config, validate_build_environment


class BuildManager:
    """Manages different build operations and workflows."""
    
    def __init__(self):
        """Initialize the build manager."""
        self.config = get_build_config()
        
    def build_production(self, clean: bool = True) -> bool:
        """
        Build production executable.
        
        Args:
            clean: Whether to clean build directories first
            
        Returns:
            True if build was successful
        """
        print("🏭 Building production executable...")
        builder = PyInstallerBuilder(dev_mode=False)
        return builder.build(clean=clean)
    
    def build_development(self, clean: bool = False) -> bool:
        """
        Build development executable (faster, larger).
        
        Args:
            clean: Whether to clean build directories first
            
        Returns:
            True if build was successful
        """
        print("🔧 Building development executable...")
        builder = PyInstallerBuilder(dev_mode=True)
        return builder.build(clean=clean)
    
    def clean_all(self) -> None:
        """Clean all build artifacts."""
        print("🧹 Cleaning all build artifacts...")
        
        # Clean build directories
        for directory in [self.config["build_dir"], self.config["dist_dir"]]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                print(f"   Cleaned: {directory}")
        
        # Clean spec files
        spec_dir = Path(self.config["spec_dir"])
        if spec_dir.exists():
            for spec_file in spec_dir.glob("*.spec"):
                spec_file.unlink()
                print(f"   Cleaned: {spec_file}")
        
        # Clean PyInstaller cache
        cache_dir = Path.home() / ".pyinstaller"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            print(f"   Cleaned PyInstaller cache: {cache_dir}")
        
        # Clean Python cache
        for root, dirs, files in os.walk(self.config["project_root"]):
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    cache_path = Path(root) / dir_name
                    shutil.rmtree(cache_path)
                    print(f"   Cleaned: {cache_path}")
        
        print("✅ All build artifacts cleaned")
    
    def install_dependencies(self) -> bool:
        """
        Install build dependencies.
        
        Returns:
            True if installation was successful
        """
        print("📦 Installing build dependencies...")
        
        dependencies = [
            "pyinstaller",
            "setuptools",
            "wheel",
        ]
        
        for dep in dependencies:
            print(f"   Installing {dep}...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], check=True, capture_output=True)
                print(f"   ✅ {dep} installed")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install {dep}: {e}")
                return False
        
        print("✅ All build dependencies installed")
        return True
    
    def validate_environment(self) -> bool:
        """
        Validate the build environment.
        
        Returns:
            True if environment is valid
        """
        return PyInstallerBuilder().validate_environment()
    
    def get_build_info(self) -> Dict[str, Any]:
        """
        Get information about the current build environment.
        
        Returns:
            Build information dictionary
        """
        info = {
            "app_name": self.config["app_name"],
            "app_version": self.config["app_version"],
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "build_dir": self.config["build_dir"],
            "dist_dir": self.config["dist_dir"],
            "main_script": self.config["main_script"],
            "timestamp": datetime.now().isoformat(),
        }
        
        # Check if PyInstaller is available
        try:
            import PyInstaller
            info["pyinstaller_version"] = PyInstaller.__version__
        except ImportError:
            info["pyinstaller_version"] = "Not installed"
        
        # Check build directories
        info["build_dir_exists"] = os.path.exists(self.config["build_dir"])
        info["dist_dir_exists"] = os.path.exists(self.config["dist_dir"])
        
        return info
    
    def create_installer(self, installer_type: str = "nsis") -> bool:
        """
        Create an installer for the built application.
        
        Args:
            installer_type: Type of installer to create ("nsis", "inno", etc.)
            
        Returns:
            True if installer creation was successful
        """
        print(f"📦 Creating {installer_type.upper()} installer...")
        
        if installer_type.lower() == "nsis":
            return self._create_nsis_installer()
        elif installer_type.lower() == "inno":
            return self._create_inno_installer()
        else:
            print(f"❌ Unsupported installer type: {installer_type}")
            return False
    
    def _create_nsis_installer(self) -> bool:
        """Create NSIS installer."""
        # This would require NSIS to be installed
        print("⚠️  NSIS installer creation not implemented yet")
        print("   Requires NSIS to be installed on the system")
        return False
    
    def _create_inno_installer(self) -> bool:
        """Create Inno Setup installer."""
        # This would require Inno Setup to be installed
        print("⚠️  Inno Setup installer creation not implemented yet")
        print("   Requires Inno Setup to be installed on the system")
        return False
    
    def package_for_distribution(self, include_installer: bool = False) -> bool:
        """
        Package the application for distribution.
        
        Args:
            include_installer: Whether to include an installer
            
        Returns:
            True if packaging was successful
        """
        print("📦 Packaging for distribution...")
        
        # Build production executable
        if not self.build_production():
            return False
        
        # Create installer if requested
        if include_installer:
            if not self.create_installer():
                return False
        
        print("✅ Distribution package created successfully")
        return True
    
    def run_tests(self) -> bool:
        """
        Run tests before building.
        
        Returns:
            True if tests passed
        """
        print("🧪 Running tests...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", "tests/", "-v"
            ], check=True, capture_output=True, text=True)
            
            print("✅ All tests passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Tests failed:")
            if e.stdout:
                print(f"   stdout: {e.stdout}")
            if e.stderr:
                print(f"   stderr: {e.stderr}")
            return False
    
    def build_with_tests(self, clean: bool = True) -> bool:
        """
        Run tests and build if they pass.
        
        Args:
            clean: Whether to clean build directories first
            
        Returns:
            True if tests passed and build was successful
        """
        if not self.run_tests():
            return False
        
        return self.build_production(clean=clean)


def main():
    """Main entry point for the build manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Manager for the automation application")
    parser.add_argument("command", choices=[
        "build", "build-dev", "clean", "install-deps", "validate", "info", 
        "package", "test", "build-with-tests"
    ], help="Build command to execute")
    parser.add_argument("--no-clean", action="store_true", help="Don't clean build directories")
    parser.add_argument("--installer", action="store_true", help="Include installer in package")
    
    args = parser.parse_args()
    
    manager = BuildManager()
    
    if args.command == "build":
        success = manager.build_production(clean=not args.no_clean)
    elif args.command == "build-dev":
        success = manager.build_development(clean=not args.no_clean)
    elif args.command == "clean":
        manager.clean_all()
        success = True
    elif args.command == "install-deps":
        success = manager.install_dependencies()
    elif args.command == "validate":
        success = manager.validate_environment()
    elif args.command == "info":
        info = manager.get_build_info()
        print("📋 Build Information:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        success = True
    elif args.command == "package":
        success = manager.package_for_distribution(include_installer=args.installer)
    elif args.command == "test":
        success = manager.run_tests()
    elif args.command == "build-with-tests":
        success = manager.build_with_tests(clean=not args.no_clean)
    else:
        print(f"❌ Unknown command: {args.command}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
