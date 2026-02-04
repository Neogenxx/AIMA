"""
Mathematical utilities for AIMA
Includes demand forecasting, popularity calculation, and statistical functions
"""

import numpy as np
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class DemandForecaster:
    """Forecasts demand using exponential smoothing and trend analysis"""
    
    def __init__(self, alpha: float = 0.3, beta: float = 0.1):
        """
        Initialize forecaster
        
        Args:
            alpha: Smoothing parameter for level (0-1)
            beta: Smoothing parameter for trend (0-1)
        """
        self.alpha = alpha
        self.beta = beta
    
    def exponential_smoothing(self, data: List[float], alpha: Optional[float] = None) -> List[float]:
        """
        Apply exponential smoothing to data
        
        Args:
            data: Historical data points
            alpha: Smoothing factor (uses default if None)
        
        Returns:
            Smoothed data points
        """
        if not data:
            return []
        
        alpha = alpha or self.alpha
        smoothed = [data[0]]
        
        for i in range(1, len(data)):
            smoothed_value = alpha * data[i] + (1 - alpha) * smoothed[i-1]
            smoothed.append(smoothed_value)
        
        return smoothed
    
    def double_exponential_smoothing(self, data: List[float]) -> Tuple[float, float]:
        """
        Apply double exponential smoothing (Holt's method)
        
        Returns:
            (level, trend) for forecasting
        """
        if len(data) < 2:
            return (data[0] if data else 0, 0)
        
        # Initialize
        level = data[0]
        trend = data[1] - data[0]
        
        # Smooth
        for value in data[1:]:
            last_level = level
            level = self.alpha * value + (1 - self.alpha) * (level + trend)
            trend = self.beta * (level - last_level) + (1 - self.beta) * trend
        
        return level, trend
    
    def forecast_next_period(self, historical_sales: List[float], periods_ahead: int = 1) -> float:
        """
        Forecast demand for future periods
        
        Args:
            historical_sales: List of historical sales data
            periods_ahead: Number of periods to forecast ahead
        
        Returns:
            Forecasted demand
        """
        if not historical_sales:
            return 0.0
        
        if len(historical_sales) == 1:
            return historical_sales[0]
        
        level, trend = self.double_exponential_smoothing(historical_sales)
        forecast = level + (periods_ahead * trend)
        
        return max(0, forecast)  # Demand can't be negative
    
    def calculate_moving_average(self, data: List[float], window: int) -> List[float]:
        """Calculate moving average"""
        if len(data) < window:
            return [np.mean(data)] * len(data)
        
        moving_avg = []
        for i in range(len(data)):
            if i < window - 1:
                moving_avg.append(np.mean(data[:i+1]))
            else:
                moving_avg.append(np.mean(data[i-window+1:i+1]))
        
        return moving_avg
    
    def detect_seasonality(self, data: List[float], period: int = 7) -> bool:
        """
        Detect if data shows seasonal pattern
        
        Args:
            data: Time series data
            period: Expected seasonal period (default 7 for weekly)
        
        Returns:
            True if seasonality detected
        """
        if len(data) < period * 2:
            return False
        
        # Simple autocorrelation check
        mean = np.mean(data)
        var = np.var(data)
        
        if var == 0:
            return False
        
        # Calculate autocorrelation at lag = period
        autocorr = sum((data[i] - mean) * (data[i-period] - mean) 
                      for i in range(period, len(data))) / (len(data) - period) / var
        
        # If autocorrelation > 0.5, likely seasonal
        return autocorr > 0.5


class PopularityCalculator:
    """Calculates and updates product popularity index"""
    
    def __init__(self, window_days: int = 7, decay_factor: float = 0.9):
        """
        Initialize calculator
        
        Args:
            window_days: Number of days to consider for calculation
            decay_factor: Exponential decay for older data
        """
        self.window_days = window_days
        self.decay_factor = decay_factor
    
    def calculate_sales_velocity(self, sales_data: List[Tuple[datetime, int]]) -> float:
        """
        Calculate sales velocity (units per day)
        
        Args:
            sales_data: List of (timestamp, quantity) tuples
        
        Returns:
            Average units sold per day
        """
        if not sales_data:
            return 0.0
        
        # Sort by date
        sorted_sales = sorted(sales_data, key=lambda x: x[0])
        
        # Calculate total quantity
        total_quantity = sum(qty for _, qty in sorted_sales)
        
        # Calculate time span in days
        if len(sorted_sales) == 1:
            return total_quantity
        
        time_span = (sorted_sales[-1][0] - sorted_sales[0][0]).days
        if time_span == 0:
            time_span = 1
        
        return total_quantity / time_span
    
    def calculate_weighted_velocity(self, sales_data: List[Tuple[datetime, int]]) -> float:
        """
        Calculate weighted sales velocity with exponential decay for older sales
        
        Args:
            sales_data: List of (timestamp, quantity) tuples
        
        Returns:
            Weighted velocity
        """
        if not sales_data:
            return 0.0
        
        now = datetime.now()
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for sale_date, quantity in sales_data:
            days_ago = (now - sale_date).days
            weight = self.decay_factor ** days_ago
            weighted_sum += quantity * weight
            weight_sum += weight
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    def calculate_popularity_index(self, sales_data: List[Tuple[datetime, int]], 
                                  base_velocity: float = 1.0) -> float:
        """
        Calculate popularity index
        
        Args:
            sales_data: List of (timestamp, quantity) tuples
            base_velocity: Base velocity for normalization
        
        Returns:
            Popularity index (0-10+)
        """
        current_velocity = self.calculate_weighted_velocity(sales_data)
        
        if base_velocity == 0:
            base_velocity = 1.0
        
        # Normalize to base velocity
        popularity = current_velocity / base_velocity
        
        # Clamp to reasonable range
        return max(0.1, min(10.0, popularity))
    
    def detect_trend(self, sales_data: List[Tuple[datetime, int]]) -> str:
        """
        Detect sales trend
        
        Returns:
            'increasing', 'decreasing', or 'stable'
        """
        if len(sales_data) < 2:
            return 'stable'
        
        # Sort by date
        sorted_sales = sorted(sales_data, key=lambda x: x[0])
        
        # Split into two halves
        mid = len(sorted_sales) // 2
        first_half = sorted_sales[:mid]
        second_half = sorted_sales[mid:]
        
        # Calculate average for each half
        first_avg = sum(qty for _, qty in first_half) / len(first_half)
        second_avg = sum(qty for _, qty in second_half) / len(second_half)
        
        # Determine trend
        change_pct = (second_avg - first_avg) / first_avg if first_avg > 0 else 0
        
        if change_pct > 0.2:
            return 'increasing'
        elif change_pct < -0.2:
            return 'decreasing'
        else:
            return 'stable'


