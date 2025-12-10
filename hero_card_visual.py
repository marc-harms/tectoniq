"""
TECTONIQ - Visual Hero Card with Image Anchors
===============================================

Enhanced Hero Card component with visual regime anchors (images).
Integrates with get_current_market_state() for accurate display.

Author: TECTONIQ Team
Version: 1.0 (Beta)
"""

import streamlit as st


def get_regime_visuals(criticality: float, is_invested: bool, trend: str, volatility_percentile: float = 50):
    """
    Map market state to visual theme (regime name, color, image, narrative).
    
    Integrates with TECTONIQ's get_current_market_state() output.
    
    Args:
        criticality: Criticality score (0-100) from get_current_market_state()
        is_invested: Investment status (True/False) from get_current_market_state()
        trend: 'BULL' or 'BEAR' from get_current_market_state()
        volatility_percentile: Optional percentile (0-100)
    
    Returns:
        Tuple: (regime_name, hex_color, image_url, oracle_text)
    
    Visual Anchors (Unsplash Images):
        - PROTECTIVE STASIS: Zen stones (stillness, preservation)
        - CRITICAL: Abstract chaos/network (instability)
        - HIGH ENERGY: Supernova/explosion (intense activity)
        - STABLE GROWTH: Geometric patterns (organic structure)
        - STRUCTURAL DECLINE: Stormy sea (turbulence)
    """
    crit = int(criticality)
    vola_p = int(volatility_percentile)
    
    # === STATE 1: PROTECTIVE STASIS (Not Invested - Cash/Safety) ===
    if not is_invested:
        return (
            "PROTECTIVE STASIS",
            "#95A5A6",  # Fossil Grey (Dormant theme)
            "https://images.unsplash.com/photo-1480618757544-71636f183e2e?q=80&w=500&auto=format&fit=crop",  # Zen Stones
            "Algorithm has decoupled from market volatility. Capital is preserved in protective mode. "
            f"Criticality: {crit}/100. Awaiting favorable re-entry conditions."
        )
    
    # === STATE 2: CRITICAL INSTABILITY (High Risk - Minimal Exposure) ===
    if crit >= 80:
        return (
            "CRITICAL INSTABILITY",
            "#C0392B",  # Terracotta Red
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=500&auto=format&fit=crop",  # Abstract Network/Chaos
            f"System stress is extremely elevated ({crit}/100). Statistical indicators suggest heightened "
            "phase transition probability. Position sizing reduced to minimal exposure."
        )
    
    # === STATE 3: HIGH ENERGY (Moderate Risk - Partial Exposure) ===
    if crit >= 60:
        return (
            "HIGH ENERGY REGIME",
            "#D35400",  # Pumpkin Orange
            "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=500&auto=format&fit=crop",  # Supernova
            f"Volatility surging with elevated energy state ({crit}/100). Trend remains positive but "
            "structural fragility increasing. Position sizing adjusted to partial exposure for risk management."
        )
    
    # === STATE 4: STRUCTURAL DECLINE (Bear Market - Cash) ===
    # Note: This should be caught by is_invested=False, but keep as fallback
    if trend == "BEAR" or trend == "DOWN":
        return (
            "STRUCTURAL DECLINE",
            "#7F8C8D",  # Concrete Grey
            "https://images.unsplash.com/photo-1518558997970-4ddc236affcd?q=80&w=500&auto=format&fit=crop",  # Stormy Sea
            f"Negative momentum dominates. Price below long-term trend (SMA200). "
            f"Algorithm in protective mode. Criticality: {crit}/100."
        )
    
    # === STATE 5: STABLE GROWTH (Low Risk - Full Exposure) ===
    # Default state for invested + low criticality
    return (
        "STABLE GROWTH",
        "#27AE60",  # Moss Green
        "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=500&auto=format&fit=crop",  # Geometric Growth
        f"Healthy market structure with favorable risk-reward profile. "
        f"Volatility and criticality ({crit}/100) within normal parameters. Full position maintained."
    )


