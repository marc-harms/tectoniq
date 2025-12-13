"""
Portfolio Risk Mirror - Phase 3 UX Layer

Pure UI module for portfolio-first risk display.
NO logic changes. NO strategy. NO forecasting.

The portfolio is the product. Assets are supporting evidence.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
from logic import compute_market_state, MarketState
from portfolio_state import AssetInput, PortfolioInput, compute_portfolio_state, PortfolioState


# =====================================================================
# LAYER 1: PORTFOLIO STATUS (DEFAULT VIEW)
# =====================================================================

def render_portfolio_status(portfolio_state: PortfolioState) -> None:
    """
    LAYER 1: Portfolio Status - The landing screen.
    
    User must understand portfolio risk in ≤5 seconds.
    
    Shows:
    1. Portfolio Regime (PRIMARY) - Large, color-coded
    2. Portfolio Criticality (SECONDARY) - One number
    3. One-Sentence Explanation (MANDATORY) - From explainability
    4. Top Risk Contributors (RANKED) - Max 5
    
    NO charts. NO jargon. NO action verbs.
    """
    
    # Color mapping (same as asset-level for consistency)
    regime_colors = {
        "GREEN": "#27ae60",
        "YELLOW": "#f39c12",
        "RED": "#e74c3c"
    }
    
    regime_emojis = {
        "GREEN": "🟢",
        "YELLOW": "🟡",
        "RED": "🔴"
    }
    
    regime_labels = {
        "GREEN": "STABLE",
        "YELLOW": "ELEVATED",
        "RED": "CRITICAL"
    }
    
    # Get regime details
    regime = portfolio_state.portfolio_regime
    criticality = portfolio_state.portfolio_criticality
    color = regime_colors.get(regime, "#667eea")
    emoji = regime_emojis.get(regime, "⚪")
    label = regime_labels.get(regime, regime)
    
    # === 1️⃣ PORTFOLIO REGIME (PRIMARY) ===
    st.markdown(
        f"""
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <div style='font-size: 4rem; margin-bottom: 0.5rem;'>{emoji}</div>
            <div style='font-size: 2.5rem; font-weight: 700; color: {color}; font-family: Merriweather, serif;'>
                {label}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # === 2️⃣ PORTFOLIO CRITICALITY (SECONDARY) ===
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"""
            <div style='text-align: center; padding: 1rem 0;'>
                <div style='font-size: 3rem; font-weight: 600; color: {color};'>
                    {criticality}
                </div>
                <div style='font-size: 0.9rem; color: #7f8c8d; margin-top: -0.5rem;'>
                    0 = stable, 100 = unstable
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # === 3️⃣ ONE-SENTENCE EXPLANATION (MANDATORY) ===
    explanation = generate_portfolio_explanation(portfolio_state)
    
    st.markdown(
        f"""
        <div style='text-align: center; padding: 1rem 2rem; background: rgba(0,0,0,0.02); border-radius: 8px; margin: 1rem 0;'>
            <div style='font-size: 1.1rem; line-height: 1.6; color: #2c3e50; font-family: Roboto, sans-serif;'>
                {explanation}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # === 4️⃣ TOP RISK CONTRIBUTORS (RANKED) ===
    st.markdown("### Risk Attribution")
    
    if portfolio_state.top_risk_contributors:
        # Create a clean table
        contributors_data = []
        for contributor in portfolio_state.top_risk_contributors[:5]:
            contributors_data.append({
                "Asset": contributor.symbol,
                "Weight": f"{contributor.weight*100:.1f}%",
                "Criticality": contributor.criticality,
                "Risk Share": f"{contributor.contribution_pct:.1f}%"
            })
        
        df_contributors = pd.DataFrame(contributors_data)
        
        # Display as clean table (no sparklines, no charts)
        st.dataframe(
            df_contributors,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Asset": st.column_config.TextColumn("Asset", width="medium"),
                "Weight": st.column_config.TextColumn("Weight", width="small"),
                "Criticality": st.column_config.NumberColumn("Criticality", format="%d"),
                "Risk Share": st.column_config.TextColumn("% of Portfolio Risk", width="medium")
            }
        )
    else:
        st.info("No risk contributors to display")


