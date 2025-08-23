# Cafe Manager Data Structure (v2.0)

## Overview
The system has been redesigned around a **simplified daily inventory counting workflow**. Users now only need to count their current stock daily - the system automatically calculates usage patterns and generates recommendations.

## 📊 Core Data Files

### Primary Data Source
- **`inventory_snapshots.json`** - Daily inventory counts (what users enter)
  - Date, item_id, stock_level, waste_amount, deliveries_received, notes
  - This is the PRIMARY data source that drives everything else

### Auto-Generated Data
- **`daily_usage.json`** - Automatically calculated from inventory snapshots
  - Formula: `Usage = Previous Stock + Deliveries - Current Stock - Waste`
  - Used by forecasting engine for pattern analysis

### Master Data (Setup Once)
- **`inventory_items.json`** - Master catalog of items
  - Item details, capacity, thresholds, supplier info, costs
- **`suppliers.json`** - Supplier contact information and terms
- **`order_history.json`** - Historical orders for trend analysis

## 🔄 Data Flow

```
User Daily Input → Automatic Processing → Smart Recommendations

Daily Inventory Count → inventory_snapshots.json
         ↓
   UsageCalculator → daily_usage.json  
         ↓
   ForecastingEngine → Order Recommendations
```

## 📝 Templates for Users

### Google Sheets Templates (`google_sheets_templates/`)
- **`daily_inventory_template.csv`** - Daily stock counting (PRIMARY USE)
- **`current_inventory_template.csv`** - Initial setup only
- **`suppliers_template.csv`** - Initial setup only  
- **`order_history_template.csv`** - Import past orders (optional)

### Web Templates (`static/templates/`)
- Same as Google Sheets templates but for direct CSV upload

## ✅ What Changed from v1.0

### REMOVED (No Longer Needed)
- ❌ `daily_usage_template.csv` - Users don't manually enter usage anymore
- ❌ `google_sheets_data/` folder - Old CSV storage location
- ❌ Backup folders - Old sample data

### NEW (Simplified Workflow)  
- ✅ `inventory_snapshots.json` - Primary data source
- ✅ `daily_inventory_template.csv` - Simple stock counting
- ✅ Automatic usage calculation
- ✅ Smart forecasting based on inventory trends

## 🎯 User Experience

### OLD Workflow (Complex)
1. Count current stock daily
2. Manually calculate and enter usage amounts
3. Track waste separately
4. Enter sales data
5. Update multiple spreadsheets

### NEW Workflow (Simple)  
1. **Count current stock daily** (2-3 minutes)
2. **Optional:** Note waste and deliveries
3. **Automatic:** System calculates everything else

## 🧠 Intelligence Layer

The system now provides:
- **Usage Pattern Analysis**: Identifies trends and day-of-week patterns
- **Smart Reordering**: Recommendations based on lead times and usage rates
- **Confidence Levels**: High confidence when based on actual counting data
- **Waste Tracking**: Separate tracking of spoilage vs normal consumption

## 📈 Sample Data Insights

Current demo data shows:
- **Whole Milk**: 2.76 gal/day usage → Need to reorder immediately
- **House Blend Coffee**: 1.66 lbs/day usage → Reorder in 1.5 days
- **Paper Cups**: 1.03 cases/day usage → Reorder in 1 day (long lead time!)
- **Vanilla Syrup**: 0.75 bottles/day usage → Good for 5 more days

## 🔧 Technical Implementation

### Key Classes
- **`UsageCalculator`**: Processes inventory snapshots → usage records
- **`ForecastingEngine`**: Analyzes patterns → order recommendations  
- **Web Interface**: Daily inventory entry with mobile-friendly design

### API Endpoints
- `POST /api/save_inventory_snapshot` - Save daily counts
- `GET /api/inventory_items` - Get master item catalog
- `GET /daily-inventory` - Daily counting interface

This structure provides maximum value with minimum user effort - the key to successful adoption by busy cafe owners!