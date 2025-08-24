#!/usr/bin/env python3
"""
Unit Tests for Inventory Engine
"""

import unittest
import pandas as pd
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from inventory_engine import InventoryEngine

class TestInventoryEngine(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.engine = InventoryEngine(data_dir=self.test_dir)
        
        # Create test data files
        self.create_test_data()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def create_test_data(self):
        """Create test CSV files"""
        # Stock levels data
        stock_data = [
            ['2025-08-20', 'Test Item', 10.0],
            ['2025-08-21', 'Test Item', 8.5],
            ['2025-08-22', 'Test Item', 7.0],
            ['2025-08-23', 'Test Item', 15.0],  # With delivery
        ]
        stock_df = pd.DataFrame(stock_data, columns=['Date', 'Item_Name', 'Current_Stock'])
        stock_df.to_csv(self.engine.stock_file, index=False)
        
        # Deliveries data
        delivery_data = [
            ['2025-08-23', 'Test Item', 10.0, 'Weekly delivery']
        ]
        delivery_df = pd.DataFrame(delivery_data, columns=['Date', 'Item_Name', 'Delivery_Amount', 'Notes'])
        delivery_df.to_csv(self.engine.delivery_file, index=False)
        
        # Item info data
        item_data = [
            ['Test Item', 'units', 2.0, 20.0, 3, 5.0, 'Test Supplier', 'Test item']
        ]
        item_df = pd.DataFrame(item_data, columns=['Item_Name', 'Unit', 'Min_Threshold', 'Max_Capacity', 'Lead_Time_Days', 'Cost_Per_Unit', 'Supplier', 'Notes'])
        item_df.to_csv(self.engine.item_info_file, index=False)
    
    def test_load_stock_data(self):
        """Test loading stock data"""
        stock_df = self.engine.load_stock_data()
        
        self.assertFalse(stock_df.empty)
        self.assertEqual(len(stock_df), 4)
        self.assertIn('Test Item', stock_df['Item_Name'].values)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(stock_df['Date']))
    
    def test_load_delivery_data(self):
        """Test loading delivery data"""
        delivery_df = self.engine.load_delivery_data()
        
        self.assertFalse(delivery_df.empty)
        self.assertEqual(len(delivery_df), 1)
        self.assertEqual(delivery_df.iloc[0]['Delivery_Amount'], 10.0)
    
    def test_load_item_info(self):
        """Test loading item info"""
        item_df = self.engine.load_item_info()
        
        self.assertFalse(item_df.empty)
        self.assertEqual(len(item_df), 1)
        self.assertEqual(item_df.iloc[0]['Item_Name'], 'Test Item')
        self.assertEqual(item_df.iloc[0]['Min_Threshold'], 2.0)
    
    def test_calculate_daily_consumption(self):
        """Test consumption calculation"""
        consumption_df = self.engine.calculate_daily_consumption()
        
        # Should have 3 consumption records (4 stock entries - 1 for starting point)
        self.assertEqual(len(consumption_df), 3)
        
        # Test specific consumption calculations
        # Day 2: 10.0 -> 8.5 = 1.5 consumption
        day2_record = consumption_df[consumption_df['Date'].dt.strftime('%Y-%m-%d') == '2025-08-21'].iloc[0]
        self.assertEqual(day2_record['Consumption'], 1.5)
        self.assertEqual(day2_record['Delivery_Amount'], 0.0)
        
        # Day 4: 7.0 + 10.0 delivery -> 15.0 = 2.0 consumption
        day4_record = consumption_df[consumption_df['Date'].dt.strftime('%Y-%m-%d') == '2025-08-23'].iloc[0]
        self.assertEqual(day4_record['Consumption'], 2.0)
        self.assertEqual(day4_record['Delivery_Amount'], 10.0)
    
    def test_calculate_forecast(self):
        """Test forecast calculation"""
        # First calculate consumption
        self.engine.calculate_daily_consumption()
        
        # Then calculate forecast
        forecast_df = self.engine.calculate_forecast()
        
        self.assertFalse(forecast_df.empty)
        self.assertEqual(len(forecast_df), 1)
        
        forecast = forecast_df.iloc[0]
        self.assertEqual(forecast['Item_Name'], 'Test Item')
        self.assertEqual(forecast['Current_Stock'], 15.0)
        self.assertGreater(forecast['Avg_Daily_Consumption'], 0)
        self.assertGreater(forecast['Days_Remaining'], 0)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        # Set up a scenario where item needs reordering
        # Modify stock to be very low
        stock_data = [
            ['2025-08-20', 'Test Item', 5.0],
            ['2025-08-21', 'Test Item', 3.0],
            ['2025-08-22', 'Test Item', 1.0],  # Very low stock
        ]
        stock_df = pd.DataFrame(stock_data, columns=['Date', 'Item_Name', 'Current_Stock'])
        stock_df.to_csv(self.engine.stock_file, index=False)
        
        # Generate recommendations
        recommendations_df = self.engine.generate_recommendations()
        
        self.assertFalse(recommendations_df.empty)
        self.assertEqual(len(recommendations_df), 1)
        
        rec = recommendations_df.iloc[0]
        self.assertEqual(rec['Item_Name'], 'Test Item')
        self.assertIn(rec['Urgency'], ['CRITICAL', 'HIGH', 'MEDIUM'])
        self.assertGreater(rec['Recommended_Quantity'], 0)
    
    def test_get_current_status(self):
        """Test status summary"""
        status = self.engine.get_current_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('total_items', status)
        self.assertIn('items_below_threshold', status)
        self.assertIn('critical_items', status)
        self.assertIn('recommendations_count', status)
        self.assertGreaterEqual(status['total_items'], 0)
    
    def test_add_stock_entry(self):
        """Test adding new stock entry"""
        initial_count = len(self.engine.load_stock_data())
        
        success = self.engine.add_stock_entry('2025-08-24', 'Test Item', 12.5)
        
        self.assertTrue(success)
        updated_stock_df = self.engine.load_stock_data()
        self.assertEqual(len(updated_stock_df), initial_count + 1)
        
        # Check the new entry
        new_entry = updated_stock_df[updated_stock_df['Date'].dt.strftime('%Y-%m-%d') == '2025-08-24']
        self.assertEqual(len(new_entry), 1)
        self.assertEqual(new_entry.iloc[0]['Current_Stock'], 12.5)
    
    def test_add_delivery_entry(self):
        """Test adding new delivery entry"""
        initial_count = len(self.engine.load_delivery_data())
        
        success = self.engine.add_delivery_entry('2025-08-24', 'Test Item', 8.0, 'Test delivery')
        
        self.assertTrue(success)
        updated_delivery_df = self.engine.load_delivery_data()
        self.assertEqual(len(updated_delivery_df), initial_count + 1)
        
        # Check the new entry
        new_entry = updated_delivery_df[updated_delivery_df['Date'].dt.strftime('%Y-%m-%d') == '2025-08-24']
        self.assertEqual(len(new_entry), 1)
        self.assertEqual(new_entry.iloc[0]['Delivery_Amount'], 8.0)
        self.assertEqual(new_entry.iloc[0]['Notes'], 'Test delivery')
    
    def test_duplicate_stock_entry_replacement(self):
        """Test that duplicate stock entries replace existing ones"""
        # Add an entry for a date that already exists
        success = self.engine.add_stock_entry('2025-08-21', 'Test Item', 99.9)
        
        self.assertTrue(success)
        stock_df = self.engine.load_stock_data()
        
        # Should still have same number of entries (replacement, not addition)
        date_entries = stock_df[stock_df['Date'].dt.strftime('%Y-%m-%d') == '2025-08-21']
        self.assertEqual(len(date_entries), 1)
        self.assertEqual(date_entries.iloc[0]['Current_Stock'], 99.9)
    
    def test_empty_data_files(self):
        """Test handling of empty data files"""
        # Remove all data files
        for file_path in [self.engine.stock_file, self.engine.delivery_file, self.engine.item_info_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Should handle empty files gracefully
        stock_df = self.engine.load_stock_data()
        delivery_df = self.engine.load_delivery_data()
        item_df = self.engine.load_item_info()
        
        self.assertTrue(stock_df.empty)
        self.assertTrue(delivery_df.empty)
        self.assertTrue(item_df.empty)
        
        # Calculations should handle empty data
        consumption_df = self.engine.calculate_daily_consumption()
        forecast_df = self.engine.calculate_forecast()
        recommendations_df = self.engine.generate_recommendations()
        
        self.assertTrue(consumption_df.empty)
        self.assertTrue(forecast_df.empty or len(forecast_df) == 0)
        self.assertTrue(recommendations_df.empty or len(recommendations_df) == 0)
    
    def test_consumption_with_missing_delivery_data(self):
        """Test consumption calculation when no delivery data exists"""
        # Remove delivery file
        if os.path.exists(self.engine.delivery_file):
            os.remove(self.engine.delivery_file)
        
        consumption_df = self.engine.calculate_daily_consumption()
        
        # Should still calculate consumption, just with 0 deliveries
        self.assertFalse(consumption_df.empty)
        # All delivery amounts should be 0
        self.assertTrue((consumption_df['Delivery_Amount'] == 0).all())
    
    def test_forecast_confidence_levels(self):
        """Test forecast confidence calculation based on data points"""
        # Test with minimal data (should be Low confidence)
        stock_data = [
            ['2025-08-22', 'Test Item', 10.0],
            ['2025-08-23', 'Test Item', 8.0],
        ]
        stock_df = pd.DataFrame(stock_data, columns=['Date', 'Item_Name', 'Current_Stock'])
        stock_df.to_csv(self.engine.stock_file, index=False)
        
        forecast_df = self.engine.calculate_forecast()
        self.assertEqual(forecast_df.iloc[0]['Confidence'], 'Low')
        
        # Test with more data points (should be higher confidence)
        stock_data = []
        base_date = datetime.now().date() - timedelta(days=10)
        for i in range(10):
            date = base_date + timedelta(days=i)
            stock_data.append([date.strftime('%Y-%m-%d'), 'Test Item', 10.0 - i * 0.5])
        
        stock_df = pd.DataFrame(stock_data, columns=['Date', 'Item_Name', 'Current_Stock'])
        stock_df.to_csv(self.engine.stock_file, index=False)
        
        forecast_df = self.engine.calculate_forecast()
        self.assertIn(forecast_df.iloc[0]['Confidence'], ['Medium', 'High'])


if __name__ == '__main__':
    unittest.main()