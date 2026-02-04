# AIMA - Autonomous Inventory Management Agent

An AI agent that autonomously manages store inventory without fixed rules or manual monitoring.

## 🎯 Overview

AIMA (Autonomous Inventory Management Agent) is an intelligent system that:

- **Observes sales** in real-time and updates stock levels automatically
- **Adapts dynamically** based on product popularity and demand patterns
- **Predicts demand** using historical sales data
- **Makes autonomous restocking decisions** with transparent reasoning
- **Maintains optimal inventory** with minimal human intervention

Unlike traditional inventory systems with static reorder points, AIMA continuously learns from sales patterns and adjusts its behavior accordingly.

## 🧠 Core Concepts

### 1. Popularity Index
Each product has a dynamic **Popularity Index** that changes based on recent sales velocity:
- High popularity → Earlier restocking threshold
- Low popularity → Lower threshold to prevent overstock
- Calculated using exponential decay for recent data

### 2. Adaptive Thresholds
Reorder points adapt automatically based on:
- Current popularity index
- Predicted short-term demand
- Supplier lead time
- Safety stock requirements

### 3. Three-Signal Decision Framework
Every restocking decision considers:
1. **Current stock level** - How much inventory is available now
2. **Adaptive threshold** - Dynamic reorder point based on popularity
3. **Predicted demand** - Forecasted sales for the coming days

### 4. Transparent Reasoning
All decisions are logged with clear explanations:
- Why a decision was made
- What data influenced it
- Confidence score for the recommendation

## 📁 Project Structure

```
AIMA/
├── agents/              # AI agent logic
│   └── inventory_agent.py
├── data/                # Database storage
├── engine/              # Core processing engine
│   └── core.py
├── simulations/         # Testing & simulation
│   └── simulator.py
├── tests/               # Unit tests
│   └── test_aima.py
├── ui/                  # Dashboard interface
│   └── dashboard.py
├── utils/               # Utilities
│   ├── database.py      # Database operations
│   └── math_utils.py    # Forecasting & calculations
├── app.py               # Main application
├── config.py            # Configuration
└── requirements.txt     # Dependencies
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Neogenxx/AIMA.git
cd AIMA

# Install dependencies
pip install -r requirements.txt
```

### Demo Mode

```bash
# Setup demo environment with simulated data
python app.py demo --products 20 --days 30
```

This will:
- Create 20 sample products
- Simulate 30 days of sales
- Generate initial agent decisions
- Show performance report

### View Dashboard

```bash
# Launch interactive dashboard
python app.py dashboard
```

The dashboard shows:
- Inventory status with stock levels
- Product popularity rankings
- Restock recommendations
- Pending orders
- Analysis summary

### Cashier Workflow (NEW!)

AIMA now includes a robust cashier interface for point-of-sale transactions:

```bash
# Start web server with cashier
python web_server.py
```

Navigate to **http://localhost:5000** and click **"CASHIER"** (top-right button).

**Submit a Sale**:
1. Select product from dropdown
2. Enter quantity
3. Click "Submit Sale"
4. See success timestamp (ISO-8601 UTC)

**View Pending Sales**:
- Sidebar shows pending sales count
- Displays projected stock after pending sales
- Shows `inventory - pending_sales` preview

**Run Agent** (Demo only):
1. Click "Run Agent (Demo)" button
2. Confirm execution
3. Agent processes all pending sales
4. Updates `inventory.csv` and creates restock decisions
5. See results in `restock_log.csv`

**CSV Files Updated**:
- `data/sales_log.csv` - Atomic append of each sale
- `data/inventory.csv` - Updated by agent
- `data/restock_log.csv` - Agent decisions logged
- `data/last_run.json` - Tracks processed sales

See [Cashier Workflow Guide](docs/cashier_workflow.md) for full documentation.

### Interactive Mode
- Inventory status with stock levels
- Product popularity rankings
- Restock recommendations
- Pending orders
- Analysis summary

### Interactive Mode

```bash
# Start interactive command mode
python app.py interactive
```

Available commands:
- `sell <qty> units of <product_id>` - Process a sale
- `analyze <product_id>` - Analyze specific product
- `analyze all` - Analyze all products
- `list products` - List all products
- `decisions` - Show recent decisions
- `report` - Generate performance report
- `simulate day` - Simulate one day of sales
- `help` - Show help

### Run Tests

```bash
# Run complete test suite
python app.py test
```

## 🔧 Configuration

Edit `config.py` to customize agent behavior:

```python
# Popularity Index Parameters
POPULARITY_WINDOW_DAYS = 7        # Days to consider
POPULARITY_DECAY_FACTOR = 0.9     # Decay for older data

# Demand Prediction Parameters
DEMAND_HISTORY_DAYS = 14          # Days of history
DEMAND_PREDICTION_HORIZON = 3     # Days to predict ahead

# Restock Decision Parameters
BASE_REORDER_POINT = 20.0         # Base threshold
SAFETY_STOCK_MULTIPLIER = 1.5     # Safety stock factor
```

