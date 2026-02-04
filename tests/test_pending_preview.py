"""
Test Pending Sales Preview
Tests preview calculation logic
"""

import unittest
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.csv_helpers import read_csv, write_csv, atomic_append_csv, get_utc_timestamp


class TestPendingPreview(unittest.TestCase):
    """Test pending sales preview calculations"""
    
    def setUp(self):
        """Create temporary files for testing"""
        # Create temp inventory
        self.temp_inventory = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.temp_inventory.write('product_id,name,stock,base_threshold,adaptive_threshold,popularity_ewma,popularity_index\n')
        self.temp_inventory.write('PROD-001,Test Product 1,100,20,25.0,1.0,1.0\n')
        self.temp_inventory.write('PROD-002,Test Product 2,50,15,18.0,0.8,0.9\n')
        self.temp_inventory.close()
        self.inventory_path = self.temp_inventory.name
        
        # Create temp sales log
        self.temp_sales = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.temp_sales.write('timestamp,product_id,qty\n')
        self.temp_sales.close()
        self.sales_path = self.temp_sales.name
        
        # Create temp last_run.json
        self.temp_last_run = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump({'last_processed_row': 0}, self.temp_last_run)
        self.temp_last_run.close()
        self.last_run_path = self.temp_last_run.name
    
    def tearDown(self):
        """Clean up temporary files"""
        for path in [self.inventory_path, self.sales_path, self.last_run_path]:
            if os.path.exists(path):
                os.remove(path)
    
    def test_no_pending_sales(self):
        """Test preview with no pending sales"""
        inventory = read_csv(self.inventory_path)
        sales_log = read_csv(self.sales_path)
        
        with open(self.last_run_path, 'r') as f:
            last_run = json.load(f)
        
        last_processed_row = last_run['last_processed_row']
        pending_sales = sales_log[last_processed_row:]
        
        self.assertEqual(len(pending_sales), 0, "Should have no pending sales")
    
    def test_pending_sales_calculation(self):
        """Test pending sales calculation"""
        # Add some sales
        atomic_append_csv(self.sales_path, [get_utc_timestamp(), 'PROD-001', '10'])
        atomic_append_csv(self.sales_path, [get_utc_timestamp(), 'PROD-001', '5'])
        atomic_append_csv(self.sales_path, [get_utc_timestamp(), 'PROD-002', '20'])
        
        # Load data
        inventory = read_csv(self.inventory_path)
        sales_log = read_csv(self.sales_path)
        
        with open(self.last_run_path, 'r') as f:
            last_run = json.load(f)
        
        # Calculate pending
        last_processed_row = last_run['last_processed_row']
        pending_sales = sales_log[last_processed_row:]
        
        self.assertEqual(len(pending_sales), 3, "Should have 3 pending sales")
        
        # Calculate pending quantities per product
        pending_qty = {}
        for sale in pending_sales:
            product_id = sale['product_id']
            qty = int(sale['qty'])
            pending_qty[product_id] = pending_qty.get(product_id, 0) + qty
        
        self.assertEqual(pending_qty['PROD-001'], 15, "PROD-001 should have 15 pending")
        self.assertEqual(pending_qty['PROD-002'], 20, "PROD-002 should have 20 pending")
    
    def test_projected_stock_calculation(self):
        """Test projected stock after pending sales"""
        # Add sales
        atomic_append_csv(self.sales_path, [get_utc_timestamp(), 'PROD-001', '30'])
        
        # Load inventory
        inventory = read_csv(self.inventory_path)
        inventory_dict = {p['product_id']: p for p in inventory}
        
        # Load pending sales
        sales_log = read_csv(self.sales_path)
        with open(self.last_run_path, 'r') as f:
            last_run = json.load(f)
        
        pending_sales = sales_log[last_run['last_processed_row']:]
        
        # Calculate projected stock
        for sale in pending_sales:
            product_id = sale['product_id']
            qty = int(sale['qty'])
            
            if product_id in inventory_dict:
                current_stock = int(inventory_dict[product_id]['stock'])
                projected_stock = current_stock - qty
                
                self.assertEqual(projected_stock, 70, "PROD-001 projected stock should be 70")
    
    def test_multiple_pending_batches(self):
        """Test pending calculation after partial processing"""
        # Add first batch of sales
        atomic_append_csv(self.sales_path, [get_utc_timestamp(), 'PROD-001', '10'])
        atomic_append_csv(self.sales_path, [get_utc_timestamp(), 'PROD-002', '5'])
        
        # Simulate agent processing first batch
        with open(self.last_run_path, 'w') as f:
            json.dump({'last_processed_row': 2}, f)
        
        # Add second batch
        atomic_append_csv(self.sales_path, [get_utc_timestamp(), 'PROD-001', '20'])
        
        # Load and calculate pending
        sales_log = read_csv(self.sales_path)
        with open(self.last_run_path, 'r') as f:
            last_run = json.load(f)
        
        pending_sales = sales_log[last_run['last_processed_row']:]
        
        self.assertEqual(len(pending_sales), 1, "Should have 1 pending sale")
        self.assertEqual(pending_sales[0]['product_id'], 'PROD-001')
        self.assertEqual(pending_sales[0]['qty'], '20')


if __name__ == '__main__':
    unittest.main()
