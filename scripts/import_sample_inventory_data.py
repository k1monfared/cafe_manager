#!/usr/bin/env python3
"""
Import multi-day sample inventory data to demonstrate the system
"""

import json
import csv
from datetime import datetime
from usage_calculator import UsageCalculator

def import_daily_inventory_from_csv(csv_file_path="static/templates/daily_inventory_template.csv"):
    """Import daily inventory data from CSV and create snapshots"""
    
    # Initialize usage calculator
    calculator = UsageCalculator()
    calculator.load_data()
    
    # Read CSV data
    inventory_by_date = {}
    
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Skip instruction row
            if '📝 INSTRUCTIONS' in row.get('Date', ''):
                continue
                
            date = row['Date'].strip()
            item_name = row['Item_Name'].strip()
            
            # Skip if no valid date
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                continue
                
            # Find item_id from item name
            item_id = get_item_id_by_name(item_name)
            if not item_id:
                print(f"Warning: Could not find item_id for '{item_name}', skipping")
                continue
            
            # Parse data
            current_stock = float(row['Current_Stock']) if row['Current_Stock'] else 0.0
            waste_amount = float(row['Waste_Amount']) if row['Waste_Amount'] else 0.0
            deliveries = float(row['Deliveries_Received']) if row['Deliveries_Received'] else 0.0
            notes = row['Notes'].strip()
            
            # Group by date
            if date not in inventory_by_date:
                inventory_by_date[date] = []
                
            inventory_by_date[date].append({
                "item_id": item_id,
                "stock_level": current_stock,
                "waste_amount": waste_amount,
                "deliveries_received": deliveries,
                "notes": notes
            })
    
    # Import data for each date
    dates_processed = 0
    for date in sorted(inventory_by_date.keys()):
        inventory_data = inventory_by_date[date]
        
        print(f"Importing inventory data for {date} ({len(inventory_data)} items)")
        success = calculator.add_inventory_snapshot(date, inventory_data)
        
        if success:
            dates_processed += 1
            print(f"  ✓ Successfully saved inventory snapshot for {date}")
        else:
            print(f"  ✗ Failed to save inventory snapshot for {date}")
    
    # Calculate usage and update daily_usage.json
    print("\nCalculating usage from inventory snapshots...")
    records_updated = calculator.update_daily_usage_file()
    
    print(f"\n=== Import Summary ===")
    print(f"Dates processed: {dates_processed}")
    print(f"Usage records created: {records_updated}")
    
    return dates_processed, records_updated

def get_item_id_by_name(item_name):
    """Get item_id from item name by looking up in inventory_items.json"""
    try:
        with open('sample_data/inventory_items.json', 'r') as f:
            items = json.load(f)
        
        for item in items:
            if item.get('name', '').lower() == item_name.lower():
                return item.get('item_id')
        
        # If exact match not found, try partial match
        for item in items:
            if item_name.lower() in item.get('name', '').lower():
                return item.get('item_id')
                
    except FileNotFoundError:
        print("Error: inventory_items.json not found")
    
    return None

def create_realistic_order_history():
    """Create order history that matches the deliveries in our inventory data"""
    
    orders = []
    
    # Monday delivery (matches our CSV data)
    orders.append({
        "order_id": "ORD-2025-08-19-001",
        "order_date": "2025-08-18",
        "supplier_id": "SUP002",
        "delivery_date": "2025-08-19",
        "total_cost": 287.0,
        "status": "delivered",
        "line_items": [
            {
                "item_id": "ITEM002",  # Whole Milk
                "quantity_ordered": 20.0,
                "quantity_received": 20.0,
                "unit_cost": 4.25,
                "line_total": 85.0
            },
            {
                "item_id": "ITEM003",  # House Blend Coffee
                "quantity_ordered": 10.0,
                "quantity_received": 10.0,
                "unit_cost": 8.50,
                "line_total": 85.0
            },
            {
                "item_id": "ITEM004",  # Paper Cups
                "quantity_ordered": 5.0,
                "quantity_received": 5.0,
                "unit_cost": 42.0,
                "line_total": 210.0
            },
            {
                "item_id": "ITEM005",  # Vanilla Syrup
                "quantity_ordered": 6.0,
                "quantity_received": 6.0,
                "unit_cost": 9.25,
                "line_total": 55.5
            }
        ]
    })
    
    # Save to order history
    try:
        with open('sample_data/order_history.json', 'w') as f:
            json.dump(orders, f, indent=2)
        print("Created realistic order history")
        return True
    except Exception as e:
        print(f"Error creating order history: {e}")
        return False

def main():
    """Main function to import all sample data"""
    print("=== Importing Multi-Day Sample Inventory Data ===\n")
    
    # Create realistic order history first
    create_realistic_order_history()
    
    # Import inventory snapshots from CSV
    dates_processed, records_updated = import_daily_inventory_from_csv()
    
    if dates_processed > 0:
        print("\n🎉 Sample data imported successfully!")
        print("\nWhat you can now see:")
        print("- Multiple days of inventory snapshots")
        print("- Automatically calculated usage patterns")
        print("- Realistic forecasting recommendations")
        print("- Stock level trends over time")
        print("\nYou can now:")
        print("1. Visit the Dashboard to see current status")
        print("2. Check Order Recommendations for what to buy")
        print("3. View Usage Analysis to see patterns")
        print("4. Use Daily Inventory to add today's counts")
    else:
        print("\n❌ No data was imported. Please check the CSV file format.")

if __name__ == "__main__":
    main()