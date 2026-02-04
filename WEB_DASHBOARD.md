# AIMA Web Dashboard

## 🌐 Web-Based Black & White Dashboard

A stunning, minimalist web interface for monitoring and managing your inventory with AIMA.

## 🎨 Design Philosophy

The dashboard features a **distinctive black-and-white aesthetic** with:

- **Typography**: JetBrains Mono (monospace) + Crimson Text (serif) for contrast
- **Animated grain texture** that subtly shifts in the background
- **Bold geometric layouts** with sharp borders and clean lines
- **Smooth animations** that feel premium and responsive
- **High contrast** for maximum readability
- **No color distractions** - pure monochrome focus

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- Flask-CORS (API support)
- NumPy (calculations)

### 2. Setup Demo Data (First Time Only)

```bash
python app.py demo --products 20 --days 30
```

This creates sample products and sales history.

### 3. Start the Web Server

```bash
python web_server.py
```

The server will start at: **http://localhost:5000**

### 4. Open Your Browser

Navigate to: **http://localhost:5000**

You should see the beautiful black-and-white dashboard!

## 📊 Dashboard Features

### Real-Time Metrics Bar
- **Total Products** - Number of products in catalog
- **Total Stock** - All units available
- **Inventory Value** - Total dollar value
- **Low Stock Alerts** - Critical items count

### Inventory Status Table
- Current stock levels for all products
- Adaptive thresholds (dynamically calculated)
- Status badges (OK / LOW / CRITICAL)
- Sorted by urgency (lowest stock first)

### Product Popularity Rankings
- Visual bars showing popularity index
- Top 10 most popular products
- Animated bar charts that grow on load
- Real-time velocity metrics

### Restock Recommendations
- AI-generated restock suggestions
- Order quantities calculated automatically
- Confidence scores for each recommendation
- Reasoning for transparency

### Recent Decisions Log
- Last 8 agent decisions
- Decision type (RESTOCK / HOLD)
- Confidence visualization
- Timestamps for tracking

### Demand Analysis
- Predicted demand metrics
- Average popularity index
- Confidence trends
- Predicted vs actual comparison

## 🎯 API Endpoints

The dashboard communicates with these endpoints:

### GET `/api/dashboard`
Returns complete dashboard data including products, decisions, orders, and metrics.

**Response:**
```json
{
  "success": true,
  "products": [...],
  "decisions": [...],
  "orders": [...],
  "metrics": {
    "total_products": 20,
    "total_stock": 1250,
    "total_value": 15000.00,
    "low_stock_count": 3,
    "out_of_stock": 0
  }
}
```

### GET `/api/product/<product_id>`
Get detailed information about a specific product.

### POST `/api/analyze/<product_id>`
Trigger agent analysis for a product.

### POST `/api/analyze-all`
Analyze all products at once.

### POST `/api/sale`
Record a sale transaction.

**Request:**
```json
{
  "product_id": "PROD-001",
  "quantity": 5
}
```

### GET `/api/decisions?limit=20`
Get recent agent decisions.

## 🎨 Design Elements

### Color Palette
```css
--black: #000000      /* Primary text, borders */
--white: #FFFFFF      /* Background */
--gray-100: #F5F5F5   /* Hover states */
--gray-200: #E5E5E5   /* Borders, bars */
--gray-700: #404040   /* Secondary text */
--gray-900: #171717   /* Dark badges */
```

### Typography
- **Headers**: JetBrains Mono (monospace, bold, uppercase)
- **Body**: JetBrains Mono (monospace, clean)
- **Accents**: Crimson Text (serif, italic for subtlety)

### Animations
- **Grain texture**: Continuously shifting background noise
- **Fade-ins**: Staggered card reveals on page load
- **Hover effects**: Subtle lift with sharp shadow
- **Bar charts**: Smooth growth animations
- **Refresh button**: 180° rotation on click

### Layout Grid
- **Responsive**: Adapts to mobile, tablet, desktop
- **Two-column**: Left (inventory), Right (decisions)
- **Metrics bar**: 4-column auto-fit grid
- **Cards**: Bordered with hover shadow effects

## 🔄 Auto-Refresh

The dashboard automatically refreshes every **30 seconds** to show the latest data.

You can also manually refresh by clicking the **↻** button in the bottom-right corner.

## 📱 Responsive Design

The dashboard works beautifully on:
- **Desktop** (1920px+) - Full grid layout
- **Laptop** (1024px+) - Optimized columns
- **Tablet** (768px+) - Stacked layout
- **Mobile** (320px+) - Single column, touch-friendly

## 🎯 Usage Examples

### Monitor Inventory in Real-Time

1. Open dashboard at http://localhost:5000
2. Watch metrics update automatically
3. Check "Low Stock" count for urgent items
4. Review popularity trends

### Track Agent Decisions

1. Scroll to "Recent Decisions" panel
2. See AI reasoning for each decision
3. Check confidence bars
4. Review restock recommendations

### Analyze Product Performance

1. Check "Product Popularity" section
2. Compare bar lengths visually
3. Identify trending products
4. Spot declining items

## 🛠️ Customization

### Change Refresh Interval

Edit `templates/dashboard.html`:

```javascript
// Change from 30 seconds to 60 seconds
setInterval(loadDashboard, 60000);
```

### Adjust Visual Style

Edit CSS variables in `templates/dashboard.html`:

```css
:root {
    --border-weight: 3px;  /* Thicker borders */
    --spacing: 10px;        /* More spacing */
}
```

### Modify Table Rows

Change how many products show:

```javascript
// In renderInventoryTable function
tbody.innerHTML = sorted.slice(0, 20).map(p => {  // Show 20 instead of 15
```

## 🚀 Production Deployment

### Using Gunicorn (Recommended)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_server:app
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_server:app"]
```

Build and run:

```bash
docker build -t aima-dashboard .
docker run -p 5000:5000 aima-dashboard
```

### Environment Variables

```bash
export FLASK_ENV=production
export DATABASE_PATH=/path/to/aima.db
python web_server.py
```

## 🔒 Security Notes

For production use:
- Enable HTTPS with SSL certificates
- Add authentication (Flask-Login)
- Use environment variables for secrets
- Enable CORS only for trusted domains
- Rate limit API endpoints

## 📊 Performance

The dashboard is optimized for:
- **Fast load times** - Minimal JavaScript, CSS-first animations
- **Smooth updates** - Efficient DOM manipulation
- **Low bandwidth** - Compressed responses, minimal assets
- **Responsive** - Runs well even on slower connections

## 🎓 Technical Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: Vanilla JavaScript (no frameworks needed!)
- **Styling**: Pure CSS with modern features
- **Data**: SQLite database
- **API**: RESTful JSON endpoints

## 🌟 Why This Design?

Unlike typical inventory dashboards that use:
- ❌ Generic Material Design
- ❌ Boring Excel-like tables
- ❌ Cluttered interfaces with too many colors
- ❌ Confusing navigation

AIMA's dashboard features:
- ✅ **Distinctive monochrome aesthetic**
- ✅ **Clean, focused data presentation**
- ✅ **Memorable visual identity**
- ✅ **Premium feel with smooth animations**
- ✅ **Instant understanding at a glance**

## 🎯 Next Steps

1. **Try it**: `python web_server.py`
2. **Customize**: Edit colors, fonts, layouts
3. **Extend**: Add new API endpoints
4. **Deploy**: Use Gunicorn or Docker
5. **Share**: Show off your autonomous inventory system!

---

**Enjoy your beautiful AIMA dashboard!** 🎨📊✨
