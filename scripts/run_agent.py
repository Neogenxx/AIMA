#!/usr/bin/env python3
"""
Run AIMA Agent
Processes pending sales and makes restock decisions
"""

import sys
import os
import json
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.csv_helpers import (
    read_csv, write_csv, atomic_append_csv, get_utc_timestamp
)


def load_last_run() -> dict:
    """Load last run metadata"""
    path = 'data/last_run.json'
    if not os.path.exists(path):
        return {
            'timestamp': None,
            'status': 'never_run',
            'last_processed_row': 0,
            'sales_processed': 0,
            'restocks_created': 0
        }
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return {'last_processed_row': 0}


def save_last_run(data: dict):
    """Save last run metadata"""
    path = 'data/last_run.json'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


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
    """Main agent execution"""
    
    print("=" * 60)
    print("  AIMA Agent - Batch Processing")
    print("=" * 60)
    
    # Load metadata
    last_run = load_last_run()
    start_row = last_run.get('last_processed_row', 0)
    
    print(f"Last processed row: {start_row}")
    
    # Load sales log
    sales_log = read_csv('data/sales_log.csv')
    pending_sales = sales_log[start_row:]
    
    if not pending_sales:
        print("No pending sales to process.")
        save_last_run({
            'timestamp': get_utc_timestamp(),
            'status': 'ok',
            'last_processed_row': start_row,
            'sales_processed': 0,
            'restocks_created': 0
        })
        return
    
    print(f"Processing {len(pending_sales)} pending sales...")
    
    # Load inventory
    inventory = read_csv('data/inventory.csv')
    inventory_dict = {row['product_id']: row for row in inventory}
    
    # Process each sale
    restocks_created = 0
    
    for sale in pending_sales:
        product_id = sale['product_id']
        qty = int(sale['qty'])
        
        if product_id not in inventory_dict:
            print(f"  Warning: Unknown product {product_id}")
            continue
        
        product = inventory_dict[product_id]
        
        # Update stock
        current_stock = int(product['stock'])
        new_stock = current_stock - qty
        product['stock'] = str(max(0, new_stock))
        
        # Update popularity EWMA
        sales_velocity = qty  # Simplified: use qty as velocity
        current_ewma = float(product.get('popularity_ewma', 0))
        new_ewma = calculate_popularity_ewma(current_ewma, sales_velocity)
        product['popularity_ewma'] = f"{new_ewma:.2f}"
        
        # Calculate popularity index (normalized)
        base_velocity = 1.0
        popularity_index = new_ewma / base_velocity
        product['popularity_index'] = f"{popularity_index:.2f}"
        
        # Calculate adaptive threshold
        base_threshold = float(product['base_threshold'])
        adjustment_factor = 1 + 0.2 * (popularity_index - 1)
        adaptive_threshold = base_threshold * adjustment_factor
        product['adaptive_threshold'] = f"{adaptive_threshold:.1f}"
        
        print(f"  Processed: {product_id} (Stock: {current_stock} → {new_stock})")
        
        # Check if restock needed
        if new_stock < adaptive_threshold:
            # Calculate restock quantity
            shortage = adaptive_threshold - new_stock
            
            # Predict 5-day demand
            recent_sales = [int(s['qty']) for s in pending_sales if s['product_id'] == product_id]
            predicted_demand_5d = calculate_demand_prediction(recent_sales, days=5)
            
            restock_qty = int(shortage + predicted_demand_5d)
            restock_qty = max(10, min(restock_qty, 1000))  # Clamp to [10, 1000]
            
            # Confidence score (simplified: based on data availability)
            confidence = min(0.95, 0.5 + 0.1 * len(recent_sales))
            
            # Reason
            reason = f"Stock {new_stock} below threshold {adaptive_threshold:.0f}"
            
            # Append to restock log
            restock_row = [
                get_utc_timestamp(),
                product_id,
                str(new_stock),
                product['base_threshold'],
                f"{adaptive_threshold:.1f}",
                f"{predicted_demand_5d:.1f}",
                product['popularity_index'],
                str(restock_qty),
                reason,
                f"{confidence:.2f}"
            ]
            
            atomic_append_csv('data/restock_log.csv', restock_row)
            print(f"    → RESTOCK: {restock_qty} units (confidence: {confidence:.0%})")
            restocks_created += 1
    
    # Save updated inventory
    fieldnames = ['product_id', 'name', 'stock', 'base_threshold', 
                  'adaptive_threshold', 'popularity_ewma', 'popularity_index']
    write_csv('data/inventory.csv', list(inventory_dict.values()), fieldnames)
    
    # Update last run
    last_run_data = {
        'timestamp': get_utc_timestamp(),
        'status': 'ok',
        'last_processed_row': start_row + len(pending_sales),
        'sales_processed': len(pending_sales),
        'restocks_created': restocks_created
    }
    save_last_run(last_run_data)
    
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
        save_last_run({
            'timestamp': get_utc_timestamp(),
            'status': 'fail',
            'error': str(e)
        })
        
        import traceback
        traceback.print_exc()
        sys.exit(1)
