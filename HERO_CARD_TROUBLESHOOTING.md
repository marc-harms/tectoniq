# Hero Card Visual - Troubleshooting Guide

## Issue: HTML Showing as Text Instead of Rendering

### Problem
When running `streamlit run hero_card_visual.py`, you see raw HTML code displayed as text instead of a beautiful rendered card.

### Root Cause
Streamlit's `unsafe_allow_html=True` is sensitive to:
1. HTML indentation/whitespace
2. Unclosed tags
3. Invalid CSS syntax

---

## ✅ Fix Applied

### Change 1: Remove Leading Whitespace
**Before:**
```python
card_html = f"""
        <style>  # ← Extra spaces cause issues
            ...
```

**After:**
```python
card_html = f"""<style>  # ← No leading spaces
...
```

### Change 2: Add Container Wrapper
```python
# Added st.container() wrapper
with st.container():
    st.markdown(card_html, unsafe_allow_html=True)
```

---

## 🧪 Test After Fix

Run the demo again:
```bash
streamlit run hero_card_visual.py
```

**Expected result:**
- ✅ You should see 4 beautiful cards with images
- ✅ No raw HTML text
- ✅ Proper colors and styling
- ✅ Images loaded from Unsplash

---

## 🔍 Still Not Working? Try These

### Debug Step 1: Check Streamlit Version
```bash
streamlit --version
```

**Required:** Streamlit >= 1.30.0  
**Update if needed:** `pip install --upgrade streamlit`

### Debug Step 2: Test Minimal HTML
Create `test_html.py`:
```python
import streamlit as st

st.markdown("""<div style="background: red; color: white; padding: 20px;">
Test HTML Rendering
</div>""", unsafe_allow_html=True)
```

Run: `streamlit run test_html.py`

**If this shows red box:** HTML works, issue is in hero_card_visual.py
**If this shows text:** Streamlit HTML rendering is disabled

### Debug Step 3: Check Browser Console
1. Open browser DevTools (F12)
2. Look for JavaScript errors
3. Check Network tab for image loading issues

### Debug Step 4: Simplify the Card
Try this minimal version:
```python
import streamlit as st

st.markdown("""<style>
.test-card {
    background: white;
    border: 1px solid black;
    padding: 20px;
}
</style>

<div class="test-card">
    <h1>Test</h1>
    <p>If you see this formatted, HTML works!</p>
</div>""", unsafe_allow_html=True)
```

---

## 🔧 Alternative Fix: Use st.components

If `st.markdown()` continues to have issues, use custom components:

```python
import streamlit.components.v1 as components

def render_hero_specimen(...):
    # ... build card_html ...
    
    # Instead of st.markdown
    components.html(card_html, height=350)
```

---

## 🎨 Fallback: Streamlit Native Components

If HTML continues to be problematic, here's a pure-Streamlit version (no HTML):

```python
import streamlit as st

def render_hero_native(ticker, asset_name, price, change, criticality, regime):
    """Pure Streamlit version - no HTML."""
    
    with st.container():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Use st.image for the visual anchor
            image_url = get_regime_image_url(criticality, regime)
            st.image(image_url, use_column_width=True)
        
        with col2:
            # Header
            st.markdown(f"### {asset_name}")
            st.caption(ticker)
            
            # Criticality badge
            st.metric("Criticality", f"{int(criticality)}/100")
            
            # Price
            col_price, col_change = st.columns([2, 1])
            with col_price:
                st.markdown(f"## ${price}")
            with col_change:
                delta_color = "normal" if change >= 0 else "inverse"
                st.metric("24h", f"{change:+.2f}%", delta=f"{change:+.2f}%")
            
            # Oracle text
            st.info(f'"{get_oracle_text(criticality, regime)}"')
```

---

## 🎯 Quick Diagnosis Checklist

Run through this checklist:

- [ ] Streamlit version >= 1.30.0?
- [ ] Running `streamlit run hero_card_visual.py` directly?
- [ ] Browser opened automatically?
- [ ] Checked browser console for errors?
- [ ] Tried refreshing browser (Ctrl+F5)?
- [ ] Tried different browser (Chrome vs Firefox)?

---

## 💡 Most Common Causes

### 1. Indentation Issue (FIXED)
✅ Already fixed by removing leading whitespace

### 2. Unclosed Tags
Check that all HTML tags are properly closed:
```html
<div>  ← Opens
</div> ← Closes
```

### 3. CSS Syntax Error
One missing semicolon can break everything:
```css
color: red;  ← Need semicolon
```

### 4. f-string Variable Error
If a variable is undefined, the whole f-string fails:
```python
f"{undefined_var}"  # ← Causes error
```

---

## 🚀 Expected Working Output

After the fix, you should see:

```
Test 1: PROTECTIVE STASIS (Not Invested)
┌──────────────────────────────────────────────┐
│ [Image: Zen Stones] │  Apple Inc.       [88] │
│                     │  AAPL                  │
│ (Grey/Beige Image)  │                        │
│                     │  [PROTECTIVE STASIS]   │
│                     │  $278.85  -2.15% 24h   │
│                     │  "Algorithm has..."    │
└──────────────────────────────────────────────┘

Test 2: CRITICAL INSTABILITY (20% Invested)
┌──────────────────────────────────────────────┐
│ [Image: Red Chaos]  │  Bitcoin USD      [85] │
│                     │  BTC-USD               │
│ (Red Network)       │                        │
│                     │  [CRITICAL]            │
│                     │  $43,520  -5.42% 24h   │
│                     │  "System stress..."    │
└──────────────────────────────────────────────┘

... (and 2 more cards)
```

---

## 📝 Test Commands

```bash
# 1. Test the visual hero card demo
streamlit run hero_card_visual.py

# 2. If you see HTML text, restart:
# Stop with Ctrl+C
# Run again:
streamlit run hero_card_visual.py

# 3. If still broken, try clearing cache:
rm -rf ~/.streamlit/cache
streamlit run hero_card_visual.py
```

---

## 🆘 Emergency Fallback

If it still doesn't work, use this simplified version:

```python
import streamlit as st

def render_simple_visual_hero(ticker, name, price, change, crit, image_url):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(image_url, use_column_width=True)
    
    with col2:
        st.markdown(f"### {name}")
        st.caption(ticker)
        st.metric("Price", f"${price}", delta=f"{change:+.2f}%")
        st.metric("Criticality", f"{int(crit)}/100")
```

This uses pure Streamlit components (no custom HTML/CSS).

---

## Summary

✅ **Fixed:** Removed leading whitespace from HTML
✅ **Added:** Container wrapper for safer rendering
✅ **Ready:** Run `streamlit run hero_card_visual.py` again

**Expected:** Beautiful cards with images should now render properly!

If you still see HTML text after this fix, let me know and I'll create a pure-Streamlit version without any custom HTML/CSS.

