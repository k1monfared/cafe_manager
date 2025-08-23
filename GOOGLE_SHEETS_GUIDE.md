# 📊 Google Sheets Integration Guide

## 🎯 Overview
Your Cafe Supply Manager now works seamlessly with Google Sheets! This means you can:
- ✅ Keep your data in familiar Google Sheets
- ✅ Update inventory, usage, and orders in sheets
- ✅ Automatically sync to get smart recommendations
- ✅ No more editing complex JSON files!

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Your Templates
1. Open your cafe manager: http://localhost:5001
2. Click **"Google Sheets"** in the sidebar
3. Download the 4 template files:
   - **Inventory Template** - Your current stock levels
   - **Usage Template** - Daily consumption tracking
   - **Orders Template** - Purchase history
   - **Suppliers Template** - Vendor contact info

### Step 2: Set Up Google Sheets
1. Go to Google Sheets (sheets.google.com)
2. Create a **new spreadsheet** for each template
3. **Import each CSV**: File → Import → Upload → Choose file
4. Select "Replace spreadsheet" and "Detect automatically"

### Step 3: Customize Your Data
Replace the sample data with your real information:
- Update stock quantities to match what you actually have
- Add your daily usage patterns
- Include your real supplier contact information
- Add recent order history

### Step 4: Sync Back to Cafe Manager
1. **Export from Google Sheets**: File → Download → CSV
2. **Upload to Cafe Manager**: Go to Google Sheets page → Upload files
3. **Sync Data**: Click "Sync All Data"
4. **View Results**: Go to Dashboard to see your updated data

## 📋 Detailed Sheet Instructions

### 📦 Current Inventory Sheet

**Purpose**: Track what you have in stock right now

**Key Columns**:
- `Item_Name`: Exact product name (e.g., "Whole Milk", "12oz Paper Cups")
- `Category`: dairy, coffee, supplies, syrups, food
- `Current_Stock`: How much you have now
- `Min_Threshold`: When to reorder (usually 20% of max capacity)
- `Max_Capacity`: Maximum you can store
- `Cost_Per_Unit`: Current price per unit (no $ symbol)
- `Supplier`: Which supplier you buy from

**Example Row**:
```
Whole Milk | dairy | gallons | 15 | 5 | 30 | 4.25 | Metro Dairy Supply
```

**Tips**:
- ✅ Use consistent naming (always "Whole Milk", not sometimes "milk - whole")
- ✅ Update stock levels weekly
- ✅ Set realistic min/max thresholds

### 📈 Daily Usage Sheet

**Purpose**: Track what you use each day to identify patterns

**Key Columns**:
- `Date`: YYYY-MM-DD format (e.g., 2025-08-23)
- `Item_Name`: Must match exactly with inventory sheet
- `Quantity_Used`: Amount consumed (same units as inventory)
- `Waste_Amount`: Amount spoiled/discarded
- `Sales_Count`: Number of drinks/items sold
- `Weather`: Sunny, Rainy, Cloudy (affects sales)
- `Notes`: Special circumstances

**Example Row**:
```
2025-08-23 | Whole Milk | 3.2 | 0.1 | 85 | Sunny | | Busy Friday
```

**Tips**:
- ✅ Enter data daily (takes 2 minutes)
- ✅ Track waste separately - reveals important patterns  
- ✅ Note weather and events - they affect usage
- ✅ Don't worry about perfection - estimates are fine

### 🛒 Order History Sheet

**Purpose**: Track past orders to learn your buying patterns

**Key Columns**:
- `Order_Date`: When you placed the order
- `Supplier_Name`: Must match supplier sheet
- `Item_Name`: What you ordered
- `Quantity_Ordered` vs `Quantity_Received`: Track delivery accuracy
- `Unit_Cost`: Price per unit for this order
- `Order_Status`: delivered, pending, partial, cancelled
- `Payment_Status`: paid, pending, overdue

**Example Row**:
```
2025-08-15 | Metro Dairy Supply | Whole Milk | 20 | 20 | 4.25 | delivered | paid
```

**Tips**:
- ✅ Add entries when you place orders
- ✅ Update when deliveries arrive
- ✅ Track price changes over time
- ✅ Note any delivery issues

