# 🚀 Installation Instructions - Cafe Supply Manager

## For Non-Technical Users (Recommended)

### Windows Installation

1. **Install Python** (One-time setup)
   - Go to https://www.python.org/downloads/
   - Download Python 3.8 or newer 
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
   - Click "Install Now"

2. **Download the Cafe Manager**
   - Download or copy this entire `cafe_manager` folder to your computer
   - Remember where you put it (Desktop is fine)

3. **Run the Application**
   - Find the `cafe_manager` folder
   - **Double-click** `run_cafe_manager.py`
   - Wait for it to install needed packages (first time only)
   - Your web browser will open automatically to http://localhost:5000

4. **That's It!**
   - The application is now running
   - Bookmark http://localhost:5000 for easy access
   - To stop: close the black window that appeared

### Mac Installation

1. **Python Check**
   - Open Terminal (found in Applications > Utilities)
   - Type: `python3 --version`
   - If you see "Python 3.x.x", you're good!
   - If not, install from https://www.python.org/downloads/

2. **Run the Application**
   - In Terminal, navigate to the folder: `cd /path/to/cafe_manager`
   - Run: `python3 run_cafe_manager.py`
   - Your browser will open to http://localhost:5000

### Android/Mobile (Advanced)

The system runs in your web browser, so:
1. Follow Windows/Mac instructions on a computer
2. Find your computer's IP address (usually starts with 192.168.x.x)
3. On your phone, go to: http://[your-computer-ip]:5000
4. Bookmark it for easy access

## For Technical Users

### Quick Setup
```bash
git clone [this-repository]
cd cafe_manager
pip install -r requirements.txt
python app.py
```

### Docker (Optional)
```bash
docker build -t cafe-manager .
docker run -p 5000:5000 cafe-manager
```

### Development Setup
```bash
# Create virtual environment
python -m venv cafe_manager_env
source cafe_manager_env/bin/activate  # Linux/Mac
# or
cafe_manager_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run in development mode
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows
python app.py
```

## Troubleshooting

### "python is not recognized" (Windows)
- Python wasn't added to PATH during installation
- Reinstall Python and check "Add Python to PATH"
- Or use: `py run_cafe_manager.py` instead

### "Permission denied" (Mac/Linux)
- Run: `chmod +x run_cafe_manager.py`
- Then: `python3 run_cafe_manager.py`

### "Port 5000 is busy"
- Another application is using port 5000
- Edit `app.py` and change `port=5000` to `port=5001`
- Or stop other applications using port 5000

### Browser doesn't open automatically
- Manually go to: http://localhost:5000
- Check if antivirus/firewall is blocking it
- Try: http://127.0.0.1:5000 instead

### Packages won't install
```bash
# Try upgrading pip first
python -m pip install --upgrade pip

# Then install requirements
pip install -r requirements.txt

# If still failing, install manually:
pip install Flask==2.3.2
```

### No data showing
- Make sure `sample_data/` folder exists with JSON files
- Check file permissions (should be readable)
- Look at browser developer console for errors (F12)

## Alternative Installation Methods

### Portable Version (Advanced)
Create a standalone version that doesn't need Python installation:
```bash
pip install pyinstaller
pyinstaller --onedir --windowed --add-data "templates;templates" --add-data "sample_data;sample_data" app.py
```

### Cloud Deployment (Advanced)
Deploy to free cloud services:

**Heroku:**
```bash
# Create Procfile
echo "web: python app.py" > Procfile
# Deploy
git add .
git commit -m "Deploy to Heroku"
heroku create your-cafe-manager
git push heroku main
```

**Railway/Vercel:**
- Connect your GitHub repository
- Set build command: `pip install -r requirements.txt`
- Set start command: `python app.py`

## Data Migration

### From Existing Google Sheets
1. Export your current sheets as CSV files
2. Compare with templates in `google_sheets_templates/`
3. Adjust column names to match templates
4. Save as JSON in `sample_data/` folder
5. Restart application

### From Other Systems
- Most inventory systems can export CSV
- Map your fields to our template structure
- Use the sample data as a reference format

## Security Notes

### For Local Use Only
- This application is designed for local/internal use
- Don't expose it to the public internet without additional security
- Default configuration is safe for local networks

### For Public Deployment
If you want to share with others:
- Add authentication (login system)
- Use HTTPS (SSL certificates)  
- Validate all user inputs
- Use environment variables for sensitive data

## Performance Tuning

### For Large Datasets
- Consider switching from JSON files to SQLite database
- Implement pagination for large inventory lists
- Add caching for frequently accessed data

### For Multiple Locations
- Add location/store field to all data models
- Filter recommendations by location
- Consider separate databases per location

## Getting Help

1. **Check the Help page** in the application
2. **Review sample data** for format examples  
3. **Read the templates README** for Google Sheets instructions
4. **Start small** - just track your top 5 items first

Remember: The system learns and improves with more data, so don't expect perfection immediately!