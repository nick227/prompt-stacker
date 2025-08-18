#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Enhanced build script for Prompt Stacker executable
    
.DESCRIPTION
    This script cleans previous builds and creates a fresh executable
    using PyInstaller with icon, signing, ZIP creation, and SHA256 hash.
#>

Write-Host "🚀 Starting enhanced EXE build..." -ForegroundColor Green

# Step 1: Clean previous builds
Write-Host "🧹 Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Host "  ✓ Removed build directory" -ForegroundColor Green
}
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
    Write-Host "  ✓ Removed dist directory" -ForegroundColor Green
}
if (Test-Path "*.spec") {
    Remove-Item -Path "*.spec" -Force
    Write-Host "  ✓ Removed spec files" -ForegroundColor Green
}

# Step 2: Verify dependencies
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import pyinstaller; print('PyInstaller version:', pyinstaller.__version__)"
    python -c "import customtkinter; print('CustomTkinter available')"
    python -c "import pyautogui; print('PyAutoGUI available')"
    python -c "import pyperclip; print('PyPerclip available')"
    python -c "import pynput; print('Pynput available')"
    python -c "import psutil; print('Psutil available')"
    Write-Host "  ✓ All dependencies available" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Missing dependencies. Please install required packages." -ForegroundColor Red
    exit 1
}

# Step 3: Verify icon file
Write-Host "🎨 Checking icon file..." -ForegroundColor Yellow
$iconPath = "build\promptstacker.ico"
if (Test-Path $iconPath) {
    Write-Host "  ✓ Icon file found: $iconPath" -ForegroundColor Green
    $useIcon = $true
} else {
    Write-Host "  ⚠️  Icon file not found: $iconPath" -ForegroundColor Yellow
    Write-Host "  Building without custom icon..." -ForegroundColor Yellow
    $useIcon = $false
}

# Step 4: Run PyInstaller build
Write-Host "🔨 Building executable with PyInstaller..." -ForegroundColor Yellow
if ($useIcon) {
    $buildCommand = @"
pyinstaller --onefile --windowed --name "PromptStacker" --icon "build\promptstacker.ico" --add-data "prompt_lists/prompt_list.py;prompt_lists" --hidden-import "customtkinter" --hidden-import "tkinter" --hidden-import "pyautogui" --hidden-import "pyperclip" --hidden-import "pynput" --hidden-import "psutil" --hidden-import "collections" --hidden-import "threading" --hidden-import "time" --hidden-import "gc" cursor.py
"@
} else {
    $buildCommand = @"
pyinstaller --onefile --windowed --name "PromptStacker" --add-data "prompt_lists/prompt_list.py;prompt_lists" --hidden-import "customtkinter" --hidden-import "tkinter" --hidden-import "pyautogui" --hidden-import "pyperclip" --hidden-import "pynput" --hidden-import "psutil" --hidden-import "collections" --hidden-import "threading" --hidden-import "time" --hidden-import "gc" cursor.py
"@
}

Write-Host "Running: $buildCommand" -ForegroundColor Cyan
Invoke-Expression $buildCommand

# Step 5: Sign executable
Write-Host "🔐 Signing executable..." -ForegroundColor Yellow
$signtoolPath = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName

if ($signtoolPath) {
    Write-Host "  ✓ Found signtool: $signtoolPath" -ForegroundColor Green
    Write-Host "  Signing with SHA256..." -ForegroundColor Yellow
    
    try {
        & $signtoolPath sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a "dist\PromptStacker.exe"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Executable signed successfully" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Signing failed (this is normal without a code signing certificate)" -ForegroundColor Yellow
            Write-Host "  Executable will work without signature" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠️  Signing failed (this is normal without a code signing certificate)" -ForegroundColor Yellow
        Write-Host "  Executable will work without signature" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  Signtool not found - skipping signing" -ForegroundColor Yellow
    Write-Host "  Executable will work without signature" -ForegroundColor Yellow
}

# Step 6: Check build result and create distribution package
Write-Host "📦 Creating distribution package..." -ForegroundColor Yellow
if (Test-Path "dist/PromptStacker.exe") {
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host "📁 Executable location: dist/PromptStacker.exe" -ForegroundColor Cyan
    
    # Get file size
    $fileSize = (Get-Item "dist/PromptStacker.exe").Length / 1MB
    Write-Host "📊 File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan
    
    # Create ZIP file
    Write-Host "📦 Creating ZIP archive..." -ForegroundColor Yellow
    try {
        Compress-Archive -Path "dist\PromptStacker.exe" -DestinationPath "dist\PromptStacker.zip" -Force
        Write-Host "  ✓ ZIP created: dist\PromptStacker.zip" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  ZIP creation failed" -ForegroundColor Yellow
    }
    
    # Generate SHA256 hash
    Write-Host "🔐 Generating SHA256 hash..." -ForegroundColor Yellow
    try {
        $hash = Get-FileHash -Path "dist\PromptStacker.exe" -Algorithm SHA256
        $hash.Hash | Out-File -FilePath "dist\PromptStacker.exe.sha256" -Encoding ASCII
        Write-Host "  ✓ SHA256 hash saved: dist\PromptStacker.exe.sha256" -ForegroundColor Green
        Write-Host "  Hash: $($hash.Hash)" -ForegroundColor Cyan
    } catch {
        Write-Host "  ⚠️  SHA256 generation failed" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "           BUILD COMPLETED!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 Your distribution package is ready!" -ForegroundColor Green
    Write-Host "📁 Executable: dist\PromptStacker.exe" -ForegroundColor Cyan
    Write-Host "📦 ZIP Archive: dist\PromptStacker.zip" -ForegroundColor Cyan
    Write-Host "🔐 SHA256 Hash: dist\PromptStacker.exe.sha256" -ForegroundColor Cyan
    Write-Host ""
    
    # Step 7: Optional - Test the executable
    Write-Host "🧪 Would you like to test the executable? (y/n)" -ForegroundColor Yellow
    $testResponse = Read-Host
    if ($testResponse -eq "y" -or $testResponse -eq "Y") {
        Write-Host "🚀 Starting executable test..." -ForegroundColor Green
        Start-Process -FilePath "dist/PromptStacker.exe" -Wait
        Write-Host "✅ Test completed" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Build failed! Check the error messages above." -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Enhanced build process completed!" -ForegroundColor Green