class AdaptiveThresholdCalculator:
    """Calculates adaptive reorder thresholds based on popularity"""
    
    def __init__(self, base_threshold: float = 20.0, 
                 adjustment_rate: float = 0.2):
        """
        Initialize calculator
        
        Args:
            base_threshold: Base reorder point
            adjustment_rate: Rate of threshold adjustment
        """
        self.base_threshold = base_threshold
        self.adjustment_rate = adjustment_rate
    
    def calculate_threshold(self, popularity_index: float, 
                          predicted_demand: float,
                          lead_time_days: int = 3,
                          safety_factor: float = 1.5) -> float:
        """
        Calculate adaptive reorder threshold
        
        Args:
            popularity_index: Current popularity (0-10+)
            predicted_demand: Predicted daily demand
            lead_time_days: Supplier lead time
            safety_factor: Safety stock multiplier
        
        Returns:
            Adaptive reorder threshold
        """
        # Base threshold adjusted by popularity
        popularity_adjusted = self.base_threshold * (1 + self.adjustment_rate * (popularity_index - 1))
        
        # Lead time demand
        lead_time_demand = predicted_demand * lead_time_days
        
        # Safety stock
        safety_stock = lead_time_demand * (safety_factor - 1)
        
        # Combined threshold
        threshold = max(
            popularity_adjusted,
            lead_time_demand + safety_stock
        )
        
        return threshold
    
    def calculate_order_quantity(self, current_stock: float,
                                adaptive_threshold: float,
                                predicted_demand: float,
                                lead_time_days: int = 3,
                                max_order: int = 1000,
                                min_order: int = 10) -> int:
        """
        Calculate optimal order quantity
        
        Args:
            current_stock: Current inventory level
            adaptive_threshold: Reorder point
            predicted_demand: Daily demand forecast
            lead_time_days: Supplier lead time
            max_order: Maximum order quantity
            min_order: Minimum order quantity
        
        Returns:
            Recommended order quantity
        """
        # If above threshold, don't order
        if current_stock >= adaptive_threshold:
            return 0
        
        # Calculate shortage
        shortage = adaptive_threshold - current_stock
        
        # Add demand during lead time
        lead_time_demand = predicted_demand * lead_time_days
        
        # Total quantity needed
        quantity = int(shortage + lead_time_demand)
        
        # Apply bounds
        if quantity < min_order:
            return min_order if current_stock < adaptive_threshold else 0
        
        return min(quantity, max_order)


class ConfidenceScorer:
    """Calculates confidence scores for agent decisions"""
    
    def calculate_decision_confidence(self, 
                                     data_quality: float,
                                     trend_clarity: float,
                                     prediction_error: float) -> float:
        """
        Calculate confidence score for a decision
        
        Args:
            data_quality: Quality of historical data (0-1)
            trend_clarity: Clarity of trend signal (0-1)
            prediction_error: Historical prediction error (0-1, lower is better)
        
        Returns:
            Confidence score (0-1)
        """
        # Weighted combination
        confidence = (
            0.4 * data_quality +
            0.3 * trend_clarity +
            0.3 * (1 - prediction_error)
        )
        
        return max(0.0, min(1.0, confidence))
    
    def assess_data_quality(self, num_data_points: int, 
                           min_required: int = 7,
                           data_completeness: float = 1.0) -> float:
        """
        Assess quality of historical data
        
        Args:
            num_data_points: Number of historical data points
            min_required: Minimum points for good quality
            data_completeness: Ratio of expected vs actual data points
        
        Returns:
            Quality score (0-1)
        """
        if num_data_points == 0:
            return 0.0
        
        quantity_score = min(1.0, num_data_points / min_required)
        
        return 0.7 * quantity_score + 0.3 * data_completeness
