"""
AIMA Configuration
Centralized configuration for Autonomous Inventory Management Agent
"""

import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class AgentConfig:
    """Configuration for the AIMA agent behavior"""
    
    # Popularity Index Parameters
    POPULARITY_WINDOW_DAYS: int = 7  # Days to consider for popularity calculation
    POPULARITY_DECAY_FACTOR: float = 0.9  # Exponential decay for older data
    POPULARITY_MIN_THRESHOLD: float = 0.1  # Minimum popularity index
    POPULARITY_MAX_THRESHOLD: float = 10.0  # Maximum popularity index
    
    # Demand Prediction Parameters
    DEMAND_HISTORY_DAYS: int = 14  # Days of history for demand prediction
    DEMAND_PREDICTION_HORIZON: int = 3  # Days to predict ahead
    DEMAND_SMOOTHING_ALPHA: float = 0.3  # Exponential smoothing factor
    
    # Restock Decision Parameters
    BASE_REORDER_POINT: float = 20.0  # Base reorder point (units)
    SAFETY_STOCK_MULTIPLIER: float = 1.5  # Multiplier for safety stock
    MAX_ORDER_QUANTITY: int = 1000  # Maximum units per order
    MIN_ORDER_QUANTITY: int = 10  # Minimum units per order
    
    # Adaptive Threshold Parameters
    THRESHOLD_ADJUSTMENT_RATE: float = 0.2  # How fast thresholds adapt
    HIGH_POPULARITY_THRESHOLD: float = 3.0  # Threshold for "high demand" products
    LOW_POPULARITY_THRESHOLD: float = 0.5  # Threshold for "low demand" products
    
    # Economic Order Quantity (EOQ) Parameters
    HOLDING_COST_PER_UNIT: float = 2.0  # Annual holding cost per unit
    ORDER_COST: float = 50.0  # Fixed cost per order
    
    # Decision Logging
    LOG_ALL_DECISIONS: bool = True
    DECISION_CONFIDENCE_THRESHOLD: float = 0.7  # Minimum confidence to auto-execute

@dataclass
class DatabaseConfig:
    """Database configuration"""
    DB_PATH: str = "data/aima.db"
    BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 24

@dataclass
class UIConfig:
    """UI/Dashboard configuration"""
    DASHBOARD_THEME: str = "monochrome"  # Black and white theme
    REFRESH_INTERVAL_SECONDS: int = 5
    MAX_PRODUCTS_DISPLAY: int = 50
    ALERT_THRESHOLD_DAYS: int = 2  # Days until stockout to show alert

@dataclass
class SimulationConfig:
    """Simulation parameters for testing"""
    SIMULATION_DAYS: int = 90
    NUM_PRODUCTS: int = 20
    SALES_VOLATILITY: float = 0.3  # Standard deviation factor
    SEASONAL_AMPLITUDE: float = 0.5  # Seasonal variation amplitude
    LEAD_TIME_DAYS: int = 3  # Supplier lead time

# Global configuration instances
AGENT = AgentConfig()
DATABASE = DatabaseConfig()
UI = UIConfig()
SIMULATION = SimulationConfig()

# Product Categories
PRODUCT_CATEGORIES = [
    "Electronics",
    "Clothing",
    "Food & Beverage",
    "Home & Garden",
    "Sports & Outdoors",
    "Books & Media",
    "Health & Beauty",
    "Toys & Games"
]

# Supplier Configuration
SUPPLIERS = {
    "supplier_a": {"lead_time": 2, "reliability": 0.95},
    "supplier_b": {"lead_time": 5, "reliability": 0.85},
    "supplier_c": {"lead_time": 3, "reliability": 0.90}
}

def get_config() -> Dict:
    """Get all configuration as a dictionary"""
    return {
        "agent": AGENT.__dict__,
        "database": DATABASE.__dict__,
        "ui": UI.__dict__,
        "simulation": SIMULATION.__dict__,
        "suppliers": SUPPLIERS,
        "categories": PRODUCT_CATEGORIES
    }

def validate_config() -> bool:
    """Validate configuration parameters"""
    try:
        assert AGENT.POPULARITY_WINDOW_DAYS > 0
        assert 0 < AGENT.POPULARITY_DECAY_FACTOR < 1
        assert AGENT.DEMAND_HISTORY_DAYS >= AGENT.POPULARITY_WINDOW_DAYS
        assert 0 < AGENT.DEMAND_SMOOTHING_ALPHA < 1
        assert AGENT.MIN_ORDER_QUANTITY < AGENT.MAX_ORDER_QUANTITY
        return True
    except AssertionError:
        return False

if __name__ == "__main__":
    if validate_config():
        print("✓ Configuration validated successfully")
        print(f"\nCurrent Configuration:")
        import json
        print(json.dumps(get_config(), indent=2, default=str))
    else:
        print("✗ Configuration validation failed")
