# Hero Card Layout Update - Vertical Stack

## ✅ Changes Applied

### 1. Width: Reduced to 50%
The card is now **centered and 50% width** on desktop, making it more focused and elegant.

### 2. Height: Increased to 550px
The iframe height was increased from 350px to 550px so all content is visible (no cut-off).

### 3. Layout: Vertical Stack
Changed from side-by-side to **vertical stacking**:

```
┌──────────────────────────────────────┐
│  Apple Inc.                     [88] │ ← Header (Asset + Badge)
│  AAPL                      Criticality│
├──────────────────────────────────────┤
│                                      │
│     [Visual Anchor Image]            │ ← Image (200px height)
│        (Zen Stones)                  │
│                                      │
├──────────────────────────────────────┤
│  [PROTECTIVE STASIS REGIME]          │ ← Regime Tag
│                                      │
│  $278.85  -2.15% 24h                 │ ← Price + Change
│                                      │
│  "Algorithm has decoupled from       │ ← Oracle Text
│   market volatility..."              │
└──────────────────────────────────────┘
        50% width, centered
```

---

## 🧪 Test Now

Run the updated version:
```bash
streamlit run hero_card_visual_v2.py
```

**You should see:**
- ✅ Card is **50% width** and **centered**
- ✅ Image appears **between header and content**
- ✅ **All content visible** (nothing cut off)
- ✅ Oracle text fully readable at bottom

---

## 📏 Dimensions

| Element | Size |
|---------|------|
| **Card Width** | 50% of screen (centered) |
| **Card Height** | Auto (content-based) |
| **Iframe Height** | 550px |
| **Image Height** | 200px |
| **Header** | ~80px |
| **Content** | ~270px |

---

## 📱 Responsive Breakpoints

| Screen Size | Card Width |
|------------|------------|
| **Large Desktop (>1200px)** | 50% |
| **Tablet (768-1200px)** | 70% |
| **Mobile (<768px)** | 95% |

---

## 🎨 Visual Hierarchy

The vertical layout creates a natural reading flow:

1. **Asset Identity** (Name + Ticker)
2. **Visual Anchor** (Image representing state)
3. **Status** (Regime + Criticality)
4. **Price Action** (Current + 24h change)
5. **Interpretation** (Oracle text)

---

## ✨ Advantages of 50% Width

### Before (Full Width)
```
┌────────────────────────────────────────────────────────────┐
│  Stretched across entire screen                            │
│  Too wide, hard to read                                    │
└────────────────────────────────────────────────────────────┘
```

### After (50% Width, Centered)
```
            ┌──────────────────────┐
            │  Focused, readable   │
            │  Professional look   │
            └──────────────────────┘
         More elegant and focused
```

**Benefits:**
- ✅ Better visual focus
- ✅ Easier to read (optimal line length)
- ✅ More elegant/premium feel
- ✅ Matches magazine/editorial design

---

## 🔧 Fine-Tuning Options

If you want to adjust further:

### Make it Wider/Narrower
```css
.card {
    max-width: 50%;  /* Current */
    max-width: 60%;  /* Wider */
    max-width: 40%;  /* Narrower */
}
```

### Adjust Image Height
```css
.visual {
    height: 200px;  /* Current */
    height: 250px;  /* Taller */
    height: 150px;  /* Shorter */
}
```

### Adjust Total Height
```python
components.html(html_content, height=550)  # Current
components.html(html_content, height=600)  # Taller
components.html(html_content, height=500)  # Shorter
```

---

## 📊 Layout Comparison

### Old (Horizontal Split)
```
┌────────────┬─────────────────┐
│            │  Asset Name     │
│   Image    │  Badge          │
│  (33%)     │  Regime         │
│            │  Price          │
│            │  Oracle         │
└────────────┴─────────────────┘
     100% width
```

### New (Vertical Stack, Centered)
```
        ┌──────────────────┐
        │  Asset + Badge   │
        ├──────────────────┤
        │                  │
        │     Image        │
        │                  │
        ├──────────────────┤
        │  Regime          │
        │  Price           │
        │  Oracle          │
        └──────────────────┘
           50% width
```

---

## ✅ Changes Summary

1. **Width:** Full screen → 50% centered
2. **Height:** 350px → 550px (all content visible)
3. **Layout:** Horizontal → Vertical stack
4. **Image Position:** Left side → Between header and content
5. **Responsive:** Added breakpoints for tablet/mobile

---

## 🎯 Result

You now have a **focused, elegant, vertically-stacked** Hero Card that:
- ✅ Shows image as a visual separator
- ✅ All content is visible (no cut-off)
- ✅ Centered at 50% width for better focus
- ✅ Responsive on all devices

**Test it:** `streamlit run hero_card_visual_v2.py`

The cards should now display perfectly! 🎨

