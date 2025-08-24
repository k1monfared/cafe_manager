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

## Data Files

- `data/daily_stock_levels.csv` - Daily stock counts (input via upload)
- `data/deliveries.csv` - Delivery records (input via upload)
- `data/daily_consumption.csv` - Calculated consumption (auto-generated)
- `data/item_info.csv` - Item configuration (thresholds, lead times, etc.)
- `data/forecast_results.csv` - Forecast data with chart information (auto-generated)
- `data/recommendations.csv` - Purchase recommendations with detailed reasoning (auto-generated)
- `data/audit_results.csv` - Data validation results (auto-generated)

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