# AIMA System Architecture

## Overview

AIMA is built with a modular architecture that separates concerns into distinct layers:

```
┌─────────────────────────────────────────────────────────┐
│                   USER INTERFACE                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Dashboard   │  │ Interactive  │  │   CLI Args   │ │
│  │   (ui/)      │  │    Mode      │  │   (app.py)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    ENGINE LAYER                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  AIMAEngine - Core Orchestration                │   │
│  │  • Coordinates all components                   │   │
│  │  • Processes commands                           │   │
│  │  • Manages lifecycle                            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    AGENT LAYER                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  InventoryAgent - Autonomous Decision Maker     │   │
│  │  • Observes sales events                        │   │
│  │  • Calculates popularity & demand               │   │
│  │  • Makes restock decisions                      │   │
│  │  • Logs reasoning                               │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
           ↓                    ↓                  ↓
┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐
│ MATH UTILITIES   │  │  DATABASE UTILS  │  │ SIMULATION  │
│                  │  │                  │  │             │
│ • DemandForecast │  │ • Product CRUD   │  │ • Sales Gen │
│ • Popularity     │  │ • Sales Tracking │  │ • Testing   │
│ • Thresholds     │  │ • Decision Log   │  │ • Analysis  │
│ • Confidence     │  │ • Orders         │  │             │
└──────────────────┘  └──────────────────┘  └─────────────┘
                          ↓
                    ┌─────────────┐
                    │   SQLite    │
                    │  Database   │
                    └─────────────┘
```

## Component Details

### 1. UI Layer (`ui/`)

**Purpose**: User interaction and data visualization

**Components**:
- `dashboard.py`: Terminal-based black & white dashboard
  - Real-time inventory status
  - Popularity rankings
  - Restock recommendations
  - Pending orders

### 2. Engine Layer (`engine/`)

**Purpose**: System orchestration and coordination

**Components**:
- `core.py`: Main engine
  - `AIMAEngine`: Coordinates all subsystems
  - `AIMACommandProcessor`: Natural language command processing

**Responsibilities**:
- Initialize all components
- Route commands to appropriate handlers
- Aggregate data for reporting
- Manage system lifecycle

### 3. Agent Layer (`agents/`)

**Purpose**: Autonomous decision-making

**Components**:
- `inventory_agent.py`: Core AI agent
  - Event observation (sales)
  - Multi-signal analysis
  - Decision generation
  - Reasoning explanation

**Decision Process**:
```
1. Observe Sale Event
   ↓
2. Update Stock
   ↓
3. Calculate Popularity Index
   ↓
4. Predict Demand
   ↓
5. Compute Adaptive Threshold
   ↓
6. Make Decision (Restock/Hold)
   ↓
7. Calculate Order Quantity
   ↓
8. Generate Reasoning
   ↓
9. Log Decision
   ↓
10. Execute (if auto_execute enabled)
```

### 4. Utilities Layer (`utils/`)

**Purpose**: Reusable functionality

**Components**:

**database.py**:
- Database connection management
- CRUD operations
- Transaction logging
- Data retrieval

**math_utils.py**:
- `DemandForecaster`: Time series forecasting
  - Exponential smoothing
  - Trend detection
  - Seasonality analysis
  
- `PopularityCalculator`: Popularity metrics
  - Sales velocity calculation
  - Weighted averages with decay
  - Trend classification
  
- `AdaptiveThresholdCalculator`: Dynamic thresholds
  - Popularity-based adjustment
  - Lead time consideration
  - Safety stock calculation
  - Order quantity optimization
  
- `ConfidenceScorer`: Decision confidence
  - Data quality assessment
  - Trend clarity evaluation
  - Combined confidence scoring

### 5. Simulation Layer (`simulations/`)

**Purpose**: Testing and performance analysis

**Components**:
- `simulator.py`:
  - `SalesSimulator`: Generate realistic sales patterns
  - `PerformanceAnalyzer`: Evaluate agent performance

**Simulation Features**:
- Configurable volatility
- Seasonal patterns
- Trend generation
- Multi-product support

### 6. Data Layer (`data/`)

**Purpose**: Persistent storage

**Database Schema**:

```sql
products
  - product_id (PK)
  - name, category
  - current_stock
  - unit_cost, selling_price
  - supplier, lead_time_days

sales
  - sale_id (PK)
  - product_id (FK)
  - quantity, total_amount
  - sale_date

inventory_transactions
  - transaction_id (PK)
  - product_id (FK)
  - transaction_type (sale/restock/initial)
  - quantity, stock_before, stock_after
  - notes

agent_decisions
  - decision_id (PK)
  - product_id (FK)
  - decision_type, confidence_score
  - current_stock, popularity_index
  - adaptive_threshold, predicted_demand
  - restock_quantity, reasoning
  - executed, decision_date

popularity_metrics
  - metric_id (PK)
  - product_id (FK)
  - popularity_index, sales_velocity
  - trend, calculated_at

restock_orders
  - order_id (PK)
  - product_id (FK)
  - quantity_ordered, cost
  - order_date, expected_delivery_date
  - actual_delivery_date, status
```

