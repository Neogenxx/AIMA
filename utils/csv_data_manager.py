"""
CSV Data Manager
100% CSV-based data storage - NO DATABASE
"""

import os
import sys
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Get absolute path to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.csv_helpers import read_csv, write_csv, get_utc_timestamp


class CSVDataManager:
    """Manages all data operations using CSV files only"""
    
    # CSV schemas
    INVENTORY_HEADERS = [
        'product_id', 'name', 'stock', 'base_threshold', 'adaptive_threshold',
        'popularity_ewma', 'popularity_index', 'cost_price', 'selling_price'
    ]
    
    SALES_LOG_HEADERS = [
        'timestamp', 'product_id', 'qty', 'cost_price', 'selling_price',
        'total_cost', 'total_revenue', 'profit'
    ]
    
    RESTOCK_LOG_HEADERS = [
        'timestamp', 'product_id', 'stock_after_sale', 'base_threshold',
        'adaptive_threshold', 'predicted_demand_5d', 'popularity_index',
        'restock_qty', 'reason', 'confidence'
    ]
    
    def __init__(self, data_dir: str = None):
        """
        Initialize CSV data manager
        
        Args:
            data_dir: Path to data directory (default: PROJECT_ROOT/data)
        """
        if data_dir is None:
            self.data_dir = os.path.join(PROJECT_ROOT, 'data')
        else:
            self.data_dir = os.path.abspath(data_dir)
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # File paths (absolute)
        self.inventory_path = os.path.join(self.data_dir, 'inventory.csv')
        self.sales_log_path = os.path.join(self.data_dir, 'sales_log.csv')
        self.restock_log_path = os.path.join(self.data_dir, 'restock_log.csv')
        self.last_run_path = os.path.join(self.data_dir, 'last_run.json')

        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Create CSV files with headers if they don't exist"""
        # Inventory
        if not os.path.exists(self.inventory_path):
            write_csv(self.inventory_path, [], self.INVENTORY_HEADERS)
        
        # Sales log
        if not os.path.exists(self.sales_log_path):
            write_csv(self.sales_log_path, [], self.SALES_LOG_HEADERS)
        
        # Restock log
        if not os.path.exists(self.restock_log_path):
            write_csv(self.restock_log_path, [], self.RESTOCK_LOG_HEADERS)
    
    # ==================== INVENTORY OPERATIONS ====================
    
    def get_all_products(self) -> List[Dict]:
        """Get all products from inventory safely"""

        products = read_csv(self.inventory_path)

        for p in products:
            try:
                p['stock'] = int(p.get('stock', 0))
                p['base_threshold'] = float(p.get('base_threshold', 20))
                p['adaptive_threshold'] = float(p.get('adaptive_threshold', p['base_threshold']))
                p['popularity_ewma'] = float(p.get('popularity_ewma', 1.0))
                p['popularity_index'] = float(p.get('popularity_index', 1.0))
                p['cost_price'] = float(p.get('cost_price', 0))
                p['selling_price'] = float(p.get('selling_price', 0))

            except Exception:
                # Auto-fix corrupted product rows instead of crashing
                p['stock'] = int(p.get('stock', 0) or 0)
                p['base_threshold'] = float(p.get('base_threshold', 20) or 20)
                p['adaptive_threshold'] = float(p.get('adaptive_threshold', p['base_threshold']))
                p['popularity_ewma'] = 1.0
                p['popularity_index'] = 1.0
                p['cost_price'] = float(p.get('cost_price', 0) or 0)
                p['selling_price'] = float(p.get('selling_price', 0) or 0)

        return products
 
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get single product by ID"""
        products = self.get_all_products()
        for p in products:
            if p['product_id'] == product_id:
                return p
        return None
    
    def update_product(self, product_id: str, updates: Dict) -> bool:
        """Update a product's fields"""
        products = self.get_all_products()
        
        for p in products:
            if p['product_id'] == product_id:
                # Update fields
                for key, value in updates.items():
                    if key in p:
                        p[key] = str(value)
                
                # Write back to CSV
                return write_csv(self.inventory_path, products, self.INVENTORY_HEADERS)
        
        return False
    
    def update_inventory_batch(self, updates: Dict[str, Dict]) -> bool:
        """
        Update multiple products at once
        
        Args:
            updates: Dict of {product_id: {field: value, ...}}
        """
        products = self.get_all_products()
        
        for p in products:
            if p['product_id'] in updates:
                for key, value in updates[p['product_id']].items():
                    if key in p:
                        p[key] = str(value)
        
        return write_csv(self.inventory_path, products, self.INVENTORY_HEADERS)
    
    # ==================== SALES OPERATIONS ====================
    
    def get_all_sales(self) -> List[Dict]:
        """Get all sales from log"""
        sales = read_csv(self.sales_log_path)
        
        # Convert numeric fields
        for s in sales:
            s['qty'] = int(s['qty'])
            s['cost_price'] = float(s['cost_price'])
            s['selling_price'] = float(s['selling_price'])
            s['total_cost'] = float(s['total_cost'])
            s['total_revenue'] = float(s['total_revenue'])
            s['profit'] = float(s['profit'])
        
        return sales
    
    def get_sales_for_product(self, product_id: str, limit: int = None) -> List[Dict]:
        """Get sales for a specific product"""
        all_sales = self.get_all_sales()
        product_sales = [s for s in all_sales if s['product_id'] == product_id]
        
        if limit:
            return product_sales[-limit:]
        return product_sales
    
    def get_pending_sales(self, last_processed_row: int = 0) -> List[Dict]:
        """Get sales that haven't been processed by agent"""
        all_sales = self.get_all_sales()
        return all_sales[last_processed_row:]
    
    # ==================== RESTOCK OPERATIONS ====================
    
    def get_all_restocks(self):
        """Get all restock records safely"""

        restocks = read_csv(self.restock_log_path)
        safe_restocks = []

        for r in restocks:
            try:
                # Convert safely with float → int when needed
                r['restock_qty'] = int(float(r.get('restock_qty', 0)))
                r['stock_before'] = int(float(r.get('stock_before', r.get('current_stock', 0))))

                r['stock_after_sale'] = int(float(
                    r.get('stock_after_sale', r.get('stock_before', 0))
                ))

                r['base_threshold'] = float(r.get('base_threshold', 0))
                r['adaptive_threshold'] = float(r.get('adaptive_threshold', 0))

                # Handle both old & new demand keys
                r['predicted_demand_5d'] = float(
                    r.get('predicted_demand_5d', r.get('predicted_demand', 0))
                )

                r['popularity_index'] = float(r.get('popularity_index', 0))
                r['confidence'] = float(r.get('confidence', 0))

                safe_restocks.append(r)

            except Exception as e:
                print("Skipping corrupted restock row:", r, "Error:", e)

        return safe_restocks
    
    def get_recent_restocks(self, limit: int = 20) -> List[Dict]:
        """Get recent restock decisions"""
        all_restocks = self.get_all_restocks()
        return all_restocks[-limit:] if all_restocks else []
    
    # ==================== DASHBOARD DATA ====================
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        products = self.get_all_products()
        recent_restocks = self.get_recent_restocks(20)
        all_sales = self.get_all_sales()
        
        # Calculate metrics
        total_stock = sum(p['stock'] for p in products)
        total_value = sum(p['stock'] * p['cost_price'] for p in products)
        low_stock_count = sum(1 for p in products if p['stock'] < p['adaptive_threshold'])
        out_of_stock = sum(1 for p in products if p['stock'] == 0)
        
        # Calculate total profit
        total_profit = sum(s['profit'] for s in all_sales)
        total_revenue = sum(s['total_revenue'] for s in all_sales)
        
        # Add status to each product
        for p in products:
            if p['stock'] == 0:
                p['status'] = 'critical'
            elif p['stock'] < p['adaptive_threshold'] * 0.5:
                p['status'] = 'critical'
            elif p['stock'] < p['adaptive_threshold']:
                p['status'] = 'low'
            else:
                p['status'] = 'ok'
        
        return {
            'products': products,
            'recent_restocks': recent_restocks,
            'metrics': {
                'total_products': len(products),
                'total_stock': total_stock,
                'total_value': round(total_value, 2),
                'low_stock_count': low_stock_count,
                'out_of_stock': out_of_stock,
                'total_profit': round(total_profit, 2),
                'total_revenue': round(total_revenue, 2)
            }
        }
    
    # ==================== PENDING SALES PREVIEW ====================
    
    def get_pending_preview(self, last_processed_row: int = 0) -> Dict:
        """
        Calculate pending sales preview showing projected stock
        
        Returns:
            Dict with pending_sales list and preview data
        """
        products = self.get_all_products()
        pending_sales = self.get_pending_sales(last_processed_row)
        
        # Calculate pending quantities per product
        pending_qty = {}
        for sale in pending_sales:
            pid = sale['product_id']
            pending_qty[pid] = pending_qty.get(pid, 0) + sale['qty']
        
        # Build preview
        preview = []
        for p in products:
            pending = pending_qty.get(p['product_id'], 0)
            projected = max(0, p['stock'] - pending)
            
            preview.append({
                'product_id': p['product_id'],
                'name': p['name'],
                'current_stock': p['stock'],
                'pending_sales': pending,
                'projected_stock': projected,
                'threshold': p['adaptive_threshold'],
                'cost_price': p['cost_price'],
                'selling_price': p['selling_price']
            })
        
        return {
            'pending_sales': pending_sales,
            'pending_count': len(pending_sales),
            'preview': preview
        }


# Global instance
_csv_manager = None

def get_csv_manager() -> CSVDataManager:
    """Get global CSV data manager instance"""
    global _csv_manager
    if _csv_manager is None:
        _csv_manager = CSVDataManager()
    return _csv_manager