### 🏢 Suppliers Sheet

**Purpose**: Manage vendor contact information and terms

**Key Columns**:
- `Supplier_Name`: Business name
- `Phone` & `Email`: Contact information
- `Lead_Time_Days`: Days from order to delivery
- `Min_Order_Value`: Minimum purchase requirement
- `Payment_Terms`: Net 7, Net 15, Net 30, etc.
- `Reliability_Rating`: 1-5 stars (your experience)
- `Specialty`: What they supply

**Example Row**:
```
Metro Dairy Supply | (555) 234-5678 | orders@metro.com | 1 | 200 | Net 15 | 5 | Dairy products
```

## 🔄 Daily Workflow (5 minutes/day)

### Morning (2 minutes)
1. Check cafe manager dashboard for alerts
2. Note any critical items needing immediate orders

### End of Day (3 minutes)
1. Open your Daily Usage Google Sheet
2. Add today's consumption for key items:
   - How much milk/coffee/cups used
   - Any waste or spoilage
   - Number of drinks sold
   - Weather conditions
3. Save the sheet

### Weekly (15 minutes)
1. Update Current Inventory with actual counts
2. Export all sheets as CSV
3. Upload to cafe manager and sync
4. Review recommendations and place orders

## 🎯 Pro Tips for Success

### Start Simple
- **Week 1**: Track only your top 5 items (milk, coffee, cups, etc.)
- **Week 2**: Add 5 more items once you're comfortable
- **Week 3**: Add remaining items and fine-tune thresholds

### Data Quality Tips
- ✅ **Consistent naming**: Always use exact same spelling
- ✅ **Regular updates**: Weekly inventory counts are sufficient
- ✅ **Realistic thresholds**: Set minimums based on actual usage
- ✅ **Track patterns**: Note busy days, weather, events

### Common Mistakes to Avoid
- ❌ **Inconsistent names**: "Oat Milk" vs "oat milk" vs "Oatmilk"
- ❌ **Wrong units**: Mixing gallons and bottles for same item
- ❌ **Unrealistic thresholds**: Min too high/low for actual usage
- ❌ **Ignoring waste**: Spoilage reveals storage/ordering issues

## 🔧 Troubleshooting

### "Item not found" errors
- Check spelling matches exactly between sheets
- Remove extra spaces or special characters
- Use consistent capitalization

### Wrong recommendations
- Verify min/max thresholds are realistic
- Check that usage data is complete
- Ensure supplier lead times are accurate

### Upload/sync failures
- Ensure files are saved as CSV format
- Check that all required columns are present
- Verify date format is YYYY-MM-DD

### Missing data
- System handles gaps gracefully
- Rough estimates are better than no data
- Focus on high-value items first

## 📊 Understanding Your Reports

### Dashboard Colors
- 🔴 **Critical (Red)**: Order immediately
- 🟡 **Warning (Orange)**: Order this week
- 🟢 **Normal (Green)**: On schedule
- 🔵 **Stock Up (Blue)**: Good time for bulk orders

### Usage Analysis
- **Day patterns**: Monday vs weekend usage
- **Trends**: Growing or declining demand
- **Volatility**: How predictable each item is
- **Insights**: Personalized recommendations

### Order Recommendations
- **Why**: Clear reasoning for each suggestion
- **When**: Based on your typical ordering frequency
- **How much**: Optimized quantities
- **Cost**: Budget estimates

## 🎉 Success Metrics

After 30 days of using this system, you should see:
- ⏱️ **Time savings**: 5 minutes for ordering decisions vs 30 minutes
- 📉 **Reduced waste**: Better prediction of needs
- 💰 **Cost optimization**: Bulk ordering opportunities identified
- 😌 **Less stress**: Never run out of critical items unexpectedly

## 🆘 Need Help?

1. **Built-in Help**: Click "Help" in the cafe manager
2. **Sample Data**: Use the provided examples as templates
3. **Start Simple**: Begin with 3-5 items and expand gradually
4. **Be Patient**: System learns and improves with more data

Remember: This system is designed to learn YOUR patterns and get smarter over time. Don't expect perfection on day one - it will improve as you add more data!