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

