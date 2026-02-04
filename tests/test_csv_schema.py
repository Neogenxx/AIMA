"""
Test CSV Schema Validation
Validates all CSV files have correct headers
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.csv_helpers import validate_csv_headers, read_csv


class TestCSVSchema(unittest.TestCase):
    """Test CSV file schemas"""
    
    def test_inventory_csv_headers(self):
        """Test inventory.csv has correct headers"""
        expected = ['product_id', 'name', 'stock', 'base_threshold', 
                   'adaptive_threshold', 'popularity_ewma', 'popularity_index']
        
        self.assertTrue(
            validate_csv_headers('data/inventory.csv', expected),
            "inventory.csv headers do not match expected schema"
        )
    
    def test_sales_log_csv_headers(self):
        """Test sales_log.csv has correct headers"""
        expected = ['timestamp', 'product_id', 'qty']
        
        self.assertTrue(
            validate_csv_headers('data/sales_log.csv', expected),
            "sales_log.csv headers do not match expected schema"
        )
    
    def test_restock_log_csv_headers(self):
        """Test restock_log.csv has correct headers"""
        expected = ['timestamp', 'product_id', 'stock_after_sale', 'base_threshold',
                   'adaptive_threshold', 'predicted_demand_5d', 'popularity_index',
                   'restock_qty', 'reason', 'confidence']
        
        self.assertTrue(
            validate_csv_headers('data/restock_log.csv', expected),
            "restock_log.csv headers do not match expected schema"
        )
    
    def test_inventory_csv_readable(self):
        """Test inventory.csv can be read"""
        inventory = read_csv('data/inventory.csv')
        
        self.assertIsInstance(inventory, list, "Inventory should be a list")
        self.assertGreater(len(inventory), 0, "Inventory should have at least one product")
        
        # Check first product has all required fields
        if inventory:
            product = inventory[0]
            required_fields = ['product_id', 'name', 'stock', 'base_threshold']
            for field in required_fields:
                self.assertIn(field, product, f"Product missing field: {field}")
    
    def test_csv_files_exist(self):
        """Test all required CSV files exist"""
        files = [
            'data/inventory.csv',
            'data/sales_log.csv',
            'data/restock_log.csv'
        ]
        
        for filepath in files:
            self.assertTrue(
                os.path.exists(filepath),
                f"Required CSV file missing: {filepath}"
            )


if __name__ == '__main__':
    unittest.main()
