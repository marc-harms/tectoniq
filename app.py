
"""
SOC Market Seismograph - Streamlit Application
==============================================

Interactive web dashboard for Self-Organized Criticality (SOC) market analysis.

Features:
    - Multi-asset scanning with 5-Tier regime classification
    - Deep dive analysis with historical signal performance
    - Instability Score indicator (0-100)
    - Lump Sum investment simulation with Dynamic Position Sizing
    - Dark/Light theme support

Theory:
    Markets exhibit Self-Organized Criticality - they naturally evolve toward
    critical states where small inputs can trigger events of any size.
    This app visualizes market "energy states" through volatility clustering.

Author: Market Analysis Team
Version: 6.0 (Cleaned & Documented)
"""

# =============================================================================
# IMPORTS
# =============================================================================
import requests
from typing import List, Dict, Any

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

from logic import DataFetcher, SOCAnalyzer, run_dca_simulation, calculate_audit_metrics
from ui_simulation import render_dca_simulation
from ui_detail import render_detail_panel, render_regime_persistence_chart, render_current_regime_outlook
from ui_auth import render_disclaimer, render_auth_page, render_sticky_cockpit_header, render_scientific_masthead, render_education_landing
from auth_manager import (
    is_authenticated, logout, get_current_user_id, get_current_user_email,
    get_user_portfolio, can_access_simulation, show_upgrade_prompt,
    can_run_simulation, increment_simulation_count
)
from config import get_scientific_heritage_css, HERITAGE_THEME, REGIME_COLORS
from analytics_engine import MarketForensics


# =============================================================================
# HERO CARD (Specimen Style)
# =============================================================================
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import textwrap

def generate_market_narrative(regime_raw: str, trend: str, score: float, change_24h: float) -> str:
    """
    Generates a concise one-sentence market narrative for the hero card.
    Combines regime context, price trend and 24h move into a short insight.
    """
    try:
        change_val = float(change_24h)
    except Exception:
        change_val = 0.0

    regime = str(regime_raw).upper()

    # Basis-Satz basierend auf Regime (Zustand)
    if "CRITICAL" in regime:
        base = "The market is showing signs of systemic instability and extreme stress"
    elif "HIGH" in regime and "ENERGY" in regime:
        base = "Volatility is surging, indicating an overheated market state"
    elif "ACTIVE" in regime:
        base = "Trading activity is normal with healthy liquidity"
    elif "STABLE" in regime:
        base = "The asset is in a calm, low-volatility accumulation phase"
    elif "DORMANT" in regime:
        base = "Market participation is minimal; the asset is currently asleep"
    else:
        base = "Market conditions are currently being analyzed"

    # Ergänzung basierend auf Trend/Preis (Richtung)
    if change_val < -2.0:
        direction = ", accompanied by sharp selling pressure."
    elif change_val > 2.0:
        direction = ", driven by strong buying momentum."
    elif str(trend).upper() == "UP":
        direction = ", supporting a steady upward trend."
    elif str(trend).upper() == "DOWN":
        direction = ", weighing down on price action."
    else:
        direction = "."

    return f"{base}{direction}"


