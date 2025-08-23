#!/usr/bin/env python3
"""
Data Conversion Tool for Cafe Supply Manager
Helps convert messy, disorganized data to the proper format
"""

import csv
import json
import pandas as pd
from datetime import datetime
import re
from typing import Dict, List, Any

class DataConverter:
    def __init__(self):
        self.suppliers_map = {}
        self.items_map = {}
        
    def load_excel_file(self, filepath: str) -> Dict[str, pd.DataFrame]:
        """Load Excel file and return all sheets as DataFrames"""
        try:
            # Try to read the Excel file
            excel_data = pd.read_excel(filepath, sheet_name=None, engine='openpyxl')
            print(f"✅ Loaded Excel file with {len(excel_data)} sheets:")
            for sheet_name in excel_data.keys():
                print(f"   - {sheet_name}: {len(excel_data[sheet_name])} rows")
            return excel_data
        except Exception as e:
            print(f"❌ Error loading Excel file: {e}")
            print("💡 Try exporting your Excel file to CSV format first")
            return {}
    
    def load_csv_file(self, filepath: str) -> pd.DataFrame:
        """Load CSV file"""
        try:
            data = pd.read_csv(filepath)
            print(f"✅ Loaded CSV file with {len(data)} rows and {len(data.columns)} columns")
            print(f"   Columns: {list(data.columns)}")
            return data
        except Exception as e:
            print(f"❌ Error loading CSV file: {e}")
            return pd.DataFrame()
    
    def analyze_data_structure(self, df: pd.DataFrame, sheet_name: str = "data"):
        """Analyze the structure of messy data"""
        print(f"\n📊 Analyzing {sheet_name}:")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")
        
        print(f"\n📋 Column names and sample data:")
        for col in df.columns:
            print(f"   '{col}':")
            # Show first few non-null values
            sample_values = df[col].dropna().head(3).tolist()
            print(f"      Sample values: {sample_values}")
            print(f"      Data type: {df[col].dtype}")
            print()
    
    def guess_data_type(self, df: pd.DataFrame) -> str:
        """Guess what type of data this might be"""
        columns = [col.lower() for col in df.columns]
        
        # Look for inventory-related columns
        inventory_keywords = ['stock', 'inventory', 'quantity', 'amount', 'current', 'on_hand', 'available']
        if any(keyword in ' '.join(columns) for keyword in inventory_keywords):
            return "inventory"
        
        # Look for usage/consumption columns
        usage_keywords = ['used', 'consumed', 'sold', 'daily', 'usage', 'consumption']
        if any(keyword in ' '.join(columns) for keyword in usage_keywords):
            return "usage"
        
        # Look for order-related columns
        order_keywords = ['order', 'purchase', 'bought', 'supplier', 'vendor', 'cost', 'price']
        if any(keyword in ' '.join(columns) for keyword in order_keywords):
            return "orders"
        
        # Look for supplier information
        supplier_keywords = ['supplier', 'vendor', 'contact', 'phone', 'email', 'address']
        if any(keyword in ' '.join(columns) for keyword in supplier_keywords):
            return "suppliers"
        
        return "unknown"
    
    def standardize_item_names(self, name: str) -> str:
        """Clean up item names for consistency"""
        if pd.isna(name):
            return ""
        
        name = str(name).strip()
        
        # Common replacements for coffee shop items
        replacements = {
            'whole milk': 'Whole Milk',
            'milk - whole': 'Whole Milk', 
            'milk whole': 'Whole Milk',
            'oat milk': 'Oat Milk',
            'milk - oat': 'Oat Milk',
            'almond milk': 'Almond Milk',
            'coffee beans': 'Coffee Beans',
            'beans': 'Coffee Beans',
            'paper cups': 'Paper Cups',
            'cups': 'Paper Cups',
            'lids': 'Cup Lids',
            'cup lids': 'Cup Lids',
            'syrup': 'Syrup',
            'vanilla syrup': 'Vanilla Syrup',
            'caramel syrup': 'Caramel Syrup'
        }
        
        name_lower = name.lower()
        for old, new in replacements.items():
            if old in name_lower:
                return new
        
        # Capitalize first letter of each word
        return ' '.join(word.capitalize() for word in name.split())
    
    def parse_date(self, date_str: Any) -> str:
        """Try to parse various date formats"""
        if pd.isna(date_str):
            return ""
        
        date_str = str(date_str).strip()
        
        # Common date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y', 
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%m/%d/%y',
            '%d/%m/%y',
            '%B %d, %Y',
            '%b %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        print(f"⚠️  Could not parse date: '{date_str}'")
        return ""
    
    def extract_numbers(self, value: Any) -> float:
        """Extract numeric values from messy text"""
        if pd.isna(value):
            return 0.0
        
        value_str = str(value).strip()
        
        # Remove currency symbols and common text
        value_str = re.sub(r'[\$£€,]', '', value_str)
        value_str = re.sub(r'[a-zA-Z]+', '', value_str)
        
        # Extract first number found
        numbers = re.findall(r'[\d.]+', value_str)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return 0.0
    
    def convert_to_inventory_format(self, df: pd.DataFrame) -> List[Dict]:
        """Convert messy data to inventory format"""
        inventory_items = []
        
        print("🔄 Converting to inventory format...")
        
        for index, row in df.iterrows():
            # Try to identify key fields
            item_name = ""
            current_stock = 0.0
            cost_per_unit = 0.0
            supplier = ""
            category = "unknown"
            unit = "pieces"
            
            # Look for item name in various columns
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['item', 'product', 'name', 'description']):
                    item_name = self.standardize_item_names(row[col])
                    break
            
            # Look for stock/quantity
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['stock', 'quantity', 'amount', 'current', 'on_hand']):
                    current_stock = self.extract_numbers(row[col])
                    break
            
            # Look for cost/price
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['cost', 'price', 'unit', 'each']):
                    cost_per_unit = self.extract_numbers(row[col])
                    break
            
            # Look for supplier
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['supplier', 'vendor', 'from']):
                    supplier = str(row[col]).strip() if not pd.isna(row[col]) else ""
                    break
            
            # Guess category from item name
            if item_name:
                name_lower = item_name.lower()
                if any(keyword in name_lower for keyword in ['milk', 'dairy']):
                    category = "dairy"
                    unit = "gallons"
                elif any(keyword in name_lower for keyword in ['coffee', 'bean']):
                    category = "coffee_beans"
                    unit = "lbs"
                elif any(keyword in name_lower for keyword in ['cup', 'lid']):
                    category = "supplies"
                    unit = "cases"
                elif any(keyword in name_lower for keyword in ['syrup']):
                    category = "syrups"
                    unit = "bottles"
            
            if item_name and current_stock > 0:
                item_id = f"ITEM{len(inventory_items)+1:03d}"
                
                inventory_items.append({
                    "item_id": item_id,
                    "name": item_name,
                    "category": category,
                    "subcategory": category,
                    "unit": unit,
                    "current_stock": current_stock,
                    "min_threshold": max(1, current_stock * 0.2),  # 20% of current as minimum
                    "max_capacity": current_stock * 3,  # 3x current as maximum
                    "cost_per_unit": cost_per_unit if cost_per_unit > 0 else 10.0,
                    "supplier_id": "SUP001",  # Default supplier
                    "lead_time_days": 5,  # Default lead time
                    "shelf_life_days": 365 if category == "coffee_beans" else 30,
                    "storage_requirements": "Cool, dry place"
                })
        
        print(f"✅ Converted {len(inventory_items)} inventory items")
        return inventory_items
    
    def save_converted_data(self, data: List[Dict], filename: str):
        """Save converted data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved converted data to {filename}")
    
    def create_suppliers_from_data(self, inventory_data: List[Dict]) -> List[Dict]:
        """Extract unique suppliers and create supplier records"""
        suppliers = []
        supplier_names = set()
        
        # Extract unique supplier names from inventory
        for item in inventory_data:
            supplier_name = item.get('supplier_name', 'Unknown Supplier')
            if supplier_name not in supplier_names and supplier_name != 'Unknown Supplier':
                supplier_names.add(supplier_name)
        
        # Create supplier records
        for i, name in enumerate(supplier_names, 1):
            suppliers.append({
                "supplier_id": f"SUP{i:03d}",
                "name": name,
                "contact_phone": "(555) 000-0000",  # Placeholder
                "contact_email": f"orders@{name.lower().replace(' ', '')}.com",
                "lead_time_days": 5,
                "minimum_order_value": 100,
                "payment_terms": "Net 30",
                "reliability_rating": 3,
                "specialty": "Various supplies"
            })
        
        return suppliers

def main():
    print("🔧 Cafe Supply Data Converter")
    print("=" * 50)
    
    converter = DataConverter()
    
    # First try to load the Excel file
    excel_file = "/home/k1/Projects/cafe_manager/sample_data/real_messy_data.xlsx"
    
    try:
        import openpyxl
    except ImportError:
        print("❌ openpyxl not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "openpyxl"])
        import openpyxl
    
    print(f"📂 Looking for: {excel_file}")
    
    # Try to load and analyze the Excel file
    excel_data = converter.load_excel_file(excel_file)
    
    if excel_data:
        print("\n📊 Data Analysis:")
        print("=" * 30)
        
        all_converted_data = []
        
        for sheet_name, df in excel_data.items():
            print(f"\n🔍 Analyzing sheet: '{sheet_name}'")
            
            if df.empty:
                print("   Empty sheet, skipping...")
                continue
            
            converter.analyze_data_structure(df, sheet_name)
            data_type = converter.guess_data_type(df)
            print(f"   📝 Guessed data type: {data_type}")
            
            if data_type == "inventory" or data_type == "unknown":
                converted = converter.convert_to_inventory_format(df)
                all_converted_data.extend(converted)
        
        if all_converted_data:
            # Save converted inventory data
            output_file = "/home/k1/Projects/cafe_manager/sample_data/converted_inventory.json"
            converter.save_converted_data(all_converted_data, output_file)
            
            # Create suppliers from the data
            suppliers = converter.create_suppliers_from_data(all_converted_data)
            supplier_file = "/home/k1/Projects/cafe_manager/sample_data/converted_suppliers.json"
            converter.save_converted_data(suppliers, supplier_file)
            
            print(f"\n🎉 Conversion Complete!")
            print(f"   📦 Inventory items: {len(all_converted_data)}")
            print(f"   🏢 Suppliers: {len(suppliers)}")
            print(f"   📁 Files created:")
            print(f"      - {output_file}")
            print(f"      - {supplier_file}")
            
            print(f"\n📋 Next Steps:")
            print("   1. Review the converted files")
            print("   2. Edit any incorrect item names or categories")
            print("   3. Update supplier contact information")
            print("   4. Replace the sample data files with converted files")
            print("   5. Restart the cafe manager application")
        else:
            print("❌ No inventory data could be converted")
            print("💡 Your Excel file might need manual review")
    
    else:
        print("\n💡 Excel file couldn't be loaded. Try these steps:")
        print("   1. Open your Excel file")
        print("   2. Save each sheet as a separate CSV file")
        print("   3. Put CSV files in the sample_data folder")
        print("   4. Run this converter again")
        print("\n   Example CSV filenames:")
        print("      - inventory.csv")
        print("      - orders.csv") 
        print("      - suppliers.csv")

if __name__ == "__main__":
    main()