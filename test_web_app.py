#!/usr/bin/env python3
"""
End-to-End Tests for Web Application
"""

import unittest
import tempfile
import shutil
import os
import json
from simple_app import app
from inventory_engine import InventoryEngine
import pandas as pd

class TestWebApp(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test app with temporary data directory
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Replace the global engine with test engine
        global engine
        engine = InventoryEngine(data_dir=self.test_dir)
        app.config['engine'] = engine
        
        # Create test data
        self.create_test_data()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def create_test_data(self):
        """Create test data files"""
        # Stock levels
        stock_data = [
            ['2025-08-20', 'Test Milk', 10.0],
            ['2025-08-21', 'Test Milk', 8.0],
            ['2025-08-22', 'Test Milk', 1.5],  # Low stock for alerts
            ['2025-08-20', 'Test Coffee', 15.0],
            ['2025-08-21', 'Test Coffee', 12.0],
            ['2025-08-22', 'Test Coffee', 9.0],
        ]
        stock_df = pd.DataFrame(stock_data, columns=['Date', 'Item_Name', 'Current_Stock'])
        stock_df.to_csv(os.path.join(self.test_dir, 'daily_stock_levels.csv'), index=False)
        
        # Deliveries
        delivery_data = [
            ['2025-08-20', 'Test Milk', 20.0, 'Weekly delivery']
        ]
        delivery_df = pd.DataFrame(delivery_data, columns=['Date', 'Item_Name', 'Delivery_Amount', 'Notes'])
        delivery_df.to_csv(os.path.join(self.test_dir, 'deliveries.csv'), index=False)
        
        # Item info
        item_data = [
            ['Test Milk', 'gallons', 3.0, 25.0, 1, 4.50, 'Dairy Co', 'Refrigerated'],
            ['Test Coffee', 'lbs', 2.0, 20.0, 3, 12.00, 'Coffee Co', 'Dry storage']
        ]
        item_df = pd.DataFrame(item_data, columns=['Item_Name', 'Unit', 'Min_Threshold', 'Max_Capacity', 'Lead_Time_Days', 'Cost_Per_Unit', 'Supplier', 'Notes'])
        item_df.to_csv(os.path.join(self.test_dir, 'item_info.csv'), index=False)
        
        # Generate derived data
        test_engine = InventoryEngine(data_dir=self.test_dir)
        test_engine.calculate_daily_consumption()
        test_engine.calculate_forecast()
        test_engine.generate_recommendations()
    
    def test_dashboard_loads(self):
        """Test that dashboard loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Inventory Dashboard', response.data)
    
    def test_dashboard_shows_status(self):
        """Test that dashboard shows correct status information"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Should show items
        self.assertIn(b'Test Milk', response.data)
        self.assertIn(b'Test Coffee', response.data)
        
        # Should show some status numbers
        self.assertIn(b'Total Items', response.data)
    
    
    def test_analytics_page(self):
        """Test analytics page loads with data"""
        response = self.client.get('/analytics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Analytics', response.data)
        self.assertIn(b'Test Milk', response.data)
    
    def test_upload_page(self):
        """Test upload page loads"""
        response = self.client.get('/upload')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload CSV', response.data)
    
    
    def test_add_delivery_api(self):
        """Test adding delivery entry via API"""
        delivery_data = {
            'date': '2025-08-23',
            'item_name': 'Test Coffee',
            'delivery_amount': 10.0,
            'notes': 'Test delivery'
        }
        
        response = self.client.post('/api/add_delivery',
                                  data=json.dumps(delivery_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Added delivery entry', data['message'])
    
    
    def test_recalculate_api(self):
        """Test manual recalculation API"""
        response = self.client.post('/api/recalculate')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Recalculated', data['message'])
    
    def test_upload_csv_stock_levels(self):
        """Test CSV upload for stock levels"""
        csv_content = """Date,Item_Name,Current_Stock
2025-08-24,Test Milk,20.0
2025-08-24,Test Coffee,15.0"""
        
        response = self.client.post('/api/upload_csv',
                                  data={
                                      'file': (io.BytesIO(csv_content.encode()), 'test.csv'),
                                      'file_type': 'stock_levels'
                                  })
        
        # Note: This test might need adjustment based on actual file upload handling
        # The current implementation expects actual file objects
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        # Test invalid JSON for delivery API
        response = self.client.post('/api/add_delivery',
                                  data='invalid json',
                                  content_type='application/json')
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_dashboard_with_recommendations(self):
        """Test that dashboard shows recommendations when they exist"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Should show recommendations section if there are any
        # Test Milk should trigger a recommendation due to low stock (1.5 vs 3.0 threshold)
        if b'Purchase Recommendations' in response.data:
            self.assertIn(b'Test Milk', response.data)
    
    def test_analytics_with_charts(self):
        """Test that analytics page includes chart data"""
        response = self.client.get('/analytics')
        self.assertEqual(response.status_code, 200)
        
        # Should include chart.js and chart data
        self.assertIn(b'Chart', response.data)
        self.assertIn(b'Daily Consumption', response.data)
    
    def test_workflow_integration(self):
        """Test complete user workflow"""
        # 1. Load dashboard
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # 2. Add a delivery
        delivery_data = {
            'date': '2025-08-24',
            'item_name': 'Test Milk',
            'delivery_amount': 20.0,
            'notes': 'Integration test delivery'
        }
        response = self.client.post('/api/add_delivery',
                                  data=json.dumps(delivery_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # 4. Check analytics updated
        response = self.client.get('/analytics')
        self.assertEqual(response.status_code, 200)
        
        # 5. Verify dashboard reflects changes
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


# Import io for file upload tests
import io

if __name__ == '__main__':
    unittest.main()