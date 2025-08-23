#!/usr/bin/env python3
"""
Cafe Supply Management - Forecasting Engine
Handles inventory forecasting, usage prediction, and ordering recommendations
"""

import json
import csv
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class UsagePattern:
    """Represents usage patterns for an inventory item"""
    item_id: str
    daily_averages: Dict[str, float]  # day_of_week -> average_usage
    trend_factor: float
    seasonal_multiplier: float
    volatility: float
    last_updated: str

@dataclass
class OrderRecommendation:
    """Represents an order recommendation"""
    item_id: str
    item_name: str
    current_stock: float
    projected_usage: float
    days_until_reorder: int
    recommended_quantity: float
    urgency_level: str  # "critical", "warning", "normal", "stock_up"
    reasoning: str
    supplier: str
    estimated_cost: float

class ForecastingEngine:
    def __init__(self, data_dir: str = "sample_data"):
        self.data_dir = data_dir
        self.inventory_items = {}
        self.suppliers = {}
        self.usage_history = []
        self.order_history = []
        self.usage_patterns = {}
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON files"""
        try:
            with open(f"{self.data_dir}/inventory_items.json", 'r') as f:
                items_list = json.load(f)
                self.inventory_items = {item['item_id']: item for item in items_list}
            
            with open(f"{self.data_dir}/suppliers.json", 'r') as f:
                suppliers_list = json.load(f)
                self.suppliers = {sup['supplier_id']: sup for sup in suppliers_list}
            
            with open(f"{self.data_dir}/daily_usage.json", 'r') as f:
                self.usage_history = json.load(f)
            
            with open(f"{self.data_dir}/order_history.json", 'r') as f:
                self.order_history = json.load(f)
                
        except FileNotFoundError as e:
            print(f"Warning: Could not load data file: {e}")
    
    def analyze_usage_patterns(self) -> Dict[str, UsagePattern]:
        """Analyze historical usage to identify patterns"""
        patterns = {}
        
        # Group usage by item_id
        usage_by_item = defaultdict(list)
        for usage in self.usage_history:
            usage_by_item[usage['item_id']].append(usage)
        
        for item_id, usages in usage_by_item.items():
            if len(usages) < 3:  # Need at least 3 data points
                continue
            
            # Calculate daily averages by day of week
            daily_usage = defaultdict(list)
            total_usage = []
            
            for usage in usages:
                date_obj = datetime.strptime(usage['date'], '%Y-%m-%d')
                day_of_week = date_obj.strftime('%A')
                daily_usage[day_of_week].append(usage['quantity_used'])
                total_usage.append(usage['quantity_used'])
            
            # Calculate averages for each day
            daily_averages = {}
            for day, values in daily_usage.items():
                daily_averages[day] = statistics.mean(values)
            
            # Fill in missing days with overall average
            overall_avg = statistics.mean(total_usage)
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in days:
                if day not in daily_averages:
                    daily_averages[day] = overall_avg
            
            # Calculate trend factor (simple linear trend)
            trend_factor = self._calculate_trend(usages)
            
            # Calculate volatility (coefficient of variation)
            volatility = statistics.stdev(total_usage) / statistics.mean(total_usage) if total_usage else 0
            
            patterns[item_id] = UsagePattern(
                item_id=item_id,
                daily_averages=daily_averages,
                trend_factor=trend_factor,
                seasonal_multiplier=1.0,  # TODO: Implement seasonal analysis
                volatility=volatility,
                last_updated=datetime.now().isoformat()
            )
        
        self.usage_patterns = patterns
        return patterns
    
    def _calculate_trend(self, usages: List[Dict]) -> float:
        """Calculate trend factor from usage history"""
        if len(usages) < 2:
            return 1.0
        
        # Sort by date
        sorted_usages = sorted(usages, key=lambda x: x['date'])
        
        # Simple trend calculation: compare recent vs older usage
        half_point = len(sorted_usages) // 2
        older_avg = statistics.mean([u['quantity_used'] for u in sorted_usages[:half_point]])
        recent_avg = statistics.mean([u['quantity_used'] for u in sorted_usages[half_point:]])
        
        if older_avg == 0:
            return 1.0
        
        trend_factor = recent_avg / older_avg
        # Cap extreme trends
        return max(0.5, min(2.0, trend_factor))
    
    def predict_usage(self, item_id: str, days_ahead: int = 7) -> float:
        """Predict usage for an item over specified days"""
        if item_id not in self.usage_patterns:
            # Fall back to simple average if no pattern available
            item_usage = [u for u in self.usage_history if u['item_id'] == item_id]
            if not item_usage:
                return 0.0
            return statistics.mean([u['quantity_used'] for u in item_usage]) * days_ahead
        
        pattern = self.usage_patterns[item_id]
        
        # Project usage for each day
        total_predicted = 0.0
        today = datetime.now()
        
        for i in range(days_ahead):
            future_date = today + timedelta(days=i)
            day_name = future_date.strftime('%A')
            
            base_usage = pattern.daily_averages.get(day_name, 0.0)
            adjusted_usage = base_usage * pattern.trend_factor * pattern.seasonal_multiplier
            total_predicted += adjusted_usage
        
        return total_predicted
    
    def calculate_reorder_frequency(self, item_id: str) -> Tuple[int, float]:
        """Calculate how often an item is typically reordered"""
        # Find all orders for this item
        item_orders = []
        for order in self.order_history:
            for line_item in order.get('line_items', []):
                if line_item['item_id'] == item_id:
                    item_orders.append({
                        'order_date': order['order_date'],
                        'quantity': line_item['quantity_ordered']
                    })
        
        if len(item_orders) < 2:
            # Default to 14 days if insufficient data
            return 14, 0.0
        
        # Sort by date
        item_orders.sort(key=lambda x: x['order_date'])
        
        # Calculate days between orders
        intervals = []
        for i in range(1, len(item_orders)):
            prev_date = datetime.strptime(item_orders[i-1]['order_date'], '%Y-%m-%d')
            curr_date = datetime.strptime(item_orders[i]['order_date'], '%Y-%m-%d')
            intervals.append((curr_date - prev_date).days)
        
        avg_interval = statistics.mean(intervals) if intervals else 14
        avg_quantity = statistics.mean([order['quantity'] for order in item_orders])
        
        return int(avg_interval), avg_quantity
    
    def generate_order_recommendations(self) -> List[OrderRecommendation]:
        """Generate ordering recommendations for all items"""
        if not self.usage_patterns:
            self.analyze_usage_patterns()
        
        recommendations = []
        
        for item_id, item in self.inventory_items.items():
            # Calculate reorder frequency and typical quantity
            avg_reorder_days, avg_quantity = self.calculate_reorder_frequency(item_id)
            
            # Predict usage until next typical reorder
            predicted_usage = self.predict_usage(item_id, avg_reorder_days)
            
            # Calculate when we'll hit minimum threshold
            if predicted_usage == 0:
                days_until_reorder = 999  # Very high number if no usage predicted
            else:
                daily_usage = predicted_usage / avg_reorder_days
                if daily_usage > 0:
                    days_until_reorder = max(0, (item['current_stock'] - item['min_threshold']) / daily_usage)
                else:
                    days_until_reorder = 999
            
            # Determine urgency and recommended quantity
            urgency = "normal"
            reasoning = f"Typically reorder every {avg_reorder_days} days"
            
            if item['current_stock'] <= item['min_threshold']:
                urgency = "critical"
                reasoning = f"Below minimum threshold ({item['min_threshold']})"
                recommended_qty = max(avg_quantity, item['max_capacity'] * 0.8)
            elif days_until_reorder <= item['lead_time_days']:
                urgency = "warning" 
                reasoning = f"Will hit minimum in {days_until_reorder:.1f} days (lead time: {item['lead_time_days']})"
                recommended_qty = avg_quantity
            elif days_until_reorder <= avg_reorder_days * 1.2:
                urgency = "normal"
                recommended_qty = avg_quantity
            else:
                urgency = "stock_up"
                reasoning = f"Good time to stock up - {days_until_reorder:.1f} days of stock remaining"
                recommended_qty = avg_quantity * 0.7  # Smaller quantity for stock-up
            
            # Don't exceed max capacity
            max_can_order = item['max_capacity'] - item['current_stock']
            recommended_qty = min(recommended_qty, max_can_order)
            
            if recommended_qty > 0:
                supplier = self.suppliers.get(item['supplier_id'], {})
                estimated_cost = recommended_qty * item['cost_per_unit']
                
                recommendations.append(OrderRecommendation(
                    item_id=item_id,
                    item_name=item['name'],
                    current_stock=item['current_stock'],
                    projected_usage=predicted_usage,
                    days_until_reorder=int(days_until_reorder),
                    recommended_quantity=recommended_qty,
                    urgency_level=urgency,
                    reasoning=reasoning,
                    supplier=supplier.get('name', 'Unknown'),
                    estimated_cost=estimated_cost
                ))
        
        # Sort by urgency
        urgency_order = {"critical": 1, "warning": 2, "normal": 3, "stock_up": 4}
        recommendations.sort(key=lambda x: (urgency_order.get(x.urgency_level, 3), -x.estimated_cost))
        
        return recommendations
    
    def get_inventory_alerts(self) -> List[Dict]:
        """Get immediate inventory alerts"""
        alerts = []
        
        for item_id, item in self.inventory_items.items():
            if item['current_stock'] <= item['min_threshold']:
                alerts.append({
                    'type': 'low_stock',
                    'severity': 'critical' if item['current_stock'] == 0 else 'warning',
                    'item_name': item['name'],
                    'current_stock': item['current_stock'],
                    'min_threshold': item['min_threshold'],
                    'message': f"{item['name']}: {item['current_stock']} {item['unit']} remaining (min: {item['min_threshold']})"
                })
            
            # Check for expiring items (if shelf life is tracked)
            if 'last_received_date' in item and item['shelf_life_days'] > 0:
                # This would need last_received_date in the data
                pass
        
        return alerts

    def export_recommendations_csv(self, recommendations: List[OrderRecommendation], filename: str):
        """Export recommendations to CSV file"""
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Item_Name', 'Current_Stock', 'Recommended_Quantity', 'Urgency', 
                         'Days_Until_Reorder', 'Estimated_Cost', 'Supplier', 'Reasoning']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for rec in recommendations:
                writer.writerow({
                    'Item_Name': rec.item_name,
                    'Current_Stock': rec.current_stock,
                    'Recommended_Quantity': f"{rec.recommended_quantity:.1f}",
                    'Urgency': rec.urgency_level,
                    'Days_Until_Reorder': rec.days_until_reorder,
                    'Estimated_Cost': f"${rec.estimated_cost:.2f}",
                    'Supplier': rec.supplier,
                    'Reasoning': rec.reasoning
                })

def main():
    """Demo the forecasting engine"""
    print("🔮 Cafe Supply Forecasting Engine")
    print("=" * 50)
    
    engine = ForecastingEngine()
    
    # Analyze patterns
    print("📊 Analyzing usage patterns...")
    patterns = engine.analyze_usage_patterns()
    print(f"Found patterns for {len(patterns)} items")
    
    # Generate recommendations
    print("\n📋 Generating order recommendations...")
    recommendations = engine.generate_order_recommendations()
    
    # Display recommendations by urgency
    urgency_groups = {"critical": [], "warning": [], "normal": [], "stock_up": []}
    for rec in recommendations:
        urgency_groups[rec.urgency_level].append(rec)
    
    for urgency, recs in urgency_groups.items():
        if not recs:
            continue
            
        print(f"\n🚨 {urgency.upper()} ITEMS ({len(recs)})")
        print("-" * 30)
        
        for rec in recs:
            print(f"• {rec.item_name}")
            print(f"  Current: {rec.current_stock} | Recommend: {rec.recommended_quantity:.1f}")
            print(f"  Cost: ${rec.estimated_cost:.2f} | Supplier: {rec.supplier}")
            print(f"  Reason: {rec.reasoning}")
            print()
    
    # Export to CSV
    engine.export_recommendations_csv(recommendations, "order_recommendations.csv")
    print("💾 Exported recommendations to order_recommendations.csv")
    
    # Show alerts
    alerts = engine.get_inventory_alerts()
    if alerts:
        print(f"\n⚠️  INVENTORY ALERTS ({len(alerts)})")
        print("-" * 30)
        for alert in alerts:
            print(f"• {alert['message']}")

if __name__ == "__main__":
    main()