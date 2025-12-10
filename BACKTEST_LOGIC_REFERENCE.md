# SOC Backtest Logic Reference
## Ensuring 1:1 Correspondence Between Simulation and Current State

This document explains how `get_current_market_state()` replicates the exact logic from `DynamicExposureSimulator` to ensure perfect consistency.

---

## Core Principle

**The current state function MUST return the same values that would appear in the last row of the backtest simulation.**

If the backtest shows:
- Exposure = 0% (flat line in cash) → `get_current_market_state()` returns `is_invested=False`
- Exposure = 50% → `get_current_market_state()` returns `exposure_pct=50.0`
- Exposure = 100% → `get_current_market_state()` returns `exposure_pct=100.0`

---

## Logic Flow Comparison

### DynamicExposureSimulator._prepare_data()
```python
# 1. Calculate SMA200
df['sma_200'] = df['close'].rolling(window=200).mean()

# 2. Calculate volatility
df['returns'] = df['close'].pct_change()
df['volatility'] = df['returns'].rolling(window=30).std()

# 3. Calculate criticality score (volatility percentile)
vol_window = min(504, len(df) - 1)  # ~2 years
df['criticality_score'] = df['volatility'].rolling(window=vol_window).apply(
    lambda x: (x.iloc[-1] <= x).sum() / len(x) * 100, raw=False
)

# 4. Apply trend modifier
df['trend_modifier'] = 0
df.loc[df['close'] < df['sma_200'], 'trend_modifier'] = 10  # Downtrend penalty
price_deviation = (df['close'] - df['sma_200']) / df['sma_200'] * 100
df.loc[price_deviation > 30, 'trend_modifier'] = 10  # Parabolic penalty

df['criticality_score'] = (df['criticality_score'] + df['trend_modifier']).clip(0, 100)

# 5. Determine trend
df['is_uptrend'] = df['close'] > df['sma_200']
```

### get_current_market_state()
```python
# IDENTICAL preparation logic applied to input dataframe
# Returns only the LATEST row (TODAY)
```

---

## Exposure Calculation Rules

### Defensive Strategy
| Condition | Exposure | Logic |
|-----------|----------|-------|
| **Bear Market** (Price < SMA200) | **0%** | Cash - exit completely |
| **Critical** (Criticality > 80) | **20%** | Minimal exposure |
| **High Energy** (Criticality > 60) | **50%** | Partial exposure |
| **Stable** (Criticality ≤ 60) | **100%** | Full exposure |

### Aggressive Strategy
| Condition | Exposure | Logic |
|-----------|----------|-------|
| **Bear Market** (Price < SMA200) | **0%** | Cash - exit completely |
| **Critical** (Criticality > 80) | **50%** | Reduced exposure |
| **High Energy** (Criticality > 60) | **100%** | Full exposure (ride momentum!) |
| **Stable** (Criticality ≤ 60) | **100%** | Full exposure |

**Both strategies** follow this hierarchy:
1. **First**: Check trend (above/below SMA200)
2. **Then**: Check criticality score thresholds
3. **Result**: Determine exposure percentage

---

## Code Correspondence

### DynamicExposureSimulator.run_simulation()
```python
# Line ~1519-1528 in logic.py
def calc_exposure(row):
    if not row['is_uptrend']:
        return bear_market_exposure  # 0%
    if row['criticality_score'] > 80:
        return high_stress_exposure  # Defensive=20%, Aggressive=50%
    elif row['criticality_score'] > 60:
        return medium_stress_exposure  # Defensive=50%, Aggressive=100%
    else:
        return 1.0  # 100% invested
```

### get_current_market_state()
```python
# Line ~2069-2078 in logic.py
# EXACT SAME LOGIC
if not is_uptrend:
    exposure = bear_market_exposure
elif criticality_score > high_stress_threshold:
    exposure = high_stress_exposure
elif criticality_score > medium_stress_threshold:
    exposure = medium_stress_exposure
else:
    exposure = 1.0
```

---

## Verification Process

To verify correctness, run:

```bash
python test_current_state.py
```

This script will:
1. Get current state using `get_current_market_state()`
2. Run full backtest using `run_dca_simulation()`
3. Compare the last day of backtest with current state
4. Report any mismatches

**Expected output:**
```
✅ MATCH: Current state matches backtest!
```

---

## Common Pitfalls (Avoided)

❌ **Wrong:** Using different window sizes (e.g., 30 vs 60 days)
✅ **Correct:** Both use 30-day volatility window

❌ **Wrong:** Using different thresholds (e.g., 70 vs 80)
✅ **Correct:** Both use high_stress=80, medium_stress=60

❌ **Wrong:** Different trend calculations
✅ **Correct:** Both use Price > SMA200 for uptrend

❌ **Wrong:** Forgetting trend modifier (+10 for downtrend/parabolic)
✅ **Correct:** Both apply identical trend modifier logic

---

## Usage Examples

### Example 1: Simple Query
```python
from logic import get_current_market_state
import yfinance as yf

df = yf.download("AAPL", period="2y")
state = get_current_market_state(df, strategy_mode="defensive")

print(f"Invested: {state['is_invested']}")
print(f"Exposure: {state['exposure_pct']:.0f}%")
```

### Example 2: With Error Handling
```python
state = get_current_market_state(df, strategy_mode="aggressive")

if 'error' in state:
    print(f"Error: {state['error']}")
else:
    if state['is_invested']:
        print(f"✅ {state['regime']}")
        print(f"Exposure: {state['exposure_pct']:.1f}%")
    else:
        print(f"❌ {state['regime']}")
```

### Example 3: Full Dashboard Display
```python
state = get_current_market_state(df, strategy_mode="defensive")

print(f"""
{'='*50}
CURRENT MARKET STATE
{'='*50}
Investment Status:  {state['regime']}
Exposure:           {state['exposure_pct']:.1f}%
Criticality Score:  {state['criticality_score']:.1f}/100
Trend:              {state['trend_signal']}
Current Price:      ${state['raw_data']['current_price']:,.2f}
SMA 200:            ${state['raw_data']['sma_200']:,.2f}
Price vs SMA:       {state['raw_data']['price_deviation_pct']:+.2f}%
{'='*50}
""")
```

---

## Maintenance Notes

**When updating the backtest logic**, you MUST update BOTH:

1. `DynamicExposureSimulator._prepare_data()` and `run_simulation()`
2. `get_current_market_state()`

**Testing after changes:**
```bash
# Run verification
python test_current_state.py

# Expected: All tests show "✅ MATCH"
```

---

## Summary

The `get_current_market_state()` function is a **stateless query** that applies the exact same rules as the full backtest but only for TODAY. This allows:

- ✅ Real-time portfolio decisions
- ✅ API endpoints for current status
- ✅ Dashboard displays without rerunning full history
- ✅ Guaranteed consistency with backtests

**Key guarantee:** If you run a backtest ending today, the last data point will match `get_current_market_state()` exactly.

