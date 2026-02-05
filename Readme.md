# AIMA - Autonomous Inventory Management Agent
## 100% CSV-Based Edition

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows | Linux | macOS](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/yourusername/AIMA)

**Intelligent inventory management powered by AI, with 100% reliable CSV storage, full profit analytics, and clear pending sales workflow.**

---

## ✨ Features

- 🎯 **100% CSV-Based** - No database required, fully portable
- 💰 **Full Profit Analytics** - Cost tracking, revenue, and profit calculations
- 📊 **Real-time Dashboard** - Web-based UI with live inventory status
- 🤖 **Intelligent Agent** - Automatic restock decisions based on demand
- 🔄 **Pending Sales Workflow** - Clear distinction between submitted and processed sales
- 🪟 **Windows Compatible** - Reliable file operations on all platforms
- 🔒 **Atomic Operations** - Safe concurrent access with file locking
- 📈 **Adaptive Thresholds** - Dynamic restocking based on popularity

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Demo Data
```bash
python app.py demo --products 20 --sales 50
```

This creates:
- 20 products in `data/inventory.csv`
- 50 simulated sales transactions

### 3. Launch Dashboard
```bash
python app.py dashboard
```

Open your browser to: **http://localhost:5000**

---

## 📋 Complete Solution to All Requirements

### ✅ Requirement 1: Fix Cashier Sale Error (Windows)
**Problem:** "Failed to write to sales log"

**Solution:** 
- Atomic CSV operations with automatic file creation
- Absolute path handling works from any directory
- Auto-adds headers if file missing
- Windows file locking via `msvcrt`
- Force disk flush with `os.fsync()`

**Implementation:** `scripts/csv_helpers.py`

### ✅ Requirement 2: Remove Database Layer
**Status:** Complete - 100% CSV storage

**Removed:**
- `utils/database.py` - SQLite dependencies
- Database references in all modules

**Replaced with:**
- `utils/csv_data_manager.py` - Pure CSV operations
- `scripts/csv_helpers.py` - Atomic file operations

### ✅ Requirement 3: Add Pricing & Profit Support
**Status:** Fully implemented

**Inventory Schema:**
```csv
product_id,name,stock,base_threshold,adaptive_threshold,popularity_ewma,popularity_index,cost_price,selling_price
```

**Sales Log Schema (Upgraded):**
```csv
timestamp,product_id,qty,cost_price,selling_price,total_cost,total_revenue,profit
```

Every sale captures:
- Cost price (snapshot at sale time)
- Selling price
- Total cost = qty × cost_price
- Total revenue = qty × selling_price
- Profit = revenue - cost

### ✅ Requirement 4: Upgrade Sales Log Schema
**Status:** Complete with full analytics fields

Each sale event stores:
- ✅ `timestamp` - ISO-8601 UTC
- ✅ `product_id` - Product identifier
- ✅ `qty` - Quantity sold
- ✅ `cost_price` - Cost per unit
- ✅ `selling_price` - Selling price per unit
- ✅ `total_cost` - Total cost
- ✅ `total_revenue` - Total revenue
- ✅ `profit` - Net profit

Supports:
- Revenue analysis
- Profit margins by product
- Cost tracking over time
- Time-series profitability

### ✅ Requirement 5: Fix Cashier Workflow
**Status:** Complete with clear UI indicators

**Workflow:**
1. **Cashier submits sale** → Atomically appends to `sales_log.csv`
2. **Dashboard shows pending** → "⚠️ 3 sales pending agent processing"
3. **Inventory shows projected stock** → Current: 50, Pending: -3, Projected: 47
4. **Agent processes pending** → Updates inventory + logs restock decisions
5. **UI updates** → Pending count goes to 0, inventory reflects actual stock

**UI clearly shows:**
- Number of pending sales
- Projected stock after pending sales are processed
- Current stock vs. projected stock
- "Run Agent" button to process pending sales

---

## 📁 Project Structure

```
AIMA_REFACTORED/
├── app.py                      # Main CLI entry point
├── web_server.py               # Flask web server
├── requirements.txt            # Python dependencies
├── IMPLEMENTATION_GUIDE.md     # Complete technical guide
│
├── data/                       # CSV data storage
│   ├── inventory.csv          # Product catalog
│   ├── sales_log.csv          # Sales transactions
│   ├── restock_log.csv        # Restock decisions
│   └── last_run.json          # Agent checkpoint
│
├── scripts/
│   ├── csv_helpers.py         # Atomic CSV operations
│   └── run_agent.py           # Agent processor
│
├── utils/
│   └── csv_data_manager.py    # CSV data layer
│
├── simulations/
│   ├── product_generator.py   # Demo product generator
│   └── sales_simulator.py     # Sales simulator
│
└── templates/
    └── dashboard.html          # Web dashboard UI
```

