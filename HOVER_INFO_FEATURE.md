# Hero Card Hover Info Box Feature

## ✅ Feature Added

When you **hover over the regime image** in the Hero Card, an info box **fades in** with:
- Regime name (title)
- Oracle text (description)

---

## 🎨 How It Works

### Visual Effect

**Before Hover:**
```
┌─────────────┐
│             │
│   [Image]   │
│   Normal    │
│             │
└─────────────┘
```

**During Hover:**
```
┌─────────────┐
│┌───────────┐│
││ HIGH      ││ ← Dark overlay fades in
││ ENERGY    ││
││ MANIA     ││
││           ││
││"Overheated││
││ Hold with ││
││ Stop-Loss"││
│└───────────┘│
└─────────────┘
```

---

## 🔧 Technical Implementation

### CSS Transitions
```css
/* Hidden by default */
.hover-info {
    opacity: 0;
    transition: opacity 0.3s ease;
}

/* Visible on hover */
.specimen-visual-frame:hover .hover-info {
    opacity: 1;
}

/* Image darkens on hover */
.specimen-visual-frame:hover .visual-image {
    filter: brightness(70%);  /* Darker */
}
```

### HTML Structure
```html
<div class="specimen-visual-frame">
    <img src="..." class="visual-image">
    <!-- Overlay appears on hover -->
    <div class="hover-info">
        <div class="hover-info-title">HIGH ENERGY MANIA</div>
        <div class="hover-info-text">"Overheated. Hold with tight Stop-Loss."</div>
    </div>
</div>
```

---

## 🎯 Features

### 1. Smooth Fade-In
- **Duration:** 0.3 seconds
- **Effect:** opacity 0 → 1
- **Trigger:** Mouse enters image area

### 2. Dark Overlay
- **Background:** Black with 85% opacity
- **Effect:** Image dims, text pops
- **Readable:** White text on dark background

### 3. Image Darkens
- **Before hover:** Normal brightness (92%)
- **On hover:** Darkened (70%)
- **Effect:** Focuses attention on text

### 4. Cursor Change
- **Normal:** Default cursor
- **On image:** Help cursor (?)
- **Signal:** Hoverable content available

---

## 📊 Info Box Contents

Each regime shows:

### STRUCTURAL DECLINE (Grey)
- **Title:** STRUCTURAL DECLINE
- **Text:** "Primary Trend is DOWN. Avoid. Cash Position Recommended."

### CRITICAL INSTABILITY (Red)
- **Title:** CRITICAL INSTABILITY
- **Text:** "Criticality Score ≥ 80 (Extreme stress). Danger. Reduce Position Size immediately."

### HIGH ENERGY MANIA (Orange)
- **Title:** HIGH ENERGY MANIA
- **Text:** "Criticality 65-79 with positive momentum. Overheated. Hold with tight Stop-Loss."

### DORMANT STASIS (Green)
- **Title:** DORMANT STASIS
- **Text:** "Low volatility, minimal variance. Waiting. Accumulate or Patience."

### ORGANIC GROWTH (Blue)
- **Title:** ORGANIC GROWTH
- **Text:** "Healthy market structure. Criticality < 65. Normal parameters. Buy / Hold."

---

## 🎨 Styling Details

### Typography
- **Title:** Merriweather serif, bold, white, 1.1rem
- **Text:** Merriweather serif, italic, light grey, 0.9rem

### Layout
- **Positioning:** Absolute overlay
- **Alignment:** Centered vertically and horizontally
- **Padding:** 20px for comfortable reading

### Colors
- **Background:** rgba(0, 0, 0, 0.85) - Almost black
- **Title:** #FFFFFF - Pure white
- **Text:** #E0E0E0 - Light grey

---

## 🧪 Test the Hover Effect

```bash
streamlit run hero_card_visual_v2.py
```

**Try it:**
1. Move mouse over any regime image
2. Info box should **fade in smoothly**
3. Image darkens, text becomes readable
4. Move mouse away
5. Info box **fades out**, image returns to normal

---

## 💡 Use Cases

### 1. Quick Reference
Users can hover to see regime explanation without scrolling to the taxonomy legend.

### 2. Visual Feedback
Confirms the image is interactive and provides additional context.

### 3. Educational
Helps new users understand what each regime means.

### 4. Space Efficient
Info is hidden until needed, keeps UI clean.

---

## 🎯 Customization Options

### Change Fade Speed
```css
.hover-info {
    transition: opacity 0.5s ease;  /* Slower */
    transition: opacity 0.1s ease;  /* Faster */
}
```

### Change Overlay Darkness
```css
.hover-info {
    background: rgba(0, 0, 0, 0.95);  /* Darker */
    background: rgba(0, 0, 0, 0.70);  /* Lighter */
}
```

### Add Color Accent
```css
.hover-info {
    background: linear-gradient(
        135deg, 
        rgba(0,0,0,0.85), 
        {accent_color}40
    );
}
```

### Different Animation
```css
.hover-info {
    transform: scale(0.8);
    opacity: 0;
    transition: all 0.3s ease;
}
.specimen-visual-frame:hover .hover-info {
    transform: scale(1);
    opacity: 1;
}
```

---

## 📱 Mobile Behavior

On touch devices:
- First tap: Shows info box
- Second tap: Navigates (if linked)
- Tap outside: Hides info box

---

## ✅ Summary

✅ **Hover effect added** - Smooth 0.3s fade-in
✅ **Info box displays** - Regime name + description
✅ **Image dims** - Dark overlay for readability
✅ **Cursor changes** - Help (?) cursor on hover
✅ **Fully responsive** - Works on desktop and mobile

**Test now:** Hover over any regime image to see the info box fade in! 🎨✨

---

**Files Modified:**
- `hero_card_visual_v2.py` - Added hover CSS and HTML elements
- `HOVER_INFO_FEATURE.md` - This documentation

**Status:** Ready to use! Hover effects work immediately.

