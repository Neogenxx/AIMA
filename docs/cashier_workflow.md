# Cashier Workflow Guide

## Overview

The AIMA cashier interface allows point-of-sale transactions to be recorded atomically in CSV format, with pending sales tracked separately from processed inventory updates.

## Quick Start

1. **Open the Dashboard**
   ```bash
   python web_server.py
   ```
   Navigate to http://localhost:5000

2. **Click "CASHIER" button** (top-right corner)

3. **Submit a Sale**:
   - Select product from dropdown
   - Enter quantity
   - Click "Submit Sale"
   - See success timestamp

4. **View Pending Sales** (in sidebar):
   - Shows count of unprocessed sales
   - Displays projected stock levels

5. **Run Agent** (click "Run Agent (Demo)"):
   - Confirm the action
   - Agent processes all pending sales
   - Updates inventory and creates restock decisions

## Workflow Details

### 1. Sale Submission

**What Happens**:
- Product ID and quantity validated
- Stock availability checked (from `inventory.csv`)
- Row atomically appended to `data/sales_log.csv`
- Timestamp recorded in ISO-8601 UTC format

**Atomic Append**:
- Uses file locking (`fcntl.flock` on Unix, `msvcrt.locking` on Windows)
- Prevents race conditions from concurrent submissions
- Calls `fsync()` to ensure durability

**Example Entry**:
```csv
2026-02-04T10:30:45.123Z,PROD-001,5
```

### 2. Pending Sales Preview

**Calculation**:
```
pending_sales = sales_log[last_processed_row:]
projected_stock = current_stock - sum(pending_sales for product)
```

**Shows**:
- Current stock from `inventory.csv`
- Pending sales quantity (not yet processed)
- Projected stock after agent runs

### 3. Agent Execution

**Triggered By**:
- Click "Run Agent (Demo)" button
- User confirmation required

**Process**:
1. Read `last_processed_row` from `data/last_run.json`
2. Load pending sales from `sales_log.csv`
3. For each sale:
   - Update stock in `inventory.csv`
   - Recalculate popularity EWMA
   - Update adaptive threshold
   - Check if restock needed
4. Append restock decisions to `restock_log.csv`
5. Update `last_run.json` with new processed row count

**Example Output**:
```
==============================================================
  AIMA Agent - Batch Processing
==============================================================
Last processed row: 0
Processing 3 pending sales...
  Processed: PROD-001 (Stock: 100 → 95)
  Processed: PROD-001 (Stock: 95 → 90)
  Processed: PROD-002 (Stock: 50 → 30)
    → RESTOCK: 45 units (confidence: 85%)
==============================================================
  Agent run complete!
  Sales processed: 3
  Restocks created: 1
==============================================================
```

## CSV File Structure

### sales_log.csv
```csv
timestamp,product_id,qty
2026-02-04T10:30:45.123Z,PROD-001,5
2026-02-04T10:31:02.456Z,PROD-002,10
```

**Fields**:
- `timestamp`: ISO-8601 UTC (e.g., `2026-02-04T10:30:45.123Z`)
- `product_id`: Product identifier
- `qty`: Quantity sold (positive integer)

### inventory.csv
```csv
product_id,name,stock,base_threshold,adaptive_threshold,popularity_ewma,popularity_index
PROD-001,Gaming Laptop,95,20,25.5,1.2,1.15
```

**Updated By**: Agent only (not cashier)

### restock_log.csv
```csv
timestamp,product_id,stock_after_sale,base_threshold,adaptive_threshold,predicted_demand_5d,popularity_index,restock_qty,reason,confidence
2026-02-04T10:35:00.789Z,PROD-002,30,15,18.0,25.5,0.95,45,Stock 30 below threshold 40,0.85
```

**Appended By**: Agent during restock decisions

### last_run.json
```json
{
  "timestamp": "2026-02-04T10:35:00.789Z",
  "status": "ok",
  "last_processed_row": 3,
  "sales_processed": 3,
  "restocks_created": 1
}
```

**Tracks**: Last agent execution and processed sales count

## API Endpoints

### POST `/api/cashier/submit-sale`
Submit a sale transaction.

**Request**:
```json
{
  "product_id": "PROD-001",
  "qty": 5
}
```

**Response**:
```json
{
  "success": true,
  "timestamp": "2026-02-04T10:30:45.123Z",
  "product_id": "PROD-001",
  "product_name": "Gaming Laptop",
  "qty": 5,
  "message": "Sale recorded: 5x Gaming Laptop"
}
```

### GET `/api/cashier/pending-preview`
Get pending sales preview.

**Response**:
```json
{
  "success": true,
  "pending_count": 3,
  "last_processed_row": 0,
  "total_sales_logged": 3,
  "preview": [
    {
      "product_id": "PROD-001",
      "name": "Gaming Laptop",
      "current_stock": 100,
      "pending_sales": 15,
      "projected_stock": 85,
      "threshold": 25.5
    }
  ]
}
```

