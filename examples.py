#!/usr/bin/env python3
"""
AIMA Usage Examples
Demonstrates various ways to use the AIMA system
"""

import sys
from engine.core import AIMAEngine
from utils.database import DatabaseManager
from agents.inventory_agent import InventoryAgent

def example_1_basic_setup():
    """Example 1: Basic Setup and First Sale"""
    
    print("\n" + "="*60)
    print("Example 1: Basic Setup and First Sale")
    print("="*60)
    
    # Initialize engine
    engine = AIMAEngine(db_path="data/example1.db", auto_execute=False)
    
    # Add a product manually
    engine.db.add_product(
        product_id="LAPTOP-001",
        name="Gaming Laptop X1",
        category="Electronics",
        initial_stock=50,
        unit_cost=800.0,
        selling_price=1200.0,
        supplier="supplier_a",
        lead_time_days=3
    )
    
    print("✓ Product added: Gaming Laptop X1")
    
    # Simulate some sales
    print("\nSimulating sales over time...")
    for i in range(5):
        result = engine.process_sale("LAPTOP-001", quantity=2)
        print(f"  Day {i+1}: Sold 2 units")
    
    # Analyze the product
    print("\nAgent Analysis:")
    decision = engine.analyze_product("LAPTOP-001")
    
    print("\n✓ Example 1 complete!")


def example_2_automated_restocking():
    """Example 2: Automated Restocking with Auto-Execute"""
    
    print("\n" + "="*60)
    print("Example 2: Automated Restocking")
    print("="*60)
    
    # Initialize with auto-execute enabled
    engine = AIMAEngine(db_path="data/example2.db", auto_execute=True)
    
    # Add product with low stock
    engine.db.add_product(
        product_id="COFFEE-001",
        name="Premium Coffee Beans",
        category="Food & Beverage",
        initial_stock=15,  # Low initial stock
        unit_cost=8.0,
        selling_price=15.0,
        supplier="supplier_b",
        lead_time_days=2
    )
    
    print("✓ Product added with low stock (15 units)")
    
    # Make a sale that should trigger restocking
    print("\nProcessing sale of 10 units...")
    result = engine.process_sale("COFFEE-001", quantity=10)
    
    # Check decision
    decision = result.get('decision', {})
    if decision.get('executed'):
        print(f"\n✓ Automatic restock order created!")
        print(f"  Order ID: {decision['order_id']}")
        print(f"  Quantity: {decision['order_quantity']} units")
    else:
        print("\nNo automatic restock (confidence too low or stock sufficient)")
    
    print("\n✓ Example 2 complete!")


def example_3_popularity_tracking():
    """Example 3: Tracking Product Popularity"""
    
    print("\n" + "="*60)
    print("Example 3: Tracking Product Popularity")
    print("="*60)
    
    engine = AIMAEngine(db_path="data/example3.db")
    
    # Add multiple products
    products = [
        ("SHIRT-001", "Basic T-Shirt", 100),
        ("SHIRT-002", "Premium T-Shirt", 100),
    ]
    
    for prod_id, name, stock in products:
        engine.db.add_product(
            product_id=prod_id,
            name=name,
            category="Clothing",
            initial_stock=stock,
            unit_cost=5.0,
            selling_price=15.0
        )
    
    print("✓ Added 2 products with equal initial stock")
    
    # Simulate different popularity
    print("\nSimulating sales patterns...")
    print("  Basic T-Shirt: Low popularity (1-2 units/day)")
    for _ in range(7):
        engine.db.record_sale("SHIRT-001", 1)
    
    print("  Premium T-Shirt: High popularity (5-8 units/day)")
    for _ in range(7):
        engine.db.record_sale("SHIRT-002", 6)
    
    # Analyze both
    print("\nAnalyzing products...")
    print("\n--- Basic T-Shirt ---")
    decision1 = engine.agent.make_decision("SHIRT-001")
    print(f"Popularity: {decision1['popularity_index']:.2f}")
    print(f"Threshold: {decision1['adaptive_threshold']:.0f}")
    
    print("\n--- Premium T-Shirt ---")
    decision2 = engine.agent.make_decision("SHIRT-002")
    print(f"Popularity: {decision2['popularity_index']:.2f}")
    print(f"Threshold: {decision2['adaptive_threshold']:.0f}")
    
    print("\nNotice how the high-popularity product has a higher threshold!")
    print("\n✓ Example 3 complete!")


