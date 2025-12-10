# TECTONIQ - Algorithmic Market Forensics

## Overview
Professional-grade platform for analyzing Self-Organized Criticality (SOC) in financial markets.
Physics-based approach to identifying market regime transitions, volatility clusters, and systemic stress.

---

## Features

### 🎴 Trading Card Hero Cards
- Art-framed regime visualizations with heritage filters
- Interactive hover info overlays
- 5 custom regime images (crash, critical, high energy, dormant, growth)
- Real-time regime classification synced with plot colors

### 📊 SOC Analysis
- 5-tier regime classification system
- Criticality scoring (0-100) with trend modifiers
- Real-time market state queries
- Historical regime performance analysis
- Crash detection and signal audit

### 🎯 Portfolio Simulation
- Buy & Hold vs Defensive vs Aggressive strategies
- Dynamic position sizing based on criticality
- Realistic friction costs (fees, interest)
- Drawdown protection analysis
- Historical stress testing

### 🔬 Scientific Design
- Academic journal-style masthead
- Scientific Heritage typography (Merriweather serif)
- Warm paper background aesthetic
- Thematic loaders with geological metaphors

---

## File Structure

```
TECTONIQ/
├── app.py                    # Main Streamlit application
├── logic.py                  # SOC analysis engine & data fetching
├── config.py                 # Configuration & constants
├── auth_manager.py           # Supabase authentication
├── analytics_engine.py       # Crash detection forensics
├── hero_card_visual_v2.py    # Trading card Hero Card component
├── ui_auth.py                # Authentication UI
├── ui_detail.py              # Asset deep dive UI
├── ui_simulation.py          # Portfolio simulation UI
├── market_status.py          # CLI tool for quick ticker checks
├── requirements.txt          # Python dependencies
├── news.txt                  # Platform updates
├── assets/                   # Regime images
│   ├── crash_regime.jpg
│   ├── critical_regime.jpg
│   ├── high_energy_regime.jpg
│   ├── dormant_regime.jpg
│   └── growth_regime.jpg
└── data/                     # CSV cache for historical prices
```

---

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Supabase (Required)
Create `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "your-project-url"
SUPABASE_KEY = "your-anon-key"
```

### 3. Run Application
```bash
streamlit run app.py
```

---

## Core Functions

### Real-Time Market State
```python
from logic import get_current_market_state
import yfinance as yf

# Fetch data
df = yf.download("AAPL", period="2y", auto_adjust=True)
df.columns = [c.lower() for c in df.columns]

# Get current state
state = get_current_market_state(df, strategy_mode="defensive")

# Check investment status
if state['is_invested']:
    print(f"✅ Invested at {state['exposure_pct']:.0f}%")
    print(f"Regime: {state['regime']}")
else:
    print(f"❌ Cash (RISK_OFF)")
```

### Centralized Regime Classification
```python
from logic import determine_market_regime

# Classify regime
regime = determine_market_regime(
    criticality=75,
    trend="UP",
    volatility_percentile=50
)

print(regime['name'])   # "HIGH ENERGY MANIA"
print(regime['color'])  # "#D35400"
print(regime['icon'])   # "🟠"
```

---

## Regime Classification System

| Regime | Condition | Color | Icon |
|--------|-----------|-------|------|
| **STRUCTURAL DECLINE** | Trend DOWN | Grey `#7F8C8D` | ⚫ |
| **CRITICAL INSTABILITY** | Criticality ≥ 80 | Red `#C0392B` | 🔴 |
| **HIGH ENERGY MANIA** | Criticality 65-79 or Vol >85% | Orange `#D35400` | 🟠 |
| **DORMANT STASIS** | Volatility <20% | Green `#27AE60` | 🟢 |
| **ORGANIC GROWTH** | Normal parameters | Blue `#2980B9` | 🔵 |

**Hierarchy:** Trend > Criticality > Volatility > Default

---

## CLI Tool

Quick market status checks:
```bash
python market_status.py AAPL
python market_status.py BTC-USD --strategy aggressive --verbose
```

---

## Key Technologies

- **Streamlit** - Web framework
- **pandas/numpy** - Data processing
- **yfinance** - Market data
- **Plotly** - Interactive charts
- **Supabase** - Authentication & user management

---

## Authentication

- Multi-user SaaS with Supabase backend
- Free and Premium tiers
- Portfolio management (unlimited assets)
- User-specific settings and preferences

---

## Beta Testing

Currently in beta. For access:
1. Create account (no credit card required)
2. Start with Free tier (unlimited portfolio, simulations)
3. Search any ticker to analyze

---

## License

© 2025 TECTONIQ. All rights reserved.

**Disclaimer:** This application is for educational and informational purposes only. Not financial advice. See in-app disclaimer for complete terms.

---

## Support

For issues or questions:
- Check in-app News & Updates
- Review inline help text
- Contact: support@tectoniq.app

---

**Version:** 1.1 (Scientific Heritage Polish)
**Status:** Beta - Production Ready
