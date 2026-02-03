import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_consumption_data(item_name, start_date, num_days, base_consumption, seasonality_amplitude=0.3, trend_rate=0.001, noise_level=0.2):
    """
    Generate consumption data with weekly seasonality, upward trend, and noise.
    
    Args:
        item_name: Name of the item
        start_date: Starting date (datetime object)
        num_days: Number of days to generate
        base_consumption: Base daily consumption amount
        seasonality_amplitude: Amplitude of weekly seasonality (0.3 = 30% variation)
        trend_rate: Daily trend increase rate (0.001 = 0.1% per day)
        noise_level: Random noise level (0.2 = 20% variation)
    
    Returns:
        List of tuples: (date, consumption)
    """
    np.random.seed(hash(item_name) % 2**32)
    
    consumption_data = []
    
    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        day_of_week = current_date.weekday()
        
        # Weekly seasonality (higher on weekends, lower on Mondays)
        seasonal_factor = 1 + seasonality_amplitude * np.sin((day_of_week + 1) * 2 * np.pi / 7 + np.pi/4)
        
        # Upward trend
        trend_factor = 1 + trend_rate * day
        
        # Random noise
        noise_factor = 1 + np.random.normal(0, noise_level)
        
        # Ensure consumption is positive
        consumption = max(0.1, base_consumption * seasonal_factor * trend_factor * noise_factor)
        
        consumption_data.append((current_date, round(consumption, 1)))
    
    return consumption_data

def generate_delivery_schedule(item_name, start_date, num_days, delivery_interval_days=10, delivery_amount_base=100, interval_noise_days=3, amount_noise=0.15):
    """
    Generate delivery schedule with some randomness in timing and amounts.
    
    Args:
        item_name: Name of the item
        start_date: Starting date (datetime object)
        num_days: Number of days to cover
        delivery_interval_days: Average days between deliveries
        delivery_amount_base: Base delivery amount
        interval_noise_days: Random variation in delivery timing (±days)
        amount_noise: Random variation in delivery amounts (percentage)
    
    Returns:
        Dictionary: {date: delivery_amount}
    """
    random.seed(hash(item_name) % 2**32)
    np.random.seed(hash(item_name) % 2**32)
    
    deliveries = {}
    current_day = random.randint(0, delivery_interval_days - 1)  # Random first delivery
    
    while current_day < num_days:
        delivery_date = start_date + timedelta(days=current_day)
        
        # Add noise to delivery amount
        amount_variation = 1 + np.random.normal(0, amount_noise)
        delivery_amount = max(1, delivery_amount_base * amount_variation)
        
        deliveries[delivery_date] = round(delivery_amount, 1)
        
        # Next delivery with some randomness
        next_interval = delivery_interval_days + random.randint(-interval_noise_days, interval_noise_days)
        current_day += max(7, next_interval)  # Minimum 7 days between deliveries
    
    return deliveries

def simulate_inventory(item_name, start_date, num_days, initial_stock, consumption_data, deliveries):
    """
    Simulate daily inventory levels based on consumption and deliveries.
    
    Returns:
        List of tuples: (date, stock_level)
    """
    inventory_data = []
    current_stock = initial_stock
    
    consumption_dict = {date: amount for date, amount in consumption_data}
    
    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        
        # Add delivery if scheduled
        delivery_amount = deliveries.get(current_date, 0)
        if delivery_amount > 0:
            current_stock += delivery_amount
        
        # Subtract consumption
        daily_consumption = consumption_dict.get(current_date, 0)
        current_stock = max(0, current_stock - daily_consumption)
        
        inventory_data.append((current_date, round(current_stock, 1)))
    
    return inventory_data

