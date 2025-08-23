#!/usr/bin/env python3
"""
Google Sheets Sync System
Converts CSV exports from Google Sheets to JSON format for the cafe manager
"""

import csv
import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import shutil

class SheetsSync:
    def __init__(self, sheets_folder="google_sheets_data", data_folder="sample_data"):
        self.sheets_folder = sheets_folder
        self.data_folder = data_folder
        
        # Create folders if they don't exist
        os.makedirs(sheets_folder, exist_ok=True)
        os.makedirs(data_folder, exist_ok=True)
        
        # Map of expected CSV files to JSON files
        self.file_mappings = {
            "current_inventory.csv": "inventory_items.json",
            "daily_usage.csv": "daily_usage.json", 
            "order_history.csv": "order_history.json",
            "suppliers.csv": "suppliers.json"
        }
    
    def backup_current_data(self):
        """Create backup of current JSON files"""
        backup_folder = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.data_folder, backup_folder)
        os.makedirs(backup_path, exist_ok=True)
        
        for json_file in self.file_mappings.values():
            json_path = os.path.join(self.data_folder, json_file)
            if os.path.exists(json_path):
                shutil.copy2(json_path, backup_path)
        
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    
    def convert_inventory_csv_to_json(self, csv_file: str) -> List[Dict]:
        """Convert inventory CSV to JSON format"""
        print(f"🔄 Converting {csv_file} to inventory format...")
        
        df = pd.read_csv(csv_file)
        print(f"   📊 Found {len(df)} rows")
        
        # Expected columns (flexible matching)
        expected_columns = {
            'item_name': ['Item_Name', 'item_name', 'Item Name', 'Product Name', 'Name'],
            'category': ['Category', 'category', 'Type', 'Item Type'],
            'subcategory': ['Subcategory', 'subcategory', 'Sub Category', 'Subtype'], 
            'unit': ['Unit', 'unit', 'Units', 'Measurement'],
            'current_stock': ['Current_Stock', 'current_stock', 'Stock', 'Quantity', 'On Hand'],
            'min_threshold': ['Min_Threshold', 'min_threshold', 'Min Stock', 'Minimum', 'Reorder Point'],
            'max_capacity': ['Max_Capacity', 'max_capacity', 'Max Stock', 'Maximum', 'Max'],
            'cost_per_unit': ['Cost_Per_Unit', 'cost_per_unit', 'Unit Cost', 'Price', 'Cost'],
            'supplier': ['Supplier', 'supplier', 'Vendor', 'Supplier Name'],
            'lead_time_days': ['Lead_Time_Days', 'lead_time_days', 'Lead Time', 'Delivery Days'],
            'shelf_life_days': ['Shelf_Life_Days', 'shelf_life_days', 'Shelf Life', 'Expiry Days'],
            'storage_requirements': ['Storage_Requirements', 'storage_requirements', 'Storage', 'Storage Notes'],
            'last_updated': ['Last_Updated', 'last_updated', 'Updated', 'Last Modified']
        }
        
        # Map columns
        column_map = {}
        df_columns = [col.strip() for col in df.columns]
        
        for key, possible_names in expected_columns.items():
            for col in df_columns:
                if col in possible_names:
                    column_map[key] = col
                    break
        
        print(f"   📋 Mapped columns: {column_map}")
        
        # Convert to inventory format
        inventory_items = []
        supplier_map = self._load_supplier_map()
        
        for index, row in df.iterrows():
            try:
                # Get basic info
                item_name = str(row.get(column_map.get('item_name', ''), '')).strip()
                if not item_name or item_name.lower() in ['', 'nan', 'none']:
                    continue
                
                # Generate item ID
                item_id = f"ITEM{len(inventory_items)+1:03d}"
                
                # Get category and subcategory
                category = str(row.get(column_map.get('category', ''), 'unknown')).strip().lower()
                subcategory = str(row.get(column_map.get('subcategory', ''), category)).strip().lower()
                
                # Get numeric values with defaults
                current_stock = self._safe_float(row.get(column_map.get('current_stock', ''), 0))
                min_threshold = self._safe_float(row.get(column_map.get('min_threshold', ''), max(1, current_stock * 0.2)))
                max_capacity = self._safe_float(row.get(column_map.get('max_capacity', ''), current_stock * 3))
                cost_per_unit = self._safe_float(row.get(column_map.get('cost_per_unit', ''), 10.0))
                lead_time_days = int(self._safe_float(row.get(column_map.get('lead_time_days', ''), 5)))
                shelf_life_days = int(self._safe_float(row.get(column_map.get('shelf_life_days', ''), 30)))
                
                # Get unit
                unit = str(row.get(column_map.get('unit', ''), 'pieces')).strip().lower()
                
                # Get supplier
                supplier_name = str(row.get(column_map.get('supplier', ''), 'Default Supplier')).strip()
                supplier_id = supplier_map.get(supplier_name, 'SUP001')
                
                # Storage requirements
                storage = str(row.get(column_map.get('storage_requirements', ''), 'Cool, dry place')).strip()
                
                inventory_item = {
                    "item_id": item_id,
                    "name": item_name,
                    "category": category,
                    "subcategory": subcategory,
                    "unit": unit,
                    "current_stock": current_stock,
                    "min_threshold": min_threshold,
                    "max_capacity": max_capacity,
                    "cost_per_unit": cost_per_unit,
                    "supplier_id": supplier_id,
                    "lead_time_days": lead_time_days,
                    "shelf_life_days": shelf_life_days,
                    "storage_requirements": storage
                }
                
                inventory_items.append(inventory_item)
                
            except Exception as e:
                print(f"   ⚠️  Error processing row {index}: {e}")
                continue
        
        print(f"   ✅ Converted {len(inventory_items)} items")
        return inventory_items
    
    def convert_daily_usage_csv_to_json(self, csv_file: str) -> List[Dict]:
        """Convert daily usage CSV to JSON format"""
        print(f"🔄 Converting {csv_file} to daily usage format...")
        
        df = pd.read_csv(csv_file)
        print(f"   📊 Found {len(df)} rows")
        
        # Expected columns
        expected_columns = {
            'date': ['Date', 'date', 'Day', 'Date Used'],
            'item_name': ['Item_Name', 'item_name', 'Item', 'Product'],
            'quantity_used': ['Quantity_Used', 'quantity_used', 'Used', 'Amount Used', 'Consumption'],
            'waste_amount': ['Waste_Amount', 'waste_amount', 'Waste', 'Spoiled', 'Discarded'],
            'sales_count': ['Sales_Count', 'sales_count', 'Sales', 'Items Sold', 'Units Sold'],
            'weather': ['Weather', 'weather', 'Conditions'],
            'day_of_week': ['Day_Of_Week', 'day_of_week', 'Weekday'],
            'special_events': ['Special_Events', 'special_events', 'Events', 'Notes'],
            'notes': ['Notes', 'notes', 'Comments', 'Remarks']
        }
        
        column_map = self._map_columns(df, expected_columns)
        usage_records = []
        item_name_to_id_map = self._load_item_name_map()
        
        for index, row in df.iterrows():
            try:
                # Parse date
                date_str = str(row.get(column_map.get('date', ''), '')).strip()
                if not date_str or date_str.lower() in ['', 'nan', 'none']:
                    continue
                
                parsed_date = self._parse_date(date_str)
                if not parsed_date:
                    continue
                
                # Get item
                item_name = str(row.get(column_map.get('item_name', ''), '')).strip()
                item_id = item_name_to_id_map.get(item_name, item_name)  # Fall back to name if no ID
                
                # Get quantities
                quantity_used = self._safe_float(row.get(column_map.get('quantity_used', ''), 0))
                waste_amount = self._safe_float(row.get(column_map.get('waste_amount', ''), 0))
                sales_count = int(self._safe_float(row.get(column_map.get('sales_count', ''), 0)))
                
                if quantity_used <= 0:
                    continue
                
                # Additional info
                weather = str(row.get(column_map.get('weather', ''), '')).strip()
                notes = str(row.get(column_map.get('notes', ''), '')).strip()
                special_events = str(row.get(column_map.get('special_events', ''), '')).strip()
                
                usage_record = {
                    "date": parsed_date,
                    "item_id": item_id,
                    "quantity_used": quantity_used,
                    "waste_amount": waste_amount,
                    "sales_volume": sales_count,
                    "notes": notes
                }
                
                if weather:
                    usage_record["weather"] = weather
                if special_events:
                    usage_record["special_events"] = special_events
                
                usage_records.append(usage_record)
                
            except Exception as e:
                print(f"   ⚠️  Error processing row {index}: {e}")
                continue
        
        print(f"   ✅ Converted {len(usage_records)} usage records")
        return usage_records
    
    def convert_order_history_csv_to_json(self, csv_file: str) -> List[Dict]:
        """Convert order history CSV to JSON format"""
        print(f"🔄 Converting {csv_file} to order history format...")
        
        df = pd.read_csv(csv_file)
        print(f"   📊 Found {len(df)} rows")
        
        # Expected columns
        expected_columns = {
            'order_date': ['Order_Date', 'order_date', 'Date', 'Order Date'],
            'supplier_name': ['Supplier_Name', 'supplier_name', 'Supplier', 'Vendor'],
            'item_name': ['Item_Name', 'item_name', 'Item', 'Product'],
            'quantity_ordered': ['Quantity_Ordered', 'quantity_ordered', 'Ordered', 'Qty Ordered'],
            'quantity_received': ['Quantity_Received', 'quantity_received', 'Received', 'Qty Received'],
            'unit_cost': ['Unit_Cost', 'unit_cost', 'Cost', 'Price'],
            'total_cost': ['Total_Cost', 'total_cost', 'Total', 'Amount'],
            'delivery_date': ['Delivery_Date', 'delivery_date', 'Delivered', 'Received Date'],
            'order_status': ['Order_Status', 'order_status', 'Status'],
            'payment_status': ['Payment_Status', 'payment_status', 'Payment', 'Paid'],
            'notes': ['Notes', 'notes', 'Comments']
        }
        
        column_map = self._map_columns(df, expected_columns)
        
        # Group by order (same date + supplier)
        orders_dict = {}
        supplier_map = self._load_supplier_map()
        item_name_to_id_map = self._load_item_name_map()
        
        for index, row in df.iterrows():
            try:
                order_date = self._parse_date(str(row.get(column_map.get('order_date', ''), '')).strip())
                if not order_date:
                    continue
                
                supplier_name = str(row.get(column_map.get('supplier_name', ''), 'Unknown')).strip()
                
                # Create order key
                order_key = f"{order_date}_{supplier_name}"
                
                if order_key not in orders_dict:
                    orders_dict[order_key] = {
                        "order_id": f"ORD{len(orders_dict)+1:03d}",
                        "order_date": order_date,
                        "supplier_id": supplier_map.get(supplier_name, 'SUP001'),
                        "delivery_date": self._parse_date(str(row.get(column_map.get('delivery_date', ''), order_date)).strip()) or order_date,
                        "total_cost": 0.0,
                        "status": str(row.get(column_map.get('order_status', ''), 'delivered')).strip().lower(),
                        "line_items": []
                    }
                
                # Add line item
                item_name = str(row.get(column_map.get('item_name', ''), '')).strip()
                item_id = item_name_to_id_map.get(item_name, f"ITEM{index:03d}")
                
                quantity_ordered = self._safe_float(row.get(column_map.get('quantity_ordered', ''), 0))
                quantity_received = self._safe_float(row.get(column_map.get('quantity_received', ''), quantity_ordered))
                unit_cost = self._safe_float(row.get(column_map.get('unit_cost', ''), 0))
                line_total = self._safe_float(row.get(column_map.get('total_cost', ''), quantity_ordered * unit_cost))
                
                if quantity_ordered > 0:
                    line_item = {
                        "item_id": item_id,
                        "quantity_ordered": quantity_ordered,
                        "quantity_received": quantity_received,
                        "unit_cost": unit_cost,
                        "line_total": line_total
                    }
                    
                    orders_dict[order_key]["line_items"].append(line_item)
                    orders_dict[order_key]["total_cost"] += line_total
                
            except Exception as e:
                print(f"   ⚠️  Error processing row {index}: {e}")
                continue
        
        orders = list(orders_dict.values())
        print(f"   ✅ Converted {len(orders)} orders")
        return orders
    
    def convert_suppliers_csv_to_json(self, csv_file: str) -> List[Dict]:
        """Convert suppliers CSV to JSON format"""
        print(f"🔄 Converting {csv_file} to suppliers format...")
        
        df = pd.read_csv(csv_file)
        print(f"   📊 Found {len(df)} rows")
        
        expected_columns = {
            'supplier_name': ['Supplier_Name', 'supplier_name', 'Name', 'Supplier'],
            'contact_person': ['Contact_Person', 'contact_person', 'Contact', 'Rep'],
            'phone': ['Phone', 'phone', 'Contact_Phone', 'Telephone'],
            'email': ['Email', 'email', 'Contact_Email', 'E-mail'],
            'address': ['Address', 'address', 'Location'],
            'lead_time_days': ['Lead_Time_Days', 'lead_time_days', 'Lead Time', 'Delivery Days'],
            'min_order_value': ['Min_Order_Value', 'min_order_value', 'Minimum Order', 'MOV'],
            'payment_terms': ['Payment_Terms', 'payment_terms', 'Terms', 'Payment'],
            'reliability_rating': ['Reliability_Rating', 'reliability_rating', 'Rating', 'Score'],
            'specialty': ['Specialty', 'specialty', 'Products', 'Category'],
            'notes': ['Notes', 'notes', 'Comments']
        }
        
        column_map = self._map_columns(df, expected_columns)
        suppliers = []
        
        for index, row in df.iterrows():
            try:
                supplier_name = str(row.get(column_map.get('supplier_name', ''), '')).strip()
                if not supplier_name or supplier_name.lower() in ['', 'nan', 'none']:
                    continue
                
                supplier_id = f"SUP{len(suppliers)+1:03d}"
                
                phone = str(row.get(column_map.get('phone', ''), '(555) 000-0000')).strip()
                email = str(row.get(column_map.get('email', ''), f"orders@{supplier_name.lower().replace(' ', '')}.com")).strip()
                lead_time = int(self._safe_float(row.get(column_map.get('lead_time_days', ''), 5)))
                min_order = self._safe_float(row.get(column_map.get('min_order_value', ''), 100))
                payment_terms = str(row.get(column_map.get('payment_terms', ''), 'Net 30')).strip()
                rating = int(self._safe_float(row.get(column_map.get('reliability_rating', ''), 4)))
                specialty = str(row.get(column_map.get('specialty', ''), 'General supplies')).strip()
                
                supplier = {
                    "supplier_id": supplier_id,
                    "name": supplier_name,
                    "contact_phone": phone,
                    "contact_email": email,
                    "lead_time_days": lead_time,
                    "minimum_order_value": min_order,
                    "payment_terms": payment_terms,
                    "reliability_rating": min(5, max(1, rating)),
                    "specialty": specialty
                }
                
                suppliers.append(supplier)
                
            except Exception as e:
                print(f"   ⚠️  Error processing row {index}: {e}")
                continue
        
        print(f"   ✅ Converted {len(suppliers)} suppliers")
        return suppliers
    
    def _map_columns(self, df: pd.DataFrame, expected_columns: Dict) -> Dict:
        """Map DataFrame columns to expected column names"""
        column_map = {}
        df_columns = [col.strip() for col in df.columns]
        
        for key, possible_names in expected_columns.items():
            for col in df_columns:
                if col in possible_names:
                    column_map[key] = col
                    break
        
        return column_map
    
    def _safe_float(self, value, default=0.0) -> float:
        """Safely convert value to float"""
        try:
            if pd.isna(value) or value == '':
                return default
            return float(str(value).replace(',', '').replace('$', '').strip())
        except (ValueError, TypeError):
            return default
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str or date_str.lower() in ['', 'nan', 'none']:
            return None
        
        date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y',
            '%m/%d/%y', '%d/%m/%y', '%B %d, %Y', '%b %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _load_supplier_map(self) -> Dict[str, str]:
        """Load supplier name to ID mapping"""
        try:
            with open(os.path.join(self.data_folder, "suppliers.json"), 'r') as f:
                suppliers = json.load(f)
                return {supplier['name']: supplier['supplier_id'] for supplier in suppliers}
        except:
            return {}
    
    def _load_item_name_map(self) -> Dict[str, str]:
        """Load item name to ID mapping"""
        try:
            with open(os.path.join(self.data_folder, "inventory_items.json"), 'r') as f:
                items = json.load(f)
                return {item['name']: item['item_id'] for item in items}
        except:
            return {}
    
    def sync_from_sheets(self) -> Dict[str, bool]:
        """Main sync function - convert all CSV files to JSON"""
        print("🔄 Starting Google Sheets sync...")
        
        # Create backup
        backup_path = self.backup_current_data()
        
        results = {}
        
        # Check which CSV files are available
        for csv_file, json_file in self.file_mappings.items():
            csv_path = os.path.join(self.sheets_folder, csv_file)
            
            if not os.path.exists(csv_path):
                print(f"⏭️  Skipping {csv_file} (file not found)")
                results[csv_file] = False
                continue
            
            try:
                # Convert based on file type
                if csv_file == "current_inventory.csv":
                    data = self.convert_inventory_csv_to_json(csv_path)
                elif csv_file == "daily_usage.csv":
                    data = self.convert_daily_usage_csv_to_json(csv_path)
                elif csv_file == "order_history.csv":
                    data = self.convert_order_history_csv_to_json(csv_path)
                elif csv_file == "suppliers.csv":
                    data = self.convert_suppliers_csv_to_json(csv_path)
                else:
                    print(f"⚠️  Unknown file type: {csv_file}")
                    results[csv_file] = False
                    continue
                
                # Save JSON file
                json_path = os.path.join(self.data_folder, json_file)
                with open(json_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"✅ Successfully converted {csv_file} → {json_file}")
                results[csv_file] = True
                
            except Exception as e:
                print(f"❌ Error converting {csv_file}: {e}")
                results[csv_file] = False
        
        # Summary
        successful = sum(results.values())
        total = len([f for f in self.file_mappings.keys() if os.path.exists(os.path.join(self.sheets_folder, f))])
        
        print(f"\n📊 Sync Summary:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {total - successful}")
        print(f"   💾 Backup: {backup_path}")
        
        return results

