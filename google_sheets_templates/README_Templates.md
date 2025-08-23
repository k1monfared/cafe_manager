# Google Sheets Templates for Cafe Supply Management

These CSV templates can be imported into Google Sheets to organize your cafe's supply data. Each template includes sample data to show you the expected format.

## Template Files

### 1. Current_Inventory_Template.csv
**Purpose**: Track your current stock levels, costs, and supplier information
**Key Fields**:
- `Current_Stock`: How much you have right now
- `Min_Threshold`: When to reorder (red flag level)
- `Max_Capacity`: Maximum you can store
- `Lead_Time_Days`: How long orders take to arrive
- `Shelf_Life_Days`: How long items stay fresh

**Update Frequency**: Daily for perishables, weekly for non-perishables

### 2. Daily_Usage_Template.csv  
**Purpose**: Record what you use each day to identify patterns
**Key Fields**:
- `Quantity_Used`: Amount consumed during service
- `Waste_Amount`: Amount spoiled/discarded
- `Sales_Count`: Number of drinks/items sold
- `Weather`: Weather affects customer behavior
- `Special_Events`: Holidays, local events, etc.

**Update Frequency**: Daily (can be done at end of business day)

### 3. Order_History_Template.csv
**Purpose**: Keep track of all orders placed and received  
**Key Fields**:
- `Quantity_Ordered` vs `Quantity_Received`: Track delivery accuracy
- `Unit_Cost`: Track price changes over time
- `Order_Status`: pending, delivered, partial, cancelled
- `Payment_Status`: Track what's been paid

**Update Frequency**: When placing orders and when deliveries arrive

### 4. Suppliers_Template.csv
**Purpose**: Maintain supplier contact information and performance
**Key Fields**:
- `Lead_Time_Days`: How reliable are their delivery times
- `Min_Order_Value`: Minimum purchase requirements
- `Reliability_Rating`: 1-5 scale based on your experience
- `Payment_Terms`: Net 7, Net 15, Net 30, etc.

**Update Frequency**: As needed when supplier info changes

## How to Use These Templates

### Step 1: Import to Google Sheets
1. Go to Google Sheets (sheets.google.com)
2. Create a new spreadsheet
3. File → Import → Upload → Select the CSV file
4. Choose "Replace spreadsheet" and "Detect automatically"

### Step 2: Set Up Data Validation
- Use Data → Data validation for dropdown menus
- Set up date formatting for date columns
- Add conditional formatting to highlight low stock (red when Current_Stock < Min_Threshold)

### Step 3: Create Your Data Entry Routine
**Daily (5 minutes)**:
- Update Daily_Usage sheet with yesterday's consumption
- Quick check on Current_Inventory for any items running low

**Weekly (15 minutes)**:
- Review usage patterns 
- Update Current_Inventory stock levels
- Check for any needed orders

**When Ordering**:
- Add entries to Order_History when placing orders
- Update Order_History when deliveries arrive
- Update Current_Inventory with new stock levels

## Pro Tips for Success

### Make It Easy
- Keep templates simple - don't add complexity you won't use
- Use your phone to quickly jot notes during the day, then transfer to sheets later
- Set up shortcuts for common entries (like supplier names)

### Data Quality
- Be consistent with naming (e.g., always "Whole Milk", not sometimes "milk - whole")
- Don't worry about perfection - rough estimates are better than no data
- Track waste separately - it reveals important patterns

### Pattern Recognition
- Look for day-of-week patterns (Monday vs Saturday usage)
- Notice seasonal trends (iced drinks in summer)
- Track how weather affects sales
- Monitor supplier reliability over time

## Converting Your Existing Disorganized Sheets

If you have existing Google Sheets with supply data:

1. **Export your current data** as CSV files
2. **Map your current columns** to these template formats
3. **Clean up naming inconsistencies** (standardize product names)
4. **Fill in missing required fields** (like Min_Threshold, Lead_Time_Days)
5. **Import historical data** to the new templates to preserve ordering patterns

The cafe management app will eventually read directly from these Google Sheets to provide automated ordering recommendations and inventory alerts.