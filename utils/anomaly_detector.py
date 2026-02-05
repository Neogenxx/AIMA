"""
Anomaly Detection and Safeguards
Prevents negative stock, detects suspicious patterns, logs anomalies
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.csv_helpers import atomic_append_csv, get_utc_timestamp, read_csv
from utils.csv_schema_manager import CSVSchemaManager


class AnomalyDetector:
    """Detects and handles anomalies in inventory and sales data"""
    
    # Thresholds
    SPIKE_THRESHOLD_MULTIPLIER = 3.0  # Sales spike = 3x normal
    MAX_SINGLE_SALE_QTY = 500  # Maximum reasonable single sale
    NEGATIVE_STOCK_SEVERITY = "CRITICAL"
    SPIKE_SEVERITY = "WARNING"
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.anomaly_log_path = os.path.join(data_dir, 'anomaly_log.csv')
        
        # Ensure anomaly log exists
        CSVSchemaManager.ensure_file_exists(
            self.anomaly_log_path,
            'anomaly_log'
        )
    
    def check_stock_validity(self, product_id: str, stock: int) -> Tuple[bool, str]:
        """
        Check if stock level is valid
        
        Args:
            product_id: Product ID
            stock: Stock level to check
        
        Returns:
            (is_valid, error_message)
        """
        if stock < 0:
            msg = f"CRITICAL: Negative stock detected for {product_id}: {stock}"
            self.log_anomaly(
                anomaly_type='negative_stock',
                product_id=product_id,
                severity=self.NEGATIVE_STOCK_SEVERITY,
                description=msg,
                value=str(stock),
                threshold='0',
                action_taken='Stock clamped to 0'
            )
            return False, msg
        
        return True, ""
    
    def prevent_negative_stock(self, product_id: str, current_stock: int, requested_qty: int) -> int:
        """
        Prevent negative stock by adjusting quantity
        
        Args:
            product_id: Product ID
            current_stock: Current stock level
            requested_qty: Requested sale quantity
        
        Returns:
            Adjusted quantity (clamped to available stock)
        """
        if requested_qty > current_stock:
            adjusted_qty = current_stock
            msg = f"Sale quantity adjusted: {product_id} requested {requested_qty}, only {current_stock} available"
            
            self.log_anomaly(
                anomaly_type='insufficient_stock',
                product_id=product_id,
                severity='WARNING',
                description=msg,
                value=str(requested_qty),
                threshold=str(current_stock),
                action_taken=f'Quantity reduced to {adjusted_qty}'
            )
            
            return adjusted_qty
        
        return requested_qty
    
    def detect_sales_spike(self, product_id: str, current_qty: int, sales_history: List[int]) -> bool:
        """
        Detect suspicious sales spike
        
        Args:
            product_id: Product ID
            current_qty: Current sale quantity
            sales_history: List of recent sale quantities
        
        Returns:
            True if spike detected
        """
        if not sales_history:
            return False
        
        avg_sales = sum(sales_history) / len(sales_history)
        
        if avg_sales > 0 and current_qty > avg_sales * self.SPIKE_THRESHOLD_MULTIPLIER:
            msg = f"Sales spike detected for {product_id}: {current_qty} units (avg: {avg_sales:.1f})"
            
            self.log_anomaly(
                anomaly_type='sales_spike',
                product_id=product_id,
                severity=self.SPIKE_SEVERITY,
                description=msg,
                value=str(current_qty),
                threshold=str(avg_sales * self.SPIKE_THRESHOLD_MULTIPLIER),
                action_taken='Alert logged, sale processed normally'
            )
            
            return True
        
        return False
    
    def detect_large_single_sale(self, product_id: str, qty: int) -> bool:
        """
        Detect unusually large single sale
        
        Args:
            product_id: Product ID
            qty: Sale quantity
        
        Returns:
            True if large sale detected
        """
        if qty > self.MAX_SINGLE_SALE_QTY:
            msg = f"Large single sale detected for {product_id}: {qty} units"
            
            self.log_anomaly(
                anomaly_type='large_sale',
                product_id=product_id,
                severity='INFO',
                description=msg,
                value=str(qty),
                threshold=str(self.MAX_SINGLE_SALE_QTY),
                action_taken='Sale processed normally'
            )
            
            return True
        
        return False
    

    def get_recent_sales(self, product_id: str, days: int = 7):
        sales_log_path = os.path.join(self.data_dir, 'sales_log.csv')

        if not os.path.exists(sales_log_path):
            return []

        sales = read_csv(sales_log_path)

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        recent_sales = []

        for sale in sales:
            if sale.get('product_id') == product_id:
                try:
                    sale_time = datetime.fromisoformat(
                        sale['timestamp'].replace('Z', '+00:00')
                    )

                    if sale_time.tzinfo is None:
                        sale_time = sale_time.replace(tzinfo=timezone.utc)

                    if sale_time >= cutoff_date:
                        recent_sales.append(int(sale['qty']))

                except:
                    continue

        return recent_sales
    
    def log_anomaly(self, anomaly_type: str, product_id: str, severity: str,
                    description: str, value: str, threshold: str, action_taken: str):
        """
        Log an anomaly to the anomaly log
        
        Args:
            anomaly_type: Type of anomaly
            product_id: Product ID (can be empty)
            severity: Severity level (INFO, WARNING, CRITICAL)
            description: Human-readable description
            value: Observed value
            threshold: Threshold that was exceeded
            action_taken: What action was taken
        """
        row = [
            get_utc_timestamp(),
            anomaly_type,
            product_id if product_id else 'N/A',
            severity,
            description,
            value,
            threshold,
            action_taken
        ]
        
        schema = CSVSchemaManager.get_schema('anomaly_log')
        atomic_append_csv(
            self.anomaly_log_path,
            row,
            headers=schema['headers']
        )
        
        # Print to console based on severity
        if severity == 'CRITICAL':
            print(f"🚨 CRITICAL ANOMALY: {description}")
        elif severity == 'WARNING':
            print(f"⚠️  WARNING: {description}")
        else:
            print(f"ℹ️  INFO: {description}")
    
    def get_anomalies(self, hours: int = 24):
        anomaly_log_path = os.path.join(self.data_dir, 'anomalies.csv')

        if not os.path.exists(anomaly_log_path):
            return []

        anomalies = read_csv(anomaly_log_path)

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent = []

        for anomaly in anomalies:
            try:
                anomaly_time = datetime.fromisoformat(
                    anomaly['timestamp'].replace('Z', '+00:00')
                )

                if anomaly_time.tzinfo is None:
                    anomaly_time = anomaly_time.replace(tzinfo=timezone.utc)

                if anomaly_time >= cutoff_time:
                    recent.append(anomaly)

            except:
                continue

        return recent
    
    def get_anomaly_summary(self) -> Dict:
        """
        Get summary of anomalies by type and severity
        
        Returns:
            Dictionary with counts
        """
        anomalies = self.get_anomalies(hours=24)
        
        summary = {
            'total': len(anomalies),
            'by_severity': defaultdict(int),
            'by_type': defaultdict(int)
        }
        
        for anomaly in anomalies:
            summary['by_severity'][anomaly.get('severity', 'UNKNOWN')] += 1
            summary['by_type'][anomaly.get('anomaly_type', 'UNKNOWN')] += 1
        
        return summary
