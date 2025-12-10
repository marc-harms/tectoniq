"""
TECTONIQ - Visual Hero Card with Image Anchors (Simplified Version)
====================================================================

Clean, working version with simplified CSS.
Uses centralized determine_market_regime() for perfect sync.
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path
from functools import lru_cache
from logic import determine_market_regime


@lru_cache(maxsize=8)
def image_to_data_uri(path: str) -> str:
    """
    Convert a local image to a base64 data URI for reliable rendering inside components.html.
    Supports jpg/jpeg/png. Returns None if file missing.
    """
    p = Path(path)
    if not p.exists():
        return None
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def get_regime_visuals(criticality: float, is_invested: bool, trend: str, volatility_percentile: float = 50):
    """
    Map market state to visual theme using CENTRALIZED determine_market_regime().
    This ensures Hero Card uses the EXACT SAME logic as the Plot.
    
    Returns: (name, color, image_url, description)
    """
    # Use centralized classifier (Single Source of Truth)
    regime = determine_market_regime(criticality, trend, volatility_percentile)
    
    # Map image_key to actual image path (local first, then fallback to remote)
    image_map = {
        'crash_regime': image_to_data_uri("assets/crash_regime.jpg") or "https://images.unsplash.com/photo-1473773508845-188df298d2d1?q=60&w=400&auto=format&fit=crop",
        'critical_regime': image_to_data_uri("assets/critical_regime.jpg") or "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=500&auto=format&fit=crop",
        'high_energy_regime': image_to_data_uri("assets/high_energy_regime.jpg") or "https://images.unsplash.com/photo-1451931921771-1051d312d1c5?q=60&w=400&auto=format&fit=crop",
        'dormant_regime': image_to_data_uri("assets/dormant_regime.jpg") or "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?q=60&w=400&auto=format&fit=crop",
        'growth_regime': image_to_data_uri("assets/growth_regime.jpg") or "https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=60&w=400&auto=format&fit=crop",
    }
    
    image_url = image_map.get(regime['image_key'], "https://via.placeholder.com/500x300?text=Regime")
    
    # Return tuple format for compatibility
    return (
        regime['name'],
        regime['color'],
        image_url,
        regime['description']
    )


def render_hero_specimen(ticker, asset_name, current_price, price_change_24h, 
                         criticality, trend, is_invested=True, volatility_percentile=50):
    """Render Visual Hero Card using st.components for guaranteed rendering."""
    
    try:
        # Parse change and prepare display
        price_change_str = str(price_change_24h).strip()
        try:
            # Keep the sign when parsing
            pct_val = float(price_change_str.strip('%').replace('+', ''))
        except:
            pct_val = 0.0
        
        # Get visuals (with volatility percentile for accurate regime classification)
        regime_name, accent_color, image_url, oracle_text = get_regime_visuals(
            criticality, is_invested, trend, volatility_percentile
        )
        
        # Change colors and format display (ensure single sign)
        if pct_val >= 0:
            change_color = "#27AE60"
            change_bg = "#ECFDF5"
            # Format with single + sign
            if price_change_str.startswith('+'):
                change_display = price_change_str  # Already has +
            elif price_change_str.startswith('-'):
                change_display = price_change_str  # Keep as negative
            else:
                change_display = f"+{price_change_str}"  # Add +
        else:
            change_color = "#C0392B"
            change_bg = "#FEF2F2"
            # Format with single - sign
            if price_change_str.startswith('-'):
                change_display = price_change_str  # Already has -
            else:
                change_display = f"-{price_change_str}"  # Add -
        
        # Create HTML with Trading Card Style: Grid layout with Art Frame
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
    body {{
        margin: 0;
        padding: 0;
        background: transparent;
    }}
    .card {{
        background: #F9F7F1;
        border: 1px solid #D1C4E9;
        border-radius: 12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
        max-width: 50%;
        margin: 0 auto;
        padding: 18px;
        display: grid;
        grid-template-columns: 1fr 2fr;
        gap: 20px;
    }}
    
    /* LEFT: Art Frame Section (Trading Card Style) */
    .art-section {{
        display: flex;
        flex-direction: column;
    }}
    .specimen-visual-frame {{
        border: 4px solid #7F8C8D;
        border-radius: 4px;
        padding: 8px;
        background: #EAECEE;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.3), inset 0 -2px 6px rgba(255,255,255,0.2);
        position: relative;
        cursor: help;
    }}
    .visual-image {{
        width: 100%;
        height: 320px;
        object-fit: cover;
        display: block;
        filter: sepia(45%) grayscale(25%) contrast(115%) brightness(92%);
        border-radius: 2px;
        transition: filter 0.3s ease;
    }}
    /* Hover overlay info box */
    .hover-info {{
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.85);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
        padding: 20px;
        border-radius: 2px;
    }}
    .specimen-visual-frame:hover .hover-info {{
        opacity: 1;
    }}
    .specimen-visual-frame:hover .visual-image {{
        filter: sepia(45%) grayscale(25%) contrast(115%) brightness(70%);
    }}
    .hover-info-title {{
        font-family: 'Merriweather', serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: white;
        margin-bottom: 10px;
        text-align: center;
    }}
    .hover-info-text {{
        font-family: 'Merriweather', serif;
        font-size: 0.9rem;
        color: #E0E0E0;
        text-align: center;
        line-height: 1.5;
        font-style: italic;
    }}
    
    /* RIGHT: Data Section */
    .data-section {{
        display: flex;
        flex-direction: column;
        padding: 4px;
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
    }}
    .title {{
        font-family: 'Merriweather', serif;
        font-size: 1.7rem;
        font-weight: 700;
        color: #2C3E50;
        margin: 0;
        line-height: 1.2;
    }}
    .symbol {{
        font-family: 'Roboto Mono', monospace;
        font-size: 0.85rem;
        color: #7F8C8D;
        margin-top: 4px;
        letter-spacing: 1px;
    }}
    .badge {{
        background: {accent_color};
        color: white;
        width: 52px;
        height: 52px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Roboto Mono', monospace;
        font-size: 1.3rem;
        font-weight: 700;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    }}
    .badge-label {{
        font-family: 'Roboto Mono', monospace;
        font-size: 0.6rem;
        color: #7F8C8D;
        margin-top: 4px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Type Line (MTG-inspired separator) */
    .type-line {{
        border-bottom: 2px solid #7F8C8D;
        padding-bottom: 8px;
        margin: 12px 0 14px 0;
    }}
    .regime-tag {{
        font-family: 'Merriweather', serif;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #333333;
        display: inline-block;
        background: linear-gradient(135deg, {accent_color}30, {accent_color}20);
        padding: 8px 16px;
        border-radius: 4px;
        border: 2px solid {accent_color};
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    
    /* Price Section */
    .price-row {{
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 14px;
    }}
    .price {{
        font-family: 'Roboto Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        color: #2C3E50;
    }}
    .change {{
        font-family: 'Roboto Mono', monospace;
        background: {change_bg};
        color: {change_color};
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9rem;
    }}
    
    /* Oracle Text Box */
    .oracle {{
        border-left: 4px solid {accent_color};
        background: #FFFFFF;
        padding: 14px;
        font-family: 'Merriweather', serif;
        font-style: italic;
        color: #555555;
        font-size: 0.95rem;
        line-height: 1.5;
        border-radius: 0 4px 4px 0;
        margin-top: auto;
    }}
    
    /* Responsive */
    @media (max-width: 1200px) {{
        .card {{
            max-width: 70%;
        }}
    }}
    @media (max-width: 768px) {{
        .card {{
            max-width: 95%;
            grid-template-columns: 1fr;
            gap: 16px;
        }}
        .visual-image {{
            height: 240px;
        }}
    }}
</style>
</head>
<body>
<div class="card">
    <!-- LEFT: Art Frame Section (1/3 width) -->
    <div class="art-section">
        <div class="specimen-visual-frame">
            <img src="{image_url}" class="visual-image" alt="Regime Visualization">
            <!-- Hover info box (fades in on hover) -->
            <div class="hover-info">
                <div class="hover-info-title">{regime_name}</div>
                <div class="hover-info-text">{oracle_text}</div>
            </div>
        </div>
    </div>
    
    <!-- RIGHT: Data Section (2/3 width) -->
    <div class="data-section">
        <div class="header">
            <div>
                <div class="title">{asset_name}</div>
                <div class="symbol">{ticker}</div>
            </div>
            <div style="text-align: center;">
                <div class="badge">{int(criticality)}</div>
                <div class="badge-label">Criticality</div>
            </div>
        </div>
        
        <!-- Type Line (MTG-style separator) -->
        <div class="type-line">
            <span class="regime-tag">{regime_name}</span>
        </div>
        
        <div class="price-row">
            <span class="price">{current_price}</span>
            <span class="change">{change_display}</span>
        </div>
        
        <div class="oracle">
            "{oracle_text}"
        </div>
    </div>
</div>
</body>
</html>
"""
        
        # Use components.html for guaranteed rendering
        # Increased height for trading card layout
        components.html(html_content, height=400)
        
    except Exception as e:
        st.error(f"Render error: {e}")
        st.write(f"**{asset_name}** ({ticker}) - {current_price} {price_change_24h}")


