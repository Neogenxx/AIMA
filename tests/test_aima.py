"""
Test Suite for AIMA
Unit tests for all components
"""

import unittest
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager
from utils.math_utils import (
    DemandForecaster,
    PopularityCalculator,
    AdaptiveThresholdCalculator,
    ConfidenceScorer
)
from agents.inventory_agent import InventoryAgent
from simulations.simulator import SalesSimulator

class TestDatabaseManager(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Setup test database"""
        self.db = DatabaseManager(":memory:")  # In-memory database for testing
    
    def test_add_product(self):
        """Test adding a product"""
        success = self.db.add_product(
            product_id="TEST-001",
            name="Test Product",
            category="Test",
            initial_stock=100,
            unit_cost=10.0,
            selling_price=20.0
        )
        self.assertTrue(success)
        
        # Verify product exists
        product = self.db.get_product("TEST-001")
        self.assertIsNotNone(product)
        self.assertEqual(product['name'], "Test Product")
        self.assertEqual(product['current_stock'], 100)
    
    def test_record_sale(self):
        """Test recording a sale"""
        # Add product first
        self.db.add_product("TEST-002", "Test Product 2", "Test", 50, 10.0, 20.0)
        
        # Record sale
        success = self.db.record_sale("TEST-002", 10)
        self.assertTrue(success)
        
        # Verify stock updated
        product = self.db.get_product("TEST-002")
        self.assertEqual(product['current_stock'], 40)
    
    def test_insufficient_stock_sale(self):
        """Test sale with insufficient stock"""
        self.db.add_product("TEST-003", "Test Product 3", "Test", 5, 10.0, 20.0)
        
        # Try to sell more than available
        success = self.db.record_sale("TEST-003", 10)
        self.assertFalse(success)
    
    def test_get_sales_history(self):
        """Test retrieving sales history"""
        self.db.add_product("TEST-004", "Test Product 4", "Test", 100, 10.0, 20.0)
        
        # Record multiple sales
        self.db.record_sale("TEST-004", 5)
        self.db.record_sale("TEST-004", 3)
        
        # Get history
        history = self.db.get_sales_history("TEST-004", days=30)
        self.assertEqual(len(history), 2)


class TestDemandForecaster(unittest.TestCase):
    """Test demand forecasting"""
    
    def setUp(self):
        self.forecaster = DemandForecaster(alpha=0.3)
    
    def test_exponential_smoothing(self):
        """Test exponential smoothing"""
        data = [10, 12, 11, 13, 15]
        smoothed = self.forecaster.exponential_smoothing(data)
        
        self.assertEqual(len(smoothed), len(data))
        self.assertEqual(smoothed[0], data[0])  # First value unchanged
    
    def test_forecast_next_period(self):
        """Test demand forecasting"""
        historical = [10, 11, 12, 13, 14]
        forecast = self.forecaster.forecast_next_period(historical, periods_ahead=1)
        
        # Forecast should be positive and reasonable
        self.assertGreater(forecast, 0)
        self.assertLess(forecast, 30)  # Not absurdly high
    
    def test_empty_data_forecast(self):
        """Test forecasting with empty data"""
        forecast = self.forecaster.forecast_next_period([])
        self.assertEqual(forecast, 0.0)


class TestPopularityCalculator(unittest.TestCase):
    """Test popularity calculation"""
    
    def setUp(self):
        self.calculator = PopularityCalculator(window_days=7, decay_factor=0.9)
    
    def test_sales_velocity(self):
        """Test sales velocity calculation"""
        now = datetime.now()
        sales_data = [
            (now - timedelta(days=2), 5),
            (now - timedelta(days=1), 3),
            (now, 4)
        ]
        
        velocity = self.calculator.calculate_sales_velocity(sales_data)
        
        # Should be positive
        self.assertGreater(velocity, 0)
    
    def test_weighted_velocity(self):
        """Test weighted velocity with decay"""
        now = datetime.now()
        sales_data = [
            (now - timedelta(days=5), 10),  # Older, less weight
            (now, 10)  # Recent, more weight
        ]
        
        velocity = self.calculator.calculate_weighted_velocity(sales_data)
        
        # Recent sales should have more influence
        self.assertGreater(velocity, 0)
    
    def test_trend_detection(self):
        """Test trend detection"""
        now = datetime.now()
        
        # Increasing trend
        increasing_data = [
            (now - timedelta(days=6), 2),
            (now - timedelta(days=3), 5),
            (now, 10)
        ]
        trend = self.calculator.detect_trend(increasing_data)
        self.assertEqual(trend, 'increasing')


class TestAdaptiveThresholdCalculator(unittest.TestCase):
    """Test adaptive threshold calculation"""
    
    def setUp(self):
        self.calculator = AdaptiveThresholdCalculator(base_threshold=20.0)
    
    def test_calculate_threshold(self):
        """Test threshold calculation"""
        threshold = self.calculator.calculate_threshold(
            popularity_index=2.0,
            predicted_demand=5.0,
            lead_time_days=3,
            safety_factor=1.5
        )
        
        # Should be positive and greater than base
        self.assertGreater(threshold, 0)
    
    def test_order_quantity(self):
        """Test order quantity calculation"""
        qty = self.calculator.calculate_order_quantity(
            current_stock=10,
            adaptive_threshold=30,
            predicted_demand=5.0,
            lead_time_days=3,
            max_order=1000,
            min_order=10
        )
        
        # Should order something since stock < threshold
        self.assertGreater(qty, 0)
        self.assertLessEqual(qty, 1000)
    
    def test_no_order_when_stock_sufficient(self):
        """Test no order when stock is sufficient"""
        qty = self.calculator.calculate_order_quantity(
            current_stock=50,
            adaptive_threshold=30,
            predicted_demand=5.0,
            lead_time_days=3
        )
        
        # Should not order
        self.assertEqual(qty, 0)


class TestConfidenceScorer(unittest.TestCase):
    """Test confidence scoring"""
    
    def setUp(self):
        self.scorer = ConfidenceScorer()
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        confidence = self.scorer.calculate_decision_confidence(
            data_quality=0.8,
            trend_clarity=0.7,
            prediction_error=0.2
        )
        
        # Should be between 0 and 1
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_data_quality_assessment(self):
        """Test data quality assessment"""
        quality = self.scorer.assess_data_quality(
            num_data_points=10,
            min_required=7,
            data_completeness=0.9
        )
        
        self.assertGreater(quality, 0.5)


class TestInventoryAgent(unittest.TestCase):
    """Test inventory agent"""
    
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.agent = InventoryAgent(self.db, auto_execute=False)
        
        # Add test product
        self.db.add_product(
            product_id="AGENT-001",
            name="Agent Test Product",
            category="Test",
            initial_stock=25,
            unit_cost=10.0,
            selling_price=20.0,
            lead_time_days=3
        )
    
    def test_make_decision(self):
        """Test agent decision making"""
        decision = self.agent.make_decision("AGENT-001")
        
        # Should return decision dict
        self.assertIn('decision_type', decision)
        self.assertIn('confidence', decision)
        self.assertIn('reasoning', decision)
    
    def test_observe_sale(self):
        """Test sale observation"""
        result = self.agent.observe_sale("AGENT-001", 5)
        
        self.assertTrue(result['success'])
        self.assertIn('decision', result)


class TestSalesSimulator(unittest.TestCase):
    """Test sales simulator"""
    
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.simulator = SalesSimulator(self.db)
    
    def test_generate_product_catalog(self):
        """Test product catalog generation"""
        product_ids = self.simulator.generate_product_catalog(num_products=5)
        
        self.assertEqual(len(product_ids), 5)
        
        # Verify products in database
        products = self.db.get_all_products()
        self.assertEqual(len(products), 5)
    
    def test_simulate_sales_pattern(self):
        """Test sales pattern simulation"""
        sales = self.simulator.simulate_sales_pattern(
            product_id="TEST",
            base_demand=5.0,
            volatility=0.3,
            seasonality=True
        )
        
        # Should generate sales data
        self.assertGreater(len(sales), 0)


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print(" " * 20 + "AIMA TEST SUITE")
    print("=" * 60)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDemandForecaster))
    suite.addTests(loader.loadTestsFromTestCase(TestPopularityCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveThresholdCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestConfidenceScorer))
    suite.addTests(loader.loadTestsFromTestCase(TestInventoryAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestSalesSimulator))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
