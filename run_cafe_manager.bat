@echo off
echo Cafe Supply Manager - Windows Startup
echo =====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Run the Python startup script
python run_cafe_manager.py

REM Keep window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo Something went wrong. Check the error messages above.
    pause
)