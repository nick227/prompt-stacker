# 🚀 Build Guide - Prompt Stacker

This guide explains how to build the Prompt Stacker automation tool into a distributable executable.

## 📋 Prerequisites

### System Requirements
- **Python 3.8+** (3.11+ recommended)
- **Windows 10/11** (primary target)
- **4GB+ RAM** (for building)
- **2GB+ free disk space**

### Python Dependencies
Install the required Python packages:

```bash
# Install production dependencies
pip install -r requirements.txt

# Install build dependencies
pip install pyinstaller setuptools wheel
```

Or use the build system to install dependencies:
```bash
python build.py install-deps
```

## 🛠️ Build System Overview

The build system consists of several components:

- **`build_tools/`** - Core build system
  - `build_config.py` - Configuration and settings
  - `pyinstaller_builder.py` - PyInstaller integration
  - `build_manager.py` - Unified build interface
- **`build.py`** - Simple Python build script
- **`build.ps1`** - PowerShell build script (Windows)

## 🚀 Quick Start

### 1. Validate Environment
First, validate your build environment:

```bash
python build.py validate
```

### 2. Build Production Executable
Create an optimized production build:

```bash
python build.py build
```

### 3. Test the Build
The executable will be created in `dist/` directory. Run it to test:

```bash
# Windows
dist\prompt_stacker.exe

# Or navigate to dist folder and double-click the .exe
```

## 📦 Build Commands

### Basic Commands

| Command | Description |
|---------|-------------|
| `build` | Build production executable (optimized, single file) |
| `build-dev` | Build development executable (faster, larger) |
| `clean` | Clean all build artifacts |
| `validate` | Validate build environment |
| `info` | Show build information |

### Advanced Commands

| Command | Description |
|---------|-------------|
| `install-deps` | Install build dependencies |
| `package` | Package for distribution |
| `test` | Run tests |
| `build-with-tests` | Run tests then build |

### Options

| Option | Description |
|--------|-------------|
| `--no-clean` | Don't clean build directories |
| `--installer` | Include installer in package |

## 🔧 Build Modes

### Production Build (`build`)
- **Single executable file** (~50-100MB)
- **Optimized** for size and performance
- **Stripped** of debug information
- **Best for distribution**

### Development Build (`build-dev`)
- **Directory structure** (faster to build)
- **Includes debug information**
- **Larger size** but faster rebuilds
- **Best for testing and development**

## 📁 Build Output

### Production Build
```
dist/
└── prompt_stacker.exe    # Single executable file
```

### Development Build
```
dist/
└── prompt_stacker/
    ├── prompt_stacker.exe
    ├── _internal/         # Python runtime and libraries
    └── ...                # Other dependencies
```

## 🧪 Testing Your Build

### 1. Basic Functionality Test
```bash
# Run the executable
dist\prompt_stacker.exe

# Verify the UI loads correctly
# Test basic functionality
```

### 2. Automation Test
```bash
# Test automation features
# Verify coordinate selection works
# Test prompt loading and editing
```

### 3. File Operations Test
```bash
# Test prompt file loading
# Test prompt file saving
# Test different file formats (py, txt, csv)
```

## 🔍 Troubleshooting

### Common Issues

#### 1. "PyInstaller not found"
```bash
pip install pyinstaller
```

#### 2. "Missing dependencies"
```bash
python build.py install-deps
```

#### 3. "Build fails with import errors"
```bash
# Clean and rebuild
python build.py clean
python build.py build
```

#### 4. "Executable is too large"
```bash
# Use production build (already optimized)
python build.py build

# Or manually exclude unnecessary modules in build_config.py
```

#### 5. "Executable doesn't start"
```bash
# Check Windows Defender/Antivirus
# Run as administrator
# Check for missing Visual C++ Redistributables
```

### Debug Build Issues

#### 1. Enable Console Output
Edit `build_tools/build_config.py`:
```python
PYINSTALLER_OPTIONS = {
    "onefile": True,
    "windowed": False,  # Change to False for console output
    # ... other options
}
```

#### 2. Verbose PyInstaller Output
```bash
python build.py build --verbose
```

#### 3. Check Build Logs
Look for logs in:
- `build/` directory
- PyInstaller cache: `~/.pyinstaller/`

## 📦 Distribution

### Creating Distribution Package

```bash
# Build and package
python build.py package

# Include installer (if available)
python build.py package --installer
```

### Distribution Contents

For a complete distribution, include:

1. **Executable** (`prompt_stacker.exe`)
2. **README** (usage instructions)
3. **License** (MIT license)
4. **Sample Files** (example prompt files)
5. **Installation Guide** (if needed)

### File Size Optimization

The executable size can be optimized by:

1. **Excluding unnecessary modules** in `build_config.py`
2. **Using UPX compression** (already enabled)
3. **Stripping debug symbols** (already enabled)
4. **Removing unused dependencies**

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Build
on: [push, pull_request]

jobs:
  build:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        python build.py install-deps
    - name: Run tests
      run: python build.py test
    - name: Build executable
      run: python build.py build
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: prompt-stacker
        path: dist/
```

## 🎯 Best Practices

### 1. Always Test After Building
```bash
python build.py build-with-tests
```

### 2. Use Version Control
- Commit build configuration changes
- Don't commit build artifacts (`dist/`, `build/`)
- Use `.gitignore` for build directories

### 3. Document Changes
- Update version in `build_config.py`
- Document new dependencies
- Update this guide for new features

### 4. Security Considerations
- Sign your executables (optional)
- Scan for malware (false positives common)
- Test on clean systems

## 📚 Advanced Configuration

### Customizing Build Configuration

Edit `build_tools/build_config.py`:

```python
# Add custom hidden imports
HIDDEN_IMPORTS = [
    # ... existing imports
    "your_custom_module",
]

# Add data files
DATA_FILES = [
    ("assets/", "assets/"),
    ("config/", "config/"),
]

# Custom PyInstaller options
PYINSTALLER_OPTIONS = {
    "onefile": True,
    "windowed": True,
    "upx": True,  # Enable UPX compression
    "upx_exclude": ["vcruntime140.dll"],  # Exclude from compression
}
```

### Creating Custom Spec Files

For advanced customization, create custom `.spec` files:

```bash
# Generate spec file
python build.py build --spec-only

# Edit the generated spec file
# Rebuild with custom spec
pyinstaller build_tools/specs/prompt_stacker.spec
```

## 🤝 Contributing

When contributing to the build system:

1. **Test your changes** thoroughly
2. **Update documentation** if needed
3. **Follow existing patterns** in the code
4. **Add tests** for new build features
5. **Update version numbers** appropriately

## 📞 Support

If you encounter build issues:

1. **Check this guide** for common solutions
2. **Validate your environment**: `python build.py validate`
3. **Check PyInstaller documentation**
4. **Create an issue** with detailed error information

---

**Happy Building! 🚀**