### POST `/api/cashier/run-agent`
Execute the agent to process pending sales.

**Response**:
```json
{
  "success": true,
  "status": "ok",
  "output": "Agent output...",
  "last_run": {
    "timestamp": "2026-02-04T10:35:00.789Z",
    "status": "ok",
    "last_processed_row": 3,
    "sales_processed": 3,
    "restocks_created": 1
  }
}
```

### GET `/api/cashier/products`
Get product list for cashier dropdown.

**Response**:
```json
{
  "success": true,
  "products": [
    {
      "product_id": "PROD-001",
      "name": "Gaming Laptop",
      "stock": 100,
      "threshold": 25.5
    }
  ]
}
```

## Validation Rules

### Product ID
- Alphanumeric and hyphens only
- Automatically converted to uppercase
- Must exist in `inventory.csv`

### Quantity
- Positive integer (1-1000)
- Must not exceed available stock

### Timestamp
- ISO-8601 UTC format required
- Generated automatically by server

## Concurrency Safety

### Rapid Submissions
The atomic append mechanism handles rapid consecutive submissions:

**Test Results**:
- 10 concurrent threads
- 5 appends per thread (50 total)
- **No corruption detected**
- All 50 rows successfully written

**How It Works**:
1. Thread acquires exclusive file lock
2. Appends row to CSV
3. Calls `fsync()` for durability
4. Releases lock
5. Next thread proceeds

### File Locking
- **Unix/Linux/Mac**: `fcntl.flock()`
- **Windows**: `msvcrt.locking()`
- **Fallback**: Sequential writes (no locking)

## Error Handling

### Common Errors

**Product Not Found**:
```json
{
  "success": false,
  "error": "Product PROD-999 not found in inventory"
}
```

**Insufficient Stock**:
```json
{
  "success": false,
  "error": "Insufficient stock (available: 5, requested: 10)"
}
```

**Invalid Quantity**:
```json
{
  "success": false,
  "error": "Invalid quantity (must be 1-1000)"
}
```

**Agent Failure**:
```json
{
  "success": false,
  "error": "Agent execution timed out (>30s)"
}
```

## Troubleshooting

### Sales not appearing in pending
- Check `data/sales_log.csv` has new rows
- Verify timestamp format is correct
- Reload pending preview

### Agent not processing sales
- Check `data/last_run.json` has correct `last_processed_row`
- Verify no file permission issues
- Check agent output for errors

### Concurrent submissions failing
- Verify file locking is available (`fcntl` or `msvcrt`)
- Check file permissions on data directory
- Test with single submission first

### CSV corruption
- Should never happen with atomic append
- If occurs, check file locking is working
- Restore from backup

## Best Practices

1. **Always use the agent button** - Don't manually edit CSV files
2. **Review pending sales** before running agent
3. **Confirm agent execution** - It modifies inventory
4. **Monitor restock logs** - Review agent decisions
5. **Backup regularly** - Before each agent run

## Demo Scenario

**Setup**:
```bash
# Ensure data files exist
ls data/*.csv data/*.json

# Start web server
python web_server.py
```

**Steps**:
1. Open http://localhost:5000
2. Click "CASHIER" (top-right)
3. Select "PROD-001 - Gaming Laptop"
4. Enter quantity: 5
5. Click "Submit Sale"
6. See success message with timestamp
7. Check "Pending Sales" shows 1 pending
8. Click "Run Agent (Demo)"
9. Confirm execution
10. See agent output: "1 sale processed"
11. Pending sales now shows 0
12. Check main dashboard - stock updated

## Command Line Alternative

Run agent from command line:

```bash
python scripts/run_agent.py
```

Output:
```
==============================================================
  AIMA Agent - Batch Processing
==============================================================
Last processed row: 0
Processing 3 pending sales...
  Processed: PROD-001 (Stock: 100 → 95)
    → RESTOCK: 25 units (confidence: 80%)
==============================================================
  Agent run complete!
  Sales processed: 3
  Restocks created: 1
==============================================================
```

## Integration Notes

### External POS Systems
To integrate with external POS:

1. POST to `/api/cashier/submit-sale`
2. Check response for success
3. Handle errors appropriately
4. Schedule agent runs (cron/scheduler)

### Scheduled Agent Runs
```bash
# Crontab example: Run agent every 5 minutes
*/5 * * * * cd /path/to/AIMA && python scripts/run_agent.py
```

### Webhook Notifications
Add to `scripts/run_agent.py`:
```python
import requests

def notify_webhook(status, sales_processed):
    requests.post('https://your-webhook.com', json={
        'status': status,
        'sales_processed': sales_processed
    })
```

## Security Notes

### Input Validation
- All inputs sanitized before append
- CSV injection prevented
- Path traversal blocked

### File Permissions
- Data directory: 755
- CSV files: 644
- Scripts: 755 (executable)

### Production Deployment
- Use HTTPS for API endpoints
- Add authentication to cashier UI
- Rate limit API requests
- Enable audit logging

---

**Cashier Workflow Complete!** ✅
