"""
Test Cashier Atomic Append
Tests atomic CSV append with concurrency
"""

import unittest
import sys
import os
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.csv_helpers import (
    atomic_append_csv, read_csv, count_csv_rows,
    get_utc_timestamp, sanitize_product_id, validate_quantity
)


class TestCashierAppend(unittest.TestCase):
    """Test atomic CSV append operations"""
    
    def setUp(self):
        """Create temporary CSV file for testing"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.temp_file.write('timestamp,product_id,qty\n')
        self.temp_file.close()
        self.temp_path = self.temp_file.name
    
    def tearDown(self):
        """Clean up temporary file"""
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)
    
    def test_single_append(self):
        """Test single atomic append"""
        timestamp = get_utc_timestamp()
        row = [timestamp, 'PROD-001', '5']
        
        success = atomic_append_csv(self.temp_path, row)
        self.assertTrue(success, "Append should succeed")
        
        # Verify row was written
        rows = read_csv(self.temp_path)
        self.assertEqual(len(rows), 1, "Should have 1 row")
        self.assertEqual(rows[0]['product_id'], 'PROD-001')
        self.assertEqual(rows[0]['qty'], '5')
    
    def test_multiple_sequential_appends(self):
        """Test multiple sequential appends"""
        for i in range(5):
            row = [get_utc_timestamp(), f'PROD-{i:03d}', str(i+1)]
            atomic_append_csv(self.temp_path, row)
        
        rows = read_csv(self.temp_path)
        self.assertEqual(len(rows), 5, "Should have 5 rows")
    
    def test_concurrent_appends(self):
        """Test concurrent atomic appends from multiple threads"""
        num_threads = 10
        appends_per_thread = 5
        
        def append_worker(thread_id):
            for i in range(appends_per_thread):
                row = [get_utc_timestamp(), f'PROD-T{thread_id}', str(i)]
                atomic_append_csv(self.temp_path, row)
                time.sleep(0.001)  # Small delay to increase concurrency
        
        threads = []
        for t in range(num_threads):
            thread = threading.Thread(target=append_worker, args=(t,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all appends succeeded
        rows = read_csv(self.temp_path)
        expected_count = num_threads * appends_per_thread
        
        self.assertEqual(
            len(rows), 
            expected_count,
            f"Should have {expected_count} rows from concurrent appends"
        )
        
        # Verify CSV is not corrupted (all rows parseable)
        for row in rows:
            self.assertIn('product_id', row)
            self.assertIn('qty', row)
    
    def test_product_id_sanitization(self):
        """Test product ID sanitization"""
        self.assertEqual(sanitize_product_id('PROD-001'), 'PROD-001')
        self.assertEqual(sanitize_product_id('prod-001'), 'PROD-001')
        self.assertEqual(sanitize_product_id('PROD001'), 'PROD001')
        
        # Invalid inputs
        self.assertIsNone(sanitize_product_id('PROD,001'))  # Comma
        self.assertIsNone(sanitize_product_id('PROD 001'))  # Space
        self.assertIsNone(sanitize_product_id('PROD/001'))  # Slash
        self.assertIsNone(sanitize_product_id(''))  # Empty
    
    def test_quantity_validation(self):
        """Test quantity validation"""
        self.assertEqual(validate_quantity(5), 5)
        self.assertEqual(validate_quantity('10'), 10)
        self.assertEqual(validate_quantity('100'), 100)
        
        # Invalid inputs
        self.assertIsNone(validate_quantity(0))  # Too low
        self.assertIsNone(validate_quantity(-5))  # Negative
        self.assertIsNone(validate_quantity(1001))  # Too high
        self.assertIsNone(validate_quantity('abc'))  # Not a number
        self.assertIsNone(validate_quantity(None))  # None
    
    def test_count_csv_rows(self):
        """Test row counting"""
        # Append some rows
        for i in range(3):
            row = [get_utc_timestamp(), f'PROD-{i}', str(i)]
            atomic_append_csv(self.temp_path, row)
        
        count = count_csv_rows(self.temp_path, exclude_header=True)
        self.assertEqual(count, 3, "Should count 3 data rows")
        
        count_with_header = count_csv_rows(self.temp_path, exclude_header=False)
        self.assertEqual(count_with_header, 4, "Should count 4 total rows (including header)")


if __name__ == '__main__':
    unittest.main()
