"""
AIMA Web Server - 100% CSV-Based
No database dependencies
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
import os
import json
import subprocess

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from utils.csv_data_manager import get_csv_manager
from scripts.csv_helpers import (
    atomic_append_csv, get_utc_timestamp, read_csv,
    sanitize_product_id, validate_quantity
)

app = Flask(__name__)
CORS(app)

# Initialize CSV-only data manager
csv_manager = get_csv_manager()


@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

# In app.py, add endpoint:
@app.route('/api/agent-reasoning')
def get_agent_reasoning():
    reasoning = read_csv('data/agent_reasoning.csv')
    return jsonify(reasoning[-20:])  # Last 20 decisions

# In app.py, add endpoint:
@app.route('/api/profit-dashboard')
def get_profit_dashboard():
    from utils.profit_tracker import ProfitTracker
    tracker = ProfitTracker('data')
    return jsonify(tracker.get_dashboard_data())

# In app.py, add endpoint:
@app.route('/api/anomalies')
def get_anomalies():
    from utils.anomaly_detector import AnomalyDetector
    detector = AnomalyDetector('data')
    return jsonify(detector.get_anomalies(hours=24))

@app.route('/api/simulate-sales', methods=['POST'])
def simulate_sales():
    from simulations.sales_simulator import simulate_sales_batch
    data = request.json
    count = data.get('count', 10)
    simulate_sales_batch(count)
    return jsonify({'status': 'ok', 'count': count})

@app.route('/api/run-agent', methods=['POST'])
def run_agent_endpoint():
    from scripts.run_agent import run_agent
    run_agent()
    return jsonify({'status': 'ok', 'restocks_created': 0})  # Get actual count

@app.route('/api/reset-demo', methods=['POST'])
def reset_demo():
    from flask import jsonify
    from utils.csv_data_manager import get_csv_manager
    from simulations.product_generator import generate_demo_products
    import csv

    csv_manager = get_csv_manager()

    # Clear logs
    open(csv_manager.sales_log_path, 'w').close()
    open(csv_manager.restock_log_path, 'w').close()

    # Generate demo products
    products = generate_demo_products(20)

    # Write to inventory.csv
    with open(csv_manager.inventory_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)

    return jsonify({'status': 'ok', 'products_created': len(products)})

@app.route('/api/replay-sales', methods=['POST'])
def replay_sales():
    data = request.json
    count = data.get('count', 10)
    
    # Get last N sales from log
    sales = read_csv('data/sales_log.csv')
    replay_sales = sales[-count:]
    
    # Re-add them to the log (with new timestamps)
    for sale in replay_sales:
        # Logic to re-process each sale
        pass
    
    return jsonify({'status': 'ok', 'replayed': count})

@app.route('/api/dashboard')
def get_dashboard_data():
    """Get comprehensive dashboard data from CSV files"""
    try:
        data = csv_manager.get_dashboard_data()
        return jsonify({
            'success': True,
            'products': data['products'],
            'recent_restocks': data['recent_restocks'],
            'metrics': data['metrics']
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# CASHIER ENDPOINTS
# ============================================================

@app.route('/api/cashier/submit-sale', methods=['POST'])
def cashier_submit_sale():
    """
    Submit a sale from the cashier UI
    Atomically appends to sales_log.csv with full pricing data
    """
    try:
        data = request.json
        product_id = data.get('product_id', '').strip()
        qty = data.get('qty')
        
        # Validate inputs
        product_id = sanitize_product_id(product_id)
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Invalid product ID (use alphanumeric and hyphens only)'
            }), 400
        
        qty = validate_quantity(qty)
        if qty is None:
            return jsonify({
                'success': False,
                'error': 'Invalid quantity (must be 1-1000)'
            }), 400
        
        # Get product from CSV
        product = csv_manager.get_product(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'error': f'Product {product_id} not found in inventory'
            }), 404
        
        # Check stock availability
        current_stock = product['stock']
        
        if current_stock < qty:
            return jsonify({
                'success': False,
                'error': f'Insufficient stock (available: {current_stock}, requested: {qty})'
            }), 400
        
        # Calculate pricing
        cost_price = product['cost_price']
        selling_price = product['selling_price']
        total_cost = cost_price * qty
        total_revenue = selling_price * qty
        profit = total_revenue - total_cost
        
        # Prepare row with full pricing data
        timestamp = get_utc_timestamp()
        row = [
            timestamp,
            product_id,
            str(qty),
            f"{cost_price:.2f}",
            f"{selling_price:.2f}",
            f"{total_cost:.2f}",
            f"{total_revenue:.2f}",
            f"{profit:.2f}"
        ]
        
        # Atomic append with headers auto-creation
        sales_log_path = os.path.join(csv_manager.data_dir, 'sales_log.csv')
        success = atomic_append_csv(
            sales_log_path, 
            row,
            headers=csv_manager.SALES_LOG_HEADERS
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to write to sales log - check file permissions and path'
            }), 500
        
        return jsonify({
            'success': True,
            'timestamp': timestamp,
            'product_id': product_id,
            'product_name': product['name'],
            'qty': qty,
            'cost_price': cost_price,
            'selling_price': selling_price,
            'total_revenue': round(total_revenue, 2),
            'profit': round(profit, 2),
            'message': f'Sale recorded: {qty}x {product["name"]} (Profit: ${profit:.2f})'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Internal error: {str(e)}'
        }), 500


@app.route('/api/cashier/pending-preview')
def cashier_pending_preview():
    """
    Get pending sales preview showing projected stock after pending sales
    This is inventory - pending_sales (not yet processed by agent)
    """
    try:
        # Load last run info
        last_run_path = os.path.join(csv_manager.data_dir, 'last_run.json')
        if os.path.exists(last_run_path):
            with open(last_run_path, 'r') as f:
                last_run = json.load(f)
            last_processed_row = last_run.get('last_processed_row', 0)
        else:
            last_processed_row = 0
        
        # Get pending preview from CSV manager
        preview_data = csv_manager.get_pending_preview(last_processed_row)
        
        return jsonify({
            'success': True,
            'pending_count': preview_data['pending_count'],
            'last_processed_row': last_processed_row,
            'total_sales_logged': len(csv_manager.get_all_sales()),
            'preview': preview_data['preview'],
            'message': f'{preview_data["pending_count"]} sales pending agent processing'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cashier/run-agent', methods=['POST'])
def cashier_run_agent():
    """
    Run the agent script (Demo only)
    Processes pending sales and updates inventory
    """
    try:
        # Run the agent script
        script_path = os.path.join(PROJECT_ROOT, 'scripts', 'run_agent.py')
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=PROJECT_ROOT
        )
        
        # Load updated last_run.json
        last_run_path = os.path.join(csv_manager.data_dir, 'last_run.json')
        if os.path.exists(last_run_path):
            with open(last_run_path, 'r') as f:
                last_run = json.load(f)
        else:
            last_run = {}
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'status': 'ok',
                'output': result.stdout,
                'last_run': last_run
            })
        else:
            return jsonify({
                'success': False,
                'status': 'fail',
                'error': result.stderr,
                'output': result.stdout
            }), 500
    
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Agent execution timed out (>30s)'
        }), 500
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cashier/products')
def cashier_get_products():
    """Get list of products from CSV for cashier dropdown"""
    try:
        products = csv_manager.get_all_products()
        
        product_list = [{
            'product_id': p['product_id'],
            'name': p['name'],
            'stock': p['stock'],
            'threshold': p['adaptive_threshold'],
            'cost_price': p['cost_price'],
            'selling_price': p['selling_price']
        } for p in products]
        
        return jsonify({
            'success': True,
            'products': product_list
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  AIMA Web Dashboard (CSV-Only)")
    print("="*60)
    print("  URL: http://localhost:5000")
    print("  Data: 100% CSV-based (no database)")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
