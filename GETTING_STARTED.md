# 🚀 GETTING STARTED WITH AIMA WEB DASHBOARD

## Quick Setup (3 Steps)

### Step 1: Extract and Install
```bash
# Extract the ZIP file
unzip AIMA.zip
cd AIMA

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Create Demo Data
```bash
# Generate sample products and sales history
python app.py demo --products 20 --days 30
```

This will create:
- ✅ 20 sample products across different categories
- ✅ 30 days of simulated sales data
- ✅ Agent decisions and popularity metrics
- ✅ SQLite database at `data/aima.db`

### Step 3: Launch Web Dashboard
```bash
# Start the web server
python web_server.py
```

You'll see:
```
==============================================================
  AIMA Web Dashboard Starting...
==============================================================
  URL: http://localhost:5000
  Press Ctrl+C to stop
==============================================================
```

### Step 4: Open Your Browser

Visit: **http://localhost:5000**

## 🎨 What You'll See

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  AIMA                                                           │
│  Autonomous Inventory Management Agent                         │
│  ● SYSTEM ACTIVE    14:32:15    LAST UPDATE: 14:32:15         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  TOTAL   │  │  TOTAL   │  │ INVENTORY│  │   LOW    │      │
│  │ PRODUCTS │  │  STOCK   │  │   VALUE  │  │  STOCK   │      │
│  │          │  │          │  │          │  │          │      │
│  │    20    │  │   1,250  │  │ $15,000  │  │     3    │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INVENTORY STATUS              │  RESTOCK RECOMMENDATIONS      │
│  ────────────────              │  ───────────────────────      │
│                                │                                │
│  Product        Stock  Status  │  Gaming Laptop X1             │
│  ─────────────  ─────  ──────  │  ORDER: 45 units              │
│  Laptop X1        12   [LOW]   │  Confidence: ████████░ 85%    │
│  Smartphone      156   [OK]    │                                │
│  Coffee Beans      8   [CRIT]  │  Premium Coffee Beans         │
│                                │  ORDER: 32 units              │
│  PRODUCT POPULARITY            │  Confidence: ███████░░ 72%    │
│  ──────────────────            │                                │
│                                │  RECENT DECISIONS             │
│  Premium Laptop  ████████  8.2 │  ─────────────────            │
│  Coffee Beans    ██████    6.1 │                                │
│  Sneakers Pro    ████      4.3 │  14:30 - Gaming Laptop        │
│                                │  RESTOCK - Stock below...     │
│                                │  ████████░ 85% confidence     │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 What Each Section Shows

### 📊 Metrics Bar (Top)
- **Total Products**: 20 products in catalog
- **Total Stock**: 1,250 units available
- **Inventory Value**: $15,000 total value
- **Low Stock**: 3 items need attention

### 📦 Inventory Status (Left)
- Real-time stock levels
- Adaptive thresholds per product
- Status badges: OK / LOW / CRITICAL
- Sorted by urgency

### 📈 Product Popularity (Left)
- Visual bar charts
- Popularity index scores
- Top 10 trending products
- Sales velocity metrics

### ⚠️ Restock Recommendations (Right)
- AI-generated suggestions
- Recommended order quantities
- Confidence scores with visual bars
- Stock vs threshold comparison

### 🤖 Recent Decisions (Right)
- Last 8 agent decisions
- Decision type (RESTOCK/HOLD)
- Reasoning snippets
- Timestamp tracking

### 📊 Demand Analysis (Bottom)
- Average predicted demand
- Popularity trends
- Confidence metrics
- Performance tracking

## 🎨 Design Highlights

### Black & White Aesthetic
- Pure monochrome design
- No color distractions
- High contrast for clarity
- Professional appearance

### Typography
- **JetBrains Mono**: Clean monospace for data
- **Crimson Text**: Elegant serif for accents
- Multiple font sizes for hierarchy
- Uppercase headers for impact

### Animations
- Grain texture that subtly moves
- Staggered card reveals on load
- Smooth bar chart growth
- Hover lift effects with shadows
- 180° rotation on refresh button

### Visual Elements
- Sharp borders (2px)
- Clean geometric layouts
- Generous whitespace
- Bold status badges
- Animated confidence bars

## 🔄 Auto-Refresh

The dashboard updates automatically every **30 seconds**.

Manual refresh: Click the **↻** button (bottom-right)

## 📱 Responsive Design

Works perfectly on:
- 💻 Desktop (full layout)
- 💼 Laptop (optimized grid)
- 📱 Tablet (stacked columns)
- 📞 Mobile (single column)

## 🎮 Interactive Features

### Click on Products
Future feature: Click product rows to see detailed analytics

### Refresh Data
Click ↻ button or wait 30 seconds for auto-refresh

### Scroll Animations
Cards reveal as you scroll down the page

## 🛠️ Customization Options

### Change Refresh Rate
Edit `templates/dashboard.html` line ~550:
```javascript
setInterval(loadDashboard, 60000);  // 60 seconds instead of 30
```

### Adjust Colors
Edit CSS variables in `templates/dashboard.html`:
```css
:root {
    --black: #000000;
    --white: #FFFFFF;
    --spacing: 8px;
    --border-weight: 2px;
}
```

### Show More Products
Edit `templates/dashboard.html` renderInventoryTable:
```javascript
tbody.innerHTML = sorted.slice(0, 25).map(...)  // Show 25 instead of 15
```

## 🔧 Troubleshooting

### Port 5000 Already in Use
```bash
# Use a different port
python -c "from web_server import app; app.run(port=5001)"
```

### No Data Showing
```bash
# Run demo setup first
python app.py demo --products 20 --days 30
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Database Errors
```bash
# Delete and recreate
rm data/aima.db
python app.py demo
```