def main():
    print("📊 Google Sheets Sync Tool")
    print("=" * 50)
    
    sync = SheetsSync()
    
    print("📋 Instructions:")
    print("   1. Export your Google Sheets as CSV files")
    print("   2. Place CSV files in the 'google_sheets_data' folder:")
    print("      - current_inventory.csv")
    print("      - daily_usage.csv")
    print("      - order_history.csv") 
    print("      - suppliers.csv")
    print("   3. Run this script to convert to JSON format")
    print()
    
    # Check for CSV files
    available_files = []
    for csv_file in sync.file_mappings.keys():
        csv_path = os.path.join(sync.sheets_folder, csv_file)
        if os.path.exists(csv_path):
            available_files.append(csv_file)
            print(f"✅ Found: {csv_file}")
        else:
            print(f"❌ Missing: {csv_file}")
    
    if not available_files:
        print(f"\n⚠️  No CSV files found in {sync.sheets_folder}/")
        print("   Please add your Google Sheets CSV exports and try again.")
        return
    
    print(f"\n🔄 Ready to sync {len(available_files)} files.")
    input("Press Enter to continue...")
    
    # Perform sync
    results = sync.sync_from_sheets()
    
    if any(results.values()):
        print(f"\n🎉 Sync complete! Restart your cafe manager to see the updates.")
    else:
        print(f"\n❌ Sync failed. Check error messages above.")

if __name__ == "__main__":
    main()