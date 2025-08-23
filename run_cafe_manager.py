#!/usr/bin/env python3
"""
Cafe Supply Manager - Easy Startup Script
This script helps users start the application without technical knowledge
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_python():
    """Check if Python is available and correct version"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Packages installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        print("   Try running: pip install -r requirements.txt")
        input("Press Enter to exit...")
        sys.exit(1)

def check_data_files():
    """Check if data files exist"""
    data_dir = Path("data/sample_data")
    required_files = [
        "inventory_items.json",
        "suppliers.json", 
        "daily_usage.json",
        "order_history.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not (data_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing data files: {', '.join(missing_files)}")
        print("   Make sure you have the data/sample_data directory with all required files")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("✅ Data files found")

def start_application():
    """Start the Flask application"""
    print("🚀 Starting Cafe Supply Manager...")
    print("   This will open your web browser automatically")
    print("   If it doesn't open, go to: http://localhost:5001")
    print()
    print("🛑 To stop the application, press Ctrl+C in this window")
    print()
    
    # Wait a moment then open browser
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:5001')
    except:
        pass  # Browser opening is optional
    
    # Start the Flask app
    try:
        from app import app
        app.run(debug=False, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Cafe Supply Manager stopped")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        input("Press Enter to exit...")

def main():
    print("☕ Cafe Supply Manager - Easy Startup")
    print("=" * 50)
    
    # Check system requirements
    check_python()
    
    # Install packages
    install_requirements()
    
    # Check data files
    check_data_files()
    
    print()
    print("🎉 Ready to start!")
    print()
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()