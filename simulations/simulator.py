"""
Simulation Engine for AIMA
Generates realistic sales data and tests agent performance
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager
from agents.inventory_agent import InventoryAgent
from config import SIMULATION, PRODUCT_CATEGORIES

class SalesSimulator:
    """Simulates realistic sales patterns for testing"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.simulation_date = datetime.now() - timedelta(days=SIMULATION.SIMULATION_DAYS)
    
    def generate_product_catalog(self, num_products: int = None) -> List[str]:
        """
        Generate a catalog of products
        
        Returns:
            List of product IDs
        """
        num_products = num_products or SIMULATION.NUM_PRODUCTS
        
        product_templates = [
            "Laptop", "Smartphone", "Headphones", "Keyboard", "Mouse",
            "T-Shirt", "Jeans", "Sneakers", "Jacket", "Hat",
            "Coffee", "Tea", "Snacks", "Water", "Energy Drink",
            "Desk Lamp", "Chair", "Plant", "Clock", "Rug",
            "Basketball", "Tennis Racket", "Yoga Mat", "Dumbbells", "Bicycle",
            "Novel", "Magazine", "Comics", "Textbook", "Calendar",
            "Shampoo", "Soap", "Toothpaste", "Vitamins", "Sunscreen",
            "Board Game", "Puzzle", "Action Figure", "Doll", "Building Blocks"
        ]
        
        products = []
        
        for i in range(num_products):
            product_name = random.choice(product_templates)
            product_id = f"PROD-{i+1:03d}"
            category = random.choice(PRODUCT_CATEGORIES)
            
            # Vary pricing
            base_cost = random.uniform(5, 100)
            unit_cost = round(base_cost, 2)
            selling_price = round(base_cost * random.uniform(1.3, 2.0), 2)
            
            # Initial stock
            initial_stock = random.randint(50, 200)
            
            # Add product
            self.db.add_product(
                product_id=product_id,
                name=f"{product_name} {i+1}",
                category=category,
                initial_stock=initial_stock,
                unit_cost=unit_cost,
                selling_price=selling_price,
                supplier=random.choice(["supplier_a", "supplier_b", "supplier_c"]),
                lead_time_days=random.randint(2, 5)
            )
            
            products.append(product_id)
        
        print(f"✓ Generated {num_products} products")
        return products
    
    def simulate_sales_pattern(self, product_id: str, base_demand: float,
                               volatility: float, seasonality: bool = True) -> List[int]:
        """
        Generate realistic daily sales for a product
        
        Args:
            product_id: Product identifier
            base_demand: Average daily demand
            volatility: Volatility factor (std dev / mean)
            seasonality: Whether to include seasonal patterns
        
        Returns:
            List of daily sales quantities
        """
        daily_sales = []
        
        for day in range(SIMULATION.SIMULATION_DAYS):
            # Base demand
            demand = base_demand
            
            # Add seasonality (weekly pattern)
            if seasonality:
                day_of_week = (self.simulation_date + timedelta(days=day)).weekday()
                # Higher sales on weekends
                if day_of_week >= 5:  # Saturday, Sunday
                    demand *= 1.3
                elif day_of_week == 4:  # Friday
                    demand *= 1.15
            
            # Add trend (some products grow, some decline)
            trend_factor = 1 + (random.uniform(-0.001, 0.002) * day)
            demand *= trend_factor
            
            # Add random noise
            noise = random.gauss(0, volatility * base_demand)
            demand = max(0, demand + noise)
            
            # Convert to integer
            daily_sales.append(int(round(demand)))
        
        return daily_sales
    
    def run_simulation(self, days: int = None, agent: InventoryAgent = None) -> Dict:
        """
        Run full simulation
        
        Args:
            days: Number of days to simulate (default from config)
            agent: InventoryAgent instance to use
        
        Returns:
            Simulation results
        """
        days = days or SIMULATION.SIMULATION_DAYS
        
        print(f"\n🎬 Starting {days}-day simulation...")
        
        # Get all products
        products = self.db.get_all_products()
        
        if not products:
            print("No products found. Generating catalog...")
            product_ids = self.generate_product_catalog()
            products = self.db.get_all_products()
        
        # Track metrics
        total_sales = 0
        total_restocks = 0
        stockouts = 0
        decisions_made = 0
        
        # Generate sales patterns for each product
        sales_patterns = {}
        for product in products:
            base_demand = random.uniform(1, 15)
            volatility = SIMULATION.SALES_VOLATILITY
            sales_patterns[product['product_id']] = self.simulate_sales_pattern(
                product['product_id'],
                base_demand,
                volatility
            )
        
        # Simulate day by day
        for day in range(days):
            current_date = self.simulation_date + timedelta(days=day)
            
            # Process sales for each product
            for product in products:
                product_id = product['product_id']
                daily_quantity = sales_patterns[product_id][day]
                
                if daily_quantity > 0:
                    # Attempt sale
                    success = self.db.record_sale(product_id, daily_quantity)
                    
                    if success:
                        total_sales += daily_quantity
                        
                        # Trigger agent decision if agent provided
                        if agent and random.random() < 0.3:  # 30% chance to trigger analysis
                            decision = agent.make_decision(product_id)
                            decisions_made += 1
                            
                            if decision.get('needs_restock'):
                                total_restocks += 1
                    else:
                        stockouts += 1
            
            # Process pending deliveries
            if day > 0 and random.random() < 0.2:  # 20% chance daily
                self._process_pending_deliveries()
            
            # Progress indicator
            if (day + 1) % 10 == 0:
                print(f"  Day {day + 1}/{days} - Sales: {total_sales}, Restocks: {total_restocks}")
        
        results = {
            "days_simulated": days,
            "total_sales": total_sales,
            "total_restocks": total_restocks,
            "stockouts": stockouts,
            "decisions_made": decisions_made,
            "products_tracked": len(products)
        }
        
        print(f"\n✓ Simulation complete!")
        print(f"  Total sales: {total_sales} units")
        print(f"  Restock orders: {total_restocks}")
        print(f"  Stockouts: {stockouts}")
        print(f"  Agent decisions: {decisions_made}")
        
        return results
    
    def _process_pending_deliveries(self):
        """Process pending restock orders that should have arrived"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get orders that should have arrived
            cursor.execute("""
                SELECT order_id FROM restock_orders
                WHERE status = 'pending'
                AND expected_delivery_date <= datetime('now')
                LIMIT 5
            """)
            
            orders = cursor.fetchall()
            
            for order in orders:
                self.db.receive_restock_order(order['order_id'])


class PerformanceAnalyzer:
    """Analyzes AIMA agent performance"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def analyze_decision_accuracy(self) -> Dict:
        """
        Analyze how accurate agent predictions were
        
        Returns:
            Analysis results
        """
        decisions = self.db.get_recent_decisions(limit=100)
        
        if not decisions:
            return {"error": "No decisions to analyze"}
        
        total_decisions = len(decisions)
        restock_decisions = sum(1 for d in decisions if d['decision_type'] == 'restock')
        executed_decisions = sum(1 for d in decisions if d['executed'])
        
        avg_confidence = np.mean([d['confidence_score'] for d in decisions])
        
        return {
            "total_decisions": total_decisions,
            "restock_recommendations": restock_decisions,
            "executed_restocks": executed_decisions,
            "average_confidence": round(avg_confidence, 3),
            "execution_rate": round(executed_decisions / total_decisions if total_decisions > 0 else 0, 3)
        }
    
    def analyze_inventory_health(self) -> Dict:
        """
        Analyze overall inventory health
        
        Returns:
            Health metrics
        """
        products = self.db.get_all_products()
        
        total_value = sum(p['current_stock'] * p['unit_cost'] for p in products)
        avg_stock = np.mean([p['current_stock'] for p in products])
        
        # Count low stock items
        low_stock_count = sum(1 for p in products if p['current_stock'] < 20)
        
        return {
            "total_products": len(products),
            "total_inventory_value": round(total_value, 2),
            "average_stock_level": round(avg_stock, 2),
            "low_stock_items": low_stock_count,
            "low_stock_percentage": round(100 * low_stock_count / len(products) if products else 0, 1)
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive performance report"""
        
        decision_analysis = self.analyze_decision_accuracy()
        inventory_health = self.analyze_inventory_health()
        
        report = f"""
╔════════════════════════════════════════╗
║     AIMA PERFORMANCE REPORT           ║
╠════════════════════════════════════════╣
║ DECISION ANALYSIS                      ║
║  Total Decisions: {decision_analysis.get('total_decisions', 0):<20} ║
║  Restock Recommendations: {decision_analysis.get('restock_recommendations', 0):<11} ║
║  Executed: {decision_analysis.get('executed_restocks', 0):<27} ║
║  Avg Confidence: {decision_analysis.get('average_confidence', 0):<18} ║
║                                        ║
║ INVENTORY HEALTH                       ║
║  Total Products: {inventory_health.get('total_products', 0):<20} ║
║  Total Value: ${inventory_health.get('total_inventory_value', 0):<21.2f} ║
║  Avg Stock Level: {inventory_health.get('average_stock_level', 0):<18} ║
║  Low Stock Items: {inventory_health.get('low_stock_items', 0):<18} ║
║  ({inventory_health.get('low_stock_percentage', 0):.1f}%)                          ║
╚════════════════════════════════════════╝
        """
        
        return report
