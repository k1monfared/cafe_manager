# 🏪 Cafe Manager - Windows Setup Guide

## For Non-Technical Users

This guide helps you run Cafe Manager on Windows without any programming knowledge.

## 📥 Download & Setup

### Option 1: Quick Setup (Recommended)
1. **Download the project**
   - Go to: [GitHub Repository](https://github.com/k1monfared/cafe_manager)
   - Click the green "Code" button → "Download ZIP"
   - Extract the ZIP file to your Desktop or Documents

2. **Run the automatic setup**
   - Open the extracted folder
   - **Double-click**: `setup_windows.bat`
   - Follow the on-screen instructions
   - The script will automatically install Python if needed

3. **Start using Cafe Manager**
   - **Double-click**: `run_cafe_manager.bat`
   - Your web browser will open automatically
   - The application runs at: http://localhost:5000

### Option 2: If You Already Have Python
If you already have Python installed:
1. Download and extract the project (same as above)
2. **Double-click**: `run_cafe_manager.bat`
3. The application will start automatically

## 🚀 How to Use

### First Time Setup
1. **Start the application** by double-clicking `run_cafe_manager.bat`
2. **Your web browser will open automatically** to the Cafe Manager dashboard
3. **Upload your data** using the "CSV Upload" page:
   - Stock levels (daily inventory counts)
   - Deliveries (when you receive supplies)
   - Item information (product details)

### Daily Usage
1. **Dashboard**: See current inventory status and urgent recommendations
2. **Analytics**: View consumption patterns and trends with interactive charts
3. **Data Validation**: Check for any data inconsistencies or errors
4. **CSV Upload**: Add new inventory data as it comes in

## 📁 File Structure
```
cafe_manager/
├── run_cafe_manager.bat     ← Double-click this to start
├── setup_windows.bat        ← One-time setup script
├── data/                    ← Your inventory CSV files
│   ├── daily_stock_levels.csv
│   ├── deliveries.csv
│   └── recommendations.csv
└── templates/               ← Web interface files
```

## ❓ Common Issues & Solutions

### "Python not found"
- Run `setup_windows.bat` - it will guide you to install Python
- Make sure to check "Add Python to PATH" during Python installation

### "Permission denied" or "Access denied"
- Right-click the .bat file → "Run as Administrator"
- Check if antivirus is blocking the application

### Web page doesn't open
- Wait 10-15 seconds after starting
- Manually go to: http://localhost:5000
- Check if Windows Firewall is blocking the connection

### Application won't start
- Make sure you ran `setup_windows.bat` first
- Try restarting your computer
- Check that the `data` folder exists with CSV files

## 🔧 Advanced: Building Standalone Executable

For IT administrators who want to distribute without requiring Python:

1. Run `setup_windows.bat` first
2. Run `build_executable.bat`
3. Share the `dist/CafeManager.exe` file with users
4. Users can run the .exe directly without Python

## 📞 Support

If you encounter issues:
1. Make sure you have internet connection for initial setup
2. Try running `setup_windows.bat` as Administrator
3. Check Windows Event Viewer for detailed error messages
4. Ensure you have at least 500MB free disk space

## 🔄 Updates

To update Cafe Manager:
1. Download the latest version from GitHub
2. Replace all files except the `data` folder (keep your CSV files!)
3. Run `setup_windows.bat` again if there are new dependencies

---

**Made for cafe owners, by cafe owners** ☕
No technical knowledge required - just double-click and go!