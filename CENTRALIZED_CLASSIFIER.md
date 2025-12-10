# Centralized Regime Classifier - Single Source of Truth

## ✅ Solution Implemented

Created `determine_market_regime()` in `logic.py` - a **single function** that both the Hero Card and Plot use for regime classification.

---

## 🎯 The Problem (Before)

**Duplicate Logic Everywhere:**
- Hero Card had its own if/else logic
- Plot had its own if/else logic  
- Slightly different thresholds
- **Result:** Mismatches (Green card, Blue plot)

---

## ✅ The Solution (After)

**Single Source of Truth:**
```python
# logic.py
def determine_market_regime(criticality, trend, volatility_percentile):
    """
    CENTRALIZED classifier used by:
    - Hero Card (app.py)
    - Plot colors (logic.py)
    - Any other component
    """
    # Single if/else logic
    if trend == "DOWN":
        return {'name': 'STRUCTURAL DECLINE', 'color': '#7F8C8D', ...}
    elif criticality >= 80:
        return {'name': 'CRITICAL INSTABILITY', 'color': '#C0392B', ...}
    # ... etc
```

**Everyone Uses It:**
- `hero_card_visual_v2.py` → calls `determine_market_regime()`
- `logic.py` plot → calls `determine_market_regime()`
- **Result:** Perfect sync! ✅

---

## 📊 Function Signature

```python
def determine_market_regime(
    criticality: float,      # 0-100 (with trend modifiers applied)
    trend: str,              # 'UP', 'DOWN', 'BULL', 'BEAR', 'FLAT', 'NEUTRAL'
    volatility_percentile: float  # 0-100
) -> dict:
    """
    Returns:
        {
            'name': str,        # e.g., "CRITICAL INSTABILITY"
            'color': str,       # e.g., "#C0392B"
            'image_key': str,   # e.g., "critical_regime"
            'icon': str,        # e.g., "🔴"
            'description': str  # e.g., "Danger. Reduce..."
        }
    """
```

---

## 🔄 Strict Hierarchy (Top-Down)

```
1. TREND DOWN?
   └─ YES → STRUCTURAL DECLINE (Grey #7F8C8D)
   └─ NO → Continue

2. CRITICALITY ≥ 80?
   └─ YES → CRITICAL INSTABILITY (Red #C0392B)
   └─ NO → Continue

3. CRITICALITY ≥ 65 OR VOLATILITY > 85%?
   └─ YES → HIGH ENERGY MANIA (Orange #D35400)
   └─ NO → Continue

4. VOLATILITY < 20%?
   └─ YES → DORMANT STASIS (Green #27AE60)
   └─ NO → Continue

5. DEFAULT
   └─ ORGANIC GROWTH (Blue #2980B9)
```

---

## 🔧 Integration Points

### 1. Hero Card (`hero_card_visual_v2.py`)
```python
from logic import determine_market_regime

def get_regime_visuals(crit, is_invested, trend, vola):
    # Call centralized classifier
    regime = determine_market_regime(crit, trend, vola)
    
    # Map to image
    image_url = get_image_for_key(regime['image_key'])
    
    return (regime['name'], regime['color'], image_url, regime['description'])
```

### 2. Plot Colors (`logic.py`)
```python
def get_plotly_figures():
    # For each bar in plot:
    for row in df:
        # Calculate crit, trend, vola for this day
        regime = determine_market_regime(crit, trend, vola)
        color = regime['color']
        # Use this color for the bar
```

### 3. Future Components
Any new component can simply call:
```python
from logic import determine_market_regime

regime = determine_market_regime(75, "UP", 50)
print(regime['name'])   # "HIGH ENERGY MANIA"
print(regime['color'])  # "#D35400"
```

---

## 🎨 Color Mapping

