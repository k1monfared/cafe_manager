#!/usr/bin/env python3
"""
Simplified Inventory Management Engine
Handles stock level tracking, consumption calculation, and forecasting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os
from audit_inventory import InventoryAuditor

class InventoryEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.stock_file = os.path.join(data_dir, "daily_stock_levels.csv")
        self.delivery_file = os.path.join(data_dir, "deliveries.csv")
        self.item_info_file = os.path.join(data_dir, "item_info.csv")
        self.consumption_file = os.path.join(data_dir, "daily_consumption.csv")
        self.forecast_file = os.path.join(data_dir, "forecast_results.csv")
        self.recommendations_file = os.path.join(data_dir, "recommendations.csv")
        self.auditor = InventoryAuditor(data_dir)
    
    def load_stock_data(self) -> pd.DataFrame:
        """Load daily stock levels"""
        try:
            df = pd.read_csv(self.stock_file)
            df['Date'] = pd.to_datetime(df['Date'])
            return df.sort_values(['Item_Name', 'Date'])
        except FileNotFoundError:
            return pd.DataFrame(columns=['Date', 'Item_Name', 'Current_Stock'])
    
    def load_delivery_data(self) -> pd.DataFrame:
        """Load delivery records"""
        try:
            df = pd.read_csv(self.delivery_file)
            df['Date'] = pd.to_datetime(df['Date'])
            return df.sort_values(['Item_Name', 'Date'])
        except FileNotFoundError:
            return pd.DataFrame(columns=['Date', 'Item_Name', 'Delivery_Amount', 'Notes'])
    
    def load_item_info(self) -> pd.DataFrame:
        """Load item metadata"""
        try:
            return pd.read_csv(self.item_info_file)
        except FileNotFoundError:
            return pd.DataFrame(columns=['Item_Name', 'Unit', 'Min_Threshold', 'Max_Capacity', 'Lead_Time_Days', 'Cost_Per_Unit', 'Supplier', 'Notes'])
    
    def calculate_daily_consumption(self) -> pd.DataFrame:
        """
        Calculate daily consumption for each item
        Formula: consumption = previous_stock + deliveries - current_stock
        """
        stock_df = self.load_stock_data()
        delivery_df = self.load_delivery_data()
        
        if stock_df.empty:
            return pd.DataFrame(columns=['Date', 'Item_Name', 'Consumption', 'Stock_Before_Delivery', 'Delivery_Amount', 'Previous_Stock', 'Reasoning'])
        
        # Create item name mapping from delivery names to stock names
        item_mapping = {
            'House Blend Coffee': 'Coffee Beans',
            'Whole Milk': 'Milk',
            '12oz Paper Cups': 'Paper Cups',
            'Test Coffee': 'Coffee Beans',
            'Test Milk': 'Milk',
            'Vanilla Syrup': 'Sugar'  # Assuming syrup maps to sugar for simplification
        }
        
        consumption_records = []
        
        for item in stock_df['Item_Name'].unique():
            item_stocks = stock_df[stock_df['Item_Name'] == item].copy()
            
            # Get deliveries for this item (accounting for name mapping)
            mapped_deliveries = []
            for delivery_name, stock_name in item_mapping.items():
                if stock_name == item:
                    item_deliveries = delivery_df[delivery_df['Item_Name'] == delivery_name].copy()
                    mapped_deliveries.append(item_deliveries)
            
            # Also check for exact name matches
            exact_deliveries = delivery_df[delivery_df['Item_Name'] == item].copy()
            if not exact_deliveries.empty:
                mapped_deliveries.append(exact_deliveries)
            
            # Combine all deliveries for this item
            all_deliveries = pd.concat(mapped_deliveries, ignore_index=True) if mapped_deliveries else pd.DataFrame()
            
            # Create delivery lookup (sum deliveries by date if multiple)
            delivery_lookup = {}
            if not all_deliveries.empty:
                delivery_by_date = all_deliveries.groupby(all_deliveries['Date'].dt.strftime('%Y-%m-%d'))['Delivery_Amount'].sum()
                delivery_lookup = delivery_by_date.to_dict()
            
            # Calculate consumption for each day (except first day)
            for i in range(1, len(item_stocks)):
                current_row = item_stocks.iloc[i]
                previous_row = item_stocks.iloc[i-1]
                
                current_date = current_row['Date']
                current_stock = current_row['Current_Stock']
                previous_stock = previous_row['Current_Stock']
                
                # Get deliveries for current date
                date_str = current_date.strftime('%Y-%m-%d')
                delivery_amount = delivery_lookup.get(date_str, 0.0)
                
                # Calculate consumption
                # consumption = previous_stock + deliveries - current_stock
                consumption = previous_stock + delivery_amount - current_stock
                
                # If consumption would be negative, it likely means there was a delivery
                # that increased stock beyond what was expected. In this case:
                # - If there's a recorded delivery, consumption should be 0 (no consumption, just delivery)
                # - If no recorded delivery, something is wrong with the data
                if consumption < 0:
                    if delivery_amount > 0:
                        # There was a delivery, consumption should be 0
                        consumption = 0
                    else:
                        # No delivery recorded but stock increased - this indicates missing delivery data
                        # Calculate what the delivery should have been
                        missing_delivery = current_stock - previous_stock
                        delivery_amount = missing_delivery
                        consumption = 0
                
                # Calculate stock before delivery
                stock_before_delivery = current_stock - delivery_amount
                
                # Ensure stock_before_delivery is not negative
                if stock_before_delivery < 0:
                    stock_before_delivery = 0
                
                # Create reasoning
                if delivery_amount > 0:
                    reasoning = f"Started with {previous_stock:.1f}, received {delivery_amount:.1f} delivery, ended with {current_stock:.1f}"
                else:
                    reasoning = f"Started with {previous_stock:.1f}, no deliveries, ended with {current_stock:.1f}"
                
                consumption_records.append({
                    'Date': current_date,
                    'Item_Name': item,
                    'Consumption': round(consumption, 1),
                    'Stock_Before_Delivery': round(stock_before_delivery, 1),
                    'Delivery_Amount': round(delivery_amount, 1),
                    'Previous_Stock': round(previous_stock, 1),
                    'Reasoning': reasoning
                })
        
        consumption_df = pd.DataFrame(consumption_records)
        
        # Save to CSV
        if not consumption_df.empty:
            consumption_df.to_csv(self.consumption_file, index=False)
            print(f"✅ Saved {len(consumption_df)} consumption records to {self.consumption_file}")
        
        # Run audit after consumption calculation
        try:
            audit_report = self.auditor.run_audit()
            print(f"✅ Audit completed and saved to {self.auditor.audit_results_file}")
        except Exception as e:
            print(f"⚠️  Audit failed: {str(e)}")
        
        return consumption_df
    
    def calculate_forecast(self, days_ahead: int = 30, lookback_days: int = 14) -> pd.DataFrame:
        """
        Generate forecasts for each item
        """
        stock_df = self.load_stock_data()
        consumption_df = self.calculate_daily_consumption()
        item_info_df = self.load_item_info()
        
        if stock_df.empty or consumption_df.empty:
            return pd.DataFrame()
        
        forecast_records = []
        today = datetime.now().date()
        
        for item in stock_df['Item_Name'].unique():
            # Get current stock (most recent entry)
            item_stocks = stock_df[stock_df['Item_Name'] == item]
            current_stock = item_stocks.iloc[-1]['Current_Stock'] if not item_stocks.empty else 0
            
            # Get item info
            item_info = item_info_df[item_info_df['Item_Name'] == item]
            min_threshold = item_info.iloc[0]['Min_Threshold'] if not item_info.empty else 0
            max_capacity = item_info.iloc[0]['Max_Capacity'] if not item_info.empty else 100
            lead_time = item_info.iloc[0]['Lead_Time_Days'] if not item_info.empty else 7
            unit = item_info.iloc[0]['Unit'] if not item_info.empty else 'units'
            
            # Calculate average consumption (last N days)
            item_consumption = consumption_df[consumption_df['Item_Name'] == item]
            
            # Get last N days of consumption
            cutoff_date = today - timedelta(days=lookback_days)
            recent_consumption = item_consumption[
                pd.to_datetime(item_consumption['Date']).dt.date >= cutoff_date
            ]
            
            if recent_consumption.empty:
                avg_daily_consumption = 0
                consumption_data_points = 0
            else:
                avg_daily_consumption = recent_consumption['Consumption'].mean()
                consumption_data_points = len(recent_consumption)
            
            # Calculate days remaining
            if avg_daily_consumption > 0:
                days_remaining = current_stock / avg_daily_consumption
            else:
                days_remaining = 999  # Essentially infinite if no consumption
            
            # Calculate forecast confidence
            if consumption_data_points >= 7:
                confidence = "High"
            elif consumption_data_points >= 3:
                confidence = "Medium"
            else:
                confidence = "Low"
            
            # Get consumption history for last 14 days (for charts)
            last_14_days = today - timedelta(days=14)
            chart_data = item_consumption[
                pd.to_datetime(item_consumption['Date']).dt.date >= last_14_days
            ].copy()
            
            chart_dates = chart_data['Date'].dt.strftime('%Y-%m-%d').tolist()
            chart_consumption = chart_data['Consumption'].round(2).tolist()
            
            forecast_records.append({
                'Item_Name': item,
                'Current_Stock': current_stock,
                'Unit': unit,
                'Min_Threshold': min_threshold,
                'Max_Capacity': max_capacity,
                'Lead_Time_Days': lead_time,
                'Avg_Daily_Consumption': round(avg_daily_consumption, 2),
                'Days_Remaining': round(days_remaining, 1),
                'Runout_Date': (today + timedelta(days=days_remaining)).strftime('%Y-%m-%d') if days_remaining < 365 else 'More than 1 year',
                'Data_Points_Used': consumption_data_points,
                'Confidence': confidence,
                'Chart_Dates': '|'.join(chart_dates),
                'Chart_Consumption': '|'.join(map(str, chart_consumption)),
                'Last_Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        forecast_df = pd.DataFrame(forecast_records)
        
        # Save to CSV
        if not forecast_df.empty:
            forecast_df.to_csv(self.forecast_file, index=False)
            print(f"✅ Saved {len(forecast_df)} forecast records to {self.forecast_file}")
        
        return forecast_df
    
    def generate_recommendations(self, buffer_days: int = 1) -> pd.DataFrame:
        """
        Generate purchase recommendations with detailed explanations
        """
        forecast_df = self.calculate_forecast()
        
        if forecast_df.empty:
            return pd.DataFrame()
        
        recommendations = []
        
        for _, item in forecast_df.iterrows():
            item_name = item['Item_Name']
            current_stock = item['Current_Stock']
            min_threshold = item['Min_Threshold']
            max_capacity = item['Max_Capacity']
            lead_time = item['Lead_Time_Days']
            avg_consumption = item['Avg_Daily_Consumption']
            days_remaining = item['Days_Remaining']
            unit = item['Unit']
            
            # Calculate recommended order quantity for ALL items
            # Target: 80% of max capacity
            target_stock = max_capacity * 0.8
            
            # Account for consumption during lead time
            consumption_during_lead_time = avg_consumption * lead_time
            
            # Recommended quantity (may be 0 for well-stocked items)
            recommended_quantity = target_stock - current_stock + consumption_during_lead_time
            recommended_quantity = max(0, round(recommended_quantity, 1))
            
            # Determine urgency and status for ALL items
            critical_days = lead_time + buffer_days
            
            if days_remaining <= lead_time:
                urgency = "CRITICAL"
                urgency_reason = f"Will run out in {days_remaining:.1f} days, but supplier needs {lead_time} days"
            elif days_remaining <= critical_days:
                urgency = "HIGH"
                urgency_reason = f"Will run out in {days_remaining:.1f} days, need to order soon"
            elif days_remaining <= (critical_days + 7):  # Within a week of critical
                urgency = "MEDIUM"
                urgency_reason = f"Getting low, good time to reorder"
            elif recommended_quantity > 0:
                urgency = "LOW"
                urgency_reason = f"Stock adequate, optional reorder available"
            else:
                urgency = "GOOD"
                urgency_reason = f"Stock level is good, no action needed"
            
            # Create detailed explanation
            if recommended_quantity > 0:
                explanation = f"""