def example_4_demand_forecasting():
    """Example 4: Demand Forecasting in Action"""
    
    print("\n" + "="*60)
    print("Example 4: Demand Forecasting")
    print("="*60)
    
    engine = AIMAEngine(db_path="data/example4.db")
    
    # Add product
    engine.db.add_product(
        product_id="SNACKS-001",
        name="Protein Bars",
        category="Food & Beverage",
        initial_stock=200,
        unit_cost=1.0,
        selling_price=2.5
    )
    
    print("✓ Product added: Protein Bars")
    
    # Simulate increasing demand trend
    print("\nSimulating 14 days of increasing sales...")
    for day in range(14):
        quantity = 5 + (day // 2)  # Gradually increasing
        engine.db.record_sale("SNACKS-001", quantity)
        print(f"  Day {day+1}: {quantity} units sold")
    
    # Analyze with forecasting
    print("\nAgent Analysis with Forecasting:")
    decision = engine.agent.make_decision("SNACKS-001")
    
    print(f"Current Stock: {decision['current_stock']}")
    print(f"Sales Velocity: {decision['sales_velocity']:.2f} units/day")
    print(f"Trend: {decision['trend']}")
    print(f"Predicted Demand: {decision['predicted_demand']:.2f} units/day")
    
    print("\nAgent detected the increasing trend and adjusted predictions!")
    print("\n✓ Example 4 complete!")


def example_5_batch_analysis():
    """Example 5: Batch Analysis of Multiple Products"""
    
    print("\n" + "="*60)
    print("Example 5: Batch Analysis")
    print("="*60)
    
    engine = AIMAEngine(db_path="data/example5.db")
    
    # Setup demo environment
    print("Setting up demo environment...")
    engine.setup_demo_environment(num_products=10, simulate_days=15)
    
    # Analyze all products
    print("\nRunning batch analysis on all products...")
    decisions = engine.agent.analyze_all_products()
    
    # Filter products needing restock
    restock_needed = [d for d in decisions if d['needs_restock']]
    
    print(f"\nSummary:")
    print(f"  Total products analyzed: {len(decisions)}")
    print(f"  Products needing restock: {len(restock_needed)}")
    
    if restock_needed:
        print("\nTop restock priorities:")
        sorted_restock = sorted(restock_needed, 
                               key=lambda x: x['current_stock'])
        for i, decision in enumerate(sorted_restock[:5], 1):
            print(f"  {i}. {decision['product_name']}: "
                  f"Stock={decision['current_stock']}, "
                  f"Order={decision['order_quantity']} units")
    
    print("\n✓ Example 5 complete!")


def example_6_performance_monitoring():
    """Example 6: Performance Monitoring and Reporting"""
    
    print("\n" + "="*60)
    print("Example 6: Performance Monitoring")
    print("="*60)
    
    engine = AIMAEngine(db_path="data/example6.db")
    
    # Setup and run simulation
    print("Running 30-day simulation...")
    engine.setup_demo_environment(num_products=15, simulate_days=30)
    
    # Generate performance report
    print("\nGenerating performance report...")
    report = engine.generate_performance_report()
    print(report)
    
    # Get dashboard data
    dashboard_data = engine.get_dashboard_data()
    
    print(f"\nDashboard Insights:")
    print(f"  Total products: {len(dashboard_data['products'])}")
    print(f"  Recent decisions: {len(dashboard_data['recent_decisions'])}")
    print(f"  Pending orders: {len(dashboard_data['pending_orders'])}")
    
    print("\n✓ Example 6 complete!")


def example_7_custom_agent_configuration():
    """Example 7: Custom Agent Configuration"""
    
    print("\n" + "="*60)
    print("Example 7: Custom Agent Configuration")
    print("="*60)
    
    # Create custom database and agent
    db = DatabaseManager("data/example7.db")
    agent = InventoryAgent(db, auto_execute=False)
    
    # Customize agent parameters
    print("Customizing agent parameters...")
    agent.threshold_calculator.base_threshold = 30.0
    agent.threshold_calculator.adjustment_rate = 0.3
    agent.demand_forecaster.alpha = 0.4
    
    print("✓ Agent configured with custom parameters:")
    print(f"  Base threshold: 30 units")
    print(f"  Adjustment rate: 0.3")
    print(f"  Smoothing alpha: 0.4")
    
    # Add product and test
    db.add_product(
        product_id="CUSTOM-001",
        name="Custom Product",
        category="Test",
        initial_stock=40,
        unit_cost=10.0,
        selling_price=20.0
    )
    
    # Make decision
    decision = agent.make_decision("CUSTOM-001")
    print(f"\nDecision with custom config:")
    print(f"  Threshold: {decision['adaptive_threshold']:.0f}")
    print(f"  Stock: {decision['current_stock']}")
    
    print("\n✓ Example 7 complete!")


def main():
    """Run all examples"""
    
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                                                          ║")
    print("║         AIMA Usage Examples                              ║")
    print("║                                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    examples = [
        ("Basic Setup and First Sale", example_1_basic_setup),
        ("Automated Restocking", example_2_automated_restocking),
        ("Popularity Tracking", example_3_popularity_tracking),
        ("Demand Forecasting", example_4_demand_forecasting),
        ("Batch Analysis", example_5_batch_analysis),
        ("Performance Monitoring", example_6_performance_monitoring),
        ("Custom Configuration", example_7_custom_agent_configuration),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print("  0. Run all examples")
    
    try:
        choice = input("\nSelect example (0-7): ").strip()
        
        if choice == "0":
            for name, func in examples:
                func()
                input("\nPress Enter to continue to next example...")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            examples[int(choice)-1][1]()
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\nExamples interrupted.")
    
    print("\n" + "="*60)
    print("Examples completed! Check data/ directory for databases.")
    print("="*60)


if __name__ == "__main__":
    main()
