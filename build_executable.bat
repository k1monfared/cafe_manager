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
echo This may take several minutes...
echo.

REM Create the executable
pyinstaller --onefile --windowed --name "CafeManager" ^
    --add-data "templates;templates" ^
    --add-data "data;data" ^
    --hidden-import "pandas" ^
    --hidden-import "flask" ^
    --hidden-import "webbrowser" ^
    --hidden-import "threading" ^
    simple_app.py

if errorlevel 1 (
    echo ❌ Build failed
    pause
    exit /b 1
)

echo.
echo ✅ Build completed!
echo.
echo 📁 Executable created at: dist\CafeManager.exe
echo.
echo 📋 To distribute:
echo    1. Copy the entire 'dist' folder
echo    2. Include the 'data' folder with your CSV files
echo    3. Users can run CafeManager.exe directly
echo.
pause