def render_hero_card(
    ticker: str,
    asset_name: str,
    current_price: str,
    price_change_24h: str,
    score: float,
    regime_raw: str,
    trend: str = "Unknown"
) -> None:
    """
    Renders the Asset Hero Card (Specimen Label Style) with narrative engine.
    """
    # 1) Parse percent text for logic
    try:
        pct_val = float(str(price_change_24h).strip('%').replace('+',''))
    except Exception:
        pct_val = 0.0

    narrative = generate_market_narrative(regime_raw, trend, score, pct_val)

    # 2) Regime badge color + label
    regime_upper = str(regime_raw).upper()
    if "CRITICAL" in regime_upper:
        badge_color = "#C0392B"; clean_regime = "CRITICAL"
    elif "HIGH" in regime_upper:
        badge_color = "#D35400"; clean_regime = "HIGH ENERGY"
    elif "ACTIVE" in regime_upper:
        badge_color = "#F1C40F"; clean_regime = "ACTIVE"
    elif "STABLE" in regime_upper:
        badge_color = "#27AE60"; clean_regime = "STABLE"
    else:
        badge_color = "#95A5A6"; clean_regime = "DORMANT"

    # 3) Trend colors
    if pct_val > 0:
        change_color = "#10B981"; change_bg = "#ECFDF5"
    elif pct_val < 0:
        change_color = "#EF4444"; change_bg = "#FEF2F2"
    else:
        change_color = "#6B7280"; change_bg = "#F3F4F6"

    # 4) Render HTML card
    with st.container():
        st.markdown(f"""
<div style="background-color: white; border: 1px solid #d1d5db; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div>
            <h2 style="margin: 0; font-family: 'Merriweather', serif; color: #111827; font-size: 1.8em;">{asset_name}</h2>
            <p style="margin: 0; color: #6b7280; font-size: 0.9em; font-weight: 500;">{ticker}</p>
        </div>
        <div style="text-align: center;">
             <div style="background-color: {badge_color}; color: white; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2em;">
                {int(score)}
            </div>
            <div style="font-size: 0.7em; color: #6b7280; margin-top: 4px;">Criticality</div>
        </div>
    </div>
    <div style="margin-top: 15px; background-color: {badge_color}20; color: {badge_color}; padding: 4px 12px; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 0.8em; letter-spacing: 0.05em;">
        {clean_regime} REGIME
    </div>
    <div style="margin-top: 20px; display: flex; align-items: baseline; gap: 10px;">
        <span style="font-size: 2.5em; font-weight: bold; color: #1f2937;">{current_price}</span>
        <span style="font-size: 1em; font-weight: 600; color: {change_color}; background-color: {change_bg}; padding: 2px 6px; border-radius: 4px;">
            {price_change_24h} <span style="font-size:0.8em; color:#6b7280; font-weight:normal;">24h</span>
        </span>
    </div>
    <div style="margin-top: 20px; padding: 15px; background-color: #f9fafb; border-left: 4px solid {badge_color}; border-radius: 0 4px 4px 0; color: #374151;">
        <div style="font-size: 1.05em; font-family: 'Merriweather', serif; line-height: 1.5; font-style: italic;">
            "{narrative}"
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# STATISTICAL REPORT & SIGNAL AUDIT (Clean Rebuild)
# =============================================================================
def render_advanced_analytics(df: pd.DataFrame, is_dark: bool = False) -> None:
    """
    Clean rebuild using MarketForensics engine.
    Simply calls engine and displays results.
    """
    if df is None or df.empty:
        st.info("No data available.")
        return
    
    regime_emojis = {'DORMANT': '⚪', 'STABLE': '🟢', 'ACTIVE': '🟡', 'HIGH_ENERGY': '🟠', 'CRITICAL': '🔴'}
    severity_order = ['DORMANT', 'STABLE', 'ACTIVE', 'HIGH_ENERGY', 'CRITICAL']
    severity_rank = {name: idx for idx, name in enumerate(severity_order)}
    
    # Prepare dataframe for engine
    df_work = df.copy()
    
    # Ensure lowercase column names and Regime column exists
    df_work.columns = [c.lower() if isinstance(c, str) else c for c in df_work.columns]
    
    if 'regime' not in df_work.columns and 'Regime' not in df_work.columns:
        # Derive regime from smoothed volatility
        price_col = 'close' if 'close' in df_work.columns else 'adj close' if 'adj close' in df_work.columns else df_work.select_dtypes(include='number').columns[0]
        df_work['return'] = df_work[price_col].pct_change()
        df_work['vol'] = df_work['return'].abs().rolling(5).mean()
        df_work['Regime'] = pd.cut(df_work['vol'], bins=[-1, 0.005, 0.01, 0.02, 0.03, 10], labels=['DORMANT', 'STABLE', 'ACTIVE', 'HIGH_ENERGY', 'CRITICAL']).astype(str)
    elif 'regime' in df_work.columns:
        df_work['Regime'] = df_work['regime']
    
    # Ensure Close column exists
    if 'Close' not in df_work.columns and 'close' in df_work.columns:
        df_work['Close'] = df_work['close']

    # Normalize regime labels for robust matching (strip emojis/whitespace, uppercase)
    if 'Regime' in df_work.columns:
        df_work['Regime_Clean'] = (
            df_work['Regime']
            .astype(str)
            .str.replace('[^\\w\\s]', '', regex=True)
            .str.strip()
            .str.upper()
        )
    
    # Call engine
    regime_stats = MarketForensics.get_regime_stats(df_work)
    crash_metrics = MarketForensics.get_crash_metrics(df_work)
    
    # Build display table (directly from engine output)
    regime_table = regime_stats.copy()
    # Drop missing or literal "nan" regime labels plus rows with missing metrics
    regime_table = regime_table.loc[regime_table.index.notna()]
    regime_table = regime_table.loc[~regime_table.index.to_series().astype(str).str.lower().eq('nan')]
    regime_table = regime_table.dropna(how='any')
    regime_table = regime_table.loc[
        sorted(
            regime_table.index,
            key=lambda r: severity_rank.get(str(r).upper(), len(severity_rank))
        )
    ]

    # Case-insensitive selection of desired columns
    desired_order = ['frequency_pct', 'avg_duration_days', 'median_duration_days', 'max_duration_days']
    col_lookup = {c.lower(): c for c in regime_table.columns}
    selected_cols = [col_lookup[k] for k in desired_order if k in col_lookup]
    regime_table = regime_table[selected_cols]

    rename_map = {
        col_lookup.get('frequency_pct', 'frequency_pct'): 'Freq (%)',
        col_lookup.get('avg_duration_days', 'avg_duration_days'): 'Ø Duration',
        col_lookup.get('median_duration_days', 'median_duration_days'): 'Median',
        col_lookup.get('max_duration_days', 'max_duration_days'): 'Max Days'
    }
    regime_table = regime_table.rename(columns=rename_map)

    regime_table.index = [f"{regime_emojis.get(str(r).upper(), '⚪')} {str(r).upper()}" for r in regime_table.index]
    
    # Display expander
    with st.expander("Statistical Report & Signal Audit", expanded=False):
        # Slightly reduce metric value font size to avoid truncation
        st.markdown(
            "<style>div[data-testid='stMetricValue'] { font-size: 1.05rem !important; }</style>",
            unsafe_allow_html=True
        )
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown("### 📊 Regime Profile")
            st.dataframe(regime_table, use_container_width=True)
        
        with col2:
            st.markdown("### 🛡️ Protection")
            st.metric("True Crashes", crash_metrics['total_crashes_5y'], delta=f"{crash_metrics['detected_count']} detected")
            st.metric(
                "Detection Rate",
                f"{crash_metrics['detection_rate']:.0f}%",
                help="Percentage of crashes (>20% drop) successfully flagged in advance."
            )
        
        with col3:
            st.markdown("### 🎯 Quality")
            false_alarms = crash_metrics.get('false_alarms', 0)
            total_signals = crash_metrics.get('total_signals', 0)
            detected = crash_metrics.get('detected_count', 0)
            hit_rate_value = f"{detected}/{total_signals}" if total_signals else "0/0"
            ratio = (total_signals / detected) if detected else None
            delta_text = f"1 crash per {ratio:.0f} alerts" if ratio else "No detections yet"

            st.metric(
                "False Alarms",
                f"{false_alarms}",
                help="Signals followed by market recovery (Insurance Cost)"
            )
            st.metric(
                "Hit Rate",
                hit_rate_value,
                delta=delta_text,
                help="Detected crashes versus total defensive alerts"
            )
        
        with col4:
            st.markdown("### ⏱️ Timing")
            avg_lead = crash_metrics.get('avg_lead_time_days', 0) or 0
            if avg_lead >= 1.0:
                lead_display = f"{avg_lead:.1f} Days"
            elif 0 < avg_lead < 1:
                lead_display = "< 1 Day"
            else:
                lead_display = "Same Day (Reaction)"
            st.metric(
                "Ø Lead Time",
                lead_display,
                help="Average number of days the signal turned Red/Orange before the crash peak. 'Same Day' indicates the model reacted instantly to a sudden shock event."
            )

        crash_list = crash_metrics.get('crash_list_full') or crash_metrics.get('crash_list_preview', [])
        if crash_list:
            warning_signals = {'CRITICAL', 'HIGH_ENERGY', 'HIGH ENERGY'}
            index_is_datetime = pd.api.types.is_datetime64_any_dtype(df_work.index)
            crash_rows = []
            for crash in crash_list:
                start_date = crash.get('start_date')
                drawdown = crash.get('max_loss')
                duration = crash.get('duration')

                detected = False
                found_signal = None
                if start_date is not None and index_is_datetime:
                    try:
                        crash_start = pd.to_datetime(start_date)
                        lookback_start = crash_start - pd.Timedelta(days=21)
                        lookahead_end = crash_start + pd.Timedelta(days=7)
                        window = df_work.loc[lookback_start: lookahead_end]
                        if 'Regime_Clean' in window.columns:
                            mask = window['Regime_Clean'].isin(warning_signals)
                            if mask.any():
                                detected = True
                                first_idx = window[mask].index[0]
                                found_signal = window.loc[first_idx, 'Regime_Clean']
                    except Exception:
                        detected = False

                signal_label = "Found: None"
                if found_signal:
                    found_clean = str(found_signal).upper()
                    signal_label = f"Found: {regime_emojis.get(found_clean, '⚪')} {found_clean}"

                crash_rows.append({
                    'Date': start_date.date() if hasattr(start_date, 'date') else start_date,
                    'Drawdown': f"{drawdown * 100:.1f}%" if pd.notna(drawdown) else "-",
                    'Duration': f"{duration} days" if pd.notna(duration) else "-",
                    'Detected?': "✅" if detected else "❌",
                    'Signal Found?': signal_label
                })

            crash_log_df = pd.DataFrame(crash_rows)
            st.markdown("### 🔎 Event Log: Detected vs. Missed Crashes")
            st.dataframe(crash_log_df, use_container_width=True)
        else:
            st.info("No crash events identified in the selected window.")


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="TECTONIQ - Market Analysis Platform",
    page_icon="assets/logo-soc.png",
    layout="wide",
    initial_sidebar_state="collapsed"  # No sidebar used - user menu in header
)

# =============================================================================
# CONSTANTS
# =============================================================================
ACCESS_CODE = "BETA2025"
DEFAULT_SMA_WINDOW = 200
DEFAULT_VOL_WINDOW = 30
DEFAULT_HYSTERESIS = 0.0
MIN_DATA_POINTS = 200

# Precious metals excluded from main risk scan - they act as hedges (inverse correlation)
# and distort market risk scoring. Available separately in "Hedge Assets" category.
PRECIOUS_METALS = {'GC=F', 'SI=F', 'PL=F', 'PA=F', 'GLD', 'SLV'}

# Popular tickers for quick suggestions
POPULAR_TICKERS = {
    "US Tech": ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA', 'META'],
    "Crypto": ['BTC-USD', 'ETH-USD', 'SOL-USD'],
    "ETFs": ['SPY', 'QQQ', 'IWM', 'VTI'],
}

TICKER_NAME_FIXES = {
    "SIEMENS                    N": "Siemens", "Allianz                    v": "Allianz",
    "DEUTSCHE TELEKOM           N": "Deutsche Telekom", "Airbus                     A": "Airbus",
    "BAYERISCHE MOTOREN WERKE   S": "BMW", "VOLKSWAGEN                 V": "Volkswagen",
    "BASF                       N": "BASF", "MUENCHENER RUECKVERS.-GES. N": "Munich Re",
                "SAP                       ": "SAP"
            }
            
SPECIAL_TICKER_NAMES = {"^GDAXI": "DAX 40 Index"}

# =============================================================================
# STYLING & THEME
# =============================================================================

def get_theme_css(is_dark: bool) -> str:
    """
    Generate comprehensive CSS styles for theme (dark/light mode).
    
    Handles styling for: app background, text colors, inputs, tables,
    buttons, cards, asset list items, and footer elements.
    """
    c = {
        "bg": "#0E1117" if is_dark else "#FFFFFF",
        "bg2": "#262730" if is_dark else "#F0F2F6",
        "card": "#1E1E1E" if is_dark else "#F8F9FA",
        "border": "#333" if is_dark else "#DEE2E6",
        "text": "#FAFAFA" if is_dark else "#212529",
        "muted": "#888" if is_dark else "#6C757D",
        "input": "#262730" if is_dark else "#FFFFFF"
    }
    
    return f"""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {c['bg']} !important;
    }}
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div,
    .stApp h1, .stApp h2, .stApp h3, .stMarkdown, .stMarkdown p {{
        color: {c['text']} !important;
    }}
    .stTextInput input, .stTextArea textarea, [data-baseweb="select"], [data-baseweb="select"] > div {{
        background-color: {c['input']} !important;
        color: {c['text']} !important;
        border-color: {c['border']} !important;
    }}
    .streamlit-expanderHeader {{ 
        background-color: {c['card']} !important; 
        color: {c['text']} !important;
    }}
    .streamlit-expanderHeader p, .streamlit-expanderHeader span,
    .streamlit-expanderHeader svg {{ 
        color: {c['text']} !important; 
        fill: {c['text']} !important;
    }}
    .streamlit-expanderContent {{ 
        background-color: {c['bg2']} !important; 
        color: {c['text']} !important;
    }}
    .streamlit-expanderContent p, .streamlit-expanderContent span,
    .streamlit-expanderContent label, .streamlit-expanderContent div {{
        color: {c['text']} !important;
    }}
    [data-testid="stExpander"] {{
        background-color: {c['card']} !important;
        border-color: {c['border']} !important;
    }}
    [data-testid="stExpander"] details {{
        background-color: {c['card']} !important;
    }}
    [data-testid="stExpander"] summary {{
        color: {c['text']} !important;
    }}
    .stDataFrame, [data-testid="stDataFrame"], .stDataFrame div, .stDataFrame table,
    .stDataFrame th, .stDataFrame td, [data-testid="glideDataEditor"], .dvn-scroller {{
        background-color: {c['card']} !important;
        color: {c['text']} !important;
    }}
    .stDataFrame th {{ background-color: {c['bg2']} !important; }}
    .stButton > button,
    [data-testid="baseButton-secondary"],
    [data-testid="stBaseButton-secondary"],
    button[kind="secondary"] {{
        background-color: {c['card']} !important;
        color: {c['text']} !important;
        border: 1px solid {c['border']} !important;
        font-weight: 600;
        border-radius: 8px;
    }}
    .stButton > button:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="stBaseButton-secondary"]:hover {{ 
        background-color: {c['bg2']} !important; 
        color: {c['text']} !important;
        border-color: #667eea !important;
    }}
    .stButton > button[kind="primary"],
    [data-testid="baseButton-primary"],
    [data-testid="stBaseButton-primary"],
    button[kind="primary"] {{
        background-color: #667eea !important;
        color: white !important;
        border-color: #667eea !important;
    }}
    .stButton > button[kind="primary"]:hover,
    [data-testid="baseButton-primary"]:hover {{
        background-color: #5568d9 !important;
    }}
    /* Ensure all button text is visible */
    .stButton button p,
    .stButton button span,
    [data-testid="baseButton-secondary"] p,
    [data-testid="baseButton-secondary"] span {{
        color: {c['text']} !important;
    }}
    .stRadio label {{ color: {c['text']} !important; }}
    .stRadio [role="radiogroup"] label {{ background-color: {c['card']} !important; border-color: {c['border']} !important; }}
    [data-testid="stMetricValue"] {{ color: {c['text']} !important; }}
    [data-testid="stMetricLabel"] {{ color: {c['muted']} !important; }}
    [data-testid="stSidebar"] {{ display: none; }}
    .stDeployButton {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem; max-width: 1400px; margin: 0 auto; }}
    hr {{ border-color: {c['border']} !important; }}
    .app-header {{
        display: flex; align-items: center; gap: 1rem;
        padding: 0.75rem 0; border-bottom: 2px solid {c['border']}; margin-bottom: 1rem;
    }}
    .logo {{ width: 45px; height: 45px; background: linear-gradient(135deg, #667eea, #764ba2);
             border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }}
    .app-title {{ font-size: 1.6rem; font-weight: 700;
                  background: linear-gradient(90deg, #667eea, #764ba2);
                  -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }}
    .app-subtitle {{ font-size: 0.8rem; color: {c['muted']} !important; margin: 0; }}
    .asset-item {{
        padding: 0.6rem 0.8rem; border-radius: 6px; margin-bottom: 4px;
        cursor: pointer; transition: all 0.15s ease;
        border: 1px solid transparent;
    }}
    .asset-item:hover {{ background-color: {c['bg2']}; }}
    .asset-item.selected {{ background-color: {c['bg2']}; border-color: #667eea; }}
    .asset-symbol {{ font-weight: 600; font-size: 0.95rem; }}
    .asset-price {{ color: {c['muted']}; font-size: 0.85rem; }}
    .asset-signal {{ font-size: 0.8rem; }}
    .detail-header {{ padding: 1rem; background: {c['card']}; border-radius: 8px; margin-bottom: 1rem; }}
    .signal-badge {{
        display: inline-block; padding: 0.4rem 0.8rem; border-radius: 6px;
        font-weight: 600; font-size: 0.9rem;
    }}
    .footer {{ border-top: 1px solid {c['border']}; padding-top: 0.75rem; margin-top: 1.5rem; }}
    .footer-item {{ display: inline-block; margin-right: 1.5rem; font-size: 0.8rem; color: {c['muted']}; }}
</style>
"""

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clean_name(name: str) -> str:
    """
    Clean and normalize ticker names from Yahoo Finance.
    
    Handles German stock suffixes (SE, AG), fixes common formatting issues,
    and applies hardcoded fixes for known problematic names (DAX stocks).
    """
    name = name.replace(" SE", "").replace(" AG", "").strip()
    if name in TICKER_NAME_FIXES:
        return TICKER_NAME_FIXES[name]
    name = " ".join(name.split())
    return name[:-2] if len(name) > 2 and name[-2] == " " else name


def get_signal_color(signal: str) -> str:
    """
    Get display color for 5-tier regime classification.
    
    Mapping:
        STABLE → Green (#00FF00)
        ACTIVE → Yellow (#FFCC00)
        HIGH_ENERGY → Orange (#FF6600)
        CRITICAL → Red (#FF0000)
        DORMANT → Grey (#888888)
    """
    signal_upper = signal.upper()
    if "STABLE" in signal_upper:
        return "#00FF00"
    if "CRITICAL" in signal_upper:
        return "#FF0000"
    if "HIGH_ENERGY" in signal_upper or "HIGH ENERGY" in signal_upper:
        return "#FF6600"
    if "ACTIVE" in signal_upper:
        return "#FFCC00"
    if "DORMANT" in signal_upper:
        return "#888888"
    return "#888888"


def get_signal_bg(signal: str) -> str:
    """Get semi-transparent background color for regime badge display."""
    signal_upper = signal.upper()
    if "STABLE" in signal_upper:
        return "rgba(0, 255, 0, 0.15)"
    if "CRITICAL" in signal_upper:
        return "rgba(255, 0, 0, 0.15)"
    if "HIGH_ENERGY" in signal_upper or "HIGH ENERGY" in signal_upper:
        return "rgba(255, 102, 0, 0.15)"
    if "ACTIVE" in signal_upper:
        return "rgba(255, 204, 0, 0.15)"
    if "DORMANT" in signal_upper:
        return "rgba(136, 136, 136, 0.2)"
    return "rgba(136, 136, 136, 0.15)"


# =============================================================================
# DATA FUNCTIONS
# =============================================================================

@st.cache_data(ttl=3600)
def run_analysis(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    Run SOC analysis on multiple tickers with progress indicator.
    
    For each ticker: fetches data, calculates metrics, determines market
    phase (5-tier classification), and returns analysis results.
    
    Includes robust API error handling with user-friendly messages.
    
    Returns:
        List of dictionaries containing symbol, price, signal, trend,
        criticality_score, and other phase metrics.
    """
    fetcher = DataFetcher(cache_enabled=True)
    results = []
    failed_tickers = []
    api_error_count = 0
    
    progress = st.progress(0)
    status = st.empty()
    
    for i, symbol in enumerate(tickers):
        status.caption(f"Analyzing {symbol}...")
        try:
            df = fetcher.fetch_data(symbol)
            info = fetcher.fetch_info(symbol)
            if not df.empty and len(df) > MIN_DATA_POINTS:
                analyzer = SOCAnalyzer(df, symbol, info, DEFAULT_SMA_WINDOW, DEFAULT_VOL_WINDOW, DEFAULT_HYSTERESIS)
                phase = analyzer.get_market_phase()
                phase['info'] = info
                phase['name'] = clean_name(info.get('name', symbol))
                results.append(phase)
            else:
                failed_tickers.append(symbol)
                api_error_count += 1
        except ConnectionError:
            failed_tickers.append(symbol)
            api_error_count += 1
        except TimeoutError:
            failed_tickers.append(symbol)
            api_error_count += 1
        except Exception as e:
            error_msg = str(e).lower()
            if 'rate limit' in error_msg or 'too many requests' in error_msg:
                api_error_count += 1
            elif 'connection' in error_msg or 'timeout' in error_msg or 'network' in error_msg:
                api_error_count += 1
            failed_tickers.append(symbol)
        
        progress.progress((i + 1) / len(tickers))
    
    status.empty()
    progress.empty()
    
    # Show API error warning if significant failures
    if api_error_count >= len(tickers) * 0.5:  # More than 50% failed
        st.error("""
        ⚠️ **Data Provider Unavailable**
        
        The market data API (Yahoo Finance) appears to be experiencing issues.
        This could be due to:
        - Rate limiting (too many requests)
        - Temporary service outage
        - Network connectivity issues
        
        **Please try again in 5-10 minutes.**
        
        If the problem persists, check [Yahoo Finance Status](https://finance.yahoo.com).
        """)
    elif failed_tickers:
        st.warning(f"⚠️ Could not fetch data for: {', '.join(failed_tickers[:5])}{'...' if len(failed_tickers) > 5 else ''}")
    
    return results


# =============================================================================
# TICKER SEARCH & VALIDATION FUNCTIONS
# =============================================================================

def search_ticker(query: str) -> List[Dict[str, Any]]:
    """
    Search for tickers by company name or symbol using Yahoo Finance.
    
    Args:
        query: Search term (company name or ticker symbol)
    
    Returns:
        List of matching results with ticker, name, type, exchange
    """
    if not query or len(query) < 2:
        return []
    
    try:
        # Use Yahoo Finance search API
        url = f"https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            'q': query,
            'quotesCount': 8,
            'newsCount': 0,
            'enableFuzzyQuery': True,
            'quotesQueryId': 'tss_match_phrase_query'
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for quote in data.get('quotes', []):
            # Filter for stocks, ETFs, and crypto only
            quote_type = quote.get('quoteType', '').upper()
            if quote_type in ['EQUITY', 'ETF', 'CRYPTOCURRENCY', 'INDEX', 'MUTUALFUND']:
                results.append({
                    'ticker': quote.get('symbol', ''),
                    'name': quote.get('shortname') or quote.get('longname') or quote.get('symbol', ''),
                    'type': quote_type,
                    'exchange': quote.get('exchange', '')
                })
        
        return results
        
    except requests.exceptions.RequestException:
        return []
    except Exception:
        return []


def validate_ticker(ticker: str) -> Dict[str, Any]:
    """
    Validate a ticker symbol using yfinance.
    
    Args:
        ticker: Stock/crypto ticker symbol (e.g., 'AAPL', 'BTC-USD')
    
    Returns:
        Dict with 'valid' (bool), 'name' (str), 'error' (str if invalid)
    """
    try:
        ticker = ticker.strip().upper()
        if not ticker:
            return {'valid': False, 'error': 'Empty ticker'}
        
        stock = yf.Ticker(ticker)
        
        # Try to get recent price history first (most reliable check)
        hist = stock.history(period='5d')
        
        if hist.empty:
            return {'valid': False, 'error': f'Ticker "{ticker}" not found'}
        
        # Get latest price from history
        latest_price = hist['Close'].iloc[-1] if not hist.empty else 0
        
        # Try to get info for name (but don't fail if unavailable)
        name = ticker
        try:
            info = stock.info
            if info:
                # Try multiple name fields
                name = (info.get('shortName') or 
                       info.get('longName') or 
                       info.get('name') or 
                       ticker)
                # Try multiple price fields if history price is 0
                if latest_price == 0:
                    latest_price = (info.get('regularMarketPrice') or 
                                  info.get('previousClose') or 
                                  info.get('currentPrice') or 
                                  0)
        except:
            # If info fails, just use ticker as name
            pass
        
        return {
            'valid': True,
            'ticker': ticker,
            'name': name,
            'price': latest_price
        }
        
    except requests.exceptions.RequestException:
        return {'valid': False, 'error': 'API not responding. Please try again in 5 minutes.'}
    except Exception as e:
        error_msg = str(e).lower()
        if 'connection' in error_msg or 'timeout' in error_msg or 'network' in error_msg:
            return {'valid': False, 'error': 'API not responding. Please try again in 5 minutes.'}
        return {'valid': False, 'error': f'Ticker "{ticker}" not found'}


# =============================================================================
# DETAIL PANEL UI COMPONENTS
# =============================================================================
# NOTE: Detail panel UI moved to ui_detail.py
# Import: from ui_detail import render_detail_panel, render_regime_persistence_chart, render_current_regime_outlook



# =============================================================================
# INVESTMENT SIMULATION UI
# =============================================================================

# =============================================================================
# AUTHENTICATION & NAVIGATION UI
# =============================================================================
# NOTE: Auth & navigation UI moved to ui_auth.py
# Import: from ui_auth import render_disclaimer, check_auth, login_page, render_sticky_cockpit_header, render_education_landing


# =============================================================================
# LEGAL PAGE DIALOGS
# =============================================================================

@st.dialog("⚖️ Legal Disclaimer", width="large")
def show_disclaimer_dialog():
    """Show disclaimer in a modal dialog."""
    st.markdown("""
    This application is provided for educational and informational purposes only.
    Nothing on this platform constitutes financial, investment, or trading advice.
    
    **No Investment Recommendations:**
    - We do not recommend buying, selling, or holding any financial instruments
    - All analysis is purely statistical observation
    - Past performance is not indicative of future results
    
    **Limitation of Liability:**
    - The creators shall not be liable for any damages arising from use
    - Users accept full responsibility for their investment decisions
    
    **Independent Verification Required:**
    - Consult with qualified financial advisors before making decisions
    - Conduct your own research and due diligence
    
    ---
    
    *This disclaimer is governed by applicable laws. If any provision is found unenforceable,
    the remaining provisions shall continue in full force and effect.*
    """)
    
    if st.button("Close", key="close_disclaimer", use_container_width=True):
        st.rerun()


@st.dialog("🔒 Data Protection Policy", width="large")
def show_data_protection_dialog():
    """Show data protection policy in a modal dialog."""
    st.markdown("""
    **Data Controller:** TECTONIQ Platform
    
    **Data We Collect:**
    - Email address (for authentication)
    - Portfolio preferences (ticker symbols you save)
    - Usage analytics (anonymous)
    
    **How We Use Your Data:**
    - To provide authentication services
    - To save your portfolio preferences
    - To improve the application
    
    **Data Storage:**
    - Stored securely via Supabase (EU servers)
    - Encrypted in transit and at rest
    - Not shared with third parties
    
    **Your Rights:**
    - Right to access your data
    - Right to delete your account
    - Right to data portability
    
    **GDPR Compliance:**
    - We comply with EU data protection regulations
    - Data processing is limited to stated purposes
    - You can request data deletion at any time
    
    **Contact:** For data protection inquiries, email privacy@tectoniq.app
    """)
    
    if st.button("Close", key="close_data_protection", use_container_width=True):
        st.rerun()


@st.dialog("📄 Imprint / Legal Notice", width="large")
def show_imprint_dialog():
    """Show imprint in a modal dialog."""
    st.markdown("""
    **Service Provider:**  
    TECTONIQ Platform  
    [Your Address]  
    [City, Postal Code]  
    [Country]
    
    **Contact:**  
    Email: info@tectoniq.app  
    Web: tectoniq.app
    
    **Responsible for Content:**  
    [Your Name / Company Name]
    
    **Disclaimer:**  
    This platform provides educational content only. We assume no liability for the 
    accuracy, completeness, or timeliness of the information provided.
    
    **Copyright:**  
    © 2025 TECTONIQ. All rights reserved. Unauthorized reproduction or distribution 
    of this application or its content is prohibited.
    
    **Third-Party Data:**  
    Market data provided by Yahoo Finance. We do not control or guarantee the 
    accuracy of third-party data sources.
    
    **Jurisdiction:**  
    This imprint is provided in accordance with applicable laws and regulations.
    """)
    
    if st.button("Close", key="close_imprint", use_container_width=True):
        st.rerun()


@st.dialog("🚨 News & Updates", width="large")
def show_news_dialog():
    """Show news & updates in a modal dialog with heritage styling."""
    # Read news from file
    try:
        with open("news.txt", "r") as f:
            news_content = f.read()
        # Remove excessive blank lines
        import re
        news_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', news_content)
        news_content = news_content.strip()
    except:
        news_content = "Welcome to TECTONIQ! Stay tuned for updates."
    
    # Display with heritage styling
    st.markdown(f"""
<div style="background-color: #F9F7F1; padding: 1.5rem; border-radius: 8px; border: 1px solid #D1C4E9;">
    <div style="font-size: 1rem; line-height: 1.6; white-space: pre-wrap; color: #333; font-family: 'Merriweather', serif;">
{news_content}
    </div>
</div>
""", unsafe_allow_html=True)
    
    if st.button("Close", key="close_news", use_container_width=True):
        st.rerun()


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """
    Main application entry point - Multi-User SaaS Edition.
    
    Flow:
        1. Show legal disclaimer (must accept to continue)
        2. Check user authentication (Supabase)
        3. Initialize session state
        4. Apply theme CSS
        5. Render sidebar with logout + user info
        6. Render sticky cockpit header (always visible)
        7. Main content area:
           - No asset: Education landing + quick picks
           - Asset selected: Deep Dive or Simulation tabs (tier-gated)
    """
    # Session state initialization
    if 'disclaimer_accepted' not in st.session_state:
        st.session_state.disclaimer_accepted = False
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False  # Light mode default
    if 'selected_asset' not in st.session_state:
        st.session_state.selected_asset = 0
    if 'analysis_mode' not in st.session_state:
        st.session_state.analysis_mode = "deep_dive"
    if 'current_ticker' not in st.session_state:
        st.session_state.current_ticker = None
    
    # Apply Scientific Heritage CSS theme FIRST (before any page)
    st.markdown(get_scientific_heritage_css(), unsafe_allow_html=True)
    
    # Legal disclaimer gate (must accept before anything else)
    if not st.session_state.disclaimer_accepted:
        render_disclaimer()
        return
    
    # === AUTHENTICATION GATE (THE GATEKEEPER) ===
    # Check if user is authenticated via Supabase
    if not is_authenticated():
        render_auth_page()
        return
    
    # === SCIENTIFIC MASTHEAD (Journal-style Header) ===
    render_scientific_masthead(validate_ticker, search_ticker, run_analysis)
    
    # === NEWS & UPDATES BUTTON (centered) ===
    col_news_spacer1, col_news_center, col_news_spacer2 = st.columns([2, 1, 2])
    with col_news_center:
        if st.button("🚨 News & Updates", key="btn_news_updates", use_container_width=True):
            show_news_dialog()
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # === PORTFOLIO VIEW (if toggled on) ===
    if st.session_state.get('show_portfolio', False):
        with st.container(border=True):
            col_header, col_close = st.columns([4, 1])
            with col_header:
                st.markdown("### 📁 My Portfolio")
            with col_close:
                if st.button("Close portfolio window", key="close_portfolio", use_container_width=True):
                    st.session_state.show_portfolio = False
                    st.rerun()
            
            user_id = get_current_user_id()
            user_tier = st.session_state.get('tier', 'free')
            
            if user_id:
                portfolio = get_user_portfolio(user_id)
                if portfolio:
                    st.caption(f"**{len(portfolio)}** assets tracked")
                    st.markdown("---")
                    
                    # Fetch full analysis for all portfolio assets (includes crash_warning)
                    with st.spinner("Loading portfolio data..."):
                        import time
                        portfolio_analysis = []
                        fetcher = DataFetcher(cache_enabled=True)
                        failed_tickers = []
                        
                        for i, ticker in enumerate(portfolio):
                            try:
                                # Add small delay between requests to avoid rate limiting
                                if i > 0:
                                    time.sleep(0.5)  # 500ms delay between tickers
                                
                                df = fetcher.fetch_data(ticker)
                                info = fetcher.fetch_info(ticker)
                                if not df.empty and len(df) > MIN_DATA_POINTS:
                                    analyzer = SOCAnalyzer(df, ticker, info, DEFAULT_SMA_WINDOW, DEFAULT_VOL_WINDOW, DEFAULT_HYSTERESIS)
                                    phase = analyzer.get_market_phase()
                                    
                                    # Get full analysis including crash_warning for accurate stress level
                                    try:
                                        full_analysis = analyzer.get_full_analysis()
                                        crash_warning = full_analysis.get('crash_warning', {})
                                        
                                        # Ensure crash_warning has a score
                                        if crash_warning and 'score' in crash_warning:
                                            phase['crash_warning'] = crash_warning
                                        else:
                                            print(f"Warning: {ticker} crash_warning missing score, recalculating...")
                                            # Force recalculation if missing
                                            phase['crash_warning'] = full_analysis.get('crash_warning', {'score': 0})
                                    except Exception as analysis_error:
                                        # Fallback: calculate basic stress if full analysis completely fails
                                        print(f"Full analysis failed for {ticker}: {str(analysis_error)}")
                                        phase['crash_warning'] = {'score': 0}
                                    
                                    phase['name'] = clean_name(info.get('name', ticker))
                                    portfolio_analysis.append(phase)
                                else:
                                    failed_tickers.append(ticker)
                            except Exception as e:
                                failed_tickers.append(ticker)
                                print(f"Error loading {ticker}: {str(e)}")  # Debug log
                        
                        # Show warning/error based on results
                        if failed_tickers and portfolio_analysis:
                            # Some tickers failed, but others loaded successfully
                            st.warning(f"⚠️ Could not load data for: {', '.join(failed_tickers)}")
                        elif failed_tickers and not portfolio_analysis:
                            # All tickers failed
                            st.error(f"""
                            ❌ **Could not load portfolio data**
                            
                            Failed to fetch: {', '.join(failed_tickers)}
                            
                            **Possible reasons:**
                            - Yahoo Finance API rate limiting (try again in 1-2 minutes)
                            - Network connectivity issues
                            - Invalid ticker symbols
                            
                            💡 **Tip:** Try removing and re-adding the assets, or search for them individually first.
                            """)
                    
                    if portfolio_analysis:
                        # Create table data
                        table_data = []
                        for result in portfolio_analysis:
                            table_data.append({
                                "Ticker": result['symbol'],
                                "Asset Name": result.get('name', result['symbol']),
                                "Criticality": int(result.get('criticality_score', 0)),
                                "Regime": result.get('signal', 'Unknown'),
                                "_result": result  # Store full result for actions
                            })
                        
                        # Sort by criticality (highest first)
                        table_data.sort(key=lambda x: x['Criticality'], reverse=True)
                        
                        # Display table
                        for i, row in enumerate(table_data):
                            # Color code criticality
                            crit = row['Criticality']
                            if crit > 80:
                                crit_color = "#FF4040"
                            elif crit > 60:
                                crit_color = "#FF6600"
                            else:
                                crit_color = "#00C864"
                            
                            # Get regime emoji
                            regime_text = row['Regime']
                            regime_emoji = regime_text.split()[0] if regime_text else "⚪"
                            
                            # Row container
                            with st.container():
                                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 1])
                                
                                with col1:
                                    st.markdown(f"**{row['Ticker']}**")
                                
                                with col2:
                                    st.markdown(f"{row['Asset Name']}")
                                
                                with col3:
                                    st.markdown(f"{regime_emoji} <span style='color: {crit_color}; font-weight: 600;'>Criticality: {crit}</span>", unsafe_allow_html=True)
                                
                                with col4:
                                    if st.button("→ Deep Dive", key=f"deepdive_{row['Ticker']}", use_container_width=True):
                                        # Load this asset
                                        st.session_state.current_ticker = row['Ticker']
                                        st.session_state.scan_results = [row['_result']]
                                        st.session_state.selected_asset = 0
                                        st.session_state.analysis_mode = "deep_dive"
                                        st.session_state.show_portfolio = False  # Close portfolio
                                        st.rerun()
                                
                                with col5:
                                    if st.button("🗑️", key=f"remove_{row['Ticker']}", help="Remove from portfolio", use_container_width=True):
                                        from auth_manager import remove_asset_from_portfolio
                                        success, error = remove_asset_from_portfolio(user_id, row['Ticker'])
                                        if success:
                                            st.rerun()
                                        else:
                                            st.error(error)
                                
                                st.markdown("<hr style='margin: 8px 0; opacity: 0.2;'>", unsafe_allow_html=True)
            else:
                st.warning("Please log in to view your portfolio.")
        
        st.markdown("---")
            
    # === TICKER SUGGESTIONS (if user searched by company name) ===
    if 'ticker_suggestions' in st.session_state and st.session_state.ticker_suggestions:
        # Centered info box
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            st.info("🔍 Not a ticker symbol. Did you mean one of these?")
        
        st.markdown("#### Select a ticker:")
        suggestions = st.session_state.ticker_suggestions[:6]  # Max 6 suggestions
        
        num_cols = min(3, len(suggestions))
        cols = st.columns(num_cols)
        
        for i, suggestion in enumerate(suggestions):
            col_idx = i % num_cols
            ticker = suggestion.get('ticker', '') or suggestion.get('symbol', '')  # Handle both keys
            
            # Skip empty tickers
            if not ticker:
                continue
                
            name = suggestion.get('name', ticker)[:25]
            exchange = suggestion.get('exchange', '')
            
            with cols[col_idx]:
                btn_label = f"{ticker}\n{name}"
                if exchange:
                    btn_label += f"\n({exchange})"
                
                if st.button(btn_label, key=f"suggest_{ticker}_{i}", use_container_width=True):
                    # Clear suggestions and analyze this ticker
                    st.session_state.ticker_suggestions = []
                    st.session_state.current_ticker = ticker
                    
                    # Run analysis
                    with st.spinner(f"Analyzing {ticker}..."):
                        try:
                            results = run_analysis([ticker])
                            if results and len(results) > 0:
                                st.session_state.scan_results = results
                                st.session_state.selected_asset = 0
                                st.session_state.analysis_mode = "deep_dive"
                                st.rerun()
                            else:
                                st.error(f"No data available for {ticker}. Try a different exchange variant.")
                        except Exception as e:
                            st.error(f"Error analyzing {ticker}: {str(e)}")
        
        # Clear button
        if st.button("✕ Clear suggestions", key="clear_suggestions"):
            st.session_state.ticker_suggestions = []
            st.rerun()
        
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # === MAIN CONTENT AREA (Dynamic) ===
    if 'scan_results' not in st.session_state or not st.session_state.scan_results:
        # CONDITION A: No Asset Selected - Show Education Landing
        render_education_landing(run_analysis)
    else:
        # CONDITION B: Asset Selected - Show Analysis
        results = st.session_state.scan_results
        
        # === ANALYSIS MODE TABS (all in one row) ===
        col_spacer1, col_tab1, col_tab2, col_spacer2 = st.columns([1, 2, 2, 1])
        
        with col_tab1:
            if st.button(
                "📊 Asset Deep Dive",
                key="btn_deep_dive",
                use_container_width=True
            ):
                st.session_state.analysis_mode = "deep_dive"
                st.rerun()
        
        with col_tab2:
            if st.button(
                "🎯 Portfolio Simulation",
                key="btn_simulation",
                use_container_width=True
            ):
                st.session_state.analysis_mode = "simulation"
                st.rerun()
        
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        # Active asset card removed - hero card is shown in deep dive section instead
        
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        
        # === RENDER SELECTED ANALYSIS ===
        if st.session_state.analysis_mode == "deep_dive":
            # Deep Dive Analysis
            if results:
                selected = results[st.session_state.selected_asset]
                
                # === SPECIMEN HERO CARD (Narrative Engine) ===
                symbol = selected.get('symbol', '')
                name = selected.get('name', symbol)
                full_name = selected.get('info', {}).get('longName', name)
                price = selected.get('price', 0.0)
                change = selected.get('price_change_1d', selected.get('change_pct', 0.0))
                trend = selected.get('trend', 'Unknown')
                criticality = int(selected.get('criticality_score', 0))
                signal = selected.get('signal', 'Unknown')

                is_dark = st.session_state.get('dark_mode', False)
                fetcher = DataFetcher(cache_enabled=True)
                full_history = st.session_state.get('data')
                cached_symbol = st.session_state.get('data_symbol')
                if cached_symbol != symbol or full_history is None or full_history.empty:
                    full_history = fetcher.fetch_data(symbol)
                    st.session_state['data'] = full_history
                    st.session_state['data_symbol'] = symbol

                # Prefer latest regime from history if available for narrative
                regime_for_card = signal or "Unknown"
                if full_history is not None and not full_history.empty:
                    regime_col = next((c for c in ['Regime', 'regime'] if c in full_history.columns), None)
                    if regime_col:
                        reg_series = full_history[regime_col].astype(str)
                        if len(reg_series):
                            regime_for_card = reg_series.iloc[-1]

                # Render hero card with narrative engine (centered at 50% width)
                price_display = f"${price:,.2f}"
                change_display = f"{change:+.2f}%"
                
                col_hero_left, col_hero_center, col_hero_right = st.columns([1, 2, 1])
                with col_hero_center:
                    render_hero_card(
                        ticker=symbol,
                        asset_name=full_name,
                        current_price=price_display,
                        price_change_24h=change_display,
                        score=criticality,
                        regime_raw=regime_for_card,
                        trend=trend
                    )

                # === SOC Chart (Plotly) ===
                if not full_history.empty:
                    analyzer = SOCAnalyzer(full_history, symbol, selected.get('info'))
                    figs = analyzer.get_plotly_figures(dark_mode=is_dark)
                    st.plotly_chart(figs['chart3'], width="stretch")
                    
                    # Advanced analytics (event-based)
                    render_advanced_analytics(full_history, is_dark=is_dark)
                else:
                    st.warning("No data available for this asset.")
        else:
            # Portfolio Simulation (unlimited for all users)
            st.markdown("### DCA Simulation")
            st.markdown("---")
            
            result_tickers = [r['symbol'] for r in results]
            render_dca_simulation(result_tickers)
    
    # === FOOTER WITH LEGAL LINKS ===
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; font-family: 'Merriweather', serif; font-size: 0.85rem; color: #666;">
        <p style="margin: 0 0 12px 0;">© 2025 TECTONIQ. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Legal page buttons (open as modal dialogs)
    col_spacer1, col1, col_sep1, col2, col_sep2, col3, col_spacer2 = st.columns([2, 1, 0.3, 1, 0.3, 1, 2])
    
    with col1:
        if st.button("Disclaimer", key="footer_disclaimer", use_container_width=True):
            show_disclaimer_dialog()
    
    with col_sep1:
        st.markdown("<p style='text-align: center; color: #BDC3C7; margin-top: 8px; font-size: 1.2rem;'>|</p>", unsafe_allow_html=True)
    
    with col2:
        if st.button("Data Protection", key="footer_data_protection", use_container_width=True):
            show_data_protection_dialog()
    
    with col_sep2:
        st.markdown("<p style='text-align: center; color: #BDC3C7; margin-top: 8px; font-size: 1.2rem;'>|</p>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Imprint", key="footer_imprint", use_container_width=True):
            show_imprint_dialog()


if __name__ == "__main__":
    main()
