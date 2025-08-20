@echo off
REM Start multiple instances of Cursor Automation System
REM Usage: start_multiple.bat [number_of_instances]

set instances=%1
if "%instances%"=="" set instances=2

echo Starting %instances% instances of Cursor Automation System...
echo Multiple instances are now supported by default

for /L %%i in (1,1,%instances%) do (
    echo Starting instance %%i...
    start "Cursor Instance %%i" cmd /k "python cursor.py"
    timeout /t 2 /nobreak >nul
)

echo.
echo %instances% instances started successfully!
echo Each instance is running in a separate command window.
echo.
echo To close all instances:
echo - Close each command window individually, OR
echo - Run: taskkill /f /im python.exe (closes ALL Python processes)
echo.
pause
