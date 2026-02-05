#!/usr/bin/env python3
"""
UPGRADED AIMA Agent - Full Feature Set
- Uses ONLY adaptive thresholds (no hardcoded values)
- Anomaly detection and safeguards
- Agent reasoning tracking for every decision
- Profit tracking integration
- CSV schema standardization
"""

import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')
# Get absolute path to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.csv_data_manager import get_csv_manager
from utils.anomaly_detector import AnomalyDetector
from utils.profit_tracker import ProfitTracker
from scripts.csv_helpers import atomic_append_csv, get_utc_timestamp
from utils.csv_schema_manager import CSVSchemaManager


def calculate_demand_prediction(sales_history: list, days: int = 5) -> float:
    """Calculate predicted demand over N days"""
    if not sales_history:
        return 0.0
    
    avg_daily = sum(sales_history) / len(sales_history)
    return avg_daily * days


def calculate_popularity_ewma(current_ewma: float, new_value: float, alpha: float = 0.3) -> float:
    """Calculate Exponential Weighted Moving Average for popularity"""
    if current_ewma == 0:
        return new_value
    return alpha * new_value + (1 - alpha) * current_ewma


def run_agent():
    """Main agent execution with full feature set"""
    
    print("=" * 70)
    print("   UPGRADED AIMA Agent - Full Feature Set")
    print("=" * 70)
    
    # Initialize components
    csv_manager = get_csv_manager()
    data_dir = csv_manager.data_dir
    anomaly_detector = AnomalyDetector(data_dir)
    profit_tracker = ProfitTracker(data_dir)
    
    # Ensure all CSV files have correct schemas
    print("\n Validating CSV schemas...")
    CSVSchemaManager.ensure_file_exists(
        os.path.join(data_dir, 'agent_reasoning.csv'),
        'agent_reasoning'
    )
    CSVSchemaManager.ensure_file_exists(
        os.path.join(data_dir, 'anomaly_log.csv'),
        'anomaly_log'
    )
    print(" All CSV schemas validated")
    
    # Load last run metadata
    last_run_path = os.path.join(data_dir, 'last_run.json')
    if os.path.exists(last_run_path):
        with open(last_run_path, 'r') as f:
            last_run = json.load(f)
        start_row = last_run.get('last_processed_row', 0)
    else:
        start_row = 0
    
    print(f"\n Last processed row: {start_row}")
    
    # Get pending sales
    pending_sales = csv_manager.get_pending_sales(start_row)
    
    if not pending_sales:
        print(" No pending sales to process.")
        
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
    
    print(f"\n Processing {len(pending_sales)} pending sales...")
    
    # Load all products
    products = csv_manager.get_all_products()
    product_updates = {}
    restocks_created = 0
    
    # Process each sale with anomaly detection
    for sale in pending_sales:
        product_id = sale['product_id']
        qty = sale['qty']
        
        # Find product
        product = next((p for p in products if p['product_id'] == product_id), None)
        
        if not product:
            print(f"    Warning: Unknown product {product_id}")
            continue
        
        # Initialize updates for this product if needed
        if product_id not in product_updates:
            product_updates[product_id] = {
                'original_stock': product['stock'],
                'stock': product['stock'],
                'sales_qty': []
            }
        
        # Get current stock and apply safeguards
        current_stock = product_updates[product_id]['stock']
        
        # Detect large single sale
        anomaly_detector.detect_large_single_sale(product_id, qty)
        
        # Detect sales spike
        recent_sales = anomaly_detector.get_recent_sales(product_id, days=7)
        if recent_sales:
            anomaly_detector.detect_sales_spike(product_id, qty, recent_sales)
        
        # Prevent negative stock
        adjusted_qty = anomaly_detector.prevent_negative_stock(product_id, current_stock, qty)
        
        # Update stock (prevent negative)
        new_stock = max(0, current_stock - adjusted_qty)
        product_updates[product_id]['stock'] = new_stock
        product_updates[product_id]['sales_qty'].append(adjusted_qty)
        
        # Validate stock is not negative
        anomaly_detector.check_stock_validity(product_id, new_stock)
        
        print(f"  ✓ Processed: {product_id} (Stock: {current_stock} → {new_stock})")
    
    # Now make restock decisions with full reasoning tracking
    print("\n Making restock decisions...")
    agent_reasoning_path = os.path.join(data_dir, 'agent_reasoning.csv')
    
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
        
        # Calculate adaptive threshold (NO HARDCODED VALUES)
        base_threshold = product['base_threshold']
        adjustment_factor = 1 + 0.2 * (popularity_index - 1)
        adaptive_threshold = base_threshold * adjustment_factor
        
        # Predict 5-day demand
        predicted_demand_5d = calculate_demand_prediction(sales_qty, days=5)
        
        # Make restock decision
        restock_decision = new_stock < adaptive_threshold
        restock_qty = 0
        confidence = 0.0
        explanation = ""
        
        if restock_decision:
            # Calculate restock quantity
            shortage = adaptive_threshold - new_stock
            restock_qty = int(shortage + predicted_demand_5d)
            restock_qty = max(10, min(restock_qty, 1000))  # Clamp to [10, 1000]
            
            # Confidence score
            confidence = min(0.95, 0.5 + 0.1 * len(sales_qty))
            
            # Explanation
            explanation = (
                f"Stock ({new_stock}) below adaptive threshold ({adaptive_threshold:.0f}). "
                f"Popularity index: {popularity_index:.2f}. "
                f"Predicted 5-day demand: {predicted_demand_5d:.1f}. "
                f"Recommending restock of {restock_qty} units."
            )
            
            # Log to restock log
            restock_row = [
                get_utc_timestamp(),
                product_id,
                str(new_stock),
                f"{base_threshold:.1f}",
                f"{adaptive_threshold:.1f}",
                f"{popularity_index:.2f}",
                f"{predicted_demand_5d:.1f}",
                str(restock_qty),
                f"{confidence:.2f}",
                explanation
            ]
            
            restock_schema = CSVSchemaManager.get_schema('restock_log')
            restock_log_path = os.path.join(data_dir, 'restock_log.csv')
            atomic_append_csv(
                restock_log_path,
                restock_row,
                headers=restock_schema['headers']
            )
            
            print(f"  🔄 RESTOCK: {product_id} → {restock_qty} units (confidence: {confidence:.0%})")
            restocks_created += 1
        else:
            explanation = (
                f"Stock ({new_stock}) above adaptive threshold ({adaptive_threshold:.0f}). "
                f"No restock needed. Popularity index: {popularity_index:.2f}."
            )
            confidence = 0.95  # High confidence in "no restock" decision when stock is adequate
        
        # Log agent reasoning for EVERY decision
        reasoning_row = [
            get_utc_timestamp(),
            product_id,
            str(new_stock),
            f"{adaptive_threshold:.1f}",
            f"{popularity_index:.2f}",
            f"{predicted_demand_5d:.1f}",
            'YES' if restock_decision else 'NO',
            str(restock_qty) if restock_decision else '0',
            f"{confidence:.2f}",
            explanation
        ]
        
        reasoning_schema = CSVSchemaManager.get_schema('agent_reasoning')
        atomic_append_csv(
            agent_reasoning_path,
            reasoning_row,
            headers=reasoning_schema['headers']
        )
        
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
        print("\n Failed to update inventory.csv")
        raise Exception("Failed to update inventory")
    
    # Update daily profit tracking
    print("\n Updating profit tracking...")
    profit_tracker.update_daily_profit_record()
    
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
    
    # Print summary
    print("\n" + "=" * 70)
    print("   Agent run complete!")
    print(f"   Sales processed: {len(pending_sales)}")
    print(f"   Restocks created: {restocks_created}")
    
    # Show anomaly summary
    anomaly_summary = anomaly_detector.get_anomaly_summary()
    if anomaly_summary['total'] > 0:
        print(f"    Anomalies detected: {anomaly_summary['total']}")
        for severity, count in anomaly_summary['by_severity'].items():
            print(f"      {severity}: {count}")
    
    print("=" * 70)


if __name__ == '__main__':
    try:
        run_agent()
        sys.exit(0)
    except Exception as e:
        print(f"\n Error: {e}", file=sys.stderr)
        
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
