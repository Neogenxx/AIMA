"""
Database utilities for AIMA
Handles all database operations including product, sales, and decision logging
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import os

class DatabaseManager:
    """Manages all database operations for AIMA"""
    
    def __init__(self, db_path: str = "data/aima.db"):
        self.db_path = db_path
        self._ensure_data_directory()
        self._initialize_database()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    current_stock INTEGER DEFAULT 0,
                    unit_cost REAL DEFAULT 0.0,
                    selling_price REAL DEFAULT 0.0,
                    supplier TEXT,
                    lead_time_days INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sales table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount REAL,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            """)
            
            # Inventory transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    stock_before INTEGER,
                    stock_after INTEGER,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            """)
            
            # Agent decisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_decisions (
                    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    current_stock INTEGER,
                    popularity_index REAL,
                    adaptive_threshold REAL,
                    predicted_demand REAL,
                    restock_quantity INTEGER,
                    confidence_score REAL,
                    reasoning TEXT,
                    executed BOOLEAN DEFAULT 0,
                    decision_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            """)
            
            # Popularity metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS popularity_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    popularity_index REAL NOT NULL,
                    sales_velocity REAL,
                    trend TEXT,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            """)
            
            # Restock orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS restock_orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    quantity_ordered INTEGER NOT NULL,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expected_delivery_date TIMESTAMP,
                    actual_delivery_date TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    cost REAL,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            """)
            
            conn.commit()
    
    def add_product(self, product_id: str, name: str, category: str, 
                   initial_stock: int = 0, unit_cost: float = 0.0,
                   selling_price: float = 0.0, supplier: str = "supplier_a",
                   lead_time_days: int = 3) -> bool:
        """Add a new product to inventory"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO products 
                    (product_id, name, category, current_stock, unit_cost, 
                     selling_price, supplier, lead_time_days)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, name, category, initial_stock, unit_cost,
                      selling_price, supplier, lead_time_days))
                
                # Log initial stock transaction
                if initial_stock > 0:
                    cursor.execute("""
                        INSERT INTO inventory_transactions
                        (product_id, transaction_type, quantity, stock_before, stock_after, notes)
                        VALUES (?, 'initial', ?, 0, ?, 'Initial inventory')
                    """, (product_id, initial_stock, initial_stock))
            return True
        except sqlite3.IntegrityError:
            return False
    
    def record_sale(self, product_id: str, quantity: int) -> bool:
        """Record a sale and update stock"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current stock and price
                cursor.execute("""
                    SELECT current_stock, selling_price FROM products 
                    WHERE product_id = ?
                """, (product_id,))
                result = cursor.fetchone()
                
                if not result or result['current_stock'] < quantity:
                    return False
                
                current_stock = result['current_stock']
                selling_price = result['selling_price']
                total_amount = selling_price * quantity
                
                # Record sale
                cursor.execute("""
                    INSERT INTO sales (product_id, quantity, total_amount)
                    VALUES (?, ?, ?)
                """, (product_id, quantity, total_amount))
                
                # Update stock
                new_stock = current_stock - quantity
                cursor.execute("""
                    UPDATE products SET current_stock = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                """, (new_stock, product_id))
                
                # Log transaction
                cursor.execute("""
                    INSERT INTO inventory_transactions
                    (product_id, transaction_type, quantity, stock_before, stock_after, notes)
                    VALUES (?, 'sale', ?, ?, ?, 'Customer purchase')
                """, (product_id, quantity, current_stock, new_stock))
            
            return True
        except Exception:
            return False
    
    def get_sales_history(self, product_id: str, days: int = 30) -> List[Dict]:
        """Get sales history for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sales 
                WHERE product_id = ? 
                AND sale_date >= datetime('now', '-' || ? || ' days')
                ORDER BY sale_date DESC
            """, (product_id, days))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get product details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_all_products(self) -> List[Dict]:
        """Get all products"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def log_decision(self, product_id: str, decision_type: str, 
                    current_stock: int, popularity_index: float,
                    adaptive_threshold: float, predicted_demand: float,
                    restock_quantity: int, confidence_score: float,
                    reasoning: str, executed: bool = False) -> int:
        """Log an agent decision"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_decisions
                (product_id, decision_type, current_stock, popularity_index,
                 adaptive_threshold, predicted_demand, restock_quantity,
                 confidence_score, reasoning, executed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (product_id, decision_type, current_stock, popularity_index,
                  adaptive_threshold, predicted_demand, restock_quantity,
                  confidence_score, reasoning, executed))
            return cursor.lastrowid
    
    def log_popularity_metric(self, product_id: str, popularity_index: float,
                             sales_velocity: float, trend: str):
        """Log popularity metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO popularity_metrics
                (product_id, popularity_index, sales_velocity, trend)
                VALUES (?, ?, ?, ?)
            """, (product_id, popularity_index, sales_velocity, trend))
    
    def create_restock_order(self, product_id: str, quantity: int, 
                           lead_time_days: int) -> int:
        """Create a restock order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get product cost
            cursor.execute("SELECT unit_cost FROM products WHERE product_id = ?", 
                         (product_id,))
            unit_cost = cursor.fetchone()['unit_cost']
            
            expected_delivery = datetime.now() + timedelta(days=lead_time_days)
            total_cost = unit_cost * quantity
            
            cursor.execute("""
                INSERT INTO restock_orders
                (product_id, quantity_ordered, expected_delivery_date, cost)
                VALUES (?, ?, ?, ?)
            """, (product_id, quantity, expected_delivery, total_cost))
            
            return cursor.lastrowid
    
    def receive_restock_order(self, order_id: int) -> bool:
        """Process received restock order"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get order details
                cursor.execute("""
                    SELECT product_id, quantity_ordered FROM restock_orders
                    WHERE order_id = ? AND status = 'pending'
                """, (order_id,))
                order = cursor.fetchone()
                
                if not order:
                    return False
                
                product_id = order['product_id']
                quantity = order['quantity_ordered']
                
                # Update order status
                cursor.execute("""
                    UPDATE restock_orders 
                    SET status = 'received', actual_delivery_date = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """, (order_id,))
                
                # Update product stock
                cursor.execute("""
                    SELECT current_stock FROM products WHERE product_id = ?
                """, (product_id,))
                current_stock = cursor.fetchone()['current_stock']
                new_stock = current_stock + quantity
                
                cursor.execute("""
                    UPDATE products SET current_stock = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                """, (new_stock, product_id))
                
                # Log transaction
                cursor.execute("""
                    INSERT INTO inventory_transactions
                    (product_id, transaction_type, quantity, stock_before, stock_after, notes)
                    VALUES (?, 'restock', ?, ?, ?, ?)
                """, (product_id, quantity, current_stock, new_stock, 
                      f'Restock order #{order_id} received'))
            
            return True
        except Exception:
            return False
    
    def get_recent_decisions(self, limit: int = 50) -> List[Dict]:
        """Get recent agent decisions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, p.name as product_name
                FROM agent_decisions d
                JOIN products p ON d.product_id = p.product_id
                ORDER BY d.decision_date DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Product status
            cursor.execute("""
                SELECT 
                    p.*,
                    (SELECT COUNT(*) FROM sales s 
                     WHERE s.product_id = p.product_id 
                     AND s.sale_date >= datetime('now', '-7 days')) as sales_last_7_days,
                    (SELECT popularity_index FROM popularity_metrics pm
                     WHERE pm.product_id = p.product_id
                     ORDER BY calculated_at DESC LIMIT 1) as latest_popularity
                FROM products p
            """)
            products = [dict(row) for row in cursor.fetchall()]
            
            # Recent decisions
            recent_decisions = self.get_recent_decisions(20)
            
            # Pending orders
            cursor.execute("""
                SELECT r.*, p.name as product_name
                FROM restock_orders r
                JOIN products p ON r.product_id = p.product_id
                WHERE r.status = 'pending'
                ORDER BY expected_delivery_date
            """)
            pending_orders = [dict(row) for row in cursor.fetchall()]
            
            return {
                "products": products,
                "recent_decisions": recent_decisions,
                "pending_orders": pending_orders
            }
