"""
AIMA Core Engine
Coordinates all components and manages the system lifecycle
"""

import sys
import os
from typing import Dict, List, Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager
from agents.inventory_agent import InventoryAgent
from simulations.simulator import SalesSimulator, PerformanceAnalyzer
from config import AGENT, DATABASE

class AIMAEngine:
    """
    Core engine that orchestrates the AIMA system
    """
    
    def __init__(self, db_path: str = None, auto_execute: bool = False):
        """
        Initialize the AIMA engine
        
        Args:
            db_path: Path to database file
            auto_execute: Whether agent should auto-execute restock orders
        """
        # Initialize database
        db_path = db_path or DATABASE.DB_PATH
        self.db = DatabaseManager(db_path)
        
        # Initialize agent
        self.agent = InventoryAgent(self.db, auto_execute=auto_execute)
        
        # Initialize simulator and analyzer
        self.simulator = SalesSimulator(self.db)
        self.analyzer = PerformanceAnalyzer(self.db)
        
        self.auto_execute = auto_execute
        
        print("=" * 50)
        print("  AIMA - Autonomous Inventory Management Agent")
        print("=" * 50)
        print(f"Database: {db_path}")
        print(f"Auto-execute: {auto_execute}")
        print(f"Initialized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
    
    def setup_demo_environment(self, num_products: int = 20, 
                              simulate_days: int = 30) -> Dict:
        """
        Setup demo environment with simulated data
        
        Args:
            num_products: Number of products to create
            simulate_days: Days of sales history to simulate
        
        Returns:
            Setup summary
        """
        print("\n🔧 Setting up demo environment...")
        
        # Generate product catalog
        product_ids = self.simulator.generate_product_catalog(num_products)
        
        # Run initial simulation
        print(f"\n📊 Simulating {simulate_days} days of sales...")
        sim_results = self.simulator.run_simulation(days=simulate_days)
        
        # Run initial analysis
        print("\n🤖 Running initial agent analysis...")
        decisions = self.agent.analyze_all_products()
        
        return {
            "products_created": num_products,
            "days_simulated": simulate_days,
            "simulation_results": sim_results,
            "initial_decisions": len(decisions)
        }
    
    def process_sale(self, product_id: str, quantity: int) -> Dict:
        """
        Process a sale and trigger agent decision
        
        Args:
            product_id: Product identifier
            quantity: Quantity sold
        
        Returns:
            Processing result
        """
        result = self.agent.observe_sale(product_id, quantity)
        
        if result['success']:
            decision = result['decision']
            
            print(f"\n💰 Sale processed: {quantity} units of {product_id}")
            
            if decision.get('needs_restock'):
                print(f"⚠️  RESTOCK ALERT")
                print(f"   Stock: {decision['current_stock']} → Threshold: {decision['adaptive_threshold']}")
                print(f"   Recommended order: {decision['order_quantity']} units")
                
                if decision.get('executed'):
                    print(f"   ✓ Order #{decision['order_id']} created automatically")
        
        return result
    
    def analyze_product(self, product_id: str) -> Dict:
        """
        Analyze a specific product
        
        Args:
            product_id: Product identifier
        
        Returns:
            Analysis results
        """
        decision = self.agent.make_decision(product_id)
        
        print(f"\n📊 Analysis for {decision.get('product_name', product_id)}")
        print(f"   Current Stock: {decision['current_stock']}")
        print(f"   Adaptive Threshold: {decision['adaptive_threshold']}")
        print(f"   Popularity Index: {decision['popularity_index']}")
        print(f"   Sales Velocity: {decision['sales_velocity']} units/day")
        print(f"   Trend: {decision['trend']}")
        print(f"   Predicted Demand: {decision['predicted_demand']} units/day")
        print(f"   Confidence: {decision['confidence'] * 100:.1f}%")
        print(f"\n   Decision: {decision['decision_type'].upper()}")
        
        if decision['needs_restock']:
            print(f"   Order Quantity: {decision['order_quantity']} units")
        
        print(f"\n   Reasoning: {decision['reasoning']}")
        
        return decision
    
    def run_continuous_monitoring(self, interval_seconds: int = 60):
        """
        Run agent in continuous monitoring mode
        
        Args:
            interval_seconds: Check interval in seconds
        """
        self.agent.run_continuous(check_interval_seconds=interval_seconds)
    
    def generate_performance_report(self) -> str:
        """
        Generate comprehensive performance report
        
        Returns:
            Report string
        """
        return self.analyzer.generate_report()
    
    def get_dashboard_data(self) -> Dict:
        """
        Get data for dashboard display
        
        Returns:
            Dashboard data dictionary
        """
        return self.db.get_dashboard_data()
    
    def list_products(self) -> List[Dict]:
        """
        List all products
        
        Returns:
            List of product dictionaries
        """
        products = self.db.get_all_products()
        
        print(f"\n📦 Products ({len(products)} total):")
        print("-" * 80)
        print(f"{'ID':<12} {'Name':<25} {'Stock':<8} {'Category':<15}")
        print("-" * 80)
        
        for product in products:
            print(f"{product['product_id']:<12} "
                  f"{product['name']:<25} "
                  f"{product['current_stock']:<8} "
                  f"{product['category']:<15}")
        
        return products
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent agent decisions
        
        Args:
            limit: Number of decisions to retrieve
        
        Returns:
            List of decision dictionaries
        """
        decisions = self.db.get_recent_decisions(limit)
        
        print(f"\n🤖 Recent Decisions ({len(decisions)} shown):")
        print("-" * 100)
        
        for decision in decisions:
            timestamp = decision['decision_date']
            product = decision['product_name']
            decision_type = decision['decision_type'].upper()
            executed = "✓" if decision['executed'] else "○"
            
            print(f"{executed} [{timestamp}] {product}: {decision_type} "
                  f"(confidence: {decision['confidence_score']*100:.0f}%)")
        
        return decisions
    
    def simulate_sales_day(self) -> Dict:
        """
        Simulate one day of sales activity
        
        Returns:
            Simulation results
        """
        import random
        
        products = self.db.get_all_products()
        sales_count = 0
        decisions_made = 0
        
        print("\n🎲 Simulating sales day...")
        
        for product in products:
            # Random chance of sale
            if random.random() < 0.3:  # 30% chance per product
                quantity = random.randint(1, 10)
                result = self.process_sale(product['product_id'], quantity)
                
                if result['success']:
                    sales_count += 1
                    decisions_made += 1
        
        print(f"\n✓ Day complete: {sales_count} sales, {decisions_made} decisions made")
        
        return {
            "sales_processed": sales_count,
            "decisions_made": decisions_made
        }
    
    def shutdown(self):
        """Shutdown the engine gracefully"""
        print("\n👋 AIMA Engine shutting down...")
        print("   All data saved to database")
        print("   Goodbye!")


class AIMACommandProcessor:
    """Processes text commands for AIMA"""
    
    def __init__(self, engine: AIMAEngine):
        self.engine = engine
    
    def process_command(self, command: str) -> str:
        """
        Process a natural language command
        
        Args:
            command: Command string
        
        Returns:
            Response string
        """
        command = command.lower().strip()
        
        # Sale commands
        if "sell" in command or "sale" in command:
            # Extract product and quantity
            # Format: "sell 5 units of PROD-001"
            parts = command.split()
            try:
                quantity = int(parts[1])
                product_id = parts[-1].upper()
                result = self.engine.process_sale(product_id, quantity)
                return f"Sale processed: {result}"
            except:
                return "Format: 'sell <quantity> units of <product_id>'"
        
        # Analysis commands
        elif "analyze" in command:
            parts = command.split()
            if len(parts) >= 2:
                product_id = parts[-1].upper()
                self.engine.analyze_product(product_id)
                return "Analysis complete"
            else:
                self.engine.agent.analyze_all_products()
                return "All products analyzed"
        
        # List commands
        elif "list" in command or "show products" in command:
            self.engine.list_products()
            return "Products listed"
        
        # Decision history
        elif "decisions" in command or "history" in command:
            self.engine.get_recent_decisions()
            return "Recent decisions shown"
        
        # Report
        elif "report" in command or "performance" in command:
            report = self.engine.generate_performance_report()
            print(report)
            return "Report generated"
        
        # Simulate
        elif "simulate" in command:
            if "day" in command:
                self.engine.simulate_sales_day()
                return "Day simulated"
            else:
                return "Use 'simulate day' to simulate one day of sales"
        
        # Help
        elif "help" in command:
            return self._get_help()
        
        else:
            return "Unknown command. Type 'help' for available commands."
    
    def _get_help(self) -> str:
        """Get help text"""
        return """
Available Commands:
  sell <qty> units of <product_id>  - Process a sale
  analyze <product_id>               - Analyze specific product
  analyze all                        - Analyze all products
  list products                      - List all products
  decisions                          - Show recent decisions
  report                             - Generate performance report
  simulate day                       - Simulate one day of sales
  help                               - Show this help
        """
