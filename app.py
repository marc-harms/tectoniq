
"""
SOC Market Seismograph - Streamlit Application
==============================================

Interactive web dashboard for Self-Organized Criticality (SOC) market analysis.

Features:
    - Multi-asset scanning with 5-Tier regime classification
    - Deep dive analysis with historical signal performance
    - Instability Score indicator (0-100)
    - Lump Sum investment simulation with Dynamic Position Sizing
    - Product-Led Growth tiered access (Public / Free / Premium)

Theory:
    Markets exhibit Self-Organized Criticality - they naturally evolve toward
    critical states where small inputs can trigger events of any size.
    This app visualizes market "energy states" through volatility clustering.

Author: Market Analysis Team
Version: 1.2 (PLG Implementation)
"""

# =============================================================================
# IMPORTS
# =============================================================================
import requests
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

from logic import DataFetcher, SOCAnalyzer, run_dca_simulation, calculate_audit_metrics, get_current_market_state, compute_market_state, MarketState
from ui_simulation import render_dca_simulation
from ui_detail import render_detail_panel, render_regime_persistence_chart, render_current_regime_outlook
from ui_auth import render_disclaimer, render_login_dialog, render_signup_dialog, render_education_landing
from ui_portfolio_risk import render_portfolio_risk_view, render_portfolio_input_simple, render_asset_drill_down_header
from hero_card_visual_v2 import render_hero_specimen
from auth_manager import (
    is_authenticated, logout, get_current_user_id, get_current_user_email,
    get_user_portfolio, can_access_simulation, show_upgrade_prompt,
    can_run_simulation, increment_simulation_count, get_user_tier
)
from config import get_scientific_heritage_css, HERITAGE_THEME, REGIME_COLORS
from analytics_engine import MarketForensics


# =============================================================================
# PRODUCT-LED GROWTH: AUTHENTICATION & RATE LIMITING
# =============================================================================

def check_rate_limit(action_type: str, limit_per_hour: int) -> bool:
    """
    Check if user has exceeded rate limit for a specific action.
    
    Uses session state to track action timestamps and enforce hourly limits.
    Automatically cleans up timestamps older than 1 hour.
    
    Args:
        action_type: Action identifier (e.g., 'search', 'simulation')
        limit_per_hour: Maximum allowed actions per hour
    
    Returns:
        True if action is allowed, False if limit exceeded
    """
    # Initialize rate limit tracking
    if 'rate_limits' not in st.session_state:
        st.session_state.rate_limits = {}
    
    if action_type not in st.session_state.rate_limits:
        st.session_state.rate_limits[action_type] = []
    
    # Clean up old timestamps (older than 1 hour)
    current_time = time.time()
    one_hour_ago = current_time - 3600
    st.session_state.rate_limits[action_type] = [
        ts for ts in st.session_state.rate_limits[action_type]
        if ts > one_hour_ago
    ]
    
    # Check if limit exceeded
    action_count = len(st.session_state.rate_limits[action_type])
    return action_count < limit_per_hour


def register_action(action_type: str) -> None:
    """
    Register that an action was performed (for rate limiting).
    
    Args:
        action_type: Action identifier (e.g., 'search', 'simulation')
    """
    if 'rate_limits' not in st.session_state:
        st.session_state.rate_limits = {}
    
    if action_type not in st.session_state.rate_limits:
        st.session_state.rate_limits[action_type] = []
    
    st.session_state.rate_limits[action_type].append(time.time())


def get_remaining_actions(action_type: str, limit_per_hour: int) -> int:
    """Get number of remaining actions in current hour."""
    if 'rate_limits' not in st.session_state:
        return limit_per_hour
    
    if action_type not in st.session_state.rate_limits:
        return limit_per_hour
    
    # Clean old timestamps
    current_time = time.time()
    one_hour_ago = current_time - 3600
    recent_actions = [ts for ts in st.session_state.rate_limits[action_type] if ts > one_hour_ago]
    
    return max(0, limit_per_hour - len(recent_actions))


# Authentication functions moved to auth_manager.py
# Real Supabase authentication is now used (no more demo credentials)
    # Clear rate limits on logout
    if 'rate_limits' in st.session_state:
        st.session_state.rate_limits = {}