def generate_sample_data_for_items(items_config, start_date, num_weeks=4):
    """
    Generate sample data for multiple items.
    
    Args:
        items_config: List of dictionaries with item configuration
        start_date: Starting date
        num_weeks: Number of weeks to generate data for
    """
    num_days = num_weeks * 7
    all_consumption_data = []
    all_stock_data = []
    all_delivery_data = []
    
    for item_config in items_config:
        item_name = item_config['name']
        base_consumption = item_config['base_consumption']
        initial_stock = item_config['initial_stock']
        delivery_amount = item_config['delivery_amount']
        
        # Generate consumption data
        consumption_data = generate_consumption_data(
            item_name, start_date, num_days, base_consumption
        )
        
        # Generate delivery schedule
        deliveries = generate_delivery_schedule(
            item_name, start_date, num_days, 
            delivery_amount_base=delivery_amount
        )
        
        # Simulate inventory
        inventory_data = simulate_inventory(
            item_name, start_date, num_days, initial_stock, 
            consumption_data, deliveries
        )
        
        # Collect delivery data for export
        for delivery_date, del_amount in deliveries.items():
            all_delivery_data.append({
                'Date': delivery_date.strftime('%Y-%m-%d'),
                'Item_Name': item_name,
                'Delivery_Amount': round(del_amount, 1),
                'Notes': ''
            })

        # Prepare data for CSV
        for date, consumption in consumption_data:
            delivery_amount = deliveries.get(date, 0)
            
            # Find stock levels
            stock_after = next((stock for inv_date, stock in inventory_data if inv_date == date), 0)
            stock_before = stock_after + consumption - delivery_amount
            
            reasoning = f"Started with {stock_before}, "
            if delivery_amount > 0:
                reasoning += f"received {delivery_amount} delivery, "
            else:
                reasoning += "no deliveries, "
            reasoning += f"ended with {stock_after}"
            
            all_consumption_data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Item_Name': item_name,
                'Consumption': consumption,
                'Stock_Before_Delivery': stock_before,
                'Delivery_Amount': delivery_amount,
                'Previous_Stock': stock_after,
                'Reasoning': reasoning
            })
        
        # Add daily stock levels
        for inv_date, stock_level in inventory_data:
            all_stock_data.append({
                'Date': inv_date.strftime('%Y-%m-%d'),
                'Item_Name': item_name,
                'Current_Stock': int(max(0, stock_level))
            })
    
    return all_consumption_data, all_stock_data, all_delivery_data

if __name__ == "__main__":
    # Define sample items
    items_config = [
        {
            'name': 'Coffee Beans',
            'base_consumption': 25.0,
            'initial_stock': 150.0,
            'delivery_amount': 200.0
        },
        {
            'name': 'Milk',
            'base_consumption': 40.0,
            'initial_stock': 100.0,
            'delivery_amount': 150.0
        },
        {
            'name': 'Sugar',
            'base_consumption': 8.0,
            'initial_stock': 80.0,
            'delivery_amount': 100.0
        },
        {
            'name': 'Paper Cups',
            'base_consumption': 120.0,
            'initial_stock': 500.0,
            'delivery_amount': 1000.0
        },
        {
            'name': 'Pastries',
            'base_consumption': 15.0,
            'initial_stock': 50.0,
            'delivery_amount': 80.0
        }
    ]
    
    # Generate data for the last 4 weeks up to today
    start_date = (datetime.now() - timedelta(weeks=4)).replace(hour=0, minute=0, second=0, microsecond=0)

    consumption_data, stock_data, delivery_data = generate_sample_data_for_items(
        items_config, start_date, num_weeks=4
    )

    # Create DataFrames
    stock_df = pd.DataFrame(stock_data)
    delivery_df = pd.DataFrame(delivery_data).sort_values(['Item_Name', 'Date'])

    # Save to CSV files (stock and deliveries only -- consumption is derived by the engine)
    stock_df.to_csv(os.path.join('data', 'daily_stock_levels.csv'), index=False)
    delivery_df.to_csv(os.path.join('data', 'deliveries.csv'), index=False)

    print(f"Generated {len(stock_data)} stock level records")
    print(f"Generated {len(delivery_data)} delivery records")
    print("Data saved to data/daily_stock_levels.csv and data/deliveries.csv")