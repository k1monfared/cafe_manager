# Cafe Manager - CSV-Based Inventory Analytics System

A comprehensive inventory management and analytics system that uses CSV files for data transparency, with built-in audit capabilities and interactive dashboards.

## Core Features

- **CSV-First Architecture**: All data stored in auditable CSV files with full transparency
- **Data Integrity Auditing**: Comprehensive validation system to detect discrepancies and inconsistencies
- **Interactive Analytics**: Toggle between consumption, stock levels, and combined views with delivery markers
- **Automatic Consumption Calculation**: `consumption = previous_stock + deliveries - current_stock`
- **Intelligent Forecasting**: 14-day rolling averages with runout predictions and confidence levels
- **Explainable Recommendations**: Detailed reasoning for all purchase suggestions with urgency levels

## Quick Start

### For Windows Users (No Programming Required)
**👉 See [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for detailed Windows setup guide**

1. Download this project as ZIP from GitHub
2. Extract and double-click: `setup_windows.bat` 
3. Double-click: `run_cafe_manager.bat`
4. Web browser opens automatically at http://localhost:5000

### For Developers/Linux/Mac
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python simple_app.py
   ```
   
   The web interface will automatically open at http://localhost:5000

## How to Use the Application

### 1. Dashboard (Main Page)
- **Overview Cards**: View total items, items below threshold, critical items, and recommendation count
- **Current Stock Levels**: Table showing all items with their current stock, thresholds, and status
- **Purchase Recommendations**: Urgent recommendations with detailed explanations and urgency levels
- **Quick Actions**: Navigate to analytics for deeper insights

### 2. Analytics Page
- **Interactive Charts**: Toggle between three views:
  - **Consumption View**: Daily consumption patterns over 14 days
  - **Stock View**: Current stock levels with threshold indicators  
  - **Combined View**: Both consumption and stock on dual y-axis
- **Delivery Markers**: Vertical dashed lines show when deliveries occurred
- **Item Selection**: Filter charts by specific inventory items
- **Forecast Data**: View predicted runout dates and consumption trends

### 3. Data Validation Page
- **Audit Results**: Comprehensive validation of data integrity
- **Issue Categories**: 
  - **Critical**: Mathematical inconsistencies requiring immediate attention
  - **Warnings**: Potential data quality issues
  - **Info**: General observations about the data
- **Download Options**: Export audit results as CSV
- **Manual Audit**: Trigger new validation runs

### 4. CSV Upload Page
- **File Upload**: Upload new stock levels, deliveries, or consumption data
- **Automatic Processing**: Files are automatically validated and processed
- **Real-time Updates**: Dashboard and analytics update immediately after upload

## 📋 Files You Need to Create

You only need to create **3 CSV files** to get started. The system generates everything else automatically.

### File 1: `item_info.csv` - Your Product Catalog 
**What it is:** List all products you want to track with their basic settings.

```csv
Item_Name,Unit,Min_Threshold,Max_Capacity,Lead_Time_Days,Cost_Per_Unit,Supplier,Notes
Coffee Beans,lbs,2.0,50.0,3,8.50,Coffee Roasters Inc,Store in dry place
Milk,gallons,3.0,30.0,1,4.25,Metro Dairy Supply,Keep refrigerated  
Paper Cups,cases,5.0,200.0,7,42.00,Paper Supply Co,Dry storage
```

**How to create it:**
- **Item_Name**: Use the exact same names everywhere (case-sensitive!)
- **Unit**: lbs, gallons, cases, dozen - whatever you use
- **Min_Threshold**: When to reorder (triggers alerts when stock drops below)
- **Max_Capacity**: Maximum you can store (prevents over-ordering) 
- **Lead_Time_Days**: How many days from order to delivery
- **Cost_Per_Unit**: Price you pay per unit
- **Supplier** & **Notes**: For your reference

### File 2: `daily_stock_levels.csv` - Daily Counts
**What it is:** Record your actual inventory counts each day.

```csv
Date,Item_Name,Current_Stock
2025-08-24,Coffee Beans,12.5
2025-08-24,Milk,8.0
2025-08-24,Paper Cups,150
```

**How to create it:**
- **Date**: Use YYYY-MM-DD format (2025-08-24, not 8/24/25)
- **Item_Name**: Must match exactly from your `item_info.csv` 
- **Current_Stock**: End-of-day count (decimals OK: 12.5 lbs)

💡 **Tip**: You don't need every item every day. Only record what you counted.

### File 3: `deliveries.csv` - When Shipments Arrive
**What it is:** Log when you receive deliveries to track supply patterns.

```csv
Date,Item_Name,Delivery_Amount,Notes
2025-08-24,Coffee Beans,15.0,Weekly delivery
2025-08-24,Milk,20.0,Fresh supply from Metro Dairy
```

**How to create it:**
- **Date**: Delivery date (YYYY-MM-DD format)
- **Item_Name**: Must match your `item_info.csv` exactly
- **Delivery_Amount**: How much you received (must be positive)
- **Notes**: Delivery details, which supplier, etc.

### ✅ Getting Started Checklist
1. Create `item_info.csv` with all your products first
2. Start recording daily stock counts in `daily_stock_levels.csv`
3. Log deliveries as they arrive in `deliveries.csv`
4. Upload all three files via the web interface
5. The system calculates consumption, forecasts, and recommendations automatically!

⚠️ **Critical Rule**: Item names must be identical across all files. "Coffee Beans" ≠ "coffee beans" ≠ "Coffee Bean"

---

## 🔧 Developer Reference: Generated Files

*The following files are auto-generated by the system - not for end users:*

### `data/daily_consumption.csv` - Calculated Usage Patterns
- **Purpose**: Automatically calculates daily consumption using: `consumption = previous_stock + deliveries - current_stock`
- **Contents**: Historical usage data with detailed reasoning for each calculation
- **Used for**: Forecasting algorithms and trend analysis

### `data/forecast_results.csv` - Predictive Analytics
- **Purpose**: Machine-generated demand forecasts and runout predictions  
- **Contents**: 14-day rolling averages, confidence intervals, predicted stockout dates
- **Used for**: Dashboard charts and recommendation engine

### `data/recommendations.csv` - Purchase Suggestions
- **Purpose**: AI-generated ordering recommendations with explainable logic
- **Contents**: Urgency levels (Critical/High/Medium/Low), quantities, cost calculations
- **Used for**: Dashboard alerts and purchase planning

### `data/audit_results.csv` - Data Quality Monitoring
- **Purpose**: Automated validation of data integrity and mathematical consistency
- **Contents**: Error detection, missing data alerts, threshold violations
- **Used for**: Data quality reports and debugging

## Testing

Run unit tests:
```bash
python -m pytest test_inventory_engine.py -v
```

Run integration tests:
```bash
python -m pytest test_web_app.py -v
```

## Architecture

- **Backend**: Flask web application with pandas for CSV processing
- **Frontend**: Bootstrap 5 with Chart.js for interactive visualizations
- **Data Processing**: Pure CSV operations with explainable calculations
- **Testing**: Comprehensive unit and integration test coverage