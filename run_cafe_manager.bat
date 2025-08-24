@echo off
REM Cafe Manager - Windows Startup Script
echo.
echo ==========================================
echo    🏪 CAFE MANAGER - INVENTORY SYSTEM
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install or update requirements
echo 📚 Installing/updating dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo.
    echo Try running: pip install --upgrade pip
    pause
    exit /b 1
)

echo ✅ Dependencies ready
echo.

REM Start the application
echo 🚀 Starting Cafe Manager...
echo 🌐 The web interface will open automatically
echo.
echo Press Ctrl+C to stop the application
echo ==========================================
echo.

python simple_app.py

echo.
echo 👋 Application stopped. Press any key to exit.
pause >nul