---

## 🎮 Usage Examples

### Submit a Sale (API)
```python
import requests

response = requests.post('http://localhost:5000/api/cashier/submit-sale', json={
    'product_id': 'PROD-001',
    'qty': 2
})

print(response.json())
# {
#   'success': True,
#   'profit': 800.00,
#   'message': 'Sale recorded: 2x Gaming Laptop (Profit: $800.00)'
# }
```

### Check Pending Sales
```python
response = requests.get('http://localhost:5000/api/cashier/pending-preview')
data = response.json()

print(f"Pending: {data['pending_count']} sales")
for item in data['preview']:
    print(f"  {item['product_id']}: Current={item['current_stock']}, Projected={item['projected_stock']}")
```

### Run Agent (Process Pending Sales)
```bash
python scripts/run_agent.py
```

Output:
```
==============================================================
  AIMA Agent - Batch Processing (CSV-Only)
==============================================================
Last processed row: 47
Processing 3 pending sales...
  Processed: PROD-001 (Stock: 50 → 47)
  Processed: PROD-002 (Stock: 100 → 98)
    → RESTOCK: 35 units (confidence: 85%)

==============================================================
  Agent run complete!
  Sales processed: 3
  Restocks created: 1
==============================================================
```

### Analyze Inventory
```bash
python app.py analyze
```

Output:
```
================================================================================
INVENTORY SUMMARY
================================================================================
Total Products: 20
Total Stock: 1,450 units
Total Value: $45,600.00
Low Stock Items: 3
Out of Stock: 0
Total Revenue: $35,600.00
Total Profit: $12,350.00
================================================================================

🚨 CRITICAL (2 items):
  PROD-005: USB-C Hub - Stock: 5 (Threshold: 20)
  PROD-012: Coffee Beans - Stock: 8 (Threshold: 15)

⚠️  LOW STOCK (3 items):
  PROD-003: Wireless Mouse - Stock: 18 (Threshold: 25)
  ...
```

---

## 🔒 Reliability Features

### Atomic Operations
All CSV writes use atomic operations:
1. **File locking** - Prevents concurrent write conflicts
2. **Temp file + rename** - Ensures no partial writes
3. **Force sync** - `os.fsync()` guarantees disk write

### Cross-Platform File Locking
```python
# Unix/Linux/Mac
fcntl.flock(f.fileno(), fcntl.LOCK_EX)

# Windows
msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
```

### Automatic Recovery
- Agent tracks `last_processed_row` in `last_run.json`
- If agent crashes, it resumes from last checkpoint
- Idempotent operations - safe to re-run

### Error Handling
```python
try:
    success = atomic_append_csv(filepath, row, headers=HEADERS)
    if not success:
        return jsonify({'success': False, 'error': 'Write failed'}), 500
except Exception as e:
    log_error(e)
    return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 📊 CSV Schemas

### inventory.csv
```csv
product_id,name,stock,base_threshold,adaptive_threshold,popularity_ewma,popularity_index,cost_price,selling_price
PROD-001,Gaming Laptop X1,50,20,25.5,1.2,1.15,800.00,1200.00
```

### sales_log.csv (Full Analytics)
```csv
timestamp,product_id,qty,cost_price,selling_price,total_cost,total_revenue,profit
2026-02-04T10:30:45.123Z,PROD-001,2,800.00,1200.00,1600.00,2400.00,800.00
```

### restock_log.csv
```csv
timestamp,product_id,stock_after_sale,base_threshold,adaptive_threshold,predicted_demand_5d,popularity_index,restock_qty,reason,confidence
2026-02-04T10:31:00.000Z,PROD-001,15,20,25.5,12.5,1.15,35,Stock below threshold,0.85
```

---

## 🧪 Testing

### Test 1: Concurrent Sales (100 simultaneous)
```bash
python -c "
import threading
import requests

def submit(): 
    requests.post('http://localhost:5000/api/cashier/submit-sale', 
                  json={'product_id': 'PROD-001', 'qty': 1})

threads = [threading.Thread(target=submit) for _ in range(100)]
for t in threads: t.start()
for t in threads: t.join()
"

# Verify: No data corruption, exactly 100 sales logged
wc -l data/sales_log.csv
# Output: 101 (100 sales + 1 header)
```

### Test 2: Windows Path Handling
```powershell
# Run from different directory
cd C:\Users\YourUser\Documents
python app.py demo