def render_sidebar_login() -> None:
    """
    Render login/status sidebar using real Supabase authentication.
    
    Shows login/signup prompts for unauthenticated users, status for authenticated users.
    """
    from auth_manager import is_authenticated, get_current_user_email, logout as auth_logout
    
    with st.sidebar:
        st.markdown("### Account")
        
        if not is_authenticated():
            # Not logged in - show signup/login prompts
            st.markdown("**Welcome!**")
            st.caption("Access all features with a free account")
            
            # Local admin hint
            st.info("**Local Mode:** Login with `admin` / `admin` for full access")
            
            col_login, col_signup = st.columns(2)
            with col_login:
                if st.button("Login", use_container_width=True):
                    st.session_state.show_login_dialog = True
                    st.rerun()
            
            with col_signup:
                if st.button("Sign Up", use_container_width=True):
                    st.session_state.show_signup_dialog = True
                    st.rerun()
            
            st.markdown("---")
            st.markdown("**With a Free Account:**")
            st.caption("✅ Unlimited ticker searches")
            st.caption("✅ Hero Card analysis")
            st.caption("✅ Portfolio watchlist")
            st.caption("✅ 3 simulations/hour")
            
            st.markdown("---")
            st.markdown("**Premium Features:**")
            st.caption("⭐ Deep Dive analysis")
            st.caption("⭐ Unlimited simulations")
            st.caption("⭐ Advanced alerts")
            
        else:
            # Logged in - show user status
            user_email = get_current_user_email()
            tier = st.session_state.get('tier', 'free')
            tier_upper = tier.upper()
            
            if tier == "premium":
                tier_emoji = "⭐"
                tier_color = "#FFD700"
            elif tier == "free":
                tier_emoji = "🆓"
                tier_color = "#27AE60"
            else:
                tier_emoji = "👤"
                tier_color = "#95A5A6"
            
            # Display user info
            st.markdown(f"**{user_email.split('@')[0] if user_email else 'User'}**")
            st.markdown(f"**Tier:** {tier_emoji} <span style='color: {tier_color}; font-weight: 700;'>{tier_upper}</span>", unsafe_allow_html=True)
            
            # Show usage limits
            st.markdown("---")
            st.markdown("**Current Usage:**")
            
            if tier == "free":
                sim_remaining = get_remaining_actions('simulation', 3)
                # Visual indicator for rate limit
                if sim_remaining == 0:
                    st.warning(f"⏱️ **Simulations:** 0/3 per hour\n\n_Resets at top of next hour_")
                elif sim_remaining <= 1:
                    st.info(f"🎯 **Simulations:** {sim_remaining}/3 per hour")
                else:
                    st.success(f"🎯 **Simulations:** {sim_remaining}/3 per hour")
                st.caption(f"🔍 **Searches:** Unlimited")
            else:  # premium
                st.caption("✨ All features unlimited")
            
            # Subscription management for Premium users
            if tier == "premium":
                st.markdown("---")
                st.markdown("**Subscription:**")
                if st.button("Manage Subscription", use_container_width=True):
                    from stripe_manager import create_customer_portal_session
                    from auth_manager import get_stripe_customer_id
                    
                    customer_id = get_stripe_customer_id(get_current_user_id())
                    
                    if customer_id:
                        with st.spinner("Opening subscription portal..."):
                            success, error, portal_url = create_customer_portal_session(customer_id)
                            if success:
                                st.markdown(
                                    f'<meta http-equiv="refresh" content="0; url={portal_url}">',
                                    unsafe_allow_html=True
                                )
                                st.markdown(f"[Manage Subscription →]({portal_url})")
                            else:
                                st.error(f"❌ {error}")
                    else:
                        st.warning("No active subscription found")
            
            # Logout button
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                auth_logout()
                st.success("Logged out successfully!")
                st.rerun()
            
            # Upgrade prompt for non-premium
            if tier != "premium":
                st.markdown("---")
                st.markdown("### Upgrade to Premium")
                st.markdown("**$29/month** - Cancel anytime")
                st.caption("✅ Deep Dive charts & analytics")
                st.caption("✅ Unlimited simulations")
                st.caption("✅ Monte Carlo forecasting")
                
                if st.button("Upgrade Now", use_container_width=True):
                    from stripe_manager import create_checkout_session
                    
                    user_id = get_current_user_id()
                    user_email = get_current_user_email()
                    
                    if user_id and user_email:
                        with st.spinner("🔄 Redirecting to secure checkout..."):
                            success, error, checkout_url = create_checkout_session(user_email, user_id)
                            
                            if success:
                                st.success("✅ Redirecting to Stripe Checkout...")
                                # Use JavaScript redirect for better UX
                                st.markdown(
                                    f'<meta http-equiv="refresh" content="0; url={checkout_url}">',
                                    unsafe_allow_html=True
                                )
                                st.markdown(f"[Click here if not redirected automatically]({checkout_url})")
                            else:
                                st.error(f"❌ {error}")
                    else:
                        st.error("Please log in first to upgrade")


def show_upgrade_dialog(feature_name: str, tier: str):
    """
    Show upgrade dialog for gated features.
    
    Args:
        feature_name: Name of the locked feature
        tier: Current user tier
    """
    from auth_manager import is_authenticated
    
    st.warning(f"🔒 **{feature_name}** requires a higher tier.")
    
    if not is_authenticated():
        st.markdown("""
        **Create a Free account to unlock:**
        - ✅ Unlimited ticker searches
        - ✅ Basic Hero Card analysis  
        - ✅ 3 simulations per hour
        """)
        
        if st.button("Sign Up Now", use_container_width=True):
            st.session_state.show_signup_dialog = True
            st.rerun()
            
    elif tier == "free":
        st.markdown("""
        **Upgrade to Premium to unlock:**
        - ✅ Full Deep Dive analysis with charts
        - ✅ Unlimited simulations
        - ✅ Monte Carlo forecasting
        - ✅ Advanced crash detection
        
        **Only $29/month** - Cancel anytime
        """)
        
        if st.button("Upgrade to Premium", use_container_width=True):
            from stripe_manager import create_checkout_session
            
            user_id = get_current_user_id()
            user_email = get_current_user_email()
            
            if user_id and user_email:
                with st.spinner("🔄 Redirecting to secure checkout..."):
                    success, error, checkout_url = create_checkout_session(user_email, user_id)
                    
                    if success:
                        st.success("✅ Redirecting to Stripe Checkout...")
                        st.markdown(
                            f'<meta http-equiv="refresh" content="0; url={checkout_url}">',
                            unsafe_allow_html=True
                        )
                        st.markdown(f"[Click here if not redirected]({checkout_url})")
                    else:
                        st.error(f"❌ {error}")
            else:
                st.error("Session expired. Please log in again")


# =============================================================================
# SCIENTIFIC MASTHEAD HEADER
# =============================================================================

