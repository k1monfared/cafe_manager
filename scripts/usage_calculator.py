#!/usr/bin/env python3
"""
Usage Calculator - Automatically calculate daily usage from inventory snapshots
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class InventorySnapshot:
    """Represents inventory levels at a specific date"""
    date: str
    item_id: str
    stock_level: float
    waste_amount: float = 0.0  # Optional manual waste entry
    deliveries_received: float = 0.0  # New stock received that day
    notes: str = ""

@dataclass
class CalculatedUsage:
    """Represents calculated usage between two inventory snapshots"""
    date: str
    item_id: str
    calculated_usage: float
    waste_amount: float
    sales_inferred: bool  # True if we had to estimate sales volume
    confidence_level: str  # "high", "medium", "low"
    notes: str

class UsageCalculator:
    def __init__(self, data_dir: str = "sample_data"):
        self.data_dir = data_dir
        self.inventory_snapshots = []
        self.order_history = []
        self.inventory_items = {}
        
    def load_data(self):
        """Load existing data"""
        try:
            # Load inventory snapshots (will be the new primary data)
            try:
                with open(f"{self.data_dir}/inventory_snapshots.json", 'r') as f:
                    self.inventory_snapshots = json.load(f)
            except FileNotFoundError:
                self.inventory_snapshots = []
            
            # Load order history for delivery tracking
            with open(f"{self.data_dir}/order_history.json", 'r') as f:
                self.order_history = json.load(f)
                
            # Load inventory items for item info
            with open(f"{self.data_dir}/inventory_items.json", 'r') as f:
                items_list = json.load(f)
                self.inventory_items = {item['item_id']: item for item in items_list}
                
        except FileNotFoundError as e:
            print(f"Warning: Could not load data file: {e}")
    
    def add_inventory_snapshot(self, date: str, inventory_data: List[Dict]) -> bool:
        """
        Add a daily inventory snapshot
        inventory_data: [{"item_id": "ITEM001", "stock_level": 10.5, "waste": 0.2, "notes": "..."}]
        """
        try:
            # Remove any existing snapshot for this date
            self.inventory_snapshots = [s for s in self.inventory_snapshots 
                                      if s.get('date') != date]
            
            # Add new snapshots for each item
            for item_data in inventory_data:
                snapshot = {
                    "date": date,
                    "item_id": item_data["item_id"],
                    "stock_level": float(item_data["stock_level"]),
                    "waste_amount": float(item_data.get("waste_amount", 0.0)),
                    "deliveries_received": float(item_data.get("deliveries_received", 0.0)),
                    "notes": item_data.get("notes", "")
                }
                self.inventory_snapshots.append(snapshot)
            
            # Sort by date
            self.inventory_snapshots.sort(key=lambda x: x['date'])
            
            # Save to file
            self._save_snapshots()
            return True
            
        except Exception as e:
            print(f"Error adding inventory snapshot: {e}")
            return False
    
    def calculate_usage_from_snapshots(self) -> List[CalculatedUsage]:
        """Calculate daily usage from inventory snapshots"""
        usage_records = []
        
        # Group snapshots by item
        snapshots_by_item = {}
        for snapshot in self.inventory_snapshots:
            item_id = snapshot['item_id']
            if item_id not in snapshots_by_item:
                snapshots_by_item[item_id] = []
            snapshots_by_item[item_id].append(snapshot)
        
        # Calculate usage for each item
        for item_id, snapshots in snapshots_by_item.items():
            # Sort by date
            snapshots.sort(key=lambda x: x['date'])
            
            # Calculate usage between consecutive days
            for i in range(1, len(snapshots)):
                prev_snapshot = snapshots[i-1]
                curr_snapshot = snapshots[i]
                
                usage = self._calculate_daily_usage(prev_snapshot, curr_snapshot, item_id)
                if usage:
                    usage_records.append(usage)
        
        return usage_records
    
    def _calculate_daily_usage(self, prev_snapshot: Dict, curr_snapshot: Dict, item_id: str) -> Optional[CalculatedUsage]:
        """Calculate usage between two snapshots"""
        try:
            # Get deliveries that happened between the snapshots
            deliveries = self._get_deliveries_between_dates(
                prev_snapshot['date'], 
                curr_snapshot['date'], 
                item_id
            )
            
            # Calculate usage: Previous Stock + Deliveries - Current Stock - Waste
            prev_stock = prev_snapshot['stock_level']
            curr_stock = curr_snapshot['stock_level']
            waste = curr_snapshot['waste_amount']
            
            # Usage = what we started with + what we received - what we have now - what we wasted
            calculated_usage = prev_stock + deliveries - curr_stock - waste
            
            # Determine confidence level
            confidence = "high"
            notes = []
            
            if calculated_usage < 0:
                confidence = "low"
                notes.append("Negative usage calculated - check inventory counts")
                calculated_usage = 0  # Don't allow negative usage
            
            if deliveries > 0:
                notes.append(f"Includes {deliveries} units delivered")
            
            if waste > 0:
                notes.append(f"Excludes {waste} units waste/spoilage")
            
            # Check for unusually high usage (potential data error)
            item_info = self.inventory_items.get(item_id, {})
            max_capacity = item_info.get('max_capacity', float('inf'))
            if calculated_usage > max_capacity * 0.8:  # Using more than 80% of max capacity in one day
                confidence = "medium"
                notes.append("High usage detected - please verify")
            
            return CalculatedUsage(
                date=curr_snapshot['date'],
                item_id=item_id,
                calculated_usage=calculated_usage,
                waste_amount=waste,
                sales_inferred=True,  # We don't have direct sales data
                confidence_level=confidence,
                notes="; ".join(notes) if notes else "Calculated from inventory difference"
            )
            
        except Exception as e:
            print(f"Error calculating usage for {item_id}: {e}")
            return None
    
    def _get_deliveries_between_dates(self, start_date: str, end_date: str, item_id: str) -> float:
        """Get total deliveries for an item between two dates"""
        total_deliveries = 0.0
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        for order in self.order_history:
            if order.get('status') != 'delivered':
                continue
                
            delivery_date = order.get('delivery_date')
            if not delivery_date:
                continue
            
            try:
                delivery_dt = datetime.strptime(delivery_date, '%Y-%m-%d')
                
                # Check if delivery was between the snapshots
                if start_dt < delivery_dt <= end_dt:
                    # Look for this item in the order
                    for line_item in order.get('line_items', []):
                        if line_item.get('item_id') == item_id:
                            total_deliveries += line_item.get('quantity_received', 0.0)
            
            except ValueError:
                continue
        
        return total_deliveries
    
    def export_calculated_usage_to_daily_usage_format(self) -> List[Dict]:
        """Convert calculated usage to the existing daily_usage.json format"""
        calculated_usage = self.calculate_usage_from_snapshots()
        daily_usage_records = []
        
        for usage in calculated_usage:
            # Find the inventory snapshot for additional context
            snapshot = next((s for s in self.inventory_snapshots 
                           if s['date'] == usage.date and s['item_id'] == usage.item_id), {})
            
            record = {
                "date": usage.date,
                "item_id": usage.item_id,
                "quantity_used": usage.calculated_usage,
                "waste_amount": usage.waste_amount,
                "sales_volume": 0,  # We don't track this directly anymore
                "notes": f"Auto-calculated ({usage.confidence_level} confidence): {usage.notes}",
                "weather": "",  # Optional - user can still add this
                "special_events": "",  # Optional - user can still add this
                "calculation_method": "inventory_difference",
                "confidence_level": usage.confidence_level
            }
            daily_usage_records.append(record)
        
        return daily_usage_records
    
    def _save_snapshots(self):
        """Save inventory snapshots to file"""
        with open(f"{self.data_dir}/inventory_snapshots.json", 'w') as f:
            json.dump(self.inventory_snapshots, f, indent=2)
    
    def update_daily_usage_file(self):
        """Update the daily_usage.json file with calculated usage"""
        calculated_records = self.export_calculated_usage_to_daily_usage_format()
        
        # Load existing daily usage (might have manual entries or additional data)
        try:
            with open(f"{self.data_dir}/daily_usage.json", 'r') as f:
                existing_usage = json.load(f)
        except FileNotFoundError:
            existing_usage = []
        
        # Remove old calculated entries and add new ones
        manual_entries = [record for record in existing_usage 
                         if record.get('calculation_method') != 'inventory_difference']
        
        # Combine manual entries with new calculated ones
        all_usage = manual_entries + calculated_records
        
        # Sort by date
        all_usage.sort(key=lambda x: (x['date'], x['item_id']))
        
        # Save updated file
        with open(f"{self.data_dir}/daily_usage.json", 'w') as f:
            json.dump(all_usage, f, indent=2)
        
        print(f"Updated daily usage with {len(calculated_records)} calculated records")
        return len(calculated_records)

def main():
    """Test the usage calculator"""
    calculator = UsageCalculator()
    calculator.load_data()
    
    # Example: Add today's inventory snapshot
    today = datetime.now().strftime('%Y-%m-%d')
    sample_inventory = [
        {"item_id": "ITEM002", "stock_level": 8.5, "waste_amount": 0.5, "notes": "Normal day"},
        {"item_id": "ITEM003", "stock_level": 4.2, "waste_amount": 0.0, "notes": "Good coffee day"},
    ]
    
    calculator.add_inventory_snapshot(today, sample_inventory)
    calculated_usage = calculator.calculate_usage_from_snapshots()
    
    for usage in calculated_usage:
        print(f"{usage.date} - {usage.item_id}: {usage.calculated_usage} units used "
              f"({usage.confidence_level} confidence)")

if __name__ == "__main__":
    main()