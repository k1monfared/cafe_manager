#!/usr/bin/env python3
"""
Filter and Clean Converted Data
Takes the converted data and creates a focused, manageable dataset for a cafe
"""

import json
from collections import defaultdict

def load_converted_data(filepath):
    """Load the converted inventory data"""
    with open(filepath, 'r') as f:
        return json.load(f)

def filter_cafe_essentials(inventory_data):
    """Filter for essential cafe items only"""
    
    # Define keywords for essential cafe items
    essential_keywords = {
        'dairy': ['milk', 'cream', 'half', 'oat', 'almond', 'soy'],
        'coffee': ['coffee', 'bean', 'espresso', 'roast'],
        'supplies': ['cup', 'lid', 'napkin', 'straw', 'bag', 'sleeve'],
        'syrups': ['syrup', 'vanilla', 'caramel', 'hazelnut'],
        'pastries': ['muffin', 'croissant', 'scone', 'bagel', 'danish'],
        'beverages': ['tea', 'chai', 'hot chocolate', 'matcha'],
        'food': ['sandwich', 'wrap', 'quiche', 'salad']
    }
    
    filtered_items = []
    seen_names = set()
    
    for item in inventory_data:
        item_name_lower = item['name'].lower()
        
        # Check if item matches any essential keywords
        is_essential = False
        for category, keywords in essential_keywords.items():
            if any(keyword in item_name_lower for keyword in keywords):
                is_essential = True
                # Update category
                item['category'] = category
                if category == 'dairy':
                    item['unit'] = 'gallons' if 'gallon' in item_name_lower else 'bottles'
                    item['shelf_life_days'] = 14
                elif category == 'coffee':
                    item['unit'] = 'lbs'
                    item['shelf_life_days'] = 365
                elif category == 'supplies':
                    item['unit'] = 'cases'
                    item['shelf_life_days'] = 730
                elif category == 'syrups':
                    item['unit'] = 'bottles'
                    item['shelf_life_days'] = 180
                break
        
        # Avoid duplicates
        if is_essential and item['name'] not in seen_names:
            # Consolidate similar items
            consolidated_name = consolidate_name(item['name'])
            if consolidated_name not in seen_names:
                item['name'] = consolidated_name
                filtered_items.append(item)
                seen_names.add(consolidated_name)
    
    return filtered_items

def consolidate_name(name):
    """Consolidate similar item names"""
    name_lower = name.lower()
    
    # Consolidation rules
    if 'whole milk' in name_lower or 'milk - whole' in name_lower:
        return 'Whole Milk'
    elif 'low fat' in name_lower or '2%' in name_lower:
        return '2% Milk'
    elif 'oat milk' in name_lower or 'milk - oat' in name_lower:
        return 'Oat Milk'
    elif 'almond milk' in name_lower:
        return 'Almond Milk'
    elif 'coffee' in name_lower and ('bean' in name_lower or 'ground' in name_lower):
        if 'dark' in name_lower or 'bold' in name_lower:
            return 'Dark Roast Coffee Beans'
        elif 'light' in name_lower:
            return 'Light Roast Coffee Beans'
        else:
            return 'Medium Roast Coffee Beans'
    elif 'cup' in name_lower and '12' in name_lower:
        return '12oz Paper Cups'
    elif 'cup' in name_lower and '16' in name_lower:
        return '16oz Paper Cups'
    elif 'lid' in name_lower:
        return 'Cup Lids'
    elif 'vanilla syrup' in name_lower:
        return 'Vanilla Syrup'
    elif 'caramel syrup' in name_lower:
        return 'Caramel Syrup'
    elif 'napkin' in name_lower:
        return 'Paper Napkins'
    
    return name

