@echo off
REM Cafe Manager - Windows Setup Script
echo.
echo ==========================================
echo    🏪 CAFE MANAGER - SETUP INSTALLER
echo ==========================================
echo.
echo This script will help you set up Cafe Manager on Windows
echo.

REM Check if Python is installed
echo 🔍 Checking for Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Python is not installed or not found in PATH
    echo.
    echo 📥 Please follow these steps:
    echo    1. Go to: https://www.python.org/downloads/
    echo    2. Download Python 3.8 or newer
    echo    3. During installation, CHECK "Add Python to PATH"
    echo    4. Run this setup script again
    echo.
    echo 🌐 Opening Python download page...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found
echo.

REM Check Python version (basic check for 3.x)
echo %PYTHON_VERSION% | findstr /r "^3\." >nul
if errorlevel 1 (
    echo ⚠️  Warning: Python 2.x detected. Python 3.8+ recommended
    echo    The application may not work properly
    echo.
)

REM Create virtual environment
echo 📦 Setting up isolated Python environment...
if exist "venv" (
    echo    Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo.
        echo This might happen if:
        echo - Python installation is corrupted
        echo - Insufficient disk space
        echo - Antivirus blocking the operation
        echo.
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

echo.
echo 🔧 Activating environment and installing dependencies...
call venv\Scripts\activate.bat

REM Upgrade pip first
echo    📈 Upgrading pip...
python -m pip install --quiet --upgrade pip
if errorlevel 1 (
    echo ⚠️  Warning: Failed to upgrade pip, continuing anyway...
)

REM Install requirements
echo    📚 Installing application dependencies...
pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo.
    echo Common solutions:
    echo - Check internet connection
    echo - Try running as Administrator
    echo - Temporarily disable antivirus
    echo.
    echo 🔄 Trying alternative installation method...
    pip install flask pandas openpyxl
    if errorlevel 1 (
        echo ❌ Alternative installation also failed
        pause
        exit /b 1
    )
)

echo ✅ Dependencies installed successfully
echo.

REM Test the installation
echo 🧪 Testing installation...
python -c "import flask, pandas; print('✅ Core dependencies working')" 2>nul
if errorlevel 1 (
    echo ❌ Installation test failed
    echo    Some dependencies may not be working properly
    pause
    exit /b 1
)

echo.
echo ==========================================
echo    🎉 SETUP COMPLETE!
echo ==========================================
echo.
echo To run Cafe Manager:
echo    📁 Double-click: run_cafe_manager.bat
echo    💻 Or run in command prompt: run_cafe_manager.bat
echo.
echo The web interface will open automatically in your browser
echo at: http://localhost:5000
echo.
echo 📄 Quick Start:
echo    1. Use the Dashboard to see current inventory status
echo    2. Upload CSV files with your stock and delivery data
echo    3. View Analytics for consumption patterns
echo    4. Check Data Validation for data integrity
echo.
echo Press any key to finish setup...
pause >nul

echo.
echo 🚀 Would you like to start Cafe Manager now? (y/n)
set /p START_NOW=
if /i "%START_NOW%"=="y" (
    echo.
    echo Starting Cafe Manager...
    call run_cafe_manager.bat
) else (
    echo.
    echo Setup complete! Run 'run_cafe_manager.bat' when ready.
)