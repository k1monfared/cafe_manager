#!/usr/bin/env python3
"""Test the forecasting engine with multi-day data"""

from src.forecasting_engine import ForecastingEngine

def test_forecasting_with_multiday_data():
    # Initialize forecasting engine
    engine = ForecastingEngine()
    
    # Test usage pattern analysis
    patterns = engine.analyze_usage_patterns()
    print('=== Usage Patterns ===')
    for item_id, pattern in patterns.items():
        item_name = engine.inventory_items.get(item_id, {}).get('name', item_id)
        avg_usage = sum(pattern.daily_averages.values()) / len(pattern.daily_averages) if pattern.daily_averages else 0
        print(f'{item_name}: Average daily usage = {avg_usage:.2f} units')
        print(f'  Trend factor: {pattern.trend_factor:.2f}, Volatility: {pattern.volatility:.2f}')
    
    # Test order recommendations
    recommendations = engine.generate_order_recommendations()
    print(f'\n=== Order Recommendations ({len(recommendations)} items) ===')
    
    if not recommendations:
        print("No recommendations generated - checking data...")
        print(f"Inventory items: {len(engine.inventory_items)}")
        print(f"Usage history: {len(engine.usage_history)}")
        return
    
    for i, rec in enumerate(recommendations):
        if i >= 5:  # Show first 5
            break
        item_info = engine.inventory_items.get(rec.item_id, {})
        unit = item_info.get('unit', 'units')
        
        print(f'{rec.item_name}: {rec.urgency_level.upper()}')
        print(f'  Current stock: {rec.current_stock} {unit}')
        print(f'  Recommend ordering: {rec.recommended_quantity} {unit} (${rec.estimated_cost:.2f})')
        print(f'  Days until reorder: {rec.days_until_reorder}')
        print(f'  Reason: {rec.reasoning}')
        print()
    
    # Test inventory alerts
    alerts = engine.get_inventory_alerts()
    print(f'=== Inventory Alerts ({len(alerts)} items) ===')
    for alert in alerts[:3]:  # Show first 3 alerts
        print(f'{alert["item_name"]}: {alert["type"]} ({alert["severity"]}) - {alert["message"]}')

if __name__ == "__main__":
    test_forecasting_with_multiday_data()