def generate_portfolio_explanation(portfolio_state: PortfolioState) -> str:
    """
    Generate one-sentence explanation from portfolio state.
    
    Rules:
    - One sentence only
    - No action verbs (buy, sell, avoid)
    - No time predictions
    - Must be explainable from existing data
    
    Returns:
        Single sentence explaining portfolio risk
    """
    regime = portfolio_state.portfolio_regime
    criticality = portfolio_state.portfolio_criticality
    top_contributor = portfolio_state.top_risk_contributors[0] if portfolio_state.top_risk_contributors else None
    
    # Count how many assets are in elevated/critical states
    elevated_count = sum(1 for c in portfolio_state.top_risk_contributors if c.criticality >= 40)
    critical_count = sum(1 for c in portfolio_state.top_risk_contributors if c.criticality >= 70)
    
    # Generate explanation based on regime and distribution
    if regime == "RED":
        if critical_count >= 2:
            return "Multiple holdings show critical instability levels."
        elif top_contributor and top_contributor.contribution_pct > 60:
            return f"Portfolio instability dominated by {top_contributor.symbol}."
        else:
            return "Elevated volatility across holdings."
    
    elif regime == "YELLOW":
        if top_contributor and top_contributor.contribution_pct > 70:
            return f"Risk concentration in {top_contributor.symbol}."
        elif elevated_count > 0:
            return f"Elevated volatility in {elevated_count} of {len(portfolio_state.top_risk_contributors)} holdings."
        else:
            return "Moderate volatility across portfolio."
    
    else:  # GREEN
        return "Low volatility environment across holdings."


# =====================================================================
# LAYER 2: PORTFOLIO CONTEXT (OPTIONAL EXPAND)
# =====================================================================

