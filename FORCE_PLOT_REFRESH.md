# Force Plot Color Refresh

## Issue

You updated the plot color logic in `logic.py`, but the plot still shows old colors (blue instead of orange).

## Cause

The plot data is likely cached in:
1. Streamlit's cache (`@st.cache_data`)
2. Session state (`st.session_state['data']`)

---

## 🔧 Solution: Force Refresh

### Method 1: Use the Refresh Button (Easiest)

1. Click the **🔄 Refresh** button in the app (top-right)
2. Search for the ticker again
3. The plot should now show the new colors!

---

### Method 2: Clear Session State Manually

In the app, add this temporary code before the plot:

```python
# Force clear cache for testing (remove after verifying)
if st.button("🔄 Force Refresh Plot"):
    if 'data' in st.session_state:
        del st.session_state['data']
    if 'data_symbol' in st.session_state:
        del st.session_state['data_symbol']
    st.cache_data.clear()
    st.rerun()
```

---

### Method 3: Restart Streamlit

```bash
# Stop Streamlit (Ctrl+C)
# Clear cache
rm -rf ~/.streamlit/cache

# Delete CSV cache too (forces fresh data)
rm -f data/*_cached.csv

# Restart
streamlit run app.py
```

---

## 🧪 Verification Steps

After clearing cache:

1. **Search for AAPL**
2. **Look at Hero Card** - Should show: 🟠 HIGH ENERGY MANIA (Orange/Gold)
3. **Scroll to plot**
4. **Look at last bars** - Should be: 🟠 Orange/Gold
5. **Colors should match!** ✅

---

## 🐛 If Still Blue After Refresh

Check the criticality score value:

1. Look at Hero Card - what's the criticality number?
2. If it's < 65 → Blue is correct (Organic Growth)
3. If it's 65-79 → Should be Orange (Mania)
4. If it's ≥ 80 → Should be Red (Critical)

If the Hero Card shows 75 but plot is still blue, add debug output:

```python
# In get_regime_color function, add:
print(f"DEBUG: Date={row.name}, Crit={crit:.1f}, Trend={trend}, Color={result}")
```

---

## 📊 Expected Color Distribution

For Apple (if criticality is around 75):

**Recent History:**
```
Plot bars over time:
────🟢🟢🟢🔵🔵🔵🟠🟠🟠 ← Last bars should be ORANGE
        ↑         ↑         ↑
      Green     Blue    Orange (Score 65-79)
   (Low Vol) (Normal) (High Crit)
```

---

## 🎯 Key Point

The criticality calculation in the plot now:
1. Uses same rolling window as `get_current_market_state()`
2. Applies same trend modifiers
3. Uses same thresholds (80, 65)

**If Hero Card shows Orange, plot MUST show Orange!**

---

## 💡 Quick Test

Run this in Python to check the calculation:

```python
from logic import DataFetcher, SOCAnalyzer

# Fetch data
fetcher = DataFetcher(cache_enabled=True)
df = fetcher.fetch_data("AAPL")

# Analyze
analyzer = SOCAnalyzer(df, "AAPL")
phase = analyzer.get_market_phase()

print(f"Criticality: {phase['criticality_score']}")
print(f"Trend: {phase['trend']}")

# If criticality is 65-79 and trend is UP, plot should be orange
```

---

## Summary

1. ✅ Logic is correct in code
2. ⚠️ Cache needs to be cleared
3. 🔄 Click Refresh button in app
4. 🧪 Test with AAPL again

The plot colors should now sync with the Hero Card! 🎨

