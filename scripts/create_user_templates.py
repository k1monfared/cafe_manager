#!/usr/bin/env python3
"""
Create User-Friendly Templates from Real Data
Takes the converted real data and creates easy-to-use Google Sheets templates
"""

import json
import csv
import os
from datetime import datetime, timedelta
import random

def load_real_data():
    """Load the converted real cafe data"""
    with open('sample_data/inventory_items.json', 'r') as f:
        inventory = json.load(f)
    
    with open('sample_data/suppliers.json', 'r') as f:
        suppliers = json.load(f)
    
    return inventory, suppliers

def create_inventory_template(inventory_items):
    """Create user-friendly current inventory template"""
    template_file = 'static/templates/current_inventory_template.csv'
    
    # Select the most important items (limit to 30 for manageability)
    priority_categories = ['dairy', 'coffee', 'supplies']
    important_items = []
    
    # Get items from priority categories first
    for category in priority_categories:
        category_items = [item for item in inventory_items if item['category'] == category]
        # Sort by stock level (higher stock = more important)
        category_items.sort(key=lambda x: x['current_stock'], reverse=True)
        important_items.extend(category_items[:10])  # Top 10 from each category
    
    # Remove duplicates and limit to 25 items
    seen_names = set()
    final_items = []
    for item in important_items:
        if item['name'] not in seen_names and len(final_items) < 25:
            seen_names.add(item['name'])
            final_items.append(item)
    
    # Write CSV template
    with open(template_file, 'w', newline='') as csvfile:
        fieldnames = [
            'Item_Name', 'Category', 'Unit', 'Current_Stock', 
            'Min_Threshold', 'Max_Capacity', 'Cost_Per_Unit', 
            'Supplier', 'Lead_Time_Days', 'Shelf_Life_Days', 
            'Storage_Requirements', 'Last_Updated'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Add instruction row
        writer.writerow({
            'Item_Name': '📝 INSTRUCTIONS: Replace this row with your real data. Keep column names unchanged.',
            'Category': 'dairy, coffee, supplies, syrups, etc',
            'Unit': 'lbs, gallons, cases, bottles, pieces',
            'Current_Stock': 'How much you have now',
            'Min_Threshold': 'When to reorder (usually 20% of max)',
            'Max_Capacity': 'Maximum you can store',
            'Cost_Per_Unit': 'Price per unit (no $ symbol)',
            'Supplier': 'Supplier name',
            'Lead_Time_Days': 'Days for delivery',
            'Shelf_Life_Days': 'Days before expiring',
            'Storage_Requirements': 'Cool dry place, refrigerated, etc',
            'Last_Updated': 'Today\'s date'
        })
        
        # Add real data examples
        for item in final_items:
            # Map supplier ID to name
            supplier_name = 'Unknown Supplier'
            if item['supplier_id'] == 'SUP001':
                supplier_name = 'Metro Dairy Supply'
            elif item['supplier_id'] == 'SUP003':
                supplier_name = 'Flavor Solutions Inc'
            elif item['supplier_id'] == 'SUP004':
                supplier_name = 'Pacific Coffee Roasters'
            elif item['supplier_id'] == 'SUP005':
                supplier_name = 'Restaurant Supply Co'
            
            writer.writerow({
                'Item_Name': item['name'],
                'Category': item['category'],
                'Unit': item['unit'],
                'Current_Stock': item['current_stock'],
                'Min_Threshold': item['min_threshold'],
                'Max_Capacity': item['max_capacity'],
                'Cost_Per_Unit': item['cost_per_unit'],
                'Supplier': supplier_name,
                'Lead_Time_Days': item['lead_time_days'],
                'Shelf_Life_Days': item['shelf_life_days'],
                'Storage_Requirements': item['storage_requirements'],
                'Last_Updated': datetime.now().strftime('%Y-%m-%d')
            })
    
    print(f"✅ Created inventory template with {len(final_items)} items")
    return len(final_items)

def create_daily_usage_template(inventory_items):
    """Create daily usage template with sample data"""
    template_file = 'static/templates/daily_usage_template.csv'
    
    # Get most commonly used items
    high_usage_items = [
        item for item in inventory_items 
        if item['category'] in ['dairy', 'coffee', 'supplies'] 
        and item['current_stock'] > 5  # Items with decent stock levels
    ][:15]  # Top 15 items
    
    with open(template_file, 'w', newline='') as csvfile:
        fieldnames = [
            'Date', 'Item_Name', 'Quantity_Used', 'Waste_Amount', 
            'Sales_Count', 'Weather', 'Day_Of_Week', 'Special_Events', 'Notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Add instruction row
        writer.writerow({
            'Date': '📝 INSTRUCTIONS: Enter date as YYYY-MM-DD (e.g., 2025-08-23)',
            'Item_Name': 'Exact item name from inventory',
            'Quantity_Used': 'Amount consumed (same units as inventory)',
            'Waste_Amount': 'Amount spoiled/discarded',
            'Sales_Count': 'Number of drinks/items sold',
            'Weather': 'Sunny, Rainy, Cloudy, etc',
            'Day_Of_Week': 'Monday, Tuesday, etc (optional)',
            'Special_Events': 'Holidays, events, etc (optional)',
            'Notes': 'Any special notes'
        })
        
        # Create sample usage data for the last week
        end_date = datetime.now()
        
        for days_back in range(7, 0, -1):  # Last 7 days
            current_date = end_date - timedelta(days=days_back)
            date_str = current_date.strftime('%Y-%m-%d')
            day_name = current_date.strftime('%A')
            
            # Weekend vs weekday patterns
            is_weekend = current_date.weekday() >= 5
            base_multiplier = 0.6 if is_weekend else 1.0
            
            # Generate usage for a few key items each day
            sample_items = random.sample(high_usage_items, 3)
            
            for item in sample_items:
                # Simulate realistic usage based on item type
                if item['category'] == 'dairy':
                    base_usage = random.uniform(2, 6) * base_multiplier
                    waste = random.uniform(0, base_usage * 0.1)
                    sales = int(random.uniform(30, 100) * base_multiplier)
                elif item['category'] == 'coffee':
                    base_usage = random.uniform(1, 3) * base_multiplier
                    waste = random.uniform(0, base_usage * 0.05)
                    sales = int(random.uniform(50, 120) * base_multiplier)
                elif item['category'] == 'supplies':
                    base_usage = random.uniform(0.5, 2) * base_multiplier
                    waste = 0  # Supplies don't spoil
                    sales = int(random.uniform(40, 90) * base_multiplier)
                else:
                    base_usage = random.uniform(0.5, 2) * base_multiplier
                    waste = random.uniform(0, base_usage * 0.05)
                    sales = int(random.uniform(20, 60) * base_multiplier)
                
                # Weather effects
                weather_options = ['Sunny', 'Cloudy', 'Rainy']
                weather = random.choice(weather_options)
                if weather == 'Rainy':
                    base_usage *= 1.1  # People drink more coffee when it's rainy
                
                notes = ""
                if is_weekend:
                    notes = f"Quiet {day_name}"
                elif day_name == "Friday":
                    notes = "Busy Friday"
                
                writer.writerow({
                    'Date': date_str,
                    'Item_Name': item['name'],
                    'Quantity_Used': f"{base_usage:.1f}",
                    'Waste_Amount': f"{waste:.1f}",
                    'Sales_Count': sales,
                    'Weather': weather,
                    'Day_Of_Week': day_name,
                    'Special_Events': '',
                    'Notes': notes
                })
    
    print(f"✅ Created daily usage template with sample data for last 7 days")

def create_order_history_template(inventory_items, suppliers):
    """Create order history template with realistic order data"""
    template_file = 'static/templates/order_history_template.csv'
    
    with open(template_file, 'w', newline='') as csvfile:
        fieldnames = [
            'Order_Date', 'Supplier_Name', 'Item_Name', 'Quantity_Ordered',
            'Quantity_Received', 'Unit_Cost', 'Total_Cost', 'Delivery_Date',
            'Order_Status', 'Payment_Status', 'Notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Add instruction row
        writer.writerow({
            'Order_Date': '📝 INSTRUCTIONS: Enter as YYYY-MM-DD',
            'Supplier_Name': 'Exact supplier name',
            'Item_Name': 'Item ordered',
            'Quantity_Ordered': 'How much you ordered',
            'Quantity_Received': 'How much actually delivered',
            'Unit_Cost': 'Cost per unit (no $ symbol)',
            'Total_Cost': 'Total line cost',
            'Delivery_Date': 'When order arrived',
            'Order_Status': 'delivered, pending, partial, cancelled',
            'Payment_Status': 'paid, pending, overdue',
            'Notes': 'Any special notes'
        })
        
        # Create sample orders for the last 2 months
        end_date = datetime.now()
        
        # Group suppliers by their specialties
        supplier_map = {sup['supplier_id']: sup['name'] for sup in suppliers}
        
        # Create realistic orders
        order_dates = []
        current_date = end_date - timedelta(days=60)  # Start 2 months ago
        
        # Generate order dates (roughly weekly for each supplier)
        while current_date <= end_date:
            if random.random() < 0.3:  # 30% chance of order on any given day
                order_dates.append(current_date)
            current_date += timedelta(days=1)
        
        for order_date in order_dates[-10:]:  # Last 10 orders
            # Pick a random supplier
            supplier = random.choice(suppliers)
            supplier_name = supplier['name']
            
            # Pick items that match this supplier
            supplier_items = [
                item for item in inventory_items 
                if item['supplier_id'] == supplier['supplier_id']
            ]
            
            if not supplier_items:
                continue
            
            # Order 1-3 items from this supplier
            order_items = random.sample(supplier_items, min(3, len(supplier_items)))
            
            for item in order_items:
                quantity = random.uniform(5, 50)
                unit_cost = item['cost_per_unit'] + random.uniform(-2, 2)  # Price variation
                unit_cost = max(1, unit_cost)  # Minimum $1
                total_cost = quantity * unit_cost
                
                delivery_date = order_date + timedelta(days=supplier['lead_time_days'])
                
                # Most orders are delivered successfully
                status = random.choice(['delivered', 'delivered', 'delivered', 'pending'])
                payment_status = 'paid' if status == 'delivered' else 'pending'
                
                writer.writerow({
                    'Order_Date': order_date.strftime('%Y-%m-%d'),
                    'Supplier_Name': supplier_name,
                    'Item_Name': item['name'],
                    'Quantity_Ordered': f"{quantity:.1f}",
                    'Quantity_Received': f"{quantity:.1f}" if status == 'delivered' else "0",
                    'Unit_Cost': f"{unit_cost:.2f}",
                    'Total_Cost': f"{total_cost:.2f}",
                    'Delivery_Date': delivery_date.strftime('%Y-%m-%d'),
                    'Order_Status': status,
                    'Payment_Status': payment_status,
                    'Notes': 'Regular order' if status == 'delivered' else 'Pending delivery'
                })
    
    print(f"✅ Created order history template with sample orders")

def create_suppliers_template(suppliers):
    """Create suppliers template"""
    template_file = 'static/templates/suppliers_template.csv'
    
    with open(template_file, 'w', newline='') as csvfile:
        fieldnames = [
            'Supplier_Name', 'Contact_Person', 'Phone', 'Email', 'Address',
            'Lead_Time_Days', 'Min_Order_Value', 'Payment_Terms', 
            'Reliability_Rating', 'Specialty', 'Notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Add instruction row
        writer.writerow({
            'Supplier_Name': '📝 INSTRUCTIONS: Enter supplier business name',
            'Contact_Person': 'Your sales rep name (optional)',
            'Phone': 'Main phone number',
            'Email': 'Orders email address',
            'Address': 'Business address (optional)',
            'Lead_Time_Days': 'Days from order to delivery',
            'Min_Order_Value': 'Minimum order amount (no $ symbol)',
            'Payment_Terms': 'Net 7, Net 15, Net 30, etc',
            'Reliability_Rating': '1-5 stars (5 = most reliable)',
            'Specialty': 'What they supply',
            'Notes': 'Any special notes'
        })
        
        # Add real suppliers as examples
        for supplier in suppliers:
            writer.writerow({
                'Supplier_Name': supplier['name'],
                'Contact_Person': 'Sales Rep',  # Generic since we don't have real names
                'Phone': supplier['contact_phone'],
                'Email': supplier['contact_email'],
                'Address': '',  # We don't have addresses
                'Lead_Time_Days': supplier['lead_time_days'],
                'Min_Order_Value': supplier['minimum_order_value'],
                'Payment_Terms': supplier['payment_terms'],
                'Reliability_Rating': supplier['reliability_rating'],
                'Specialty': supplier['specialty'],
                'Notes': 'Update with your actual supplier info'
            })
    
    print(f"✅ Created suppliers template with {len(suppliers)} suppliers")

def main():
    print("📊 Creating User-Friendly Templates from Your Real Data")
    print("=" * 60)
    
    # Load real data
    print("📂 Loading your real cafe data...")
    inventory, suppliers = load_real_data()
    print(f"   Found {len(inventory)} inventory items and {len(suppliers)} suppliers")
    
    # Create templates
    print("\n🔨 Creating templates...")
    create_inventory_template(inventory)
    create_daily_usage_template(inventory)
    create_order_history_template(inventory, suppliers)
    create_suppliers_template(suppliers)
    
    print(f"\n🎉 Templates created successfully!")
    print("📁 Files created in static/templates/:")
    print("   - current_inventory_template.csv")
    print("   - daily_usage_template.csv")
    print("   - order_history_template.csv")
    print("   - suppliers_template.csv")
    
    print(f"\n📋 Next steps:")
    print("   1. Go to the Google Sheets page in your cafe manager")
    print("   2. Download these templates")
    print("   3. Import them into Google Sheets")
    print("   4. Replace the sample data with your real current data")
    print("   5. Export as CSV and upload back to the cafe manager")

if __name__ == "__main__":
    main()