# Check files created with absolute paths
dir C:\path\to\AIMA\data
# Should show: inventory.csv, sales_log.csv, etc.
```

### Test 3: Pending Sales Workflow
```bash
# 1. Submit 5 sales
for i in {1..5}; do
  curl -X POST http://localhost:5000/api/cashier/submit-sale \
    -H "Content-Type: application/json" \
    -d '{"product_id":"PROD-001","qty":1}'
done

# 2. Check pending (should be 5)
curl http://localhost:5000/api/cashier/pending-preview | jq '.pending_count'
# Output: 5

# 3. Run agent
python scripts/run_agent.py

# 4. Check pending (should be 0)
curl http://localhost:5000/api/cashier/pending-preview | jq '.pending_count'
# Output: 0
```

---

## 🔧 Configuration

### Data Directory
Default: `./data/`

Change in `utils/csv_data_manager.py`:
```python
csv_manager = CSVDataManager(data_dir="/custom/path/data")
```

### Agent Settings
Edit `scripts/run_agent.py`:
```python
# Demand prediction window
predicted_demand = calculate_demand_prediction(sales_history, days=5)

# Popularity smoothing factor
new_ewma = calculate_popularity_ewma(current, new_value, alpha=0.3)

# Adaptive threshold adjustment
adjustment_factor = 1 + 0.2 * (popularity_index - 1)
```

### Web Server Port
```bash
python app.py dashboard
# Default: localhost:5000

# Custom port
FLASK_RUN_PORT=8080 python app.py dashboard
```

---

## 📈 Analytics Examples

### Total Profit
```python
from utils.csv_data_manager import get_csv_manager

csv_manager = get_csv_manager()
sales = csv_manager.get_all_sales()

total_profit = sum(s['profit'] for s in sales)
print(f"Total Profit: ${total_profit:,.2f}")
```

### Top Products by Profit
```python
from collections import defaultdict

profit_by_product = defaultdict(float)
for sale in sales:
    profit_by_product[sale['product_id']] += sale['profit']

top_products = sorted(profit_by_product.items(), key=lambda x: x[1], reverse=True)
for product_id, profit in top_products[:10]:
    print(f"{product_id}: ${profit:,.2f}")
```

### Profit Margin
```python
total_cost = sum(s['total_cost'] for s in sales)
total_revenue = sum(s['total_revenue'] for s in sales)

margin = (total_revenue - total_cost) / total_revenue * 100 if total_revenue > 0 else 0
print(f"Profit Margin: {margin:.1f}%")
```

### Daily Profit Trend
```python
import pandas as pd

df = pd.DataFrame(sales)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date

daily_profit = df.groupby('date')['profit'].sum()
print(daily_profit)
```

---

## 🚀 Deployment

### Production Checklist
- ✅ Test on target OS (Windows/Linux)
- ✅ Verify file permissions for `data/` directory
- ✅ Set up automated backups for CSV files
- ✅ Configure monitoring for pending sales
- ✅ Test concurrent access under load
- ✅ Document any custom configurations

### Backup Strategy
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backups/aima_$DATE.tar.gz data/
find backups/ -mtime +30 -delete  # Keep 30 days
```

### Monitoring Script
```python
# monitor.py
from utils.csv_data_manager import get_csv_manager
import json

csv_manager = get_csv_manager()

# Check pending sales
with open('data/last_run.json') as f:
    last_run = json.load(f)
all_sales = csv_manager.get_all_sales()
pending = len(all_sales) - last_run.get('last_processed_row', 0)

if pending > 100:
    send_alert(f"⚠️ {pending} pending sales!")

# Check out of stock
products = csv_manager.get_all_products()
out_of_stock = [p for p in products if p['stock'] == 0]

if out_of_stock:
    send_alert(f"🚨 {len(out_of_stock)} products out of stock!")
```

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📞 Support

- **Documentation:** See `IMPLEMENTATION_GUIDE.md` for complete technical details
- **Issues:** Open an issue on GitHub
- **Questions:** Check the FAQ in `IMPLEMENTATION_GUIDE.md`

---

## 🎯 Key Takeaways

✅ **All 5 Requirements Met:**
1. Sales logging is 100% reliable on Windows
2. Database completely removed - pure CSV storage
3. Full pricing and profit support implemented
4. Sales log has complete analytics schema
5. Clear pending sales workflow with UI indicators

✅ **Production Ready:**
- Cross-platform file operations
- Atomic CSV operations with locking
- Comprehensive error handling
- Extensive testing and documentation

✅ **Easy to Use:**
- Simple CLI interface
- Web dashboard for visualization
- Clear API for integration
- No complex setup or configuration

---

**Built with ❤️ for reliable, portable inventory management**
