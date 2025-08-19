"""
PyInstaller Builder

Handles building the application using PyInstaller.
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    from .build_config import get_build_config, validate_build_environment
except ImportError:
    # Fallback for when running as script
    from build_config import get_build_config, validate_build_environment


class PyInstallerBuilder:
    """Handles building the application with PyInstaller."""

    def __init__(self, dev_mode: bool = False):
        """
        Initialize the builder.
        
        Args:
            dev_mode: Whether to use development build options
        """
        self.config = get_build_config(dev_mode)
        self.dev_mode = dev_mode

    def validate_environment(self) -> bool:
        """
        Validate the build environment.
        
        Returns:
            True if environment is valid
        """
        result = validate_build_environment()

        if result["warnings"]:
            print("⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"   {warning}")

        if result["errors"]:
            print("❌ Build environment validation failed:")
            for error in result["errors"]:
                print(f"   {error}")
            return False

        print("✅ Build environment validated successfully")
        return True

    def clean_build_directories(self) -> None:
        """Clean build and dist directories."""
        print("🧹 Cleaning build directories...")

        for directory in [self.config["build_dir"], self.config["dist_dir"]]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                print(f"   Cleaned: {directory}")

        # Clean PyInstaller cache
        cache_dir = Path.home() / ".pyinstaller"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            print(f"   Cleaned PyInstaller cache: {cache_dir}")

    def build_spec_file(self) -> str:
        """
        Generate PyInstaller spec file.
        
        Returns:
            Path to the generated spec file
        """
        print("📝 Generating PyInstaller spec file...")

        spec_content = self._generate_spec_content()
        spec_file = Path(self.config["spec_dir"]) / f"{self.config['app_name'].lower().replace(' ', '_')}.spec"

        with open(spec_file, "w") as f:
            f.write(spec_content)

        print(f"   Generated: {spec_file}")
        return str(spec_file)

    def _generate_spec_content(self) -> str:
        """Generate the PyInstaller spec file content."""
        options = self.config["pyinstaller_options"]

        # Build hidden imports string
        hidden_imports_str = ",\n        ".join([f'"{imp}"' for imp in self.config["hidden_imports"]])

        # Build data files string
        data_files_str = ""
        if self.config["data_files"]:
            data_files_str = ",\n        ".join([f'("{src}", "{dst}")' for src, dst in self.config["data_files"]])

        # Build exclude patterns string
        exclude_patterns_str = ",\n        ".join([f'"{pattern}"' for pattern in self.config["exclude_patterns"]])

        # Icon option
        icon_option = f'icon="{self.config["icon_file"]}",' if self.config["icon_file"] else ""

        return f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{self.config["main_script"]}'],
    pathex=[],
    binaries=[],
    datas=[{data_files_str}],
    hiddenimports=[
        {hidden_imports_str}
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[{exclude_patterns_str}],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.config["app_name"].lower().replace(" ", "_")}',
    debug=False,
    bootloader_ignore_signals=False,
    strip={options["strip"]},
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=not {options["windowed"]},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_option}
)
"""

    def run_pyinstaller(self, spec_file: str) -> bool:
        """
        Run PyInstaller with the generated spec file.
        
        Args:
            spec_file: Path to the spec file
            
        Returns:
            True if build was successful
        """
        print("🔨 Running PyInstaller...")

        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean" if self.config["pyinstaller_options"]["clean"] else "",
            "--noconfirm" if self.config["pyinstaller_options"]["noconfirm"] else "",
            spec_file,
        ]

        # Remove empty strings
        cmd = [arg for arg in cmd if arg]

        print(f"   Command: {' '.join(cmd)}")

        try:
            start_time = time.time()
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            build_time = time.time() - start_time

            print(f"✅ Build completed successfully in {build_time:.1f} seconds")

            # Print any warnings from PyInstaller
            if result.stderr:
                print("⚠️  PyInstaller warnings:")
                for line in result.stderr.split("\n"):
                    if line.strip() and "warning" in line.lower():
                        print(f"   {line}")

            return True

        except subprocess.CalledProcessError as e:
            print("❌ PyInstaller build failed:")
            print(f"   Exit code: {e.returncode}")
            if e.stdout:
                print(f"   stdout: {e.stdout}")
            if e.stderr:
                print(f"   stderr: {e.stderr}")
            return False

    def verify_build(self) -> bool:
        """
        Verify the build output.
        
        Returns:
            True if build verification passed
        """
        print("🔍 Verifying build output...")

        if self.config["pyinstaller_options"]["onefile"]:
            # Single file mode
            exe_name = f"{self.config['app_name'].lower().replace(' ', '_')}.exe"
            exe_path = Path(self.config["dist_dir"]) / exe_name

            if not exe_path.exists():
                print(f"❌ Executable not found: {exe_path}")
                return False

            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ Executable created: {exe_path}")
            print(f"   Size: {file_size:.1f} MB")

        else:
            # Directory mode
            dist_dir = Path(self.config["dist_dir"])
            if not dist_dir.exists():
                print(f"❌ Distribution directory not found: {dist_dir}")
                return False

            exe_files = list(dist_dir.rglob("*.exe"))
            if not exe_files:
                print(f"❌ No executable files found in: {dist_dir}")
                return False

            print(f"✅ Distribution directory created: {dist_dir}")
            for exe_file in exe_files:
                file_size = exe_file.stat().st_size / (1024 * 1024)  # MB
                print(f"   {exe_file.name}: {file_size:.1f} MB")

        return True

    def build(self, clean: bool = True) -> bool:
        """
        Perform the complete build process.
        
        Args:
            clean: Whether to clean build directories first
            
        Returns:
            True if build was successful
        """
        print(f"🚀 Starting {'development' if self.dev_mode else 'production'} build...")
        print(f"   App: {self.config['app_name']} v{self.config['app_version']}")
        print(f"   Entry point: {self.config['main_script']}")

        # Validate environment
        if not self.validate_environment():
            return False

        # Clean build directories
        if clean:
            self.clean_build_directories()

        # Generate spec file
        spec_file = self.build_spec_file()

        # Run PyInstaller
        if not self.run_pyinstaller(spec_file):
            return False

        # Verify build
        if not self.verify_build():
            return False

        print("🎉 Build completed successfully!")
        return True


def main():
    """Main entry point for the builder."""
    import argparse

    parser = argparse.ArgumentParser(description="Build the automation application")
    parser.add_argument("--dev", action="store_true", help="Use development build options")
    parser.add_argument("--no-clean", action="store_true", help="Don't clean build directories")

    args = parser.parse_args()

    builder = PyInstallerBuilder(dev_mode=args.dev)
    success = builder.build(clean=not args.no_clean)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
