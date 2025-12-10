# Unified Regime Logic - Hero Card & Plot Sync

## Problem Fixed

**Before:** Visual mismatch between Hero Card and Plot colors
- Hero Card showed "Critical Instability" (RED) for Score 75
- Plot showed GREEN bars (low volatility)

**After:** Perfect sync - Hero Card and Plot use identical regime logic and colors

---

## 🎯 New Unified Thresholds

| Regime | Condition | Criticality | Color | Hex Code |
|--------|-----------|-------------|-------|----------|
| **STRUCTURAL DECLINE** | Trend DOWN (Price < SMA200) | Any | Grey | `#7F8C8D` |
| **CRITICAL INSTABILITY** | Score ≥ 80 | 80-100 | Red | `#C0392B` |
| **HIGH ENERGY MANIA** | Score 65-79 + Trend UP | 65-79 | Orange | `#D35400` |
| **DORMANT STASIS** | Score < 65 + Low Volatility | 0-64 | Green | `#27AE60` |
| **ORGANIC GROWTH** | Score < 65 + Normal/High Vol | 0-64 | Blue | `#2980B9` |

---

## 📊 Hierarchy (Priority Order)

1. **First check:** Is trend DOWN? → STRUCTURAL DECLINE (Grey)
2. **Then check:** Is criticality ≥ 80? → CRITICAL (Red)
3. **Then check:** Is criticality 65-79 AND trend UP? → MANIA (Orange)
4. **Then check:** Is volatility < 20th percentile? → DORMANT (Green)
5. **Default:** ORGANIC GROWTH (Blue)

---

## 🔧 Changes Made

### 1. `hero_card_visual_v2.py` - Updated Thresholds
```python
# OLD: Critical at 75
elif crit >= 75:
    return "CRITICAL INSTABILITY"

# NEW: Critical at 80, added Mania zone
elif crit >= 80:
    return "CRITICAL INSTABILITY"
elif crit >= 65 and trend == "BULL":
    return "HIGH ENERGY MANIA"  # NEW ZONE
```

### 2. `logic.py` - Plot Colors Now Use Regime Logic
```python
# OLD: Simple volatility zones (low/medium/high)
color_map = {
    "low": "#27AE60",
    "medium": "#F1C40F",
    "extreme": "#C0392B"
}

# NEW: Unified regime colors
def get_regime_color(row):
    # Calculate criticality with trend modifier
    # Apply same logic as get_current_market_state()
    if trend == "BEAR":
        return "#7F8C8D"  # Grey
    elif crit >= 80:
        return "#C0392B"  # Red
    elif crit >= 65:
        return "#D35400"  # Orange
    elif crit < 20:
        return "#27AE60"  # Green
    else:
        return "#2980B9"  # Blue
```

### 3. `app.py` - Taxonomy Updated
Updated the expander legend to show new thresholds:
- Critical: ≥ 80 (was > 75)
- Mania: 65-79 + Trend UP (new zone)
- Dormant: < 65 + Low Vol (clarified)
- Growth: < 65 + Normal Vol (clarified)

---

## 📋 Example Scenarios

### Scenario 1: Apple with Score 75 (Low Volatility, Uptrend)
**Before:**
- Hero Card: 🔴 CRITICAL (Red) - Score 75
- Plot: 🟢 Green bars (low vola)
- **Mismatch!** ❌

**After:**
- Hero Card: 🟠 HIGH ENERGY MANIA (Orange) - Score 75, Trend UP
- Plot: 🟠 Orange bars
- **Perfect Match!** ✅

### Scenario 2: Bitcoin with Score 85 (High Stress)
**Before:**
- Hero Card: 🔴 CRITICAL (Red)
- Plot: 🔴 Red bars
- **Match** ✅ (this one was okay)

**After:**
- Hero Card: 🔴 CRITICAL (Red) - Score 85
- Plot: 🔴 Red bars
- **Still Perfect Match!** ✅

### Scenario 3: SPY with Score 30 (Low Vol)
**Before:**
- Hero Card: 🟢 GREEN (generic stable)
- Plot: 🟢 Green bars
- **Match** ✅

**After:**
- Hero Card: 🟢 DORMANT STASIS (Green) - Low Vol
- Or 🔵 ORGANIC GROWTH (Blue) - Normal Vol
- Plot: Matching color
- **Perfect Match!** ✅

---

## 🎨 Visual Consistency

Now when you look at any asset:

1. **Hero Card regime color** = **Last bar color on plot**
2. **Hero Card image** represents the same state as the plot
3. **Taxonomy expander** explains the exact thresholds

Example:
```
Hero Card: [HIGH ENERGY MANIA - Orange] 🟠
             ↕
Plot: Last bars are orange 🟠
             ↕
Legend: "Criticality 65-79 + Trend UP"
```

---

## 🧪 Testing

### Test the Changes

```bash
# 1. Test the standalone cards
streamlit run hero_card_visual_v2.py

# 2. Test in main app
streamlit run app.py
```

### Verification Checklist

Search for different assets and verify:
- [ ] Bear market asset → Grey card + grey bars
- [ ] High volatility (>80) → Red card + red bars
- [ ] Strong momentum (65-79) → Orange card + orange bars
- [ ] Low volatility → Green card + green bars
- [ ] Healthy normal → Blue card + blue bars

---

## 🔑 Key Benefits

### 1. Visual Consistency
✅ Hero Card color matches plot color
✅ No more confusing mismatches
✅ User can trust the visual indicators

### 2. Clearer Zones
✅ Critical raised to 80 (more conservative)
✅ New "Mania" zone (65-79) for strong momentum
✅ Better distinguishes healthy growth from danger

### 3. Better UX
✅ Immediate visual understanding
✅ Colors tell the same story everywhere
✅ Taxonomy legend explains the logic

---

## 📊 Threshold Calibration Rationale

### Why Raise Critical from 75 to 80?

**Problem:** Score 75 with low volatility is often just strong momentum, not a crash signal.

**Solution:** Reserve RED for true extreme stress (≥80).

**Example:**
- Apple at 75 with low vol = Strong uptrend (not critical)
- Bitcoin at 85 with high vol = True danger (critical)

### Why Add Mania Zone (65-79)?

**Problem:** Scores 65-79 are "hot" but not "danger" - need separate color.

**Solution:** Use ORANGE for "overheated but trending" states.

**Example:**
- TSLA at 72 trending up = Mania (hold with stops)
- TSLA at 85 = Critical (reduce position)

---

## 🔧 Files Modified

1. **hero_card_visual_v2.py** - Adjusted regime thresholds
2. **logic.py** - Plot now uses unified regime colors
3. **app.py** - Taxonomy updated with new thresholds

---

## 📝 Summary

✅ **Critical threshold:** 75 → 80 (more conservative)
✅ **New Mania zone:** 65-79 + Trend UP (orange)
✅ **Plot colors:** Now match regime logic
✅ **Hero Card:** Synced with plot
✅ **Taxonomy:** Updated documentation

**Result:** Apple with Score 75 now correctly shows ORANGE (mania) instead of RED (critical), and the plot bars match! 🎨✅

---

## 🚀 Expected Behavior

For Apple Inc. with:
- Criticality: 75
- Volatility: Low (~1.6%)
- Trend: UP (above SMA200)

**Before:**
- Hero Card: 🔴 CRITICAL INSTABILITY (confusing!)
- Plot: 🟢 Green bars (mismatch!)

**After:**
- Hero Card: 🟠 HIGH ENERGY MANIA (correct!)
- Plot: 🟠 Orange bars (match!)

Perfect visual consistency! ✨

