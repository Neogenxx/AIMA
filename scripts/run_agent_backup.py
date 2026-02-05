#!/usr/bin/env python3
"""
Run AIMA Agent - 100% CSV-Based
Processes pending sales and makes restock decisions
No database dependencies
"""

import sys
import os
import json

# Get absolute path to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.csv_data_manager import get_csv_manager
from scripts.csv_helpers import atomic_append_csv, get_utc_timestamp


def calculate_demand_prediction(sales_history: list, days: int = 5) -> float:
    """
    Simple demand prediction (average of recent sales)
    
    Args:
        sales_history: List of qty values
        days: Number of days to predict
    
    Returns:
        Predicted demand over next N days
    """
    if not sales_history:
        return 0.0
    
    avg_daily = sum(sales_history) / len(sales_history)
    return avg_daily * days


def calculate_popularity_ewma(current_ewma: float, new_value: float, alpha: float = 0.3) -> float:
    """
    Calculate Exponential Weighted Moving Average for popularity
    
    Args:
        current_ewma: Current EWMA value
        new_value: New sales velocity
        alpha: Smoothing factor (0-1)
    
    Returns:
        Updated EWMA
    """
    if current_ewma == 0:
        return new_value
    return alpha * new_value + (1 - alpha) * current_ewma


def run_agent():
    """Main agent execution - CSV only"""
    
    print("=" * 60)
    print("  AIMA Agent - Batch Processing (CSV-Only)")
    print("=" * 60)
    
    # Initialize CSV manager
    csv_manager = get_csv_manager()
    
    # Load last run metadata
    last_run_path = os.path.join(csv_manager.data_dir, 'last_run.json')
    if os.path.exists(last_run_path):
        with open(last_run_path, 'r') as f:
            last_run = json.load(f)
        start_row = last_run.get('last_processed_row', 0)
    else:
        start_row = 0
    
    print(f"Last processed row: {start_row}")
    
    # Get pending sales
    pending_sales = csv_manager.get_pending_sales(start_row)
    
    if not pending_sales:
        print("No pending sales to process.")
        
        # Update last run with no changes
        last_run_data = {
            'timestamp': get_utc_timestamp(),
            'status': 'ok',
            'last_processed_row': start_row,
            'sales_processed': 0,
            'restocks_created': 0
        }
        with open(last_run_path, 'w') as f:
            json.dump(last_run_data, f, indent=2)
        
        return
    
    print(f"Processing {len(pending_sales)} pending sales...")
    
    # Load all products
    products = csv_manager.get_all_products()
    product_updates = {}  # Track updates per product
    restocks_created = 0
    
    # Process each sale
    for sale in pending_sales:
        product_id = sale['product_id']
        qty = sale['qty']
        
        # Find product
        product = next((p for p in products if p['product_id'] == product_id), None)
        
        if not product:
            print(f"  Warning: Unknown product {product_id}")
            continue
        
        # Initialize updates for this product if needed
        if product_id not in product_updates:
            product_updates[product_id] = {
                'original_stock': product['stock'],
                'stock': product['stock'],
                'sales_qty': []
            }
        
        # Update stock
        current_stock = product_updates[product_id]['stock']
        new_stock = max(0, current_stock - qty)
        product_updates[product_id]['stock'] = new_stock
        product_updates[product_id]['sales_qty'].append(qty)
        
        print(f"  Processed: {product_id} (Stock: {current_stock} → {new_stock})")
    
    # Now update each product and check for restocks
    for product_id, updates in product_updates.items():
        product = next((p for p in products if p['product_id'] == product_id), None)
        if not product:
            continue
        
        new_stock = updates['stock']
        sales_qty = updates['sales_qty']
        
        # Update popularity EWMA
        sales_velocity = sum(sales_qty) / len(sales_qty) if sales_qty else 0
        current_ewma = product['popularity_ewma']
        new_ewma = calculate_popularity_ewma(current_ewma, sales_velocity)
        
        # Calculate popularity index (normalized)
        base_velocity = 1.0
        popularity_index = new_ewma / base_velocity if base_velocity > 0 else 1.0
        
        # Calculate adaptive threshold
        base_threshold = product['base_threshold']
        adjustment_factor = 1 + 0.2 * (popularity_index - 1)
        adaptive_threshold = base_threshold * adjustment_factor
        
        # Check if restock needed
        if new_stock < adaptive_threshold:
            # Calculate restock quantity
            shortage = adaptive_threshold - new_stock
            
            # Predict 5-day demand
            predicted_demand_5d = calculate_demand_prediction(sales_qty, days=5)
            
            restock_qty = int(shortage + predicted_demand_5d)
            restock_qty = max(10, min(restock_qty, 1000))  # Clamp to [10, 1000]
            
            # Confidence score (simplified: based on data availability)
            confidence = min(0.95, 0.5 + 0.1 * len(sales_qty))
            
            # Reason
            reason = f"Stock {new_stock} below threshold {adaptive_threshold:.0f}"
            
            # Append to restock log
            restock_row = [
                get_utc_timestamp(),
                product_id,
                str(new_stock),
                f"{base_threshold:.1f}",
                f"{adaptive_threshold:.1f}",
                f"{predicted_demand_5d:.1f}",
                f"{popularity_index:.2f}",
                str(restock_qty),
                reason,
                f"{confidence:.2f}"
            ]
            
            restock_log_path = os.path.join(csv_manager.data_dir, 'restock_log.csv')
            atomic_append_csv(
                restock_log_path,
                restock_row,
                headers=csv_manager.RESTOCK_LOG_HEADERS
            )
            
            print(f"    → RESTOCK: {restock_qty} units (confidence: {confidence:.0%})")
            restocks_created += 1
        
        # Update product in memory
        product['stock'] = new_stock
        product['popularity_ewma'] = new_ewma
        product['popularity_index'] = popularity_index
        product['adaptive_threshold'] = adaptive_threshold
    
    # Write all products back to CSV
    success = csv_manager.update_inventory_batch({
        p['product_id']: p for p in products
    })
    
    if not success:
        print("\n❌ Failed to update inventory.csv")
        raise Exception("Failed to update inventory")
    
    # Update last run metadata
    last_run_data = {
        'timestamp': get_utc_timestamp(),
        'status': 'ok',
        'last_processed_row': start_row + len(pending_sales),
        'sales_processed': len(pending_sales),
        'restocks_created': restocks_created
    }
    with open(last_run_path, 'w') as f:
        json.dump(last_run_data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"  Agent run complete!")
    print(f"  Sales processed: {len(pending_sales)}")
    print(f"  Restocks created: {restocks_created}")
    print("=" * 60)


if __name__ == '__main__':
    try:
        run_agent()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        
        # Save failure status
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        last_run_path = os.path.join(PROJECT_ROOT, 'data', 'last_run.json')
        
        last_run_data = {
            'timestamp': get_utc_timestamp(),
            'status': 'fail',
            'error': str(e)
        }
        with open(last_run_path, 'w') as f:
            json.dump(last_run_data, f, indent=2)
        
        import traceback
        traceback.print_exc()
        sys.exit(1)