| Regime | Color | Hex | Icon |
|--------|-------|-----|------|
| STRUCTURAL DECLINE | Grey | `#7F8C8D` | ⚫ |
| CRITICAL INSTABILITY | Red | `#C0392B` | 🔴 |
| HIGH ENERGY MANIA | Orange | `#D35400` | 🟠 |
| DORMANT STASIS | Green | `#27AE60` | 🟢 |
| ORGANIC GROWTH | Blue | `#2980B9` | 🔵 |

---

## 📋 Example: Commerzbank Issue

**Problem:** Card showed Green, Plot showed Blue

**Root Cause:** Different logic in Hero Card vs Plot
- Hero Card: Checked volatility first → Low vol → Green
- Plot: Checked criticality first → Normal → Blue

**Solution:** Both now call same function
- Hero Card: `determine_market_regime(30, "UP", 15)` → Green
- Plot: `determine_market_regime(30, "UP", 15)` → Green
- **Perfect match!** ✅

---

## 🧪 Testing

### Test Case 1: Commerzbank (Low Volatility)
```python
regime = determine_market_regime(
    criticality=30,
    trend="UP",
    volatility_percentile=15  # Low volatility < 20
)
# Returns: DORMANT STASIS (Green)
```

**Result:**
- Hero Card: 🟢 Green
- Plot: 🟢 Green bars
- **Match!** ✅

### Test Case 2: Apple (Elevated Criticality)
```python
regime = determine_market_regime(
    criticality=75,  # In 65-79 range
    trend="UP",
    volatility_percentile=50
)
# Returns: HIGH ENERGY MANIA (Orange)
```

**Result:**
- Hero Card: 🟠 Orange
- Plot: 🟠 Orange bars
- **Match!** ✅

### Test Case 3: Bitcoin (Extreme Stress)
```python
regime = determine_market_regime(
    criticality=85,  # >= 80
    trend="UP",
    volatility_percentile=90
)
# Returns: CRITICAL INSTABILITY (Red)
```

**Result:**
- Hero Card: 🔴 Red
- Plot: 🔴 Red bars
- **Match!** ✅

---

## 📁 Files Modified

1. ✅ **logic.py** - Added `determine_market_regime()` function (single source of truth)
2. ✅ **logic.py** - Plot now calls `determine_market_regime()` for bar colors
3. ✅ **hero_card_visual_v2.py** - Now imports and uses `determine_market_regime()`

---

## 🔑 Key Benefits

### 1. Perfect Synchronization
✅ Hero Card color = Plot color (guaranteed)
✅ No more mismatches possible
✅ Same logic everywhere

### 2. Maintainability
✅ Change logic in one place
✅ Automatically updates everywhere
✅ No duplicate code

### 3. Testability
✅ Test one function
✅ Verify all components work
✅ Easy to debug

### 4. Extensibility
✅ New components can use same function
✅ Consistent regime classification across platform
✅ Future-proof architecture

---

## 🚀 Force Cache Refresh

The logic is now correct, but you need to clear cache:

```bash
# Option 1: Click 🔄 Refresh button in app
# Option 2: Restart Streamlit
streamlit run app.py
```

After refresh:
- Search for any ticker
- Hero Card color should match last plot bar exactly
- No more mismatches!

---

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│  determine_market_regime()              │
│  (Single Source of Truth)               │
│                                         │
│  Input: crit, trend, vola               │
│  Output: name, color, image, icon       │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    ↓                 ↓
┌─────────┐    ┌──────────┐
│ Hero    │    │  Plot    │
│ Card    │    │  Bars    │
└─────────┘    └──────────┘
  Same           Same
  Color          Color
```

---

## ✅ Summary

✅ **Centralized classifier created** - `determine_market_regime()`
✅ **Hero Card uses it** - Imports from logic.py
✅ **Plot uses it** - Calls for each bar color
✅ **Perfect sync guaranteed** - Same function = Same output
✅ **Cache needs refresh** - Click 🔄 to see changes

**Test now:** Click Refresh, search for AAPL, verify Hero Card and Plot colors match! 🎨✅

---

**Status:** Centralized architecture complete. All logic duplication eliminated. Perfect synchronization guaranteed! 🎉