## 📊 Sample Data Overview

After running `python app.py demo --products 20 --days 30`:

- **20 products** across 8 categories
- **30 days** of sales history
- **~500-1000** sales transactions
- **~100+** agent decisions logged
- **Popularity metrics** for each product
- **Demand predictions** calculated

## 🚀 Next Steps

1. **Explore the dashboard** - Click around, watch updates
2. **Simulate sales** - Run `python app.py simulate`
3. **View decisions** - Check the Recent Decisions panel
4. **Analyze trends** - Watch popularity bars
5. **Customize** - Edit colors, fonts, layouts
6. **Deploy** - Use Gunicorn for production

## 💡 Pro Tips

### Real-Time Monitoring
Keep the dashboard open while running simulations:

**Terminal 1:**
```bash
python web_server.py
```

**Terminal 2:**
```bash
python app.py simulate
```

Watch the dashboard update in real-time!

### Multiple Views
Open multiple browser tabs to compare different time periods or products.

### Mobile Access
Access from phone by using your computer's IP:
```
http://192.168.1.XXX:5000
```

## 🎯 What Makes This Special

Unlike typical inventory dashboards:
- ❌ No boring Excel spreadsheets
- ❌ No cluttered color schemes
- ❌ No confusing navigation
- ❌ No slow load times

AIMA dashboard features:
- ✅ **Instant understanding** - See status at a glance
- ✅ **Beautiful design** - Memorable black & white aesthetic
- ✅ **Real-time updates** - Always current data
- ✅ **AI transparency** - See why decisions were made
- ✅ **Professional feel** - Premium animations and layout

## 📚 Documentation

- `Readme.md` - Main project documentation
- `WEB_DASHBOARD.md` - Detailed web dashboard guide
- `ARCHITECTURE.md` - System architecture
- `PROJECT_SUMMARY.md` - Complete feature list

## 🎉 You're Ready!

Everything is set up and ready to go. Just run:

```bash
python web_server.py
```

And visit **http://localhost:5000** to see your autonomous inventory management system in action!

---

**Enjoy your beautiful AIMA dashboard!** 🎨📊✨