def create_realistic_suppliers(filtered_items):
    """Create realistic suppliers based on the items"""
    suppliers_map = {}
    suppliers = []
    
    # Define supplier categories
    supplier_templates = {
        'dairy': {
            'name': 'Metro Dairy Supply',
            'specialty': 'Dairy products',
            'lead_time_days': 1,
            'phone': '(555) 234-5678'
        },
        'coffee': {
            'name': 'Pacific Coffee Roasters',
            'specialty': 'Coffee beans and equipment',
            'lead_time_days': 3,
            'phone': '(555) 345-6789'
        },
        'supplies': {
            'name': 'Restaurant Supply Co',
            'specialty': 'Paper products and supplies',
            'lead_time_days': 7,
            'phone': '(555) 456-7890'
        },
        'syrups': {
            'name': 'Flavor Solutions Inc',
            'specialty': 'Syrups and flavorings',
            'lead_time_days': 4,
            'phone': '(555) 567-8901'
        },
        'pastries': {
            'name': 'Artisan Bakery Supply',
            'specialty': 'Fresh baked goods',
            'lead_time_days': 1,
            'phone': '(555) 678-9012'
        }
    }
    
    # Create suppliers based on categories present
    categories_present = set(item['category'] for item in filtered_items)
    
    for i, category in enumerate(categories_present, 1):
        if category in supplier_templates:
            template = supplier_templates[category]
            supplier_id = f"SUP{i:03d}"
            
            supplier = {
                "supplier_id": supplier_id,
                "name": template['name'],
                "contact_phone": template['phone'],
                "contact_email": f"orders@{template['name'].lower().replace(' ', '')}.com",
                "lead_time_days": template['lead_time_days'],
                "minimum_order_value": 100 if category == 'syrups' else 200,
                "payment_terms": "Net 15" if template['lead_time_days'] <= 3 else "Net 30",
                "reliability_rating": 4,
                "specialty": template['specialty']
            }
            
            suppliers.append(supplier)
            suppliers_map[category] = supplier_id
    
    # Update items with correct supplier IDs
    for item in filtered_items:
        if item['category'] in suppliers_map:
            item['supplier_id'] = suppliers_map[item['category']]
            # Set lead time to match supplier
            item['lead_time_days'] = next(s['lead_time_days'] for s in suppliers if s['supplier_id'] == item['supplier_id'])
    
    return suppliers

def main():
    print("🔧 Filtering Converted Data for Cafe Essentials")
    print("=" * 50)
    
    # Load converted data
    print("📂 Loading converted inventory data...")
    try:
        inventory_data = load_converted_data('/home/k1/Projects/cafe_manager/sample_data/converted_inventory.json')
        print(f"✅ Loaded {len(inventory_data)} items")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Filter for cafe essentials
    print("🔍 Filtering for cafe essentials...")
    filtered_items = filter_cafe_essentials(inventory_data)
    print(f"✅ Filtered to {len(filtered_items)} essential items")
    
    # Show item breakdown by category
    category_counts = defaultdict(int)
    for item in filtered_items:
        category_counts[item['category']] += 1
    
    print("\n📊 Items by category:")
    for category, count in category_counts.items():
        print(f"   {category}: {count} items")
    
    # Create realistic suppliers
    print("\n🏢 Creating suppliers...")
    suppliers = create_realistic_suppliers(filtered_items)
    print(f"✅ Created {len(suppliers)} suppliers")
    
    # Show some sample items
    print("\n📋 Sample converted items:")
    for item in filtered_items[:10]:
        print(f"   • {item['name']} ({item['category']}) - Stock: {item['current_stock']} {item['unit']}")
    
    if len(filtered_items) > 10:
        print(f"   ... and {len(filtered_items) - 10} more items")
    
    # Save filtered data
    filtered_inventory_file = '/home/k1/Projects/cafe_manager/sample_data/your_cafe_inventory.json'
    filtered_suppliers_file = '/home/k1/Projects/cafe_manager/sample_data/your_cafe_suppliers.json'
    
    with open(filtered_inventory_file, 'w') as f:
        json.dump(filtered_items, f, indent=2)
    
    with open(filtered_suppliers_file, 'w') as f:
        json.dump(suppliers, f, indent=2)
    
    print(f"\n💾 Saved filtered data:")
    print(f"   📦 Inventory: {filtered_inventory_file}")
    print(f"   🏢 Suppliers: {filtered_suppliers_file}")
    
    print(f"\n🎉 Ready to Use!")
    print("📋 Next steps:")
    print("   1. Review the filtered files - these are now cafe-focused")
    print("   2. Edit any stock quantities that seem wrong")
    print("   3. Adjust minimum/maximum thresholds as needed")
    print("   4. Update supplier contact information")
    print("   5. Replace sample data and restart the cafe manager")
    
    print(f"\n💡 Replacement commands:")
    print("   cp sample_data/your_cafe_inventory.json sample_data/inventory_items.json")
    print("   cp sample_data/your_cafe_suppliers.json sample_data/suppliers.json")

if __name__ == "__main__":
    main()