"""
Core AIMA Agent
Autonomous decision-making agent for inventory management
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager
from utils.math_utils import (
    DemandForecaster,
    PopularityCalculator,
    AdaptiveThresholdCalculator,
    ConfidenceScorer
)
from config import AGENT

class InventoryAgent:
    """
    Autonomous Inventory Management Agent
    
    Makes intelligent restocking decisions based on:
    1. Current stock levels
    2. Adaptive thresholds (based on popularity)
    3. Predicted demand
    """
    
    def __init__(self, db_manager: DatabaseManager, auto_execute: bool = False):
        """
        Initialize the agent
        
        Args:
            db_manager: Database manager instance
            auto_execute: Whether to auto-execute restock orders
        """
        self.db = db_manager
        self.auto_execute = auto_execute
        
        # Initialize calculators
        self.demand_forecaster = DemandForecaster(
            alpha=AGENT.DEMAND_SMOOTHING_ALPHA
        )
        self.popularity_calculator = PopularityCalculator(
            window_days=AGENT.POPULARITY_WINDOW_DAYS,
            decay_factor=AGENT.POPULARITY_DECAY_FACTOR
        )
        self.threshold_calculator = AdaptiveThresholdCalculator(
            base_threshold=AGENT.BASE_REORDER_POINT,
            adjustment_rate=AGENT.THRESHOLD_ADJUSTMENT_RATE
        )
        self.confidence_scorer = ConfidenceScorer()
        
        print("🤖 AIMA Agent initialized")
        print(f"   Auto-execute: {auto_execute}")
    
    def observe_sale(self, product_id: str, quantity: int) -> Dict:
        """
        Observe a sale event and trigger decision-making
        
        Args:
            product_id: Product identifier
            quantity: Quantity sold
        
        Returns:
            Decision result dictionary
        """
        # Record the sale
        success = self.db.record_sale(product_id, quantity)
        
        if not success:
            return {
                "success": False,
                "error": "Failed to record sale (insufficient stock or invalid product)"
            }
        
        # Trigger agent decision
        decision = self.make_decision(product_id)
        
        return {
            "success": True,
            "sale_recorded": True,
            "decision": decision
        }
    
    def make_decision(self, product_id: str) -> Dict:
        """
        Make a restocking decision for a product
        
        Args:
            product_id: Product identifier
        
        Returns:
            Decision dictionary with reasoning
        """
        # Get product details
        product = self.db.get_product(product_id)
        if not product:
            return {"error": "Product not found"}
        
        # Gather data
        current_stock = product['current_stock']
        lead_time = product['lead_time_days']
        
        # Get sales history
        sales_history = self.db.get_sales_history(
            product_id, 
            days=AGENT.DEMAND_HISTORY_DAYS
        )
        
        # Calculate popularity
        popularity_data = self._prepare_sales_data(sales_history)
        popularity_index = self.popularity_calculator.calculate_popularity_index(
            popularity_data
        )
        sales_velocity = self.popularity_calculator.calculate_weighted_velocity(
            popularity_data
        )
        trend = self.popularity_calculator.detect_trend(popularity_data)
        
        # Predict demand
        daily_sales = self._extract_daily_sales(sales_history)
        predicted_demand = self.demand_forecaster.forecast_next_period(
            daily_sales,
            periods_ahead=AGENT.DEMAND_PREDICTION_HORIZON
        )
        
        # Calculate adaptive threshold
        adaptive_threshold = self.threshold_calculator.calculate_threshold(
            popularity_index=popularity_index,
            predicted_demand=predicted_demand,
            lead_time_days=lead_time,
            safety_factor=AGENT.SAFETY_STOCK_MULTIPLIER
        )
        
        # Determine if restocking is needed
        needs_restock = current_stock < adaptive_threshold
        
        # Calculate order quantity
        order_quantity = 0
        if needs_restock:
            order_quantity = self.threshold_calculator.calculate_order_quantity(
                current_stock=current_stock,
                adaptive_threshold=adaptive_threshold,
                predicted_demand=predicted_demand,
                lead_time_days=lead_time,
                max_order=AGENT.MAX_ORDER_QUANTITY,
                min_order=AGENT.MIN_ORDER_QUANTITY
            )
        
        # Calculate confidence
        data_quality = self.confidence_scorer.assess_data_quality(
            len(sales_history),
            min_required=AGENT.POPULARITY_WINDOW_DAYS
        )
        trend_clarity = 0.9 if trend != 'stable' else 0.6
        prediction_error = 0.2  # Simplified for now
        
        confidence = self.confidence_scorer.calculate_decision_confidence(
            data_quality=data_quality,
            trend_clarity=trend_clarity,
            prediction_error=prediction_error
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            product_name=product['name'],
            current_stock=current_stock,
            adaptive_threshold=adaptive_threshold,
            popularity_index=popularity_index,
            trend=trend,
            predicted_demand=predicted_demand,
            needs_restock=needs_restock,
            order_quantity=order_quantity
        )
        
        # Determine decision type
        decision_type = "restock" if needs_restock else "hold"
        
        # Execute if appropriate
        executed = False
        order_id = None
        
        if needs_restock and self.auto_execute and confidence >= AGENT.DECISION_CONFIDENCE_THRESHOLD:
            order_id = self.db.create_restock_order(
                product_id=product_id,
                quantity=order_quantity,
                lead_time_days=lead_time
            )
            executed = True
        
        # Log decision
        decision_id = self.db.log_decision(
            product_id=product_id,
            decision_type=decision_type,
            current_stock=current_stock,
            popularity_index=popularity_index,
            adaptive_threshold=adaptive_threshold,
            predicted_demand=predicted_demand,
            restock_quantity=order_quantity,
            confidence_score=confidence,
            reasoning=reasoning,
            executed=executed
        )
        
        # Log popularity metrics
        self.db.log_popularity_metric(
            product_id=product_id,
            popularity_index=popularity_index,
            sales_velocity=sales_velocity,
            trend=trend
        )
        
        return {
            "decision_id": decision_id,
            "product_id": product_id,
            "product_name": product['name'],
            "decision_type": decision_type,
            "current_stock": current_stock,
            "adaptive_threshold": round(adaptive_threshold, 2),
            "popularity_index": round(popularity_index, 2),
            "sales_velocity": round(sales_velocity, 2),
            "trend": trend,
            "predicted_demand": round(predicted_demand, 2),
            "needs_restock": needs_restock,
            "order_quantity": order_quantity,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "executed": executed,
            "order_id": order_id
        }
    
    def _prepare_sales_data(self, sales_history: List[Dict]) -> List[Tuple[datetime, int]]:
        """Convert sales history to (timestamp, quantity) tuples"""
        data = []
        for sale in sales_history:
            # Parse timestamp
            timestamp = datetime.fromisoformat(sale['sale_date'])
            quantity = sale['quantity']
            data.append((timestamp, quantity))
        return data
    
    def _extract_daily_sales(self, sales_history: List[Dict]) -> List[float]:
        """Extract daily sales quantities"""
        if not sales_history:
            return []
        
        # Group by date
        from collections import defaultdict
        daily_sales = defaultdict(int)
        
        for sale in sales_history:
            date = sale['sale_date'].split()[0]  # Get date part
            daily_sales[date] += sale['quantity']
        
        # Convert to sorted list
        sorted_dates = sorted(daily_sales.keys())
        return [daily_sales[date] for date in sorted_dates]
    
    def _generate_reasoning(self, product_name: str, current_stock: int,
                          adaptive_threshold: float, popularity_index: float,
                          trend: str, predicted_demand: float,
                          needs_restock: bool, order_quantity: int) -> str:
        """Generate human-readable reasoning for the decision"""
        
        reasoning_parts = []
        
        # Stock status
        reasoning_parts.append(
            f"Product '{product_name}' currently has {current_stock} units in stock."
        )
        
        # Popularity assessment
        if popularity_index > AGENT.HIGH_POPULARITY_THRESHOLD:
            popularity_desc = "high demand"
        elif popularity_index < AGENT.LOW_POPULARITY_THRESHOLD:
            popularity_desc = "low demand"
        else:
            popularity_desc = "moderate demand"
        
        reasoning_parts.append(
            f"Popularity index is {popularity_index:.2f} ({popularity_desc}, trend: {trend})."
        )
        
        # Threshold comparison
        reasoning_parts.append(
            f"Adaptive reorder threshold is {adaptive_threshold:.0f} units "
            f"(adjusted based on popularity and predicted demand of {predicted_demand:.1f} units/day)."
        )
        
        # Decision
        if needs_restock:
            reasoning_parts.append(
                f"Stock level is below threshold. RECOMMENDATION: Restock {order_quantity} units "
                f"to maintain optimal inventory levels and prevent stockouts."
            )
        else:
            reasoning_parts.append(
                f"Stock level is adequate. RECOMMENDATION: Hold current inventory. "
                f"No restocking needed at this time."
            )
        
        return " ".join(reasoning_parts)
    
    def run_continuous(self, check_interval_seconds: int = 60):
        """
        Run agent in continuous monitoring mode
        
        Args:
            check_interval_seconds: Time between checks
        """
        import time
        
        print(f"\n🔄 Starting continuous monitoring (checking every {check_interval_seconds}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Get all products
                products = self.db.get_all_products()
                
                for product in products:
                    decision = self.make_decision(product['product_id'])
                    
                    if decision.get('needs_restock'):
                        print(f"⚠️  {product['name']}: RESTOCK NEEDED")
                        print(f"   {decision['reasoning'][:100]}...")
                
                time.sleep(check_interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Continuous monitoring stopped")
    
    def analyze_all_products(self) -> List[Dict]:
        """
        Analyze all products and return decisions
        
        Returns:
            List of decision dictionaries
        """
        products = self.db.get_all_products()
        decisions = []
        
        print(f"\n📊 Analyzing {len(products)} products...\n")
        
        for product in products:
            decision = self.make_decision(product['product_id'])
            decisions.append(decision)
            
            # Print summary
            status = "🔴 RESTOCK" if decision['needs_restock'] else "🟢 OK"
            print(f"{status} {product['name']}: "
                  f"Stock={decision['current_stock']}, "
                  f"Threshold={decision['adaptive_threshold']}, "
                  f"Popularity={decision['popularity_index']}")
        
        return decisions