def render_portfolio_context(portfolio_state: PortfolioState) -> None:
    """
    LAYER 2: Portfolio Context - Hidden behind expander.
    
    Shows:
    - Current asset weights
    - Asset-level regimes (icons only, no charts)
    - Contribution × weight logic in plain language
    
    Builds trust without cognitive overload.
    """
    
    with st.expander("📖 Why is my portfolio in this state?"):
        st.markdown("#### Portfolio Composition")
        
        # Show asset weights and regimes
        if portfolio_state.top_risk_contributors:
            regime_icons = {
                "GREEN": "🟢",
                "YELLOW": "🟡",
                "RED": "🔴"
            }
            
            # Create simple table
            context_data = []
            for contributor in portfolio_state.top_risk_contributors:
                # We don't have asset regime in PortfolioState, so infer from criticality
                if contributor.criticality < 40:
                    asset_regime = "GREEN"
                elif contributor.criticality < 70:
                    asset_regime = "YELLOW"
                else:
                    asset_regime = "RED"
                
                icon = regime_icons.get(asset_regime, "⚪")
                
                context_data.append({
                    "Asset": f"{icon} {contributor.symbol}",
                    "Portfolio Weight": f"{contributor.weight*100:.1f}%",
                    "Asset Criticality": contributor.criticality,
                    "Contribution": f"{contributor.contribution:.1f}"
                })
            
            df_context = pd.DataFrame(context_data)
            st.dataframe(df_context, hide_index=True, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### How Risk is Calculated")
            st.markdown(
                """
                Risk contribution is calculated as **weight × instability**.
                
                - Each asset's criticality (0-100) measures its current instability
                - Multiplied by its portfolio weight gives its risk contribution
                - Portfolio criticality is the weighted sum of all contributions
                
                This means:
                - A small holding with high instability contributes less risk
                - A large holding with moderate instability can dominate portfolio risk
                """
            )


# =====================================================================
# LAYER 3: ASSET DRILL-DOWN (SECONDARY NAV)
# =====================================================================

def render_asset_drill_down_header() -> None:
    """
    LAYER 3 Header: Explicit label that assets are opt-in/informational.
    
    This separates portfolio view (primary) from asset view (secondary).
    """
    st.markdown(
        """
        <div style='background: #f8f9fa; padding: 0.75rem 1rem; border-left: 4px solid #95a5a6; margin-bottom: 1rem; border-radius: 4px;'>
            <div style='font-size: 0.9rem; color: #7f8c8d; font-weight: 500;'>
                📊 ASSET VIEW — INFORMATIONAL ONLY
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================================
# MAIN ENTRY POINT: PORTFOLIO-FIRST VIEW
# =====================================================================

def render_portfolio_risk_view(user_portfolio: List[Dict[str, float]]) -> None:
    """
    Main entry point for portfolio-first UX.
    
    Renders all 3 layers in hierarchy:
    1. Portfolio Status (always visible)
    2. Portfolio Context (expandable)
    3. Asset drill-down (separate section)
    
    Args:
        user_portfolio: List of dicts with 'symbol' and 'weight' keys
        
    Example:
        user_portfolio = [
            {'symbol': 'SPY', 'weight': 0.6},
            {'symbol': 'QQQ', 'weight': 0.4}
        ]
    """
    
    # Validate portfolio
    if not user_portfolio:
        st.info("👋 Add assets to your portfolio to see risk analysis")
        return
    
    # Compute portfolio state
    with st.spinner("Computing portfolio risk state..."):
        portfolio_state = compute_portfolio_state_from_user_input(user_portfolio)
    
    if portfolio_state is None:
        st.error("Unable to compute portfolio state. Check asset symbols and data availability.")
        return
    
    # === LAYER 1: PORTFOLIO STATUS ===
    render_portfolio_status(portfolio_state)
    
    st.markdown("---")
    
    # === LAYER 2: PORTFOLIO CONTEXT ===
    render_portfolio_context(portfolio_state)
    
    st.markdown("---")
    
    # === LAYER 3: ASSET DRILL-DOWN (OPT-IN) ===
    st.markdown("### Asset Details")
    render_asset_drill_down_header()
    
    # Allow user to select an asset to drill down
    asset_symbols = [asset['symbol'] for asset in user_portfolio]
    
    if len(asset_symbols) == 1:
        selected_symbol = asset_symbols[0]
    else:
        selected_symbol = st.selectbox(
            "Select asset to view details:",
            asset_symbols,
            key="asset_drill_down_selector"
        )
    
    # Store selected asset for drill-down rendering elsewhere
    st.session_state.drill_down_asset = selected_symbol
    
    st.caption(f"Viewing detailed analysis for **{selected_symbol}**")


def suggest_ticker_correction(invalid_symbol: str) -> Optional[str]:
    """
    Suggest correct ticker symbol for common company name inputs.
    
    Args:
        invalid_symbol: The invalid symbol entered by user
    
    Returns:
        Suggested ticker symbol or None
    """
    # Common company name to ticker mappings (extensive list)
    common_mappings = {
        # Technology
        'NVIDIA': 'NVDA', 'NVIDA': 'NVDA',
        'APPLE': 'AAPL', 'APPL': 'AAPL',
        'MICROSOFT': 'MSFT', 'MS': 'MSFT',
        'GOOGLE': 'GOOGL', 'ALPHABET': 'GOOGL',
        'FACEBOOK': 'META', 'META': 'META',
        'AMAZON': 'AMZN', 'AMZN': 'AMZN',
        'TESLA': 'TSLA', 'TSLA': 'TSLA',
        'NETFLIX': 'NFLX', 'NFLX': 'NFLX',
        'INTEL': 'INTC', 'INTC': 'INTC',
        'AMD': 'AMD', 'ADVANCED MICRO': 'AMD',
        'ORACLE': 'ORCL', 'ORCL': 'ORCL',
        'SALESFORCE': 'CRM', 'CRM': 'CRM',
        'ADOBE': 'ADBE', 'ADBE': 'ADBE',
        'IBM': 'IBM', 'INTERNATIONAL BUSINESS': 'IBM',
        'CISCO': 'CSCO', 'CSCO': 'CSCO',
        'QUALCOMM': 'QCOM', 'QCOM': 'QCOM',
        
        # Healthcare
        'STRYKER': 'SYK', 'SYK': 'SYK',
        'JOHNSON': 'JNJ', 'J&J': 'JNJ', 'JNJ': 'JNJ',
        'UNITEDHEALTH': 'UNH', 'UNITED HEALTH': 'UNH', 'UNH': 'UNH',
        'PFIZER': 'PFE', 'PFE': 'PFE',
        'MERCK': 'MRK', 'MRK': 'MRK',
        'ABBVIE': 'ABBV', 'ABBV': 'ABBV',
        'BRISTOL': 'BMY', 'BMY': 'BMY',
        
        # Finance
        'JPMORGAN': 'JPM', 'JP MORGAN': 'JPM', 'JPM': 'JPM',
        'BANK OF AMERICA': 'BAC', 'BAC': 'BAC', 'BOA': 'BAC',
        'WELLS FARGO': 'WFC', 'WFC': 'WFC',
        'GOLDMAN': 'GS', 'GOLDMAN SACHS': 'GS', 'GS': 'GS',
        'MORGAN STANLEY': 'MS', 'MS': 'MS',
        'VISA': 'V', 'V': 'V',
        'MASTERCARD': 'MA', 'MA': 'MA',
        'PAYPAL': 'PYPL', 'PYPL': 'PYPL',
        'AMERICAN EXPRESS': 'AXP', 'AMEX': 'AXP', 'AXP': 'AXP',
        
        # Consumer
        'BOEING': 'BA', 'BA': 'BA',
        'WALMART': 'WMT', 'WMT': 'WMT',
        'DISNEY': 'DIS', 'DIS': 'DIS',
        'COCA-COLA': 'KO', 'COKE': 'KO', 'KO': 'KO',
        'PEPSI': 'PEP', 'PEPSICO': 'PEP', 'PEP': 'PEP',
        'MCDONALD': 'MCD', 'MCDONALDS': 'MCD', 'MCD': 'MCD',
        'NIKE': 'NKE', 'NKE': 'NKE',
        'STARBUCKS': 'SBUX', 'SBUX': 'SBUX',
        'HOME DEPOT': 'HD', 'HD': 'HD',
        
        # Crypto
        'BITCOIN': 'BTC-USD', 'BTC': 'BTC-USD',
        'ETHEREUM': 'ETH-USD', 'ETH': 'ETH-USD',
        
        # ETFs
        'S&P': 'SPY', 'S&P 500': 'SPY', 'SP500': 'SPY',
        'NASDAQ': 'QQQ', 'NASDAQ 100': 'QQQ',
        'DOW': 'DIA', 'DOW JONES': 'DIA',
        'RUSSELL': 'IWM', 'RUSSELL 2000': 'IWM'
    }
    
    # Check for matches (case-insensitive)
    invalid_upper = invalid_symbol.upper().strip()
    
    # Exact match
    if invalid_upper in common_mappings:
        return common_mappings[invalid_upper]
    
    # Partial match (more flexible)
    for name, ticker in common_mappings.items():
        # Check if search term is in company name
        if len(invalid_upper) >= 3:  # Only for 3+ character searches
            if invalid_upper in name or name in invalid_upper:
                return ticker
    
    return None


def compute_portfolio_state_from_user_input(user_portfolio: List[Dict[str, float]]) -> Optional[PortfolioState]:
    """
    Compute portfolio state from user's portfolio allocation.
    
    This is the integration point between UI and Phase 2 portfolio engine.
    
    Args:
        user_portfolio: List of dicts with 'symbol' and 'weight' keys
    
    Returns:
        PortfolioState object or None if computation fails
    """
    from logic import DataFetcher
    
    # Fetch data and compute states for each asset
    fetcher = DataFetcher(cache_enabled=True)
    asset_inputs = []
    corrected_symbols = []  # Track which symbols were auto-corrected
    
    for asset in user_portfolio:
        symbol = asset['symbol']
        weight = asset['weight']
        original_symbol = symbol  # Keep track of original input
        
        try:
            # First, try to fetch with the original symbol
            df = fetcher.fetch_data(symbol)
            
            # If no data, try auto-correction
            if df is None or df.empty:
                suggested_ticker = suggest_ticker_correction(symbol)
                if suggested_ticker:
                    # Try the suggested ticker
                    df = fetcher.fetch_data(suggested_ticker)
                    if df is not None and not df.empty:
                        # Success! Use the corrected symbol
                        symbol = suggested_ticker
                        corrected_symbols.append((original_symbol, symbol))
                        st.success(f"✅ Auto-corrected **{original_symbol}** → **{symbol}**")
                    else:
                        st.warning(f"❌ No data for **{original_symbol}** or suggested **{suggested_ticker}**")
                        continue
                else:
                    st.warning(f"❌ No data for **{original_symbol}**. Make sure you're using the ticker symbol (e.g., AAPL), not company name (Apple).")
                    continue
            
            # If we still don't have data, skip
            if df is None or df.empty:
                continue
            
            # Compute market state (using existing validated logic - NO CHANGES)
            market_state = compute_market_state(df, len(df) - 1)
            
            # Create AssetInput
            asset_input = AssetInput(
                symbol=symbol,
                weight=weight,
                state=market_state
            )
            
            asset_inputs.append(asset_input)
            # Success - no message needed (we'll show summary at the end)
            
        except Exception as e:
            st.error(f"❌ Error processing **{symbol}**: {str(e)}")
            continue
    
    if not asset_inputs:
        st.error("❌ No valid assets in portfolio. Please check your ticker symbols.")
        return None
    
    # Show success message
    if len(asset_inputs) < len(user_portfolio):
        st.info(f"ℹ️ Loaded {len(asset_inputs)} of {len(user_portfolio)} assets successfully.")
    else:
        st.success(f"✅ All {len(asset_inputs)} assets loaded successfully.")
    
    # Re-normalize weights if some assets failed to load
    # This ensures weights sum to 1.0 even if we excluded some assets
    total_weight = sum(asset.weight for asset in asset_inputs)
    if abs(total_weight - 1.0) > 1e-6:
        # Re-normalize
        st.info(f"🔄 Re-normalizing portfolio weights (original total: {total_weight:.2%})")
        for asset in asset_inputs:
            asset.weight = asset.weight / total_weight
        
        # Verify normalization
        new_total = sum(asset.weight for asset in asset_inputs)
        st.success(f"✅ Weights re-normalized to {new_total:.2%}")
    
    # Create PortfolioInput
    try:
        portfolio_input = PortfolioInput(assets=asset_inputs)
        
        # Validate (will raise ValueError if invalid)
        portfolio_input.validate()
        
        # Compute portfolio state (using Phase 2 validated logic)
        portfolio_state = compute_portfolio_state(portfolio_input)
        
        return portfolio_state
        
    except ValueError as e:
        st.error(f"❌ Portfolio validation error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Error computing portfolio state: {str(e)}")
        return None


# =====================================================================
# SIMPLIFIED PORTFOLIO INPUT UI
# =====================================================================

def render_portfolio_input_simple() -> Optional[List[Dict[str, float]]]:
    """
    Simple UI for inputting portfolio allocations.
    
    Returns user_portfolio or None if not configured.
    
    Stores in session state for persistence.
    """
    
    # Initialize session state
    if 'user_portfolio' not in st.session_state:
        # Default portfolio: 60/40 SPY/QQQ
        st.session_state.user_portfolio = [
            {'symbol': 'SPY', 'weight': 0.6},
            {'symbol': 'QQQ', 'weight': 0.4}
        ]
    
    with st.expander("Configure Portfolio", expanded=False):
        st.markdown("#### Portfolio Holdings")
        st.caption("Enter ticker symbols or company names. Auto-correction is enabled for common names (e.g., Apple → AAPL, Nvidia → NVDA).")
        
        st.markdown("---")
        
        # Allow up to 5 assets
        num_assets = st.number_input(
            "Number of assets:",
            min_value=1,
            max_value=5,
            value=len(st.session_state.user_portfolio),
            step=1
        )
        
        portfolio_entries = []
        total_weight = 0.0
        
        for i in range(num_assets):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Get existing symbol if available
                default_symbol = ""
                if i < len(st.session_state.user_portfolio):
                    default_symbol = st.session_state.user_portfolio[i]['symbol']
                
                symbol = st.text_input(
                    f"Asset {i+1}:",
                    value=default_symbol,
                    key=f"portfolio_symbol_{i}",
                    placeholder="e.g., AAPL, Apple, Tesla, BTC-USD",
                    help="Enter ticker symbol or company name. Auto-correction will attempt to match common names to ticker symbols."
                ).strip().upper()
            
            with col2:
                # Get existing weight if available
                default_weight = 0.0
                if i < len(st.session_state.user_portfolio):
                    default_weight = st.session_state.user_portfolio[i]['weight'] * 100
                
                weight_pct = st.number_input(
                    f"Weight %:",
                    min_value=0.0,
                    max_value=100.0,
                    value=default_weight,
                    step=5.0,
                    key=f"portfolio_weight_{i}"
                )
            
            if symbol:
                portfolio_entries.append({
                    'symbol': symbol,
                    'weight': weight_pct / 100.0
                })
                total_weight += weight_pct
        
        # Show total weight
        if total_weight != 100.0:
            st.warning(f"Weights sum to {total_weight:.1f}%. Must be 100%.")
        else:
            st.success(f"Weights sum to {total_weight:.1f}%")
        
        # Update button
        if st.button("Update Portfolio", use_container_width=True):
            if abs(total_weight - 100.0) > 0.1:
                st.error("Weights must sum to 100%")
            else:
                st.session_state.user_portfolio = portfolio_entries
                st.success("Portfolio updated!")
                st.rerun()
    
    return st.session_state.user_portfolio if 'user_portfolio' in st.session_state else None

