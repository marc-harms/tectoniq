"""
SOC Market Seismograph - Authentication & Navigation UI Components
===================================================================

Landing page, authentication, and sticky header components.

Contains:
- render_disclaimer(): Legal disclaimer page (must accept before using app)
- check_auth(): Authentication validation
- login_page(): Login UI
- render_sticky_cockpit_header(): Persistent search/status header
- render_education_landing(): Welcome page with quick start guide

Author: Market Analysis Team
Version: 8.0 (Modularized)
"""

from typing import Callable, Optional

import streamlit as st

from config import LEGAL_DISCLAIMER
from auth_manager import login, signup, logout, is_authenticated


def render_disclaimer() -> None:
    """
    Render legal disclaimer page that must be accepted before using the app.
    Uses session state to track acceptance.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@300;400;700&family=Roboto+Condensed:wght@300;400;700&display=swap');
        .stApp { background-color: #F9F7F1; }
        h1, h2, h3 { color: #2C3E50 !important; font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Slab', serif !important; }
        p, li { color: #333333 !important; font-size: 1rem !important; font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Condensed', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)
                
    st.title("TECTONIQ")
    st.caption("Move Beyond Buy & Hope")
    
    st.markdown("---")
    
    # Display disclaimer without HTML tags - use pure markdown
    st.markdown("""
    ## ⚖️ Legal Disclaimer & Terms of Use
    
    **IMPORTANT: Please read this disclaimer carefully before using this application.**
    
    ### 1. Educational & Informational Purpose Only
    
    This application ("SOC Market Seismograph") is provided **exclusively for educational
    and informational purposes**. The analysis, data, charts, signals, and any other
    information displayed are intended solely to help users understand market dynamics
    through the lens of Self-Organized Criticality (SOC) theory.
    
    ### 2. No Financial Advice
    
    **THIS APPLICATION DOES NOT PROVIDE FINANCIAL, INVESTMENT, TAX, LEGAL, OR
    PROFESSIONAL ADVICE OF ANY KIND.**
    
    - The content is not a recommendation to buy, sell, or hold any security,
      cryptocurrency, or financial instrument.
    - No fiduciary relationship is established between you and the creators of this application.
    - The "signals," "regimes," and "scores" are purely statistical observations based on
      historical data and mathematical models. They are NOT predictions of future performance.
    
    ### 3. No Guarantees or Warranties
    
    - Past performance is **NOT indicative of future results**.
    - All investment involves risk, including the potential loss of principal.
    - The accuracy, completeness, or reliability of the data and analysis is NOT guaranteed.
    - The application is provided "AS IS" without warranty of any kind, express or implied.
    
    ### 4. Limitation of Liability
    
    To the fullest extent permitted by applicable law:
    
    - The creators, developers, and operators of this application shall NOT be liable for
      any direct, indirect, incidental, special, consequential, or punitive damages arising
      from your use of or reliance on this application.
    - This includes, but is not limited to, any losses, damages, or claims arising from
      investment decisions made based on information displayed in this application.
    
    ### 5. Independent Verification Required
    
    Before making any financial decision, you should:
    
    - Consult with a qualified financial advisor, broker, or other professional.
    - Conduct your own independent research and due diligence.
    - Consider your personal financial situation, risk tolerance, and investment objectives.
    
    ### 6. Data Sources
    
    Market data is sourced from third-party providers (Yahoo Finance). We do not control
    or guarantee the accuracy, timeliness, or availability of this data.
    
    ### 7. Jurisdiction
    
    This disclaimer is governed by applicable laws. If any provision is found unenforceable,
    the remaining provisions shall continue in full force and effect.
    
    ---
    
    **By clicking "I Understand & Accept" below, you acknowledge that:**
    
    ✓ You have read and understood this disclaimer in its entirety.
    
    ✓ You agree that this application provides NO financial advice.
    
    ✓ You accept full responsibility for any decisions you make.
    
    ✓ You waive any claims against the creators arising from your use of this application.
    """)
    
    st.markdown("---")
    
    # Acceptance checkbox and button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        accepted = st.checkbox(
            "I have read, understood, and agree to the terms above",
            key="disclaimer_checkbox"
        )
        
        if st.button(
            "✅ I Understand & Accept",
            disabled=not accepted,
            use_container_width=True
        ):
            st.session_state.disclaimer_accepted = True
            st.rerun()
        
        if not accepted:
            st.caption("⚠️ You must check the box above to continue")
    
    st.stop()


def render_auth_page() -> None:
    """
    Render modern login/signup page with tabs.
    
    This replaces the old simple access code system with full user authentication.
    Supports both login for existing users and signup for new users.
    """
    # Apply minimal styling for auth page (light mode)
    st.markdown("""
    <style>
        .stApp { 
            background-color: #F9F7F1;
        }
        .auth-container {
            background: white;
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            max-width: 450px;
            margin: 0 auto;
        }
        .auth-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .auth-header h1 {
            color: #1a1a1a;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .auth-header p {
            color: #666;
            font-size: 0.95rem;
        }
        /* Increase font sizes and darken text */
        label, .stTextInput label, .stCheckbox label {
            color: #1a1a1a !important;
            font-size: 1.1rem !important;
            font-weight: 500 !important;
        }
        p, div, span {
            color: #333 !important;
            font-size: 1rem !important;
        }
        /* ALL BUTTONS - Cream background, charcoal border & text */
        .stButton > button,
        .stButton button,
        button,
        button[kind="primary"],
        button[kind="secondary"],
        button[data-testid="baseButton-primary"],
        button[data-testid="baseButton-secondary"],
        div[data-testid="stButton"] button {
            font-size: 1.1rem !important;
            padding: 0.6rem 1.2rem !important;
            font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Slab', serif !important;
            font-weight: bold !important;
            border-radius: 4px !important;
            border: 1px solid #333333 !important;
            background-color: #F9F7F1 !important;
            background: #F9F7F1 !important;
            color: #333333 !important;
        }
        
        /* Force charcoal text color inside buttons */
        .stButton > button p,
        .stButton > button span,
        .stButton > button div,
        .stButton > button *,
        button p,
        button span,
        button div,
        button * {
            color: #333333 !important;
        }
        
        .stButton > button:hover,
        .stButton button:hover,
        button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        button[data-testid="baseButton-primary"]:hover,
        button[data-testid="baseButton-secondary"]:hover,
        div[data-testid="stButton"] button:hover {
            background-color: #E6E1D3 !important;
            background: #E6E1D3 !important;
            border-color: #333333 !important;
            color: #333333 !important;
        }
        
        .stButton > button:hover *,
        button:hover * {
            color: #333333 !important;
        }
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] button {
            color: #1a1a1a !important;
            font-size: 1.1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the auth form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo
        try:
            col_logo_left, col_logo_center, col_logo_right = st.columns([1, 2, 1])
            with col_logo_center:
                st.image("assets/tectoniq_logo.png", width=200)
        except:
            pass  # Skip logo if not found
        
        st.markdown("""
        <div class="auth-header">
            <h1 style="color: #2C3E50; font-size: 2.2rem; font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Slab', serif; font-weight: 700; letter-spacing: -0.5px;">TECTONIQ</h1>
            <p style="color: #555; font-size: 1.1rem; font-weight: 600; font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Condensed', sans-serif;">Move Beyond Buy & Hope</p>
            <p style="color: #666; font-size: 0.9rem; line-height: 1.5; max-width: 450px; margin: 8px auto 0; font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Condensed', sans-serif;">
                Market crashes aren't random—they are physics. TECTONIQ visualizes systemic stress levels so you can navigate volatility with open eyes.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for Login / Sign Up (no emojis)
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        # === LOGIN TAB ===
        with tab1:
            st.markdown("<h3 style='color: #1a1a1a; font-size: 1.5rem;'>Welcome Back</h3>", unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="your@email.com", key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
                
                submit = st.form_submit_button("Login", use_container_width=True, type="primary")
                
                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        with st.spinner("🔐 Authenticating credentials... Establishing secure session..."):
                            success, error, user_data = login(email, password)
                            
                            if success:
                                st.session_state.user = user_data
                                st.session_state.tier = user_data['tier']
                                st.session_state.authenticated = True
                                st.success(f"✅ Welcome back, {user_data['email']}!")
                                st.rerun()
                            else:
                                st.error(f"❌ {error}")
        
        # === SIGNUP TAB ===
        with tab2:
            st.markdown("<h3 style='color: #1a1a1a; font-size: 1.5rem;'>Create Your Account</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #555; font-size: 1rem;'>Start with our <strong>Free tier</strong> - no credit card required!</p>", unsafe_allow_html=True)
            
            with st.form("signup_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
                password = st.text_input("Password", type="password", placeholder="Min. 6 characters", key="signup_password")
                password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_password_confirm")
                
                agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
                
                submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if submit:
                    # Validation
                    if not email or not password or not password_confirm:
                        st.error("Please fill in all fields")
                    elif password != password_confirm:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    elif not agree_terms:
                        st.error("Please agree to the Terms of Service")
                    else:
                        with st.spinner("🔬 Initializing new seismograph profile... Configuring monitoring arrays..."):
                            success, error, user_data = signup(email, password)
                            
                            if success:
                                st.session_state.user = user_data
                                st.session_state.tier = user_data['tier']
                                st.session_state.authenticated = True
                                st.success(f"🎉 Account created! Welcome, {user_data['email']}!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ {error}")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 1rem;">
            <p style="color: #555;">Secure authentication powered by Supabase</p>
            <p style="color: #555;">Questions? Contact <a href="mailto:support@socseismograph.com" style="color: #0066cc;">support@socseismograph.com</a></p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()


def render_scientific_masthead(validate_ticker_func: Callable, search_ticker_func: Callable, run_analysis_func: Callable) -> None:
    """
    Render the "Scientific Heritage" Masthead header (newspaper/journal style).
    
    Three-level structure:
        1. Top (Utility): User info + Logout (right-aligned)
        2. Mid (Identity): Logo + Title + Narrative (centered)
        3. Bottom (Action): Search bar (centered)
    
    Design Philosophy: Clean, open, no borders. Like a 19th-century journal masthead.
    
    Args:
        validate_ticker_func: Function to validate ticker symbols
        search_ticker_func: Function to search for ticker by company name
        run_analysis_func: Function to run analysis on ticker(s)
    """
    from auth_manager import get_current_user_email, logout
    
    # === CSS for Masthead ===
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,400;0,700;1,400&family=Roboto:wght@400;500;700&display=swap');
        
        .tectoniq-masthead {
            background-color: #F9F7F1;
            padding: 1.5rem 0 2rem 0;
            margin-bottom: 2rem;
        }
        
        .masthead-utility {
            font-family: 'Roboto', sans-serif;
            font-size: 0.85rem;
            color: #666;
            text-align: right;
            margin-bottom: 1rem;
        }
        
        .masthead-identity {
            text-align: center;
            padding: 0 2rem;
        }
        
        .masthead-title {
            font-family: 'Merriweather', serif;
            font-size: 3.5rem;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #2C3E50;
            margin: 0.5rem 0 0.25rem 0;
            line-height: 1.1;
        }
        
        .masthead-subtitle {
            font-family: 'Roboto', sans-serif;
            font-size: 1.1rem;
            font-weight: 500;
            color: #C0392B;
            margin: 0.25rem 0 1rem 0;
            letter-spacing: 0.5px;
        }
        
        .masthead-narrative {
            font-family: 'Merriweather', serif;
            font-size: 1rem;
            font-style: italic;
            color: #555;
            line-height: 1.6;
            max-width: 700px;
            margin: 0 auto 1.5rem auto;
        }
        
        .masthead-divider {
            width: 80%;
            max-width: 800px;
            height: 1px;
            background: linear-gradient(to right, transparent, #C0392B, transparent);
            margin: 1.5rem auto;
        }
        
        .masthead-action {
            text-align: center;
            padding: 1rem 0 0 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # === LEVEL 1: UTILITY BAR (User info + Logout + Refresh) ===
    col_spacer, col_utility = st.columns([2.5, 1.5])
    
    with col_utility:
        user_email = get_current_user_email()
        user_tier = st.session_state.get('tier', 'free')
        tier_label = "Premium" if user_tier == "premium" else "Free"
        
        st.markdown(f"""
        <div class="masthead-utility">
            <strong>{user_email.split('@')[0]}</strong> ({tier_label})
        </div>
        """, unsafe_allow_html=True)
        
        col_refresh, col_logout = st.columns(2)
        with col_refresh:
            if st.button("🔄 Refresh", key="masthead_refresh_btn", use_container_width=True, 
                        help="Clear cache and reload data"):
                # Clear Streamlit cache
                st.cache_data.clear()
                # Clear session state data cache
                if 'data' in st.session_state:
                    del st.session_state['data']
                if 'data_symbol' in st.session_state:
                    del st.session_state['data_symbol']
                if 'scan_results' in st.session_state:
                    del st.session_state['scan_results']
                st.success("✅ Cache cleared! Data will refresh on next search.")
                st.rerun()
        
        with col_logout:
            if st.button("Logout", key="masthead_logout_btn", use_container_width=True):
                logout()
                st.success("Logged out!")
                st.rerun()
    
    # === LEVEL 2: IDENTITY (Logo + Title + Narrative) ===
    st.markdown("""
    <div class="tectoniq-masthead">
        <div class="masthead-identity">
            <div class="masthead-title">TECTONIQ</div>
            <div class="masthead-subtitle">Move Beyond Buy & Hope</div>
            <div class="masthead-narrative">
                Market crashes aren't random—they are physics. TECTONIQ visualizes systemic stress levels 
                so you can navigate volatility with open eyes.
            </div>
        </div>
        <div class="masthead-divider"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # === LEVEL 3: ACTION (Search Bar) ===
    col_spacer1, col_search, col_spacer2 = st.columns([1, 2, 1])
    
    with col_search:
        # Clear search field if asset is already selected
        has_active_asset = 'scan_results' in st.session_state and st.session_state.scan_results
        if has_active_asset and 'cockpit_search_main' in st.session_state and st.session_state.cockpit_search_main:
            st.session_state.cockpit_search_main = ""
        
        # Dynamic placeholder
        placeholder_text = "Search for another asset (press Enter)" if has_active_asset else "Enter ticker symbol (e.g., AAPL, BTC-USD, TSLA) and press Enter"
        
        # Search field with on_change callback
        search_query = st.text_input(
            "Search Asset",
            placeholder=placeholder_text,
            label_visibility="collapsed",
            key="cockpit_search_main",
            on_change=lambda: handle_search(
                st.session_state.get('cockpit_search_main', ''),
                validate_ticker_func,
                search_ticker_func,
                run_analysis_func
            )
        )
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)


def render_sticky_cockpit_header(validate_ticker_func: Callable, search_ticker_func: Callable, run_analysis_func: Callable) -> None:
    """
    DEPRECATED: Use render_scientific_masthead() instead.
    
    Render the persistent "Cockpit" header with search and status.
    
    New Layout (Polished):
        Row 1: [Logo Placeholder] | SOC Seismograph | User: name | Status: Free/Premium
        Row 2: Centered search field (Enter to search)
        Row 3: Active asset display (if selected)
    
    Args:
        validate_ticker_func: Function to validate ticker symbols
        search_ticker_func: Function to search for ticker by company name
        run_analysis_func: Function to run analysis on ticker(s)
    """
    is_dark = st.session_state.get('dark_mode', False)
    from auth_manager import get_current_user_email, logout
    
    with st.container(border=True):
        # === ROW 1: TITLE BAR ===
        col_logo, col_title, col_user = st.columns([1, 3, 2])
        
        with col_logo:
            # TECTONIQ Logo (enlarged 4x from original)
            try:
                st.image("assets/tectoniq_logo.png", width=320)
            except:
                # Fallback if logo not found
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 48px; height: 48px; background: transparent; 
                                border: 2px solid #2C3E50; border-radius: 4px;">
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_title:
            st.markdown("""
            <div style="text-align: center; padding-top: 8px;">
                <h1 style="margin: 0; font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Slab', serif; color: #2C3E50; font-weight: 700; letter-spacing: -1px; font-size: 2.8rem;">
                    TECTONIQ
                </h1>
                <p style="margin: 4px 0 0 0; font-size: 1rem; font-weight: 600; color: #555; font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Condensed', sans-serif;">Move Beyond Buy & Hope</p>
                <p style="margin: 4px auto 0; font-size: 0.8rem; color: #666; line-height: 1.4; max-width: 500px; font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Condensed', sans-serif;">
                    Market crashes aren't random—they are physics. TECTONIQ visualizes systemic stress levels so you can navigate volatility with open eyes.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_user:
            user_email = get_current_user_email()
            user_tier = st.session_state.get('tier', 'free')
            tier_color = "#FFD700" if user_tier == "premium" else "#888888"
            tier_label = "Premium" if user_tier == "premium" else "Free"
            
            # User info display
            st.markdown(f"""
            <div style="text-align: right; padding-top: 8px;">
                <div style="font-size: 0.9rem;">
                    <span style="color: #888;">Logged in as:</span> 
                    <strong>{user_email.split('@')[0]}</strong>
                </div>
                <div style="font-size: 0.9rem; margin-top: 4px;">
                    <span style="color: #888;">Account status:</span> 
                    <strong style="color: {tier_color};">{tier_label}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Portfolio & Logout buttons (no expander - always visible)
            col_portfolio, col_logout = st.columns(2)
            with col_portfolio:
                # Disabled portfolio button with premium key icon
                st.button("🔑 Your portfolio", key="header_portfolio_btn", use_container_width=True, disabled=True)
            with col_logout:
                if st.button("Logout", key="header_logout_btn", use_container_width=True):
                    logout()
                    st.success("Logged out!")
                    st.rerun()
        
        st.markdown("---")
        
        # === ROW 2: CENTERED SEARCH FIELD ===
        col_spacer1, col_search_center, col_spacer2 = st.columns([1, 2, 1])
        
        with col_search_center:
            # Clear search field if asset is already selected
            has_active_asset = 'scan_results' in st.session_state and st.session_state.scan_results
            if has_active_asset and 'cockpit_search_main' in st.session_state and st.session_state.cockpit_search_main:
                st.session_state.cockpit_search_main = ""
            
            # Dynamic placeholder based on whether asset is active
            placeholder_text = "Search for another asset (press Enter)" if has_active_asset else "Enter ticker symbol (e.g., AAPL, BTC-USD, TSLA) and press Enter"
            
            # Search field with on_change callback (triggered by Enter key)
            search_query = st.text_input(
                "Search Asset",
                placeholder=placeholder_text,
                label_visibility="collapsed",
                key="cockpit_search_main",
                on_change=lambda: handle_search(
                    st.session_state.get('cockpit_search_main', ''),
                    validate_ticker_func,
                    search_ticker_func,
                    run_analysis_func
                )
            )
        
        # Active asset card moved to main content area below buttons (removed duplicate)


def handle_search(query: str, validate_func: Callable, search_func: Callable, analyze_func: Callable) -> None:
    """
    Handle search when user presses Enter.
    
    Args:
        query: Search query (ticker symbol or company name)
        validate_func: Function to validate ticker
        search_func: Function to search for ticker
        analyze_func: Function to run analysis
    """
    if not query or len(query.strip()) == 0:
        return
    
    ticker_input = query.strip().upper()
    
    try:
        # First try direct ticker
        validation = validate_func(ticker_input)
        
        if validation.get('valid'):
            # Valid ticker - analyze it
            results = analyze_func([ticker_input])
            if results and len(results) > 0:
                st.session_state.current_ticker = ticker_input
                st.session_state.scan_results = results
                st.session_state.selected_asset = 0
                st.session_state.analysis_mode = "deep_dive"
                # Clear search field
                st.session_state.cockpit_search_main = ""
        else:
            # Not a valid ticker - try searching for it
            search_results = search_func(ticker_input)
            if search_results:
                # Found matches - store for selection
                st.session_state.ticker_suggestions = search_results
            else:
                st.error(f"Could not find '{ticker_input}'. Try entering the exact ticker symbol.")
    except Exception as e:
        st.error(f"Search error: {str(e)}")


def render_education_landing(run_analysis_func: Callable) -> None:
    """
    Render the landing page when no asset is selected.
    
    Shows:
        - How SOC works (brief)
        - Top Movers / Risk List (teaser)
    
    Args:
        run_analysis_func: Function to run analysis on ticker(s)
    """
    st.markdown("### Welcome to TECTONIQ")
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("### 🚀 Quick Start")
    st.markdown("""
    <div style="font-size: 0.95rem; line-height: 1.8; margin-left: 1rem;">
        1. <b>Type a ticker</b> in the search box above (e.g., AAPL, TSLA, BTC-USD)<br>
        2. Analysis runs automatically<br>
        3. Explore <b>Deep Dive</b> (signals, charts) or <b>Simulation</b> (backtesting)<br>
        4. Switch assets instantly using the search bar
    </div>
    """, unsafe_allow_html=True)