## 📊 How It Works

### Sales Event Flow

1. **Sale occurs** → Agent observes the transaction
2. **Stock updated** → Current inventory decremented
3. **Popularity calculated** → Recent sales velocity analyzed
4. **Demand predicted** → Future sales forecasted
5. **Threshold computed** → Dynamic reorder point set
6. **Decision made** → Restock if stock < threshold
7. **Order placed** → Automatic or manual execution
8. **Reasoning logged** → Decision explanation stored

### Decision Logic

```python
if current_stock < adaptive_threshold:
    order_quantity = calculate_optimal_order(
        shortage=adaptive_threshold - current_stock,
        predicted_demand=forecast,
        lead_time=supplier_lead_time
    )
    
    if confidence > threshold:
        execute_restock_order(order_quantity)
```

### Popularity Calculation

```python
popularity_index = weighted_sales_velocity / base_velocity

where:
    weighted_sales_velocity = Σ(sales_t * decay^(days_ago))
```

## 🎮 Usage Examples

### Example 1: Process Sales

```python
from engine.core import AIMAEngine

engine = AIMAEngine(auto_execute=True)

# Record a sale
result = engine.process_sale("PROD-001", quantity=5)

# Agent automatically:
# - Updates stock
# - Recalculates popularity
# - Predicts demand
# - Makes restock decision
```

### Example 2: Analyze Product

```python
# Analyze specific product
decision = engine.analyze_product("PROD-001")

print(f"Stock: {decision['current_stock']}")
print(f"Threshold: {decision['adaptive_threshold']}")
print(f"Popularity: {decision['popularity_index']}")
print(f"Decision: {decision['decision_type']}")
```

### Example 3: Run Simulation

```python
from simulations.simulator import SalesSimulator

simulator = SalesSimulator(engine.db)

# Simulate 90 days of sales
results = simulator.run_simulation(days=90, agent=engine.agent)
```

## 🧪 Testing

The test suite covers:

- **Database operations** - Product management, sales recording
- **Mathematical functions** - Forecasting, popularity calculation
- **Agent decisions** - Decision-making logic, confidence scoring
- **Simulations** - Sales pattern generation, performance analysis

Run specific test categories:

```bash
python -m unittest tests.test_aima.TestInventoryAgent
python -m unittest tests.test_aima.TestDemandForecaster
```

## 📈 Features

### Current Features
✅ Autonomous inventory monitoring  
✅ Dynamic popularity-based thresholds  
✅ Demand forecasting (exponential smoothing)  
✅ Transparent decision reasoning  
✅ Black & white terminal dashboard  
✅ Sales simulation for testing  
✅ Comprehensive logging  
✅ Confidence scoring  

### Potential Enhancements
🔲 Seasonal pattern detection  
🔲 Multi-supplier optimization  
🔲 Budget constraint handling  
🔲 Substitute product awareness  
🔲 External signal integration (weather, events)  
🔲 Machine learning forecasting  
🔲 Web-based dashboard  
🔲 API endpoints  

## 🔍 Performance Metrics

AIMA tracks:

- **Decision Accuracy** - How well predictions match reality
- **Stockout Prevention** - Success rate avoiding out-of-stock
- **Inventory Turnover** - How efficiently stock is managed
- **Order Optimization** - Economic order quantity analysis
- **Confidence Trends** - Agent certainty over time

View performance report:

```bash
python app.py analyze
```

## 🛠️ Advanced Usage

### Custom Agent Behavior

```python
from agents.inventory_agent import InventoryAgent
from utils.database import DatabaseManager

# Create custom agent
db = DatabaseManager("my_store.db")
agent = InventoryAgent(db, auto_execute=True)

# Customize parameters
agent.threshold_calculator.base_threshold = 30.0
agent.demand_forecaster.alpha = 0.4
```

### Continuous Monitoring

```python
# Run agent in continuous mode
engine.run_continuous_monitoring(interval_seconds=60)

# Agent will:
# - Check all products every 60 seconds
# - Make decisions automatically
# - Execute restock orders if auto_execute=True
```

## 📝 Database Schema

AIMA uses SQLite with the following tables:

- **products** - Product catalog
- **sales** - Sales transactions
- **inventory_transactions** - All stock movements
- **agent_decisions** - Decision log with reasoning
- **popularity_metrics** - Popularity index history
- **restock_orders** - Restock order tracking

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. Advanced forecasting algorithms (ARIMA, LSTM)
2. Multi-location inventory management
3. Integration with e-commerce platforms
4. Real-time alerting system
5. Mobile app dashboard

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

AIMA was designed to demonstrate autonomous agent capabilities in real-world inventory management scenarios. The system prioritizes:

- **Transparency** - Every decision is explainable
- **Adaptability** - Learns from changing patterns
- **Autonomy** - Minimal human intervention required
- **Practicality** - Built for real business use cases

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

---

**AIMA** - Smarter inventory management through autonomous AI agents
