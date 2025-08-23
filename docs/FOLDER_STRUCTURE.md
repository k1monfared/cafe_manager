# Cafe Manager - Folder Structure

This document describes the organized folder structure of the Cafe Manager application.

## Root Directory
```
cafe_manager/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── run_cafe_manager.py     # Application launcher script
├── run_cafe_manager.bat    # Windows launcher script
└── README.md              # Main project documentation
```

## Core Directories

### `/config/` - Configuration Files
- `google_credentials.json` - Google API service account credentials
- `google_token.pickle` - Google OAuth token cache

### `/data/` - Data Storage
- `sample_data/` - JSON data files used by the application
  - `inventory_items.json` - Current inventory with thresholds and costs
  - `inventory_snapshots.json` - Daily stock counts and deliveries
  - `daily_usage.json` - Auto-calculated usage patterns
  - `order_history.json` - Purchase order records
  - `suppliers.json` - Supplier contact and lead time information

### `/docs/` - Documentation
- `README.md` - Main project documentation
- `GETTING_STARTED.md` - Quick setup guide
- `GOOGLE_SHEETS_GUIDE.md` - Google Sheets integration guide
- `GOOGLE_DRIVE_SETUP.md` - Google Drive setup instructions
- `DATA_STRUCTURE.md` - Data format specifications
- `FOLDER_STRUCTURE.md` - This file
- Other technical documentation

### `/scripts/` - Utility Scripts
- `google_drive_integration.py` - Google Drive API wrapper
- `sheets_sync.py` - Google Sheets synchronization
- `sync_scheduler.py` - Automatic sync scheduling
- `usage_calculator.py` - Usage pattern analysis
- `import_sample_inventory_data.py` - Sample data importer
- `convert_messy_data.py` - Data conversion utilities
- `test_forecasting.py` - Forecasting engine tests
- Other utility scripts

### `/src/` - Core Application Code
- `forecasting_engine.py` - Inventory forecasting and recommendations

### `/templates/` - Web Templates and CSV Export Templates
- `*.html` - Flask web interface templates
- `csv_templates/` - CSV export templates for manual workflows
  - `current_inventory_template.csv`
  - `daily_inventory_template.csv`
  - `order_history_template.csv`
  - `suppliers_template.csv`

### `/google_sheets_templates/` - Google Sheets Integration
- CSV templates specifically for Google Sheets users
- Same files as `/templates/csv_templates/` but maintained separately
- `README_Templates.md` - Template usage instructions

### `/google_sheets_data/` - Temporary Upload Directory
- Temporary storage for uploaded Google Sheets CSV files
- Files are processed and deleted after import

### `/static/` - Static Web Assets
- Currently empty - reserved for CSS, JS, images if needed

## File Organization Principles

1. **Separation of Concerns**: Scripts, configuration, data, and documentation are in separate folders
2. **Clear Naming**: Folder names clearly indicate their purpose
3. **Minimal Root**: Only essential files remain in the root directory
4. **Template Duplication**: CSV templates exist in both `/templates/csv_templates/` and `/google_sheets_templates/` to support different workflows

## Import Path Updates

After reorganization, the following import paths were updated:
- `from sheets_sync import SheetsSync` → `from scripts.sheets_sync import SheetsSync`
- `sample_data/` → `data/sample_data/`
- `static/templates/` → `templates/csv_templates/`

## Running the Application

The application can still be run normally:
```bash
python3 app.py
```

All file paths have been updated to work with the new structure automatically.