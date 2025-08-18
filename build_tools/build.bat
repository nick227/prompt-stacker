@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo    PROMPT STACKER - ENHANCED BUILD
echo ========================================
echo.

:: Step 1: Clean previous builds
echo [1/6] Cleaning previous build artifacts...
if exist "dist" (
    rmdir /s /q "dist"
    echo   ✓ Removed dist directory
)
if exist "*.spec" (
    del /q "*.spec"
    echo   ✓ Removed spec files
)
echo.

:: Step 2: Verify Python and dependencies
echo [2/6] Checking dependencies...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ Python not found! Please install Python and add it to PATH
    pause
    exit /b 1
)

echo   ✓ Python found
python -c "import pyinstaller" >nul 2>&1
if errorlevel 1 (
    echo   ❌ PyInstaller not found! Installing...
    pip install pyinstaller
)

python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo   ❌ CustomTkinter not found! Installing...
    pip install customtkinter
)

python -c "import pyautogui" >nul 2>&1
if errorlevel 1 (
    echo   ❌ PyAutoGUI not found! Installing...
    pip install pyautogui
)

python -c "import pyperclip" >nul 2>&1
if errorlevel 1 (
    echo   ❌ PyPerclip not found! Installing...
    pip install pyperclip
)

python -c "import pynput" >nul 2>&1
if errorlevel 1 (
    echo   ❌ Pynput not found! Installing...
    pip install pynput
)

python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo   ❌ Psutil not found! Installing...
    pip install psutil
)

echo   ✓ All dependencies available
echo.

:: Step 3: Verify icon file
echo [3/6] Checking icon file...
if exist "build\promptstacker.ico" (
    echo   ✓ Icon file found: build\promptstacker.ico
) else (
    echo   ❌ Icon file not found: build\promptstacker.ico
    echo   Please create the icon file at: build\promptstacker.ico
    pause
    exit /b 1
)
echo.

:: Step 4: Build executable
echo [4/6] Building executable with PyInstaller...
echo   This may take a few minutes...

pyinstaller --onefile ^
    --windowed ^
    --name "PromptStacker" ^
    --icon "build\promptstacker.ico" ^
    --add-data "prompt_lists/prompt_list.py;prompt_lists" ^
    --hidden-import "customtkinter" ^
    --hidden-import "tkinter" ^
    --hidden-import "pyautogui" ^
    --hidden-import "pyperclip" ^
    --hidden-import "pynput" ^
    --hidden-import "psutil" ^
    --hidden-import "collections" ^
    --hidden-import "threading" ^
    --hidden-import "time" ^
    --hidden-import "gc" ^
    cursor.py

if errorlevel 1 (
    echo   ❌ Build failed! Check the error messages above.
    pause
    exit /b 1
)

:: Step 5: Sign executable (if signtool available)
echo [5/6] Signing executable...
set "SIGNTOOL_PATH="
for /f "delims=" %%i in ('dir /b /s "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe" 2^>nul') do (
    set "SIGNTOOL_PATH=%%i"
    goto :found_signtool
)

:found_signtool
if defined SIGNTOOL_PATH (
    echo   ✓ Found signtool: !SIGNTOOL_PATH!
    
    :: Check for self-signed certificate
    if exist "promptstacker.pfx" (
        echo   ✓ Found self-signed certificate: promptstacker.pfx
        echo   Signing with self-signed certificate...
        "!SIGNTOOL_PATH!" sign /f "promptstacker.pfx" /p "promptstacker" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a "dist\PromptStacker.exe"
        if errorlevel 1 (
            echo   ⚠️  Self-signed signing failed (this is normal without a code signing certificate)
            echo   Executable will work without signature
        ) else (
            echo   ✓ Executable signed successfully with self-signed certificate
        )
    ) else (
        echo   ⚠️  No certificate found - run create_cert.bat to create a free self-signed certificate
        echo   Executable will work without signature
    )
) else (
    echo   ⚠️  Signtool not found - skipping signing
    echo   Executable will work without signature
)
echo.

:: Step 6: Generate SHA256 and finalize
echo [6/6] Creating distribution package...
if exist "dist\PromptStacker.exe" (
    echo   ✓ Build successful!
    echo   📁 Executable location: dist\PromptStacker.exe
    
    :: Get file size
    for %%A in ("dist\PromptStacker.exe") do (
        set "size=%%~zA"
        set /a "sizeMB=!size!/1048576"
        echo   📊 File size: !sizeMB! MB
    )
    
    :: Generate SHA256 hash
    echo   🔐 Generating SHA256 hash...
    powershell -Command "Get-FileHash -Path 'C:\wamp64\www\screen\dist\PromptStacker.exe' -Algorithm SHA256 | Out-File -FilePath 'C:\wamp64\www\screen\dist\PromptStacker.exe.sha256' -Encoding ASCII"
    if errorlevel 1 (
        echo   ⚠️  SHA256 generation failed
    ) else (
        echo   ✓ SHA256 hash saved: dist\PromptStacker.exe.sha256
    )
    
    echo.
    echo ========================================
    echo           BUILD COMPLETED!
    echo ========================================
    echo.
    echo 🎉 Your distribution package is ready!
    echo 📁 Executable: dist\PromptStacker.exe
    echo 🔐 SHA256 Hash: dist\PromptStacker.exe.sha256
    echo.
    
    :: Ask if user wants to test the executable
    set /p "test=🧪 Would you like to test the executable? (y/n): "
    if /i "!test!"=="y" (
        echo 🚀 Starting executable test...
        start "" "dist\PromptStacker.exe"
        echo ✅ Test launched!
    )
    
) else (
    echo   ❌ Build failed! Executable not found.
    pause
    exit /b 1
)

echo.
echo Press any key to exit...
pause >nul