def render_header(validate_ticker_func, search_ticker_func, run_analysis_func):
    """
    Render journal-style header with three-zone hierarchy.
    
    ZONE 1: System Context Bar (thin, muted, quiet)
    ZONE 2: Brand & Purpose (centered, no buttons, generous spacing)
    ZONE 3: Workflow Controls (navigation left, actions right)
    
    Phase 3.2: Clean, authoritative, calm information architecture.
    """
    from datetime import datetime
    
    # ==========================================================================
    # ZONE 1: SYSTEM CONTEXT BAR (Quietly establish context)
    # ==========================================================================
    
    system_bar_css = """
    <style>
        .system-context-bar {
            background-color: #FAFAFA;
            border-bottom: 1px solid #E0E0E0;
            padding: 0.5rem 0;
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            color: #6B6B6B;
        }
        .system-context-content {
            max-width: 900px;
            margin: 0 auto;
            padding: 0 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .system-context-right {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        .context-item {
            color: #6B6B6B;
            font-weight: 400;
        }
        .status-indicator {
            width: 6px;
            height: 6px;
            background-color: #4a7c59;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.25rem;
        }
    </style>
    """
    
    # Get current date and tier
    current_date = datetime.now().strftime("%B %d, %Y")
    tier = get_user_tier()
    
    # Tier label (neutral, minimal)
    tier_labels = {"premium": "Premium", "free": "Free", "public": "Public"}
    tier_label = tier_labels.get(tier, "Public")
    
    system_bar_html = f"""
    {system_bar_css}
    <div class="system-context-bar">
        <div class="system-context-content">
            <div class="system-context-left">
                <span class="context-item">Data as of {current_date}</span>
            </div>
            <div class="system-context-right">
                <span class="context-item">
                    <span class="status-indicator"></span>ONLINE
                </span>
                <span class="context-item">{tier_label}</span>
            </div>
        </div>
    </div>
    """
    
    st.markdown(system_bar_html, unsafe_allow_html=True)
    
    # Add News link as inline button (minimal styling)
    st.markdown("""
    <style>
        div[data-testid="column"]:has(button[key="inline_news_btn"]) {
            position: absolute;
            top: 0.45rem;
            right: 1.5rem;
            z-index: 1000;
        }
        button[key="inline_news_btn"] {
            background: none !important;
            border: none !important;
            color: #5a6c7d !important;
            font-size: 0.75rem !important;
            padding: 0 !important;
            font-weight: 500 !important;
            box-shadow: none !important;
        }
        button[key="inline_news_btn"]:hover {
            text-decoration: underline !important;
            background: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Invisible column container for positioning
    _news_col = st.columns([1])
    with _news_col[0]:
        if st.button("News", key="inline_news_btn"):
            show_news_dialog()
    
    # ==========================================================================
    # ZONE 2: BRAND & PURPOSE (Centered, no buttons, journal-style)
    # ==========================================================================
    
    brand_header_css = """
    <style>
        .brand-header {
            text-align: center;
            padding: 2.5rem 0 2rem 0;
            background-color: #FFFFFF;
        }
        .brand-title {
            font-family: 'Libre Baskerville', 'Georgia', serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: #2B2B2B;
            margin: 0 0 0.5rem 0;
            letter-spacing: 0.1em;
        }
        .brand-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            color: #6B6B6B;
            margin: 0 0 1.5rem 0;
            font-weight: 400;
        }
        .brand-divider {
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
            border: none;
            height: 1px;
            background: linear-gradient(
                to right,
                transparent 0%,
                rgba(0,0,0,0.12) 10%,
                rgba(0,0,0,0.12) 90%,
                transparent 100%
            );
            opacity: 0.6;
        }
    </style>
    """
    
    brand_header_html = """
    <div class="brand-header">
        <div class="brand-title">TECTONIQ</div>
        <div class="brand-subtitle">Algorithmic Market Forensics</div>
        <div class="brand-divider"></div>
    </div>
    """
    
    st.markdown(brand_header_css + brand_header_html, unsafe_allow_html=True)
    
    # ==========================================================================
    # ZONE 3: UTILITY BUTTONS (Simplified - only for authenticated users)
    # ==========================================================================
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Only show Portfolio Analysis button for authenticated users
    from auth_manager import is_authenticated
    
    if is_authenticated():
        # Center the button
        col_spacer_left, col_button, col_spacer_right = st.columns([1, 2, 1])
        
        with col_button:
            # Add custom CSS for reduced button size
            st.markdown("""
            <style>
                button[key="header_btn_portfolio"] {
                    max-width: 75% !important;
                    padding: 0.25rem 0.625rem !important;
                    margin: 0 auto !important;
                    display: block !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            if st.button("Portfolio Analysis", key="header_btn_portfolio", use_container_width=False):
                st.session_state.view_mode = "portfolio"
                st.rerun()
    
    # ==========================================================================
    # TICKER SEARCH (Below buttons)
    # ==========================================================================
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    col_spacer1, col_search, col_spacer2 = st.columns([1, 2, 1])
    
    with col_search:
        # Clear search field if asset is already selected
        has_active_asset = 'scan_results' in st.session_state and st.session_state.scan_results
        if has_active_asset and 'header_search' in st.session_state and st.session_state.header_search:
            st.session_state.header_search = ""
        
        # Dynamic placeholder
        placeholder_text = "Search another asset (ticker or company name)" if has_active_asset else "Enter ticker symbol or company name (e.g., AAPL, Apple, Tesla)"
        
        # Search field with on_change callback
        search_query = st.text_input(
            "Search Asset",
            placeholder=placeholder_text,
            label_visibility="collapsed",
            key="header_search",
            on_change=lambda: handle_header_search(
                st.session_state.get('header_search', ''),
                validate_ticker_func,
                search_ticker_func,
                run_analysis_func
            )
        )
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)


def handle_header_search(query: str, validate_func, search_func, analyze_func):
    """
    Handle search from header - accepts ticker symbols OR company names.
    
    Flow:
    1. Try as direct ticker symbol
    2. If invalid, search by company name
    3. Show suggestions if multiple matches found
    
    Rate Limits:
    - Public: 2 searches per hour
    - Free/Premium: Unlimited
    """
    if not query or len(query.strip()) == 0:
        return
    
    # PLG: Check rate limit for public tier
    tier = get_user_tier()
    
    if tier == "public":
        if not check_rate_limit('search', 2):
            st.error("Search Limit Reached (2 per hour for unauthenticated users)")
            if st.button("Sign Up for Free - Unlimited Searches", use_container_width=True):
                st.session_state.show_signup_dialog = True
                st.rerun()
            return
    
    # Register the search action
    if tier == "public":
        register_action('search')
    
    ticker_input = query.strip().upper()
    
    try:
        # First, try as direct ticker symbol
        validation = validate_func(ticker_input)
        
        if validation.get('valid'):
            # Valid ticker - analyze it directly
            results = analyze_func([ticker_input])
            if results and len(results) > 0:
                st.session_state.current_ticker = ticker_input
                st.session_state.scan_results = results
                st.session_state.selected_asset = 0
                st.session_state.analysis_mode = "deep_dive"
                st.session_state.view_mode = "asset"  # Switch to asset view
                st.session_state.header_search = ""  # Clear search field
                st.rerun()
        else:
            # Not a valid ticker - try searching by company name
            search_results = search_func(ticker_input)
            if search_results:
                # Found matches - store for selection
                st.session_state.ticker_suggestions = search_results
                st.session_state.header_search = ""  # Clear search field
                st.rerun()
            else:
                st.error(f"Could not find '{ticker_input}'. Try a different search term.")
    except Exception as e:
        st.error(f"Search error: {str(e)}")


