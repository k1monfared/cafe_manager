# Cafe Manager - Simple CSV-Based Inventory System

A simplified inventory management system that uses CSV files as the single source of truth for easy auditing and transparency.

## Core Features

- **CSV-First Architecture**: All data stored in auditable CSV files
- **Automatic Consumption Calculation**: consumption = previous_stock + deliveries - current_stock  
- **Simple Forecasting**: Average daily consumption and runout predictions
- **Interactive Analytics**: Charts showing last 14 days of consumption patterns
- **Explainable Recommendations**: Detailed reasoning for all purchase suggestions

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python simple_app.py
   ```

3. Open browser to http://localhost:5000

## Data Files

- `data/daily_stock_levels.csv` - Daily stock counts (user input)
- `data/deliveries.csv` - Delivery records (user input)  
- `data/item_info.csv` - Item configuration (thresholds, capacity, etc.)
- `data/daily_consumption.csv` - Calculated daily usage (auto-generated)
- `data/forecast_results.csv` - Forecast data with chart data (auto-generated)
- `data/recommendations.csv` - Purchase recommendations (auto-generated)

## Usage

1. **Dashboard**: View current stock levels and key metrics
2. **Stock Entry**: Add daily stock counts
3. **Delivery Entry**: Record deliveries  
4. **Analytics**: View consumption charts and forecasts
5. **Recommendations**: See purchase recommendations with detailed explanations

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