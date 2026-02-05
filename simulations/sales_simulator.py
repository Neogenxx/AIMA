"""
Sales Simulator - Generate realistic sales for testing
"""

import random
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.csv_data_manager import get_csv_manager
from scripts.csv_helpers import atomic_append_csv, get_utc_timestamp


def simulate_sales_batch(count: int = 50):
    """
    Simulate a batch of sales transactions
    
    Args:
        count: Number of sales to simulate
    """
    csv_manager = get_csv_manager()
    products = csv_manager.get_all_products()
    
    if not products:
        print("❌ No products in inventory. Run demo setup first.")
        return
    
    print(f"\n📊 Simulating {count} sales transactions...")
    
    success_count = 0
    
    for i in range(count):
        # Pick random product (weighted by popularity)
        product = random.choice(products)
        
        # Random quantity (1-10, but weighted toward smaller values)
        qty = random.choices([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                            weights=[30, 25, 20, 10, 5, 4, 3, 1, 1, 1])[0]
        
        # Check stock
        if product['stock'] < qty:
            qty = product['stock']
        
        if qty <= 0:
            continue
        
        # Calculate pricing
        cost_price = product['cost_price']
        selling_price = product['selling_price']
        total_cost = cost_price * qty
        total_revenue = selling_price * qty
        profit = total_revenue - total_cost
        
        # Create sale row
        row = [
            get_utc_timestamp(),
            product['product_id'],
            str(qty),
            f"{cost_price:.2f}",
            f"{selling_price:.2f}",
            f"{total_cost:.2f}",
            f"{total_revenue:.2f}",
            f"{profit:.2f}"
        ]
        
        # Append to sales log
        sales_log_path = os.path.join(csv_manager.data_dir, 'sales_log.csv')
        if atomic_append_csv(sales_log_path, row, headers=csv_manager.SALES_LOG_HEADERS):
            success_count += 1
            print(f"  ✓ Sale #{i+1}: {qty}x {product['name']} (Profit: ${profit:.2f})")
        else:
            print(f"  ✗ Sale #{i+1}: Failed")
    
    print(f"\n✅ Successfully simulated {success_count}/{count} sales")
    print(f"💡 Run agent to process: python scripts/run_agent.py")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulate sales transactions')
    parser.add_argument('--count', type=int, default=50, help='Number of sales to simulate')
    args = parser.parse_args()
    
    simulate_sales_batch(args.count)