# =============================================================================
# HERO CARD (Specimen Style)
# =============================================================================
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import textwrap

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
    
    # Display Statistical Report & Signal Audit (no expander - always visible)
    st.markdown("### Statistical Report & Signal Audit")
    st.markdown("<hr style='border: 1px solid #D1C4E9;'>", unsafe_allow_html=True)
    
    # Slightly reduce metric value font size to avoid truncation
    st.markdown(
        "<style>div[data-testid='stMetricValue'] { font-size: 1.05rem !important; }</style>",
        unsafe_allow_html=True
    )
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown("### Regime Profile")
        st.dataframe(regime_table, use_container_width=True)
    
    with col2:
        st.markdown("### Protection")
        st.metric("True Crashes", crash_metrics['total_crashes_5y'], delta=f"{crash_metrics['detected_count']} detected")
        st.metric(
            "Detection Rate",
            f"{crash_metrics['detection_rate']:.0f}%",
            help="Percentage of crashes (>20% drop) successfully flagged in advance."
        )
    
    with col3:
        st.markdown("### Quality")
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
        st.markdown("### Timing")
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
# GLOBAL SCIENTIFIC HERITAGE TYPOGRAPHY
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&family=Roboto:wght@300;400;500;700&display=swap');
    
    /* Global Background - Paper Texture */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #F9F7F1 !important;
    }
    
    /* Headers - Merriweather Serif (Scientific Publication Style) */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Merriweather', serif !important;
        color: #2C3E50 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }
    
    /* Body Text - Roboto Sans-Serif (Clean, Readable) */
    p, div, span, label, .stMarkdown {
        font-family: 'Roboto', sans-serif !important;
        color: #333333 !important;
    }
    
    /* Dropdown/Select Text - Ensure Visibility */
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[role="listbox"] span,
    div[role="option"] span,
    div[data-baseweb="select"] > div {
        color: #333333 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Data Tables - Monospace for Numbers */
    .stDataFrame, table {
        font-family: 'Roboto Mono', monospace !important;
    }
    
    /* Metric Labels - Merriweather */
    [data-testid="stMetricLabel"] {
        font-family: 'Merriweather', serif !important;
        color: #555555 !important;
    }
    
    /* Metric Values - Roboto Mono */
    [data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace !important;
        color: #2C3E50 !important;
    }
    
    /* Buttons - Merriweather for elegance */
    button {
        font-family: 'Merriweather', serif !important;
    }
</style>
""", unsafe_allow_html=True)

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


def render_monte_carlo_simulation(ticker_symbol: str, current_price: float, current_vola: float, regime_obj: dict) -> None:
    """
    Render interactive Monte Carlo forecast simulation.
    
    Shows probabilistic price paths based on current market regime.
    
    Args:
        ticker_symbol: Asset ticker (e.g., "BTC-USD")
        current_price: Current asset price
        current_vola: Historical volatility (daily)
        regime_obj: Dict with 'name' and 'color' keys
    """
    import analytics_engine as ae
    
    st.markdown("### 🔮 Tectonic Forecast Engine (Experimental)")
    st.caption("Monte Carlo projection based on current regime physics")
    
    # Get dark mode setting
    is_dark = st.session_state.get('dark_mode', False)
    
    # Thematic spinner
    with st.spinner(f"Calibrating Monte Carlo Engine for {ticker_symbol}... Applying {regime_obj.get('name', 'STABLE')} physics..."):
        
        # 1. Run simulation (returns quantiles + sample paths for texture)
        sim_data, sample_paths = ae.run_monte_carlo_simulation(
            start_price=current_price,
            hist_vola=current_vola,
            regime_obj=regime_obj,
            days=30,
            runs=1000
        )
        
        # 2. Draw chart with sample paths for texture
        fig = ae.plot_forecast(
            sim_data, 
            regime_obj.get('color', '#667eea'), 
            sample_paths=sample_paths,
            is_dark=is_dark
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Calculate key metrics
        start_p = sim_data['p50'].iloc[0]
        end_median = sim_data['p50'].iloc[-1]
        end_worst = sim_data['p05'].iloc[-1]
        
        exp_move = (end_median - start_p) / start_p
        risk_move = (end_worst - start_p) / start_p
        
        # 4. Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Expected Drift (30d)", 
                f"{exp_move:+.2%}",
                help="The median outcome of 1,000 simulated paths."
            )
        with col2:
            st.metric(
                "Worst Case Risk (95% VaR)", 
                f"{risk_move:+.2%}",
                help="In 5% of scenarios, the price drops lower than this."
            )
            # Visual warning for high downside risk
            if risk_move < -0.10:
                st.caption(f"⚠️ High Downside Risk detected by {regime_obj.get('name', 'UNKNOWN')} parameters.")
    
    # Footnote
    st.caption(f"Simulation based on **{regime_obj.get('name', 'STABLE')}** parameters: Volatility Multiplier & Shock Probability applied.")


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
        status.caption(f"⚡ Calibrating seismic analysis for {symbol}...")
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
    
    **Limitation of Liabilities:**
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
    Havelweg 12
    Moers, 47445 
    Germany
    
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


@st.dialog("System Updates", width="large")
def show_news_dialog():
    """Show system updates in a modal dialog with journal styling."""
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
# PHASE 3: ASSET ANALYSIS VIEW (SECONDARY)
# =============================================================================

def render_asset_analysis_view(ticker_symbol: str) -> None:
    """
    Render asset analysis for a specific ticker (Phase 3: SECONDARY VIEW).
    
    This is the asset drill-down view - informational only.
    Portfolio is the primary product.
    
    Args:
        ticker_symbol: Asset ticker to analyze
    """
    from logic import DataFetcher
    
    # Asset view header (informational only label)
    render_asset_drill_down_header()
    
    st.markdown(f"## {ticker_symbol}")
    
    tier = get_user_tier()
    is_dark = st.session_state.get('dark_mode', False)
    
    # Fetch data
    fetcher = DataFetcher(cache_enabled=True)
    
    with st.spinner(f"Loading data for {ticker_symbol}..."):
        try:
            df = fetcher.fetch_data(ticker_symbol)
            
            if df is None or df.empty:
                st.error(f"No data available for {ticker_symbol}")
                return
            
            # Get current market state
            current_state = get_current_market_state(df, strategy_mode="defensive")
            
            # Get basic info
            price = df['close'].iloc[-1] if 'close' in df.columns else 0.0
            change = ((df['close'].iloc[-1] / df['close'].iloc[-2]) - 1) * 100 if len(df) >= 2 else 0.0
            
            criticality = current_state.get('criticality_score', 0)
            trend = current_state.get('trend_signal', 'Unknown')
            is_invested = current_state.get('is_invested', True)
            vol_percentile = current_state.get('raw_data', {}).get('volatility', 0) * 100
            
            # Render hero card (simplified - no fancy regime names)
            st.markdown("### Current State")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Price", f"${price:.2f}", f"{change:+.2f}%")
            
            with col2:
                regime_color = "#27ae60" if criticality < 40 else "#f39c12" if criticality < 70 else "#e74c3c"
                regime_label = "STABLE" if criticality < 40 else "ELEVATED" if criticality < 70 else "CRITICAL"
                st.markdown(f"**Regime:** <span style='color: {regime_color}; font-weight: 700;'>{regime_label}</span>", unsafe_allow_html=True)
            
            with col3:
                st.metric("Criticality", f"{int(criticality)}/100")
            
            st.markdown("---")
            
            # Premium: Show charts
            if tier == "premium":
                st.markdown("### Historical Analysis")
                
                analyzer = SOCAnalyzer(df, ticker_symbol, {})
                figs = analyzer.get_plotly_figures(dark_mode=is_dark)
                st.plotly_chart(figs['chart3'], use_container_width=True)
                
                # Advanced analytics
                render_advanced_analytics(df, is_dark=is_dark)
                
            else:
                # Free/Public: Upgrade prompt
                st.info("🔒 **Historical charts and advanced analytics** require Premium")
                show_upgrade_dialog("Asset Analysis", tier)
                
        except Exception as e:
            st.error(f"Error loading asset data: {str(e)}")
            import traceback
            st.caption(f"```\n{traceback.format_exc()}\n```")


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """
    Main application entry point - Product-Led Growth Edition.
    
    Flow:
        1. Show legal disclaimer (must accept to continue)
        2. Initialize PLG session state (tier, rate limits)
        3. Render sidebar login/status
        4. Apply theme CSS
        5. Render header (with search)
        6. Main content area (with tier-based gating):
           - Search: Public limited (2/hr), Free/Premium unlimited
           - Hero Card: All tiers (if search allowed)
           - Deep Dive: Premium only (soft gate for Public/Free)
           - Simulation: Public locked, Free limited (3/hr), Premium unlimited
    """
    from auth_manager import is_authenticated, get_current_user_id
    
    # Session state initialization
    if 'disclaimer_accepted' not in st.session_state:
        st.session_state.disclaimer_accepted = True  # Auto-accept for local use
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False  # Light mode default
    if 'selected_asset' not in st.session_state:
        st.session_state.selected_asset = 0
    if 'analysis_mode' not in st.session_state:
        st.session_state.analysis_mode = "deep_dive"
    if 'current_ticker' not in st.session_state:
        st.session_state.current_ticker = None
    if 'show_login_dialog' not in st.session_state:
        st.session_state.show_login_dialog = False
    if 'show_signup_dialog' not in st.session_state:
        st.session_state.show_signup_dialog = False
    
    # Phase 3: Portfolio-first view mode
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "portfolio"  # Default to portfolio view
    
    # Initialize tier based on authentication status
    if is_authenticated():
        # User is logged in - tier comes from Supabase profile
        if 'tier' not in st.session_state:
            st.session_state.tier = "free"  # Default, will be loaded from profile
    else:
        # Not logged in
        st.session_state.tier = "public"
    
    # Handle payment redirect (success/cancel)
    query_params = st.query_params
    if "payment" in query_params:
        payment_status = query_params["payment"]
        
        if payment_status == "success" and is_authenticated():
            # Reload user tier from database (webhook should have updated it)
            from auth_manager import get_supabase_client
            try:
                user_id = get_current_user_id()
                if user_id:
                    supabase = get_supabase_client()
                    response = supabase.table('profiles').select('subscription_tier').eq('user_id', user_id).single().execute()
                    if response.data:
                        new_tier = response.data.get('subscription_tier', 'free')
                        st.session_state.tier = new_tier
                        
                        if new_tier == 'premium':
                            st.success("🎉 **Welcome to Premium!** All features unlocked.")
                        else:
                            st.warning("⏳ Payment processing... Your upgrade will be activated shortly.")
            except Exception as e:
                print(f"Error reloading tier: {e}")
            
            # Clear query params
            st.query_params.clear()
        
        elif payment_status == "cancelled":
            st.info("ℹ️ Payment cancelled. You can upgrade anytime from the sidebar.")
            st.query_params.clear()
    
    # Apply Scientific Heritage CSS theme FIRST (before any page)
    st.markdown(get_scientific_heritage_css(), unsafe_allow_html=True)
    
    # Legal disclaimer gate (must accept before anything else)
    if not st.session_state.disclaimer_accepted:
        render_disclaimer()
        return
    
    # Trigger auth dialogs if requested
    if st.session_state.get('show_login_dialog', False):
        render_login_dialog()
    
    if st.session_state.get('show_signup_dialog', False):
        render_signup_dialog()
    
    # PLG: Render sidebar login/status
    render_sidebar_login()
    
    # Apply Scientific Heritage CSS theme
    st.markdown(get_scientific_heritage_css(), unsafe_allow_html=True)
    
    # Handle refresh from vitals bar
    if st.session_state.get('trigger_refresh', False):
        st.cache_data.clear()
        if 'data' in st.session_state:
            del st.session_state['data']
        if 'scan_results' in st.session_state:
            del st.session_state['scan_results']
        st.session_state.trigger_refresh = False
        st.rerun()
    
    # === SCIENTIFIC MASTHEAD (Journal-style Header) ===
    # Get user tier for display
    tier = get_user_tier()
    username = st.session_state.get('username', 'Public')
    
    render_header(validate_ticker, search_ticker, run_analysis)
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # === CHECK AUTHENTICATION FOR MAIN CONTENT ===
    from auth_manager import is_authenticated
    
    # If user is NOT logged in, show minimal interface
    if not is_authenticated():
        # Only show ticker suggestions and asset results (if any)
        # TICKER SUGGESTIONS (if user searched by company name)
        if 'ticker_suggestions' in st.session_state and st.session_state.ticker_suggestions:
            col_left, col_center, col_right = st.columns([1, 2, 1])
            with col_center:
                st.info("Not a ticker symbol. Did you mean one of these?")
            
            st.markdown("#### Select a ticker:")
            suggestions = st.session_state.ticker_suggestions[:6]
            
            num_cols = min(3, len(suggestions))
            cols = st.columns(num_cols)
            
            for i, suggestion in enumerate(suggestions):
                col_idx = i % num_cols
                ticker = suggestion.get('ticker', '') or suggestion.get('symbol', '')
                
                if not ticker:
                    continue
                    
                name = suggestion.get('name', ticker)[:25]
                exchange = suggestion.get('exchange', '')
                
                with cols[col_idx]:
                    btn_label = f"{ticker}\n{name}"
                    if exchange:
                        btn_label += f"\n({exchange})"
                    
                    if st.button(btn_label, key=f"suggest_{ticker}_{i}", use_container_width=True):
                        st.session_state.ticker_suggestions = []
                        st.session_state.current_ticker = ticker
                        
                        with st.spinner(f"Analyzing {ticker}..."):
                            try:
                                results = run_analysis([ticker])
                                if results and len(results) > 0:
                                    st.session_state.scan_results = results
                                    st.session_state.selected_asset = 0
                                    st.session_state.view_mode = "asset"
                                    st.rerun()
                                else:
                                    st.error(f"No data available for {ticker}.")
                            except Exception as e:
                                st.error(f"Error analyzing {ticker}: {str(e)}")
            
            if st.button("Clear suggestions", key="clear_suggestions"):
                st.session_state.ticker_suggestions = []
                st.rerun()
        
        # SHOW ASSET RESULTS (if available)
        if 'scan_results' in st.session_state and st.session_state.scan_results:
            results = st.session_state.scan_results
            if results and len(results) > 0:
                result = results[st.session_state.get('selected_asset', 0)]
                
                # Display current asset state with hero card layout
                st.markdown("---")
                
                # Get asset data
                asset_name = result.get('name', result['symbol'])
                ticker = result['symbol']
                regime_text = result.get('signal', 'UNKNOWN')
                criticality = result.get('criticality_score', 0)
                
                # Get color based on criticality
                if criticality >= 70:
                    regime_color = "#FF6600"  # Red
                    regime_bg = "rgba(255, 102, 0, 0.1)"
                elif criticality >= 40:
                    regime_color = "#FFB800"  # Yellow
                    regime_bg = "rgba(255, 184, 0, 0.1)"
                else:
                    regime_color = "#00C864"  # Green
                    regime_bg = "rgba(0, 200, 100, 0.1)"
                
                # Hero card HTML
                hero_card_html = f"""
                <style>
                    .asset-hero-card {{
                        max-width: 700px;
                        margin: 2rem auto;
                        border: 1px solid #E0E0E0;
                        border-radius: 4px;
                        background-color: #FFFFFF;
                        padding: 2rem;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                    }}
                    .hero-top-row {{
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                        margin-bottom: 2rem;
                    }}
                    .hero-left {{
                        flex: 1;
                    }}
                    .hero-asset-name {{
                        font-family: 'Libre Baskerville', serif;
                        font-size: 1.75rem;
                        font-weight: 700;
                        color: #2B2B2B;
                        margin: 0 0 0.25rem 0;
                    }}
                    .hero-ticker {{
                        font-family: 'Inter', sans-serif;
                        font-size: 0.875rem;
                        color: #6B6B6B;
                        font-weight: 500;
                        letter-spacing: 0.05em;
                    }}
                    .hero-right {{
                        text-align: right;
                    }}
                    .hero-criticality-label {{
                        font-family: 'Inter', sans-serif;
                        font-size: 0.75rem;
                        color: #6B6B6B;
                        text-transform: uppercase;
                        letter-spacing: 0.1em;
                        margin-bottom: 0.25rem;
                    }}
                    .hero-criticality-value {{
                        font-family: 'Inter', sans-serif;
                        font-size: 2rem;
                        font-weight: 700;
                        color: #2B2B2B;
                    }}
                    .hero-criticality-max {{
                        font-size: 1rem;
                        color: #6B6B6B;
                        font-weight: 400;
                    }}
                    .hero-regime-bar {{
                        background-color: {regime_bg};
                        border-left: 4px solid {regime_color};
                        padding: 1rem 1.5rem;
                        text-align: center;
                        border-radius: 2px;
                    }}
                    .hero-regime-label {{
                        font-family: 'Inter', sans-serif;
                        font-size: 0.75rem;
                        color: #6B6B6B;
                        text-transform: uppercase;
                        letter-spacing: 0.1em;
                        margin-bottom: 0.5rem;
                    }}
                    .hero-regime-value {{
                        font-family: 'Libre Baskerville', serif;
                        font-size: 1.5rem;
                        font-weight: 700;
                        color: {regime_color};
                    }}
                    .hero-cta {{
                        text-align: center;
                        margin-top: 1.5rem;
                        font-family: 'Inter', sans-serif;
                        font-size: 0.875rem;
                        color: #6B6B6B;
                        font-style: italic;
                    }}
                </style>
                
                <div class="asset-hero-card">
                    <div class="hero-top-row">
                        <div class="hero-left">
                            <div class="hero-asset-name">{asset_name}</div>
                            <div class="hero-ticker">{ticker}</div>
                        </div>
                        <div class="hero-right">
                            <div class="hero-criticality-label">Criticality</div>
                            <div class="hero-criticality-value">
                                {criticality}<span class="hero-criticality-max"> / 100</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="hero-regime-bar">
                        <div class="hero-regime-label">Regime Status</div>
                        <div class="hero-regime-value">{regime_text}</div>
                    </div>
                    
                    <div class="hero-cta">
                        Sign up for free to access full analysis and portfolio tracking
                    </div>
                </div>
                """
                
                st.markdown(hero_card_html, unsafe_allow_html=True)
        
        # Skip to footer for public users
        st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; font-family: 'Merriweather', serif; font-size: 0.85rem; color: #666;">
            <p style="margin: 0 0 12px 0;">© 2025 TECTONIQ. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Footer buttons
        st.markdown("""
        <style>
            button[key="footer_disclaimer"],
            button[key="footer_data_protection"],
            button[key="footer_imprint"] {
                max-width: 75% !important;
                padding: 0.25rem 0.625rem !important;
                margin: 0 auto !important;
                display: block !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        col_spacer1, col1, col_sep1, col2, col_sep2, col3, col_spacer2 = st.columns([2, 1, 0.3, 1, 0.3, 1, 2])
        
        with col1:
            if st.button("Disclaimer", key="footer_disclaimer", use_container_width=False):
                show_disclaimer_dialog()
        
        with col_sep1:
            st.markdown("<p style='text-align: center; color: #BDC3C7; margin-top: 8px; font-size: 1.2rem;'>|</p>", unsafe_allow_html=True)
        
        with col2:
            if st.button("Data Protection", key="footer_data_protection", use_container_width=False):
                show_data_protection_dialog()
        
        with col_sep2:
            st.markdown("<p style='text-align: center; color: #BDC3C7; margin-top: 8px; font-size: 1.2rem;'>|</p>", unsafe_allow_html=True)
        
        with col3:
            if st.button("Imprint", key="footer_imprint", use_container_width=False):
                show_imprint_dialog()
        
        # Stop rendering here for public users
        return
    
    # === AUTHENTICATED USERS: FULL CONTENT ===
    
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
            tier = get_user_tier()
            
            if user_id:
                portfolio = get_user_portfolio(user_id)
                if portfolio:
                    st.caption(f"**{len(portfolio)}** assets tracked")
                    st.markdown("---")
                    
                    # Fetch full analysis for all portfolio assets (includes crash_warning)
                    with st.spinner("🌊 Acquiring seismic market data stream... Analyzing structural stress patterns..."):
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
                                    if st.button("Deep Dive", key=f"deepdive_{row['Ticker']}", use_container_width=True):
                                        # Load this asset
                                        st.session_state.current_ticker = row['Ticker']
                                        st.session_state.scan_results = [row['_result']]
                                        st.session_state.selected_asset = 0
                                        st.session_state.analysis_mode = "deep_dive"
                                        st.session_state.show_portfolio = False  # Close portfolio
                                        st.rerun()
                                
                                with col5:
                                    if st.button("Remove", key=f"remove_{row['Ticker']}", help="Remove from portfolio", use_container_width=True):
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
                    with st.spinner(f"🔬 Calibrating Self-Organized Criticality engine for {ticker}... Detecting phase transitions..."):
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
        if st.button("Clear suggestions", key="clear_suggestions"):
            st.session_state.ticker_suggestions = []
            st.rerun()
        
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # === MAIN CONTENT AREA (Dynamic) ===
    
    # Phase 3: Portfolio-First UX
    # Default view is PORTFOLIO, assets are opt-in secondary
    
    if st.session_state.view_mode == "portfolio":
        # === PORTFOLIO VIEW (DEFAULT) ===
        st.markdown("# Portfolio Risk Mirror")
        st.caption("Real-time structural risk assessment")
        
        st.markdown("---")
        
        # Portfolio input/configuration
        user_portfolio = render_portfolio_input_simple()
        
        if user_portfolio:
            # Render portfolio risk view (3-layer hierarchy)
            render_portfolio_risk_view(user_portfolio)
            
            # Button to drill down into selected asset
            if 'drill_down_asset' in st.session_state and st.session_state.drill_down_asset:
                st.markdown("---")
                if st.button(f"View Detailed Analysis for {st.session_state.drill_down_asset}", 
                           use_container_width=True, type="secondary"):
                    # Switch to asset view for selected asset
                    st.session_state.view_mode = "asset"
                    st.session_state.current_ticker = st.session_state.drill_down_asset
                    st.rerun()
        
    elif st.session_state.view_mode == "asset":
        # === ASSET VIEW (SECONDARY/OPT-IN) ===
        render_asset_drill_down_header()
        
        # Back to portfolio button
        if st.button("Back to Portfolio", key="back_to_portfolio"):
            st.session_state.view_mode = "portfolio"
            st.rerun()
        
        # Show asset analysis if ticker is set
        if st.session_state.current_ticker:
            # Render existing asset analysis (preserved from Phase 2)
            render_asset_analysis_view(st.session_state.current_ticker)
        else:
            st.info("No asset selected. Return to portfolio view.")
            
    # Legacy: Maintain compatibility with old flow
    elif 'scan_results' not in st.session_state or not st.session_state.scan_results:
        # CONDITION A: No Asset Selected - Show Education Landing
        render_education_landing(run_analysis)
    else:
        # CONDITION B: Asset Selected - Show Analysis
        results = st.session_state.scan_results
        
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

                is_dark = st.session_state.get('dark_mode', False)
                fetcher = DataFetcher(cache_enabled=True)
                full_history = st.session_state.get('data')
                cached_symbol = st.session_state.get('data_symbol')
                if cached_symbol != symbol or full_history is None or full_history.empty:
                    full_history = fetcher.fetch_data(symbol)
                    st.session_state['data'] = full_history
                    st.session_state['data_symbol'] = symbol

                # === GET CURRENT MARKET STATE (matches backtest tail) ===
                # This ensures Hero Card visually matches the end of the performance chart
                current_state = get_current_market_state(full_history, strategy_mode="defensive")
                
                # Map state to visual theme
                is_invested = current_state.get('is_invested', True)
                criticality = current_state.get('criticality_score', 0)
                trend = current_state.get('trend_signal', 'Unknown')
                
                # Determine regime display based on investment state and criticality
                if not is_invested:
                    # Algorithm has decoupled - show PROTECTIVE STASIS
                    regime_for_card = "PROTECTIVE STASIS"
                elif criticality > 80:
                    # High criticality while invested
                    regime_for_card = "CRITICAL"
                elif criticality > 60:
                    # Medium criticality
                    regime_for_card = "HIGH ENERGY"
                else:
                    # Low criticality - stable growth
                    regime_for_card = "STABLE GROWTH"

                # Render NEW trading card style hero card (centered at 50% width)
                price_display = f"${price:,.2f}"
                change_display = f"{change:+.2f}%"
                
                # Get volatility percentile from current state for accurate regime classification
                vol_percentile = current_state.get('raw_data', {}).get('volatility', 0) * 100
                
                # Render with new trading card style
                render_hero_specimen(
                        ticker=symbol,
                        asset_name=full_name,
                        current_price=price_display,
                        price_change_24h=change_display,
                    criticality=int(criticality),
                    trend=trend,
                    is_invested=is_invested,
                    volatility_percentile=vol_percentile
                    )

                # === SOC Chart (Plotly) - PREMIUM FEATURE ===
                tier = get_user_tier()
                
                if tier == "premium":
                    # Premium: Full access to charts and analytics
                    if not full_history.empty:
                        analyzer = SOCAnalyzer(full_history, symbol, selected.get('info'))
                        figs = analyzer.get_plotly_figures(dark_mode=is_dark)
                        st.plotly_chart(figs['chart3'], width="stretch")
                        
                        # Advanced analytics (event-based)
                        render_advanced_analytics(full_history, is_dark=is_dark)
                        
                        # === MONTE CARLO FORECAST ===
                        st.markdown("---")
                        
                        # Get current volatility from the market state (same as used in Hero Card)
                        # This is the rolling 30-day volatility already calculated by get_current_market_state
                        current_vola = current_state.get('raw_data', {}).get('volatility', 0.02)
                        
                        # Ensure it's a valid float
                        if current_vola is None or current_vola == 0:
                            current_vola = 0.02  # Default to 2% if missing or zero
                        
                        # Prepare regime object from current state
                        regime_name = current_state.get('regime_name', 'STABLE')
                        regime_obj = {
                            'name': regime_name,
                            'color': current_state.get('regime_color', '#667eea')
                        }
                        
                        # Render Monte Carlo simulation
                        render_monte_carlo_simulation(
                            ticker_symbol=symbol,
                            current_price=price,
                            current_vola=current_vola,
                            regime_obj=regime_obj
                        )
                    else:
                        st.warning("No data available for this asset.")
                else:
                    # Public/Free: Soft gate with upgrade prompt
                    st.info("🔒 **Deep Dive Analysis** (Charts & Historical Data) requires **Premium Access**")
                    show_upgrade_dialog("Deep Dive Analysis", tier)
        elif st.session_state.analysis_mode == "simulation":
            # Portfolio Simulation - TIERED ACCESS
            st.markdown("### Portfolio Simulation")
            st.markdown("---")
            
            tier = get_user_tier()
            
            if tier == "public":
                # Public: Locked
                st.info("🔒 **Portfolio Simulation** is not available for Public users")
                show_upgrade_dialog("Portfolio Simulation", tier)
            
            elif tier == "free":
                # Free: Limited (3 simulations per hour)
                remaining = get_remaining_actions('simulation', 3)
                
                if not check_rate_limit('simulation', 3):
                    st.warning("⏱️ **Simulation Limit Reached** (3 per hour for Free tier)")
                    st.info("💡 **Upgrade to Premium** for unlimited simulations!")
                    show_upgrade_dialog("Portfolio Simulation", tier)
                else:
                    # Check if they're about to run a simulation
                    if st.session_state.get('simulation_running', False):
                        register_action('simulation')
                        st.session_state.simulation_running = False
                    
                    result_tickers = [r['symbol'] for r in results]
                    
                    # Show prominent usage indicator
                    if remaining <= 1:
                        st.info(f"ℹ️ **Free tier:** {remaining}/3 simulations remaining this hour. Upgrade for unlimited!")
                    else:
                        st.success(f"✅ **Free tier:** {remaining}/3 simulations remaining this hour")
                    
                    render_dca_simulation(result_tickers)
            
            else:  # premium
                # Premium: Unlimited
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
    # Add custom CSS for reduced footer button size: 75% width, 50% height
    st.markdown("""
    <style>
        button[key="footer_disclaimer"],
        button[key="footer_data_protection"],
        button[key="footer_imprint"] {
            max-width: 75% !important;
            padding: 0.25rem 0.625rem !important;
            margin: 0 auto !important;
            display: block !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col_spacer1, col1, col_sep1, col2, col_sep2, col3, col_spacer2 = st.columns([2, 1, 0.3, 1, 0.3, 1, 2])
    
    with col1:
        if st.button("Disclaimer", key="footer_disclaimer", use_container_width=False):
            show_disclaimer_dialog()
    
    with col_sep1:
        st.markdown("<p style='text-align: center; color: #BDC3C7; margin-top: 8px; font-size: 1.2rem;'>|</p>", unsafe_allow_html=True)
    
    with col2:
        if st.button("Data Protection", key="footer_data_protection", use_container_width=False):
            show_data_protection_dialog()
    
    with col_sep2:
        st.markdown("<p style='text-align: center; color: #BDC3C7; margin-top: 8px; font-size: 1.2rem;'>|</p>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Imprint", key="footer_imprint", use_container_width=False):
            show_imprint_dialog()


if __name__ == "__main__":
    main()
