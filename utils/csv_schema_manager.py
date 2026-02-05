"""
CSV Schema Manager
Locks and standardizes CSV schemas across the project
Auto-creates files with correct headers if missing
"""

import os
import csv
from typing import List, Dict, Optional


class CSVSchemaManager:
    """Centralized CSV schema management"""
    
    # Locked schemas - DO NOT MODIFY
    INVENTORY_SCHEMA = {
        'filename': 'inventory.csv',
        'headers': [
            'product_id', 'name', 'stock', 'base_threshold', 'adaptive_threshold',
            'popularity_ewma', 'popularity_index', 'cost_price', 'selling_price'
        ],
        'required_fields': ['product_id', 'name', 'stock', 'base_threshold'],
        'numeric_fields': ['stock', 'base_threshold', 'adaptive_threshold', 
                          'popularity_ewma', 'popularity_index', 'cost_price', 'selling_price'],
        'default_values': {
            'stock': 0,
            'base_threshold': 50.0,
            'adaptive_threshold': 50.0,
            'popularity_ewma': 0.0,
            'popularity_index': 1.0,
            'cost_price': 0.0,
            'selling_price': 0.0
        }
    }
    
    SALES_LOG_SCHEMA = {
        'filename': 'sales_log.csv',
        'headers': [
            'timestamp', 'product_id', 'qty', 'cost_price', 'selling_price',
            'total_cost', 'total_revenue', 'profit'
        ],
        'required_fields': ['timestamp', 'product_id', 'qty'],
        'numeric_fields': ['qty', 'cost_price', 'selling_price', 'total_cost', 'total_revenue', 'profit']
    }
    
    RESTOCK_LOG_SCHEMA = {
        'filename': 'restock_log.csv',
        'headers': [
            'timestamp', 'product_id', 'current_stock', 'base_threshold',
            'adaptive_threshold', 'popularity_index', 'predicted_demand',
            'restock_qty', 'confidence', 'explanation'
        ],
        'required_fields': ['timestamp', 'product_id', 'restock_qty'],
        'numeric_fields': ['current_stock', 'base_threshold', 'adaptive_threshold',
                          'popularity_index', 'predicted_demand', 'restock_qty', 'confidence']
    }
    
    ANOMALY_LOG_SCHEMA = {
        'filename': 'anomaly_log.csv',
        'headers': [
            'timestamp', 'anomaly_type', 'product_id', 'severity',
            'description', 'value', 'threshold', 'action_taken'
        ],
        'required_fields': ['timestamp', 'anomaly_type', 'severity', 'description']
    }
    
    PROFIT_TRACKING_SCHEMA = {
        'filename': 'profit_tracking.csv',
        'headers': [
            'date', 'total_revenue', 'total_cost', 'total_profit',
            'profit_margin', 'transactions_count', 'avg_transaction_value'
        ],
        'required_fields': ['date'],
        'numeric_fields': ['total_revenue', 'total_cost', 'total_profit',
                          'profit_margin', 'transactions_count', 'avg_transaction_value']
    }
    
    AGENT_REASONING_SCHEMA = {
        'filename': 'agent_reasoning.csv',
        'headers': [
            'timestamp', 'product_id', 'current_stock', 'adaptive_threshold',
            'popularity_index', 'predicted_demand', 'restock_decision',
            'restock_quantity', 'confidence_score', 'explanation'
        ],
        'required_fields': ['timestamp', 'product_id', 'restock_decision'],
        'numeric_fields': ['current_stock', 'adaptive_threshold', 'popularity_index',
                          'predicted_demand', 'restock_quantity', 'confidence_score']
    }
    
    @classmethod
    def get_schema(cls, schema_name: str) -> Dict:
        """Get schema by name"""
        schema_map = {
            'inventory': cls.INVENTORY_SCHEMA,
            'sales_log': cls.SALES_LOG_SCHEMA,
            'restock_log': cls.RESTOCK_LOG_SCHEMA,
            'anomaly_log': cls.ANOMALY_LOG_SCHEMA,
            'profit_tracking': cls.PROFIT_TRACKING_SCHEMA,
            'agent_reasoning': cls.AGENT_REASONING_SCHEMA
        }
        return schema_map.get(schema_name, {})
    
    @classmethod
    def ensure_file_exists(cls, filepath: str, schema_name: str) -> bool:
        """
        Ensure CSV file exists with correct headers
        Creates file if missing, validates headers if exists
        
        Args:
            filepath: Path to CSV file
            schema_name: Name of schema to use
        
        Returns:
            True if file is valid, False otherwise
        """
        schema = cls.get_schema(schema_name)
        if not schema:
            raise ValueError(f"Unknown schema: {schema_name}")
        
        headers = schema['headers']
        
        # If file doesn't exist, create it
        if not os.path.exists(filepath):
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                return True
            except Exception as e:
                print(f"Error creating {filepath}: {e}")
                return False
        
        # Validate existing file has correct headers
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                actual_headers = next(reader, [])
                
                if actual_headers != headers:
                    print(f"Warning: {filepath} has incorrect headers")
                    print(f"  Expected: {headers}")
                    print(f"  Actual: {actual_headers}")
                    # Backup old file and create new one
                    backup_path = filepath + '.backup'
                    os.rename(filepath, backup_path)
                    print(f"  Old file backed up to {backup_path}")
                    
                    # Create new file with correct headers
                    with open(filepath, 'w', newline='', encoding='utf-8') as new_f:
                        writer = csv.writer(new_f)
                        writer.writerow(headers)
                    
                    return True
                
                return True
        except Exception as e:
            print(f"Error validating {filepath}: {e}")
            return False
    
    @classmethod
    def validate_row(cls, row: Dict, schema_name: str) -> tuple[bool, str]:
        """
        Validate a row against schema
        
        Args:
            row: Row dictionary
            schema_name: Name of schema
        
        Returns:
            (is_valid, error_message)
        """
        schema = cls.get_schema(schema_name)
        if not schema:
            return False, f"Unknown schema: {schema_name}"
        
        # Check required fields
        for field in schema.get('required_fields', []):
            if field not in row or not row[field]:
                return False, f"Missing required field: {field}"
        
        # Validate numeric fields
        for field in schema.get('numeric_fields', []):
            if field in row and row[field]:
                try:
                    float(row[field])
                except ValueError:
                    return False, f"Invalid numeric value for {field}: {row[field]}"
        
        return True, ""
    
    @classmethod
    def apply_defaults(cls, row: Dict, schema_name: str) -> Dict:
        """
        Apply default values to missing fields
        
        Args:
            row: Row dictionary
            schema_name: Name of schema
        
        Returns:
            Row with defaults applied
        """
        schema = cls.get_schema(schema_name)
        if not schema or 'default_values' not in schema:
            return row
        
        for field, default_value in schema['default_values'].items():
            if field not in row or row[field] == '':
                row[field] = default_value
        
        return row