def render_hero_specimen(
    ticker: str,
    asset_name: str,
    current_price: str,
    price_change_24h: str,
    criticality: float,
    trend: str,
    is_invested: bool = True,
    volatility_percentile: float = 50
) -> None:
    """
    Render Visual Hero Card (Specimen Style) with image anchor.
    
    Layout: 2-column grid
        Left: Regime visualization image (1/3 width)
        Right: Asset data and metrics (2/3 width)
    
    Integrates with get_current_market_state() output.
    
    Args:
        ticker: Ticker symbol (e.g., 'AAPL')
        asset_name: Full asset name (e.g., 'Apple Inc.')
        current_price: Formatted price string (e.g., '$278.85')
        price_change_24h: Formatted change (e.g., '+3.19%')
        criticality: Criticality score (0-100)
        trend: 'BULL' or 'BEAR'
        is_invested: Investment status from get_current_market_state()
        volatility_percentile: Volatility percentile (0-100)
    """
    try:
        # Parse price change for color logic
        try:
            pct_val = float(str(price_change_24h).strip('%').replace('+', ''))
        except Exception:
            pct_val = 0.0
        
        # Get visual theme based on market state
        regime_name, accent_color, image_url, oracle_text = get_regime_visuals(
            criticality, is_invested, trend, volatility_percentile
        )
        
        # Change bubble color
        change_color = "#27AE60" if pct_val >= 0 else "#C0392B"
        change_bg = "#ECFDF5" if pct_val >= 0 else "#FEF2F2"
        change_prefix = "+" if pct_val >= 0 else ""
        
        # Build HTML card with 2-column grid layout
        card_html = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;700&family=Roboto+Mono:wght@400;500&family=Roboto:wght@300;400;700&display=swap');

.specimen-card {{
                background-color: #FFFFFF; /* White card on cream background */
                border: 1px solid #D1C4E9;
                border-radius: 12px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
                overflow: hidden;
                font-family: 'Roboto', sans-serif;
                color: #2C3E50;
                margin-bottom: 2rem;
                display: grid;
                grid-template-columns: 1fr 2fr; /* Image left (33%), Data right (67%) */
            }}
            
            /* Left Column: Visual Anchor Image */
            .specimen-visual {{
                background-color: #EAECEE;
                position: relative;
                overflow: hidden;
                border-right: 1px solid #E0E0E0;
                min-height: 320px;
            }}
            
            .specimen-image {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                filter: sepia(15%) contrast(95%) saturate(90%); /* Scientific/Heritage Filter */
                transition: transform 0.5s ease;
            }}
            
            .specimen-card:hover .specimen-image {{
                transform: scale(1.05); /* Subtle zoom on hover */
            }}
            
            .visual-overlay {{
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background: linear-gradient(to bottom, rgba(44, 62, 80, 0.05), rgba(44, 62, 80, 0.3));
                pointer-events: none;
            }}
            
            /* Right Column: Asset Data */
            .specimen-data {{
                padding: 28px;
                position: relative;
                display: flex;
                flex-direction: column;
            }}
            
            .header-row {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 20px;
            }}
            
            .asset-title {{
                font-family: 'Merriweather', serif;
                font-size: 2rem;
                font-weight: 700;
                margin: 0;
                line-height: 1.1;
                color: #2C3E50;
            }}
            
            .asset-symbol {{
                font-family: 'Roboto Mono', monospace;
                font-size: 1rem;
                color: #7F8C8D;
                margin-top: 4px;
            }}
            
            /* Criticality Badge (top right) */
            .crit-badge-container {{
                text-align: center;
            }}
            .crit-badge {{
                background-color: {accent_color};
                color: white;
                width: 64px;
                height: 64px;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-family: 'Roboto Mono', monospace;
                font-size: 1.6rem;
                font-weight: 700;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            }}
            .crit-label {{
                font-size: 0.7rem;
                text-transform: uppercase;
                color: {accent_color};
                font-weight: 600;
                margin-top: 6px;
                letter-spacing: 0.5px;
            }}
            
            .regime-tag {{
                display: inline-block;
                background-color: {accent_color}25; /* 25% opacity of accent */
                color: {accent_color};
                padding: 6px 14px;
                border-radius: 4px;
                font-family: 'Roboto Mono', monospace;
                font-size: 0.85rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                margin-bottom: 20px;
                border: 1px solid {accent_color}40;
            }}
            
            .price-row {{
                display: flex;
                align-items: baseline;
                gap: 14px;
                margin-bottom: 24px;
            }}
            
            .main-price {{
                font-size: 2.8rem;
                font-weight: 700;
                font-family: 'Roboto Mono', monospace;
                color: #2C3E50;
            }}
            
            .change-bubble {{
                background-color: {change_bg};
                color: {change_color};
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 1rem;
                font-family: 'Roboto Mono', monospace;
            }}
            
            .oracle-box {{
                border-left: 4px solid {accent_color};
                background-color: #F9F7F1; /* Cream paper background */
                padding: 18px;
                font-style: italic;
                font-family: 'Merriweather', serif;
                color: #555555;
                font-size: 1.05rem;
                line-height: 1.6;
                margin-top: auto; /* Push to bottom */
                border-radius: 0 4px 4px 0;
            }}
            
            /* Responsive Design for mobile */
            @media (max-width: 768px) {{
                .specimen-card {{
                    grid-template-columns: 1fr; /* Stack vertically */
                }}
                .specimen-visual {{
                    height: 200px; /* Shorter image on mobile */
                    border-right: none;
                    border-bottom: 1px solid #E0E0E0;
                }}
}}
</style>