# Demo - Testing All 5 Regimes
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    
    st.title("TECTONIQ Visual Hero Card - Test Suite")
    st.caption("Testing all 5 regime states with local images")
    st.markdown("---")
    
    # === Test 1: STRUCTURAL DECLINE (Crash/Bear Market) ===
    st.subheader("Test 1: STRUCTURAL DECLINE ⚫")
    st.caption("Condition: Primary Trend is DOWN | Protocol: Avoid. Cash Position Recommended.")
    render_hero_specimen(
        ticker="AAPL",
        asset_name="Apple Inc.",
        current_price="$278.85",
        price_change_24h="-2.15%",
        criticality=50,  # Moderate criticality
        trend="BEAR",  # Down trend triggers STRUCTURAL DECLINE
        is_invested=False,
        volatility_percentile=50
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # === Test 2: CRITICAL INSTABILITY (High Stress >= 80) ===
    st.subheader("Test 2: CRITICAL INSTABILITY 🔴")
    st.caption("Condition: Criticality Score ≥ 80 (Extreme stress) | Protocol: Danger. Reduce Position Size immediately.")
    render_hero_specimen(
        ticker="BTC-USD",
        asset_name="Bitcoin USD",
        current_price="$43,520",
        price_change_24h="-5.42%",
        criticality=85,  # High criticality >= 80
        trend="BULL",
        is_invested=True,
        volatility_percentile=85
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # === Test 3: HIGH ENERGY MANIA (Momentum Zone 65-79) ===
    st.subheader("Test 3: HIGH ENERGY MANIA 🟠")
    st.caption("Condition: Criticality 65-79 + Trend UP (Momentum zone) | Protocol: Overheated. Hold with tight Stop-Loss.")
    render_hero_specimen(
        ticker="AAPL",
        asset_name="Apple Inc.",
        current_price="$278.85",
        price_change_24h="+2.50%",
        criticality=75,  # In mania zone (65-79)
        trend="BULL",  # Up trend required
        is_invested=True,
        volatility_percentile=60  # Normal volatility
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # === Test 4: DORMANT STASIS (Low Variance) ===
    st.subheader("Test 4: DORMANT STASIS 🟢")
    st.caption("Condition: Volatility < 20th Percentile | Protocol: Waiting. Accumulate or Patience.")
    render_hero_specimen(
        ticker="SPY",
        asset_name="SPDR S&P 500 ETF",
        current_price="$485.20",
        price_change_24h="+0.15%",
        criticality=25,  # Low criticality
        trend="BULL",
        is_invested=True,
        volatility_percentile=12  # Low volatility < 20th percentile
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # === Test 5: ORGANIC GROWTH (Healthy Normal) ===
    st.subheader("Test 5: ORGANIC GROWTH 🔵")
    st.caption("Condition: Trend UP + Normal Parameters | Protocol: Healthy. Buy / Hold.")
    render_hero_specimen(
        ticker="MSFT",
        asset_name="Microsoft Corp.",
        current_price="$425.15",
        price_change_24h="+1.24%",
        criticality=35,  # Normal criticality
        trend="BULL",  # Up trend
        is_invested=True,
        volatility_percentile=50  # Normal volatility
    )
    
    st.markdown("---")
    st.success("✅ All 5 regimes tested with local images!")
    st.info("📁 Make sure all images exist in assets/ folder: crash_regime.jpg, critical_regime.jpg, high_energy_regime.jpg, dormant_regime.jpg, growth_regime.jpg")

