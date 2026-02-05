"""
AIMA - Autonomous Inventory Management Agent
Main Application Entry Point (CSV-Only Version)
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.csv_data_manager import get_csv_manager
from scripts.run_agent import run_agent
import subprocess


def run_demo(num_products: int = 20, simulate_sales: int = 50):
    """Setup demo environment with CSV data"""
    print("\n🚀 Setting up AIMA Demo Environment (CSV-Only)...\n")
    
    csv_manager = get_csv_manager()
    
    # Generate sample products
    from simulations.product_generator import generate_demo_products
    products = generate_demo_products(num_products)
    
    # Write to inventory.csv
    success = csv_manager.update_inventory_batch({
        p['product_id']: p for p in products
    })
    
    if success:
        print(f"✅ Created {num_products} products in inventory.csv")
    else:
        print("❌ Failed to create products")
        return
    
    # Optionally simulate sales
    if simulate_sales > 0:
        from simulations.sales_simulator import simulate_sales_batch
        simulate_sales_batch(simulate_sales)
        print(f"✅ Simulated {simulate_sales} sales transactions")
    
    print("\n" + "=" * 60)
    print("Demo Setup Complete!")
    print("=" * 60)
    print("Next steps:")
    print("  python web_server.py         # Launch web dashboard")
    print("  python scripts/run_agent.py  # Process pending sales")
    print("=" * 60 + "\n")


def run_dashboard():
    """Launch web dashboard"""
    print("\n📊 Launching AIMA Dashboard (CSV-Only)...")
    print("URL: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    # Import and run Flask app
    from web_server import app
    app.run(debug=True, host='0.0.0.0', port=5000)


def run_analysis():
    """Analyze all products and show statistics"""
    print("\n📊 Analyzing Inventory (CSV-Only)...\n")
    
    csv_manager = get_csv_manager()
    data = csv_manager.get_dashboard_data()
    
    products = data['products']
    metrics = data['metrics']
    
    print("=" * 80)
    print("INVENTORY SUMMARY")
    print("=" * 80)
    print(f"Total Products: {metrics['total_products']}")
    print(f"Total Stock: {metrics['total_stock']} units")
    print(f"Total Value: ${metrics['total_value']:,.2f}")
    print(f"Low Stock Items: {metrics['low_stock_count']}")
    print(f"Out of Stock: {metrics['out_of_stock']}")
    print(f"Total Revenue: ${metrics['total_revenue']:,.2f}")
    print(f"Total Profit: ${metrics['total_profit']:,.2f}")
    print("=" * 80)
    
    # Show products by status
    critical = [p for p in products if p['status'] == 'critical']
    low = [p for p in products if p['status'] == 'low']
    ok = [p for p in products if p['status'] == 'ok']
    
    if critical:
        print(f"\n🚨 CRITICAL ({len(critical)} items):")
        for p in critical[:10]:
            print(f"  {p['product_id']}: {p['name']} - Stock: {p['stock']} (Threshold: {p['adaptive_threshold']:.0f})")
    
    if low:
        print(f"\n⚠️  LOW STOCK ({len(low)} items):")
        for p in low[:10]:
            print(f"  {p['product_id']}: {p['name']} - Stock: {p['stock']} (Threshold: {p['adaptive_threshold']:.0f})")
    
    print(f"\n✅ OK ({len(ok)} items)")
    
    # Show recent restocks
    print("\n" + "=" * 80)
    print("RECENT RESTOCK DECISIONS")
    print("=" * 80)
    
    restocks = data['recent_restocks']
    for r in restocks[-10:]:
        print(f"  {r['timestamp']}: {r['product_id']} → {r['restock_qty']} units")
        print(f"    Reason: {r['reason']} (confidence: {float(r['confidence']):.0%})")


def run_pending_check():
    """Check pending sales status"""
    print("\n📋 Checking Pending Sales...\n")
    
    csv_manager = get_csv_manager()
    
    import json
    import os
    last_run_path = os.path.join(csv_manager.data_dir, 'last_run.json')
    
    if os.path.exists(last_run_path):
        with open(last_run_path, 'r') as f:
            last_run = json.load(f)
        last_processed = last_run.get('last_processed_row', 0)
    else:
        last_processed = 0
    
    all_sales = csv_manager.get_all_sales()
    pending = all_sales[last_processed:]
    
    print(f"Total sales logged: {len(all_sales)}")
    print(f"Last processed: {last_processed}")
    print(f"Pending sales: {len(pending)}")
    
    if pending:
        print("\n" + "=" * 80)
        print("PENDING SALES (Not Yet Processed by Agent)")
        print("=" * 80)
        
        # Group by product
        from collections import defaultdict
        by_product = defaultdict(int)
        for sale in pending:
            by_product[sale['product_id']] += sale['qty']
        
        for product_id, qty in sorted(by_product.items()):
            product = csv_manager.get_product(product_id)
            if product:
                projected = max(0, product['stock'] - qty)
                print(f"  {product_id}: {product['name']}")
                print(f"    Current: {product['stock']} → Projected: {projected} (Pending: -{qty})")
        
        print("\n💡 Run agent to process: python scripts/run_agent.py")
    else:
        print("\n✅ All sales have been processed by agent")



def main():
    """Main application entry point"""
    
    parser = argparse.ArgumentParser(
        description="AIMA - Autonomous Inventory Management Agent (CSV-Only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py demo              # Setup demo environment
  python app.py dashboard         # Launch web dashboard
  python app.py analyze           # Analyze inventory
  python app.py agent             # Process pending sales
  python app.py pending           # Check pending sales status
        """
    )
    
    parser.add_argument(
        'command',
        choices=['demo', 'dashboard', 'analyze', 'agent', 'pending'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--products',
        type=int,
        default=20,
        help='Number of products for demo (default: 20)'
    )
    
    parser.add_argument(
        '--sales',
        type=int,
        default=50,
        help='Number of sales to simulate in demo (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'demo':
        run_demo(num_products=args.products, simulate_sales=args.sales)
    
    elif args.command == 'dashboard':
        run_dashboard()
    
    elif args.command == 'analyze':
        run_analysis()
    
    elif args.command == 'agent':
        # Run agent script
        run_agent()
    
    elif args.command == 'pending':
        run_pending_check()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 AIMA terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