<div class="specimen-card">
    <div class="specimen-visual">
        <img src="{image_url}" class="specimen-image" alt="Regime State Visualization">
        <div class="visual-overlay"></div>
    </div>
    
    <div class="specimen-data">
        <div class="header-row">
            <div>
                <h1 class="asset-title">{asset_name}</h1>
                <div class="asset-symbol">{ticker}</div>
            </div>
            <div class="crit-badge-container">
                <div class="crit-badge">{int(criticality)}</div>
                <div class="crit-label">Criticality</div>
            </div>
        </div>
        
        <div>
            <span class="regime-tag">{regime_name}</span>
        </div>
        
        <div class="price-row">
            <span class="main-price">{current_price}</span>
            <span class="change-bubble">{change_prefix}{price_change_24h}</span>
        </div>
        
        <div class="oracle-box">
            "{oracle_text}"
        </div>
    </div>
</div>
"""
        
        # Render with container to ensure proper HTML rendering
        with st.container():
            st.markdown(card_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"⚠️ Hero Card Render Error: {e}")
        # Fallback to simple display
        st.write(f"**{asset_name}** ({ticker})")
        st.write(f"Price: {current_price} | Change: {price_change_24h}")
        st.write(f"Criticality: {int(criticality)}/100")


# =============================================================================
# INTEGRATION WRAPPER (Uses get_current_market_state)
# =============================================================================

def render_visual_hero_card_from_state(
    ticker: str,
    asset_name: str,
    current_price: str,
    price_change_24h: str,
    current_state: dict
) -> None:
    """
    Render Visual Hero Card using output from get_current_market_state().
    
    This is the integration wrapper that connects the visual card
    with your existing get_current_market_state() function.
    
    Args:
        ticker: Ticker symbol
        asset_name: Full asset name
        current_price: Formatted price (e.g., '$278.85')
        price_change_24h: Formatted change (e.g., '+3.19%')
        current_state: Output dict from get_current_market_state()
    
    Example:
        >>> from logic import get_current_market_state
        >>> current_state = get_current_market_state(df, strategy_mode="defensive")
        >>> render_visual_hero_card_from_state(
        ...     ticker="AAPL",
        ...     asset_name="Apple Inc.",
        ...     current_price="$278.85",
        ...     price_change_24h="+3.19%",
        ...     current_state=current_state
        ... )
    """
    # Extract state from get_current_market_state()
    is_invested = current_state.get('is_invested', True)
    criticality = current_state.get('criticality_score', 0)
    trend = current_state.get('trend_signal', 'BULL')
    
    # Get volatility percentile from raw_data if available
    raw_data = current_state.get('raw_data', {})
    volatility_percentile = raw_data.get('volatility', 0) * 100  # Convert to percentage
    
    # Render the visual card
    render_hero_specimen(
        ticker=ticker,
        asset_name=asset_name,
        current_price=current_price,
        price_change_24h=price_change_24h,
        criticality=criticality,
        trend=trend,
        is_invested=is_invested,
        volatility_percentile=volatility_percentile
    )


# =============================================================================
# DEMO / TESTING
# =============================================================================

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    
    st.title("TECTONIQ Visual Hero Card - Demo")
    st.markdown("---")
    
    # === Test Case 1: PROTECTIVE STASIS (Cash) ===
    st.subheader("Test 1: PROTECTIVE STASIS (Not Invested)")
    mock_data_cash = {
        'name': 'Apple Inc.',
        'symbol': 'AAPL',
        'price': '278.85',
        'change_percent': -2.15,
        'criticality': 88,
        'trend': 'BEAR',
        'volatility_percentile': 85,
        'is_invested': False  # ← Algorithm in cash
    }
    render_hero_specimen(
        ticker=mock_data_cash['symbol'],
        asset_name=mock_data_cash['name'],
        current_price=f"${mock_data_cash['price']}",
        price_change_24h=f"{mock_data_cash['change_percent']:+.2f}%",
        criticality=mock_data_cash['criticality'],
        trend=mock_data_cash['trend'],
        is_invested=mock_data_cash['is_invested'],
        volatility_percentile=mock_data_cash['volatility_percentile']
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === Test Case 2: CRITICAL (Minimal Exposure) ===
    st.subheader("Test 2: CRITICAL INSTABILITY (20% Invested)")
    mock_data_crit = {
        'name': 'Bitcoin USD',
        'symbol': 'BTC-USD',
        'price': '43,520.50',
        'change_percent': -5.42,
        'criticality': 85,
        'trend': 'BULL',
        'volatility_percentile': 92,
        'is_invested': True
    }
    render_hero_specimen(
        ticker=mock_data_crit['symbol'],
        asset_name=mock_data_crit['name'],
        current_price=f"${mock_data_crit['price']}",
        price_change_24h=f"{mock_data_crit['change_percent']:+.2f}%",
        criticality=mock_data_crit['criticality'],
        trend=mock_data_crit['trend'],
        is_invested=mock_data_crit['is_invested'],
        volatility_percentile=mock_data_crit['volatility_percentile']
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === Test Case 3: HIGH ENERGY (Partial Exposure) ===
    st.subheader("Test 3: HIGH ENERGY (50% Invested)")
    mock_data_high = {
        'name': 'Tesla Inc.',
        'symbol': 'TSLA',
        'price': '242.80',
        'change_percent': 3.85,
        'criticality': 68,
        'trend': 'BULL',
        'volatility_percentile': 70,
        'is_invested': True
    }
    render_hero_specimen(
        ticker=mock_data_high['symbol'],
        asset_name=mock_data_high['name'],
        current_price=f"${mock_data_high['price']}",
        price_change_24h=f"{mock_data_high['change_percent']:+.2f}%",
        criticality=mock_data_high['criticality'],
        trend=mock_data_high['trend'],
        is_invested=mock_data_high['is_invested'],
        volatility_percentile=mock_data_high['volatility_percentile']
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === Test Case 4: STABLE GROWTH (Full Exposure) ===
    st.subheader("Test 4: STABLE GROWTH (100% Invested)")
    mock_data_stable = {
        'name': 'Microsoft Corporation',
        'symbol': 'MSFT',
        'price': '425.15',
        'change_percent': 1.24,
        'criticality': 35,
        'trend': 'BULL',
        'volatility_percentile': 25,
        'is_invested': True
    }
    render_hero_specimen(
        ticker=mock_data_stable['symbol'],
        asset_name=mock_data_stable['name'],
        current_price=f"${mock_data_stable['price']}",
        price_change_24h=f"{mock_data_stable['change_percent']:+.2f}%",
        criticality=mock_data_stable['criticality'],
        trend=mock_data_stable['trend'],
        is_invested=mock_data_stable['is_invested'],
        volatility_percentile=mock_data_stable['volatility_percentile']
    )
    
    st.markdown("---")
    st.markdown("""
    ### 🎨 Visual Anchors Explained
    
    Each regime state has a unique visual anchor (image) that represents its energy level:
    
    - **🔘 Zen Stones** - PROTECTIVE STASIS (stillness, preservation, safety)
    - **🔴 Abstract Chaos** - CRITICAL (network instability, system stress)
    - **🟠 Supernova** - HIGH ENERGY (explosive force, intense activity)
    - **🟢 Geometric Patterns** - STABLE GROWTH (organic structure, harmony)
    - **⚪ Stormy Sea** - STRUCTURAL DECLINE (turbulence, uncertainty)
    
    These images provide an **intuitive visual anchor** that helps users instantly 
    grasp the market's current state without reading text.
    """)