## Data Flow

### Sales Event Processing

```
User/Simulation
      ↓
[Record Sale]
      ↓
Database ← Update stock
      ↓
Agent.observe_sale()
      ↓
Agent.make_decision()
      ↓
┌─────────────────────┐
│ Gather Information  │
│ • Current stock     │
│ • Sales history     │
│ • Product details   │
└─────────────────────┘
      ↓
┌─────────────────────┐
│ Calculate Metrics   │
│ • Popularity index  │
│ • Sales velocity    │
│ • Trend direction   │
└─────────────────────┘
      ↓
┌─────────────────────┐
│ Predict Demand      │
│ • Load history      │
│ • Apply smoothing   │
│ • Forecast periods  │
└─────────────────────┘
      ↓
┌─────────────────────┐
│ Calculate Threshold │
│ • Base threshold    │
│ • Popularity adj.   │
│ • Lead time demand  │
│ • Safety stock      │
└─────────────────────┘
      ↓
┌─────────────────────┐
│ Make Decision       │
│ • Compare vs thresh │
│ • Calculate order   │
│ • Assess confidence │
│ • Generate reason   │
└─────────────────────┘
      ↓
┌─────────────────────┐
│ Log & Execute       │
│ • Log to database   │
│ • Create order?     │
│ • Return decision   │
└─────────────────────┘
      ↓
Dashboard/User
```

## Key Algorithms

### 1. Popularity Index Calculation

```python
weighted_velocity = Σ(quantity_i × decay^days_ago_i) / Σ(decay^days_ago_i)
popularity_index = weighted_velocity / base_velocity
```

### 2. Demand Forecasting (Double Exponential Smoothing)

```python
# Initialize
level_0 = data[0]
trend_0 = data[1] - data[0]

# Update for each t
level_t = α × value_t + (1-α) × (level_{t-1} + trend_{t-1})
trend_t = β × (level_t - level_{t-1}) + (1-β) × trend_{t-1}

# Forecast
forecast_{t+h} = level_t + h × trend_t
```

### 3. Adaptive Threshold Calculation

```python
# Popularity adjustment
popularity_adj = base_threshold × (1 + adjustment_rate × (popularity - 1))

# Lead time demand
lead_time_demand = predicted_demand × lead_time_days

# Safety stock
safety_stock = lead_time_demand × (safety_factor - 1)

# Final threshold
threshold = max(popularity_adj, lead_time_demand + safety_stock)
```

### 4. Order Quantity Optimization

```python
if current_stock >= threshold:
    order = 0
else:
    shortage = threshold - current_stock
    future_demand = predicted_demand × lead_time_days
    order = clamp(shortage + future_demand, min_order, max_order)
```

### 5. Confidence Scoring

```python
confidence = (
    0.4 × data_quality +      # Amount and completeness of data
    0.3 × trend_clarity +     # Clarity of trend signal
    0.3 × (1 - pred_error)    # Historical accuracy
)
```

## Configuration Management

All tunable parameters in `config.py`:

```python
AgentConfig:
  - POPULARITY_WINDOW_DAYS
  - POPULARITY_DECAY_FACTOR
  - DEMAND_HISTORY_DAYS
  - DEMAND_SMOOTHING_ALPHA
  - BASE_REORDER_POINT
  - SAFETY_STOCK_MULTIPLIER
  - THRESHOLD_ADJUSTMENT_RATE
  - DECISION_CONFIDENCE_THRESHOLD

DatabaseConfig:
  - DB_PATH
  - BACKUP_ENABLED

UIConfig:
  - DASHBOARD_THEME
  - REFRESH_INTERVAL_SECONDS
  - MAX_PRODUCTS_DISPLAY

SimulationConfig:
  - SIMULATION_DAYS
  - NUM_PRODUCTS
  - SALES_VOLATILITY
  - SEASONAL_AMPLITUDE
```

## Extensibility Points

The architecture supports extensions:

1. **Custom Forecasting Models**: Replace `DemandForecaster`
2. **Different Threshold Strategies**: Extend `AdaptiveThresholdCalculator`
3. **Additional Data Sources**: Add new utility modules
4. **Alternative UIs**: Web dashboard, mobile app
5. **External Integrations**: API connectors, webhooks
6. **Machine Learning**: Replace statistical methods with ML models

## Performance Considerations

- **Database**: SQLite for simplicity, can scale to PostgreSQL
- **In-memory caching**: Recent data cached for faster access
- **Batch processing**: Process multiple products in parallel
- **Incremental updates**: Only recalculate when needed
- **Asynchronous operations**: Non-blocking I/O for UI

## Security Considerations

- No external network access by default
- Local database with file permissions
- No user authentication (single-user system)
- Input validation on all data entry
- SQL injection prevention via parameterized queries

## Future Architecture Enhancements

1. **Microservices**: Split into separate services
2. **Message Queue**: Async event processing (Redis, RabbitMQ)
3. **API Layer**: RESTful API for external integration
4. **Distributed Computing**: Multi-store coordination
5. **Cloud Deployment**: AWS/Azure/GCP support
6. **Real-time Analytics**: Streaming data processing
