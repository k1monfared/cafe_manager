@echo off
REM Cafe Manager - Build Executable Script
echo.
echo ==========================================
echo    🏪 CAFE MANAGER - BUILD EXECUTABLE
echo ==========================================
echo.

REM Activate virtual environment
if not exist "venv" (
    echo ❌ Virtual environment not found
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM Install PyInstaller if not already installed
echo 📦 Installing PyInstaller...
pip install pyinstaller>=5.0.0
if errorlevel 1 (
    echo ❌ Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo 🔨 Building executable...
echo    This may take several minutes...
echo.

REM Build using the spec file (produces dist\CafeManager\ folder)
pyinstaller cafe_manager.spec

if errorlevel 1 (
    echo ❌ Build failed. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ✅ Build completed!
echo.
echo 📁 Distributable folder: dist\CafeManager
echo.
echo    To share with others:
echo       1. Copy the entire "dist\CafeManager" folder
echo       2. Recipient double-clicks CafeManager.exe inside it
echo       3. No Python or other software needed
echo.
pause