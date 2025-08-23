# ☕ Cafe Supply Manager

A simple, intelligent inventory management system designed specifically for coffee shops. Track your supplies, predict usage patterns, and get smart ordering recommendations - all without complex integrations.

## 🚀 Quick Start (Non-Technical Users)

### Windows Users:
1. **Download Python**: Go to https://python.org and download Python 3.8 or newer
2. **Download this folder** to your computer 
3. **Double-click** `run_cafe_manager.py` - it will handle everything automatically!
4. **Your web browser** will open to http://localhost:5000

### Mac/Linux Users:
1. Open Terminal
2. Navigate to this folder: `cd path/to/cafe_manager`
3. Run: `python3 run_cafe_manager.py`
4. Open http://localhost:5000 in your browser

**That's it!** The system will install what it needs and start automatically.

## 📊 What This System Does

### Smart Order Recommendations
- **Analyzes your usage patterns** (Monday vs Saturday, seasonal trends)
- **Predicts when you'll run out** of each item
- **Suggests what to order and when** based on your typical buying patterns
- **Shows reasoning** for each recommendation so you understand the "why"

### Inventory Management  
- **Track current stock levels** for all your supplies
- **Set minimum/maximum thresholds** for each item
- **Get alerts** when items are running low
- **See usage predictions** for the next 7-14 days

### Usage Analysis
- **Identify patterns** in your daily consumption
- **Track waste separately** from normal usage
- **Correlate usage with sales volume** and weather
- **Spot trends** - growing or declining demand

### Easy Data Entry
- **Google Sheets integration** - enter data where you're comfortable
- **CSV templates provided** for organized data collection
- **Handles missing data gracefully** - estimates are better than no data
- **Converts your existing messy spreadsheets** to organized format

## 📁 Project Structure

```
cafe_manager/
├── 🚀 run_cafe_manager.py          # Easy startup script (click this!)
├── 🌐 app.py                       # Web application
├── 📊 src/forecasting_engine.py    # Smart forecasting logic
├── 📋 google_sheets_templates/     # Templates for Google Sheets
│   ├── current_inventory_template.csv
│   ├── daily_usage_template.csv
│   ├── order_history_template.csv
│   ├── suppliers_template.csv
│   └── README_Templates.md
├── 🎯 sample_data/                 # Sample data to get started
│   ├── inventory_items.json
│   ├── suppliers.json
│   ├── daily_usage.json
│   └── order_history.json
├── 🎨 templates/                   # Web interface files
│   ├── base.html
│   ├── dashboard.html
│   ├── recommendations.html
│   ├── inventory.html
│   └── help.html
├── 📦 requirements.txt             # Required Python packages
└── 📖 README.md                   # This file
```

## 🎯 Key Features

### 1. Dashboard Overview
- **At-a-glance status** of all your inventory
- **Critical, warning, and normal items** clearly categorized
- **Total estimated ordering costs**
- **Recent order history**

### 2. Order Recommendations Page
- **Prioritized by urgency** - handle critical items first
- **Detailed reasoning** for each recommendation
- **Cost estimates** for budgeting
- **Export to CSV** for easy ordering

### 3. Current Inventory Page
- **Real-time stock levels** with visual indicators
- **Usage predictions** for planning
- **Days until empty** calculations
- **Filter and search** functionality

### 4. Usage Analysis
- **Day-of-week patterns** - see Monday vs weekend differences
- **Trend analysis** - growing or declining usage
- **Volatility measurements** - how predictable each item is

## 📈 How The Smart Forecasting Works

### Pattern Recognition
- **Learns your ordering frequency** - coffee every 2 weeks, milk every 3 days
- **Recognizes day-of-week patterns** - busy Fridays, slow Sundays  
- **Tracks seasonal trends** - iced drinks in summer
- **Adapts to changes** - growing popularity of oat milk

### Prediction Calculations
- **Current Stock - (Daily Usage × Lead Time) = Reorder Point**
- **Typical Order Frequency + Current Trends = Recommended Quantity**
- **Supplier Lead Time + Usage Rate = Order Timing**
- **Historical Patterns + Recent Changes = Future Demand**

### Handles Missing Data
- **Estimates missing days** based on similar days
- **Uses overall averages** when specific patterns aren't available
- **Improves over time** as you add more data
- **Provides confidence levels** for its recommendations

## 🛠 Customization

### Adjusting Thresholds
Edit the inventory data to set your preferred:
- **Minimum stock levels** (when to reorder)
- **Maximum capacity** (storage limits)
- **Lead times** (supplier delivery schedules)

### Adding New Items
Simply add new rows to your Google Sheets templates with:
- Item name and category
- Current stock and thresholds  
- Supplier and cost information
- Usage history (even just a few days helps)

### Connecting Your Google Sheets
The system is designed to eventually read directly from Google Sheets. For now:
1. Use the provided CSV templates
2. Export your Google Sheets as CSV
3. Place them in the `sample_data` directory
4. Restart the application

## 📞 Getting Help

### Built-in Help
- **Help page** in the application with detailed instructions
- **Sample data** showing the expected format
- **Template README** with step-by-step instructions

### Common Questions

**Q: What if I don't have much historical data?**
A: Start with rough estimates! Even 3-5 days of data helps. The system improves quickly.

**Q: Do I need to track everything perfectly?**
A: No! Focus on your biggest cost items first (coffee beans, milk). Add others gradually.

**Q: What if the recommendations seem wrong?**
A: Check your minimum thresholds and supplier lead times. The system learns from your data.

**Q: Can I use this on my phone?**
A: Yes! The web interface works on mobile devices. You can check recommendations anywhere.

## 🔧 Technical Details (For Developers)

### Technology Stack
- **Backend**: Python Flask web framework
- **Frontend**: Bootstrap 5 + vanilla JavaScript  
- **Data**: JSON files (easily replaceable with databases)
- **Forecasting**: Custom algorithms using statistical analysis

### Key Algorithms
- **Usage Pattern Recognition**: Day-of-week analysis with trend factors
- **Reorder Point Calculation**: Safety stock + lead time demand
- **Order Frequency Analysis**: Historical interval analysis with volatility
- **Demand Forecasting**: Exponential smoothing with seasonal adjustments

### Extending the System
- **Database Integration**: Replace JSON files with SQLite/PostgreSQL
- **Google Sheets API**: Direct integration for real-time sync
- **Mobile App**: React Native wrapper around the web interface
- **Advanced Analytics**: Machine learning for more sophisticated predictions

## 📄 License

This project is designed to help small coffee shop owners manage their inventory more effectively. Feel free to use, modify, and share!

## 🤝 Contributing

Found a bug or have a feature request? This system is designed to be simple and focused, but improvements are always welcome!

---

**Built with ❤️ for coffee shop owners who want to focus on great coffee, not spreadsheets!**