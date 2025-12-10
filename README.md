# SOC Market Scanner App

## Overview
Commercial-grade application for analyzing Self-Organized Criticality (SOC) in financial markets.
Scans Crypto and Stocks to identify phase transitions, volatility clusters, and crash risks.

## Structure
- `app.py`: Frontend Web Application (Streamlit)
- `logic.py`: Core Analysis Engine (Data Fetching, Metrics, Logic)

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run app: `streamlit run app.py`

## API Usage

### Get Current Market State (Real-time Query)

Query the current investment status without running a full backtest:

```python
from logic import get_current_market_state
import yfinance as yf

# Fetch recent data
df = yf.download("AAPL", period="2y")

# Get current state (defensive strategy)
state = get_current_market_state(df, strategy_mode="defensive")

# Check if we should be invested
if state['is_invested']:
    print(f"✅ Invested at {state['exposure_pct']:.0f}%")
    print(f"Regime: {state['regime']}")
else:
    print(f"❌ Cash (RISK_OFF)")

print(f"Criticality Score: {state['criticality_score']:.1f}/100")
print(f"Trend: {state['trend_signal']}")
```

**Returns:**
- `is_invested` (bool): Should we be in the market or cash?
- `criticality_score` (float): Current SOC score (0-100)
- `regime` (str): 'RISK_OFF (Cash)' or 'RISK_ON (Full/Partial/Minimal)'
- `trend_signal` (str): 'BULL' (above SMA200) or 'BEAR' (below SMA200)
- `exposure_pct` (float): Percentage to invest (0-100)
- `raw_data` (dict): Underlying metrics for debugging

**Test Script:**
```bash
python test_current_state.py
```