Current stock: {current_stock:.1f} {unit}
Daily usage: {avg_consumption:.1f} {unit}/day (14-day average)
Days remaining: {days_remaining:.1f} days
Lead time: {lead_time} days
Minimum threshold: {min_threshold:.1f} {unit}
Maximum capacity: {max_capacity:.1f} {unit}

Calculation:
- Target stock level: {target_stock:.1f} {unit} (80% of capacity)
- Expected consumption during {lead_time}-day delivery: {consumption_during_lead_time:.1f} {unit}
- Recommended order: {recommended_quantity:.1f} {unit}

Reason: {urgency_reason}
                """.strip()
            else:
                explanation = f"""
Current stock: {current_stock:.1f} {unit}
Daily usage: {avg_consumption:.1f} {unit}/day (14-day average)
Days remaining: {days_remaining:.1f} days
Lead time: {lead_time} days
Minimum threshold: {min_threshold:.1f} {unit}
Maximum capacity: {max_capacity:.1f} {unit}

Status: Stock level is sufficient. Current stock exceeds target level.
No order needed at this time.

Reason: {urgency_reason}
                """.strip()
            
            recommendations.append({
                'Item_Name': item_name,
                'Current_Stock': current_stock,
                'Recommended_Quantity': recommended_quantity,
                'Unit': unit,
                'Urgency': urgency,
                'Days_Remaining': days_remaining,
                'Urgency_Reason': urgency_reason,
                'Detailed_Explanation': explanation,
                'Target_Stock_Level': target_stock,
                'Lead_Time_Days': lead_time,
                'Avg_Daily_Usage': avg_consumption,
                'Generated_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        recommendations_df = pd.DataFrame(recommendations)
        
        # Save to CSV
        if not recommendations_df.empty:
            recommendations_df.to_csv(self.recommendations_file, index=False)
            print(f"✅ Saved {len(recommendations_df)} recommendations to {self.recommendations_file}")
        
        return recommendations_df
    
    def get_current_status(self) -> Dict:
        """Get current inventory status summary"""
        stock_df = self.load_stock_data()
        item_info_df = self.load_item_info()
        forecast_df = self.calculate_forecast()
        recommendations_df = self.generate_recommendations()
        
        if stock_df.empty:
            return {
                'total_items': 0,
                'items_below_threshold': 0,
                'critical_items': 0,
                'recommendations_count': 0
            }
        
        # Get latest stock for each item
        latest_stocks = stock_df.groupby('Item_Name').last()
        
        # Count items below threshold
        items_below_threshold = 0
        if not item_info_df.empty:
            for item_name in latest_stocks.index:
                current_stock = latest_stocks.loc[item_name, 'Current_Stock']
                item_info = item_info_df[item_info_df['Item_Name'] == item_name]
                if not item_info.empty:
                    min_threshold = item_info.iloc[0]['Min_Threshold']
                    if current_stock <= min_threshold:
                        items_below_threshold += 1
        
        # Count critical items (recommendations with CRITICAL urgency)
        critical_items = 0
        if not recommendations_df.empty:
            critical_items = len(recommendations_df[recommendations_df['Urgency'] == 'CRITICAL'])
        
        return {
            'total_items': len(latest_stocks),
            'items_below_threshold': items_below_threshold,
            'critical_items': critical_items,
            'recommendations_count': len(recommendations_df) if not recommendations_df.empty else 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    
    def add_delivery_entry(self, date: str, item_name: str, delivery_amount: float, notes: str = "") -> bool:
        """Add a new delivery entry"""
        try:
            delivery_df = self.load_delivery_data()
            
            # Create new entry
            new_entry = pd.DataFrame({
                'Date': [pd.to_datetime(date)],
                'Item_Name': [item_name],
                'Delivery_Amount': [delivery_amount],
                'Notes': [notes]
            })
            
            # Add new entry
            delivery_df = pd.concat([delivery_df, new_entry], ignore_index=True)
            delivery_df = delivery_df.sort_values(['Item_Name', 'Date'])
            
            # Save
            delivery_df.to_csv(self.delivery_file, index=False)
            
            # Recalculate everything
            self.calculate_daily_consumption()
            self.calculate_forecast()
            self.generate_recommendations()
            
            return True
        except Exception as e:
            print(f"Error adding delivery entry: {e}")
            return False


if __name__ == "__main__":
    # Test the engine
    engine = InventoryEngine()
    
    print("🧮 Calculating daily consumption...")
    consumption_df = engine.calculate_daily_consumption()
    print(f"📊 Calculated consumption for {len(consumption_df)} entries")
    
    print("\n📈 Generating forecasts...")
    forecast_df = engine.calculate_forecast()
    print(f"🔮 Generated forecasts for {len(forecast_df)} items")
    
    print("\n💡 Creating recommendations...")
    recommendations_df = engine.generate_recommendations()
    print(f"🛒 Generated {len(recommendations_df)} recommendations")
    
    print("\n📋 Current Status:")
    status = engine.get_current_status()
    for key, value in status.items():
        print(f"   {key}: {value}")