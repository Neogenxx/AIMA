"""
Profit Tracking Module
Tracks revenue, costs, profit margins, and profitability analytics
"""

import os
import sys
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.csv_helpers import read_csv, write_csv, get_utc_timestamp
from utils.csv_schema_manager import CSVSchemaManager


class ProfitTracker:
    """Tracks and analyzes profitability metrics"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.sales_log_path = os.path.join(data_dir, 'sales_log.csv')
        self.profit_tracking_path = os.path.join(data_dir, 'profit_tracking.csv')
        
        # Ensure profit tracking file exists
        CSVSchemaManager.ensure_file_exists(
            self.profit_tracking_path,
            'profit_tracking'
        )
    
    def calculate_daily_profits(self, target_date: Optional[date] = None) -> Dict:
        """
        Calculate profit metrics for a specific day
        
        Args:
            target_date: Date to calculate for (default: today)
        
        Returns:
            Dictionary with profit metrics
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        # Read sales log
        sales = read_csv(self.sales_log_path)
        
        # Filter sales for target date
        daily_sales = []
        for sale in sales:
            try:
                sale_date = datetime.fromisoformat(sale['timestamp'].replace('Z', '+00:00')).date()
                if sale_date == target_date:
                    daily_sales.append(sale)
            except (ValueError, KeyError):
                continue
        
        # Calculate metrics
        total_revenue = sum(float(s.get('total_revenue', 0)) for s in daily_sales)
        total_cost = sum(float(s.get('total_cost', 0)) for s in daily_sales)
        total_profit = total_revenue - total_cost
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        transactions_count = len(daily_sales)
        avg_transaction_value = total_revenue / transactions_count if transactions_count > 0 else 0
        
        return {
            'date': date_str,
            'total_revenue': round(total_revenue, 2),
            'total_cost': round(total_cost, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round(profit_margin, 2),
            'transactions_count': transactions_count,
            'avg_transaction_value': round(avg_transaction_value, 2)
        }
    
    def update_daily_profit_record(self, target_date: Optional[date] = None):
        """
        Update or create profit record for a specific day
        
        Args:
            target_date: Date to update (default: today)
        """
        metrics = self.calculate_daily_profits(target_date)
        
        # Read existing records
        records = read_csv(self.profit_tracking_path)
        
        # Update or append record
        found = False
        for record in records:
            if record['date'] == metrics['date']:
                # Update existing record
                record.update(metrics)
                found = True
                break
        
        if not found:
            records.append(metrics)
        
        # Write back
        schema = CSVSchemaManager.get_schema('profit_tracking')
        write_csv(self.profit_tracking_path, records, schema['headers'])
    
    def get_overall_metrics(self) -> Dict:
        """
        Get overall profit metrics (all-time)
        
        Returns:
            Dictionary with overall metrics
        """
        sales = read_csv(self.sales_log_path)
        
        total_revenue = sum(float(s.get('total_revenue', 0)) for s in sales)
        total_cost = sum(float(s.get('total_cost', 0)) for s in sales)
        total_profit = total_revenue - total_cost
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_revenue': round(total_revenue, 2),
            'total_cost': round(total_cost, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round(profit_margin, 2),
            'total_transactions': len(sales)
        }
    
    def get_today_metrics(self) -> Dict:
        """Get today's profit metrics"""
        return self.calculate_daily_profits(date.today())
    
    def get_product_profitability(self) -> List[Dict]:
        """
        Get profitability analysis per product
        
        Returns:
            List of product profitability dictionaries
        """
        sales = read_csv(self.sales_log_path)
        
        # Aggregate by product
        product_metrics = defaultdict(lambda: {
            'total_revenue': 0.0,
            'total_cost': 0.0,
            'total_profit': 0.0,
            'units_sold': 0,
            'transactions': 0
        })
        
        for sale in sales:
            product_id = sale.get('product_id', 'UNKNOWN')
            
            revenue = float(sale.get('total_revenue', 0))
            cost = float(sale.get('total_cost', 0))
            profit = float(sale.get('profit', 0))
            qty = int(sale.get('qty', 0))
            
            product_metrics[product_id]['total_revenue'] += revenue
            product_metrics[product_id]['total_cost'] += cost
            product_metrics[product_id]['total_profit'] += profit
            product_metrics[product_id]['units_sold'] += qty
            product_metrics[product_id]['transactions'] += 1
        
        # Convert to list and calculate margins
        result = []
        for product_id, metrics in product_metrics.items():
            revenue = metrics['total_revenue']
            profit_margin = (metrics['total_profit'] / revenue * 100) if revenue > 0 else 0
            
            result.append({
                'product_id': product_id,
                'total_revenue': round(revenue, 2),
                'total_cost': round(metrics['total_cost'], 2),
                'total_profit': round(metrics['total_profit'], 2),
                'profit_margin': round(profit_margin, 2),
                'units_sold': metrics['units_sold'],
                'transactions': metrics['transactions'],
                'avg_profit_per_unit': round(metrics['total_profit'] / metrics['units_sold'], 2) if metrics['units_sold'] > 0 else 0
            })
        
        # Sort by total profit descending
        result.sort(key=lambda x: x['total_profit'], reverse=True)
        
        return result
    
    def get_most_profitable_product(self) -> Optional[Dict]:
        """Get most profitable product"""
        products = self.get_product_profitability()
        return products[0] if products else None
    
    def get_least_profitable_product(self) -> Optional[Dict]:
        """Get least profitable product"""
        products = self.get_product_profitability()
        return products[-1] if products else None
    
    def get_profit_trend(self, days: int = 7) -> List[Dict]:
        """
        Get profit trend over last N days
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            List of daily profit records
        """
        records = read_csv(self.profit_tracking_path)
        
        # Sort by date descending and take last N days
        records.sort(key=lambda x: x['date'], reverse=True)
        
        return records[:days]
    
    def get_dashboard_data(self) -> Dict:
        """
        Get comprehensive dashboard data
        
        Returns:
            Dictionary with all dashboard metrics
        """
        overall = self.get_overall_metrics()
        today = self.get_today_metrics()
        most_profitable = self.get_most_profitable_product()
        least_profitable = self.get_least_profitable_product()
        trend = self.get_profit_trend(days=7)
        
        return {
            'overall': overall,
            'today': today,
            'most_profitable_product': most_profitable,
            'least_profitable_product': least_profitable,
            'profit_trend': trend
        }
