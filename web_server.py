"""
AIMA Web Server
Flask application serving the web-based dashboard
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
import os
import json
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import DatabaseManager
from agents.inventory_agent import InventoryAgent
from config import DATABASE
from scripts.csv_helpers import (
    atomic_append_csv, get_utc_timestamp, read_csv,
    sanitize_product_id, validate_quantity, count_csv_rows
)

app = Flask(__name__)
CORS(app)

# Initialize database and agent
db = DatabaseManager(DATABASE.DB_PATH)
agent = InventoryAgent(db, auto_execute=False)

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/dashboard')
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        data = db.get_dashboard_data()
        
        # Enhance with calculated metrics
        products = data['products']
        
        # Calculate aggregate metrics
        total_stock = sum(p['current_stock'] for p in products)
        total_value = sum(p['current_stock'] * p['unit_cost'] for p in products)
        low_stock_count = sum(1 for p in products if p['current_stock'] < 20)
        out_of_stock = sum(1 for p in products if p['current_stock'] == 0)
        
        # Add popularity and threshold estimates
        for product in products:
            pop = product.get('latest_popularity', 1.0) or 1.0
            product['popularity_index'] = pop
            product['adaptive_threshold'] = max(20, int(20 * pop))
            product['status'] = 'critical' if product['current_stock'] < product['adaptive_threshold'] * 0.5 else \
                              'low' if product['current_stock'] < product['adaptive_threshold'] else 'ok'
        
        return jsonify({
            'success': True,
            'products': products,
            'decisions': data['recent_decisions'],
            'orders': data['pending_orders'],
            'metrics': {
                'total_products': len(products),
                'total_stock': total_stock,
                'total_value': round(total_value, 2),
                'low_stock_count': low_stock_count,
                'out_of_stock': out_of_stock
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/product/<product_id>')
def get_product_details(product_id):
    """Get detailed product information"""
    try:
        product = db.get_product(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Get sales history
        sales_history = db.get_sales_history(product_id, days=30)
        
        # Make agent decision
        decision = agent.make_decision(product_id)
        
        return jsonify({
            'success': True,
            'product': product,
            'sales_history': sales_history,
            'decision': decision
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze/<product_id>', methods=['POST'])
def analyze_product(product_id):
    """Trigger agent analysis for a product"""
    try:
        decision = agent.make_decision(product_id)
        return jsonify({
            'success': True,
            'decision': decision
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze-all', methods=['POST'])
def analyze_all_products():
    """Analyze all products"""
    try:
        products = db.get_all_products()
        decisions = []
        
        for product in products:
            decision = agent.make_decision(product['product_id'])
            decisions.append(decision)
        
        return jsonify({
            'success': True,
            'decisions': decisions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sale', methods=['POST'])
def record_sale():
    """Record a sale"""
    try:
        data = request.json
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        if not product_id or not quantity:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        result = agent.observe_sale(product_id, quantity)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/decisions')
def get_recent_decisions():
    """Get recent decisions"""
    try:
        limit = request.args.get('limit', 20, type=int)
        decisions = db.get_recent_decisions(limit)
        return jsonify({
            'success': True,
            'decisions': decisions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# CASHIER ENDPOINTS
# ============================================================

@app.route('/api/cashier/submit-sale', methods=['POST'])
def cashier_submit_sale():
    """
    Submit a sale from the cashier UI
    Atomically appends to sales_log.csv
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
        
        # Check product exists in inventory.csv
        inventory = read_csv('data/inventory.csv')
        product_exists = any(p['product_id'] == product_id for p in inventory)
        
        if not product_exists:
            return jsonify({
                'success': False,
                'error': f'Product {product_id} not found in inventory'
            }), 404
        
        # Get product name
        product_name = next(
            (p['name'] for p in inventory if p['product_id'] == product_id),
            product_id
        )
        
        # Check stock availability (from CSV)
        current_stock = int(next(
            (p['stock'] for p in inventory if p['product_id'] == product_id),
            0
        ))
        
        if current_stock < qty:
            return jsonify({
                'success': False,
                'error': f'Insufficient stock (available: {current_stock}, requested: {qty})'
            }), 400
        
        # Atomic append to sales log
        timestamp = get_utc_timestamp()
        row = [timestamp, product_id, str(qty)]
        
        success = atomic_append_csv('data/sales_log.csv', row)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to write to sales log'
            }), 500
        
        return jsonify({
            'success': True,
            'timestamp': timestamp,
            'product_id': product_id,
            'product_name': product_name,
            'qty': qty,
            'message': f'Sale recorded: {qty}x {product_name}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cashier/pending-preview')
def cashier_pending_preview():
    """
    Get pending sales preview (inventory - pending_sales)
    Shows what inventory will be after agent processes pending sales
    """
    try:
        # Load last run info
        last_run_path = 'data/last_run.json'
        if os.path.exists(last_run_path):
            with open(last_run_path, 'r') as f:
                last_run = json.load(f)
            last_processed_row = last_run.get('last_processed_row', 0)
        else:
            last_processed_row = 0
        
        # Load inventory
        inventory = read_csv('data/inventory.csv')
        inventory_dict = {p['product_id']: p for p in inventory}
        
        # Load sales log
        sales_log = read_csv('data/sales_log.csv')
        pending_sales = sales_log[last_processed_row:]
        
        # Calculate pending stock changes
        pending_changes = {}
        for sale in pending_sales:
            product_id = sale['product_id']
            qty = int(sale['qty'])
            pending_changes[product_id] = pending_changes.get(product_id, 0) + qty
        
        # Build preview
        preview = []
        for product_id, product in inventory_dict.items():
            current_stock = int(product['stock'])
            pending_qty = pending_changes.get(product_id, 0)
            projected_stock = current_stock - pending_qty
            
            preview.append({
                'product_id': product_id,
                'name': product['name'],
                'current_stock': current_stock,
                'pending_sales': pending_qty,
                'projected_stock': max(0, projected_stock),
                'threshold': float(product.get('adaptive_threshold', product['base_threshold']))
            })
        
        return jsonify({
            'success': True,
            'pending_count': len(pending_sales),
            'last_processed_row': last_processed_row,
            'total_sales_logged': count_csv_rows('data/sales_log.csv'),
            'preview': preview
        })
    
    except Exception as e:
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
        result = subprocess.run(
            [sys.executable, 'scripts/run_agent.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Load updated last_run.json
        with open('data/last_run.json', 'r') as f:
            last_run = json.load(f)
        
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cashier/products')
def cashier_get_products():
    """Get list of products from CSV for cashier dropdown"""
    try:
        inventory = read_csv('data/inventory.csv')
        
        products = [{
            'product_id': p['product_id'],
            'name': p['name'],
            'stock': int(p['stock']),
            'threshold': float(p.get('adaptive_threshold', p['base_threshold']))
        } for p in inventory]
        
        return jsonify({
            'success': True,
            'products': products
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  AIMA Web Dashboard Starting...")
    print("="*60)
    print("  URL: http://localhost:5000")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
