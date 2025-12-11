"""
SOC Market Seismograph - Configuration
=======================================

Centralized configuration file containing all constants, thresholds,
colors, and default values used across the application.

Author: Market Analysis Team
Version: 7.0 (Modularized)
"""

# =============================================================================
# AUTHENTICATION
# =============================================================================
ACCESS_CODE = "BETA2025"

# =============================================================================
# DATA ANALYSIS PARAMETERS
# =============================================================================
DEFAULT_SMA_WINDOW = 200
DEFAULT_VOL_WINDOW = 30
DEFAULT_HYSTERESIS = 0.0
MIN_DATA_POINTS = 200

# =============================================================================
# ASSET FILTERING
# =============================================================================
# Precious metals excluded from main risk scan - they act as hedges (inverse correlation)
# and distort market risk scoring. Available separately in "Hedge Assets" category.
PRECIOUS_METALS = {'GC=F', 'SI=F', 'PL=F', 'PA=F', 'GLD', 'SLV'}

# =============================================================================
# POPULAR TICKERS FOR QUICK ACCESS
# =============================================================================
POPULAR_TICKERS = {
    "US Tech": ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA', 'META'],
    "Crypto": ['BTC-USD', 'ETH-USD', 'SOL-USD'],
    "ETFs": ['SPY', 'QQQ', 'IWM', 'VTI'],
}

# =============================================================================
# TICKER NAME FIXES
# =============================================================================
# Hardcoded fixes for known problematic ticker names (German stocks, etc.)
TICKER_NAME_FIXES = {
    "SIEMENS                    N": "Siemens",
    "Allianz                    v": "Allianz",
    "DEUTSCHE TELEKOM           N": "Deutsche Telekom",
    "Airbus                     A": "Airbus",
    "BAYERISCHE MOTOREN WERKE   S": "BMW",
    "VOLKSWAGEN                 V": "Volkswagen",
    "BASF                       N": "BASF",
    "MUENCHENER RUECKVERS.-GES. N": "Munich Re",
    "SAP                       ": "SAP"
}

SPECIAL_TICKER_NAMES = {
    "^GDAXI": "DAX 40 Index"
}

# =============================================================================
# REGIME CLASSIFICATION COLORS
# =============================================================================
REGIME_COLORS = {
    'STABLE': '#00C864',      # Green
    'ACTIVE': '#FFCC00',      # Yellow
    'HIGH_ENERGY': '#FF6600', # Orange
    'CRITICAL': '#FF4040',    # Red
    'DORMANT': '#888888'      # Grey
}

REGIME_COLORS_TRANSPARENT = {
    'STABLE': 'rgba(0, 200, 100, 0.15)',
    'ACTIVE': 'rgba(255, 204, 0, 0.15)',
    'HIGH_ENERGY': 'rgba(255, 102, 0, 0.15)',
    'CRITICAL': 'rgba(255, 64, 64, 0.15)',
    'DORMANT': 'rgba(136, 136, 136, 0.2)'
}

REGIME_EMOJIS = {
    'STABLE': '🟢',
    'ACTIVE': '🟡',
    'HIGH_ENERGY': '🟠',
    'CRITICAL': '🔴',
    'DORMANT': '⚪'
}

# =============================================================================
# STRESS LEVEL COLORS (Scientific Heritage Theme)
# =============================================================================
STRESS_LEVEL_COLORS = {
    'BASELINE': '#27AE60',   # Moss Green
    'MODERATE': '#D35400',   # Ochre
    'HEIGHTENED': '#D35400', # Ochre
    'ELEVATED': '#C0392B'    # Terracotta
}

STRESS_LEVEL_EMOJIS = {
    'BASELINE': '🟢',
    'MODERATE': '🟡',
    'HEIGHTENED': '🟠',
    'ELEVATED': '🔴'
}

# =============================================================================
# THEME COLORS - Scientific Heritage Design System
# =============================================================================
HERITAGE_THEME = {
    "bg": "#F9F7F1",        # Alabaster / Warm Paper
    "bg2": "#E6E1D3",       # Parchment / Linen
    "card": "#FFFFFF",      # Pure white on cream background
    "border": "#D1C4E9",    # Subtle border
    "text": "#333333",      # Charcoal
    "muted": "#666666",     # Muted charcoal
    "input": "#FFFFFF",     # White input fields
    "primary": "#2C3E50",   # Midnight Blue (brand color)
    "shadow": "2px 2px 5px rgba(0,0,0,0.05)"  # Subtle paper shadow
}

# Regime colors - earthier tones for "printed" look
REGIME_COLORS = {
    'STABLE': '#27AE60',     # Moss Green
    'ACTIVE': '#D35400',     # Ochre
    'HIGH_ENERGY': '#D35400', # Ochre (same as active)
    'CRITICAL': '#C0392B',   # Terracotta
    'DORMANT': '#95A5A6'     # Stone Grey
}

# =============================================================================
# LEGAL DISCLAIMER TEXT
# =============================================================================
LEGAL_DISCLAIMER = """
<div class="disclaimer-box">
    <h2>⚠️ Important Legal Disclaimer</h2>
    
    <h3>📊 For Educational & Research Purposes Only</h3>
    <p>
        This tool is designed for <strong>educational and informational purposes only</strong>. 
        It is <strong>NOT</strong> intended to provide financial, investment, or trading advice.
    </p>
    
    <h3>🔬 Experimental Analysis Tool</h3>
    <p>
        The Self-Organized Criticality (SOC) analysis presented here is based on academic research 
        and statistical models. Past performance and historical patterns <strong>do not guarantee 
        future results</strong>.
    </p>
    
    <h3>⚠️ No Investment Recommendations</h3>
    <p>
        <strong>Nothing on this platform constitutes financial advice.</strong> We do not recommend 
        buying, selling, or holding any financial instrument. All investment decisions are your own 
        responsibility.
    </p>
    
    <h3>📉 Risk Warning</h3>
    <ul>
        <li>Trading and investing involve <strong>substantial risk of loss</strong></li>
        <li>You may lose some or all of your invested capital</li>
        <li>Never invest money you cannot afford to lose</li>
        <li>Market volatility can result in rapid and significant losses</li>
    </ul>
    
    <h3>🛡️ No Warranty</h3>
    <p>
        This tool is provided <strong>"as is"</strong> without any warranty, express or implied. 
        We make no guarantees about the accuracy, reliability, or completeness of any data or analysis.
    </p>
    
    <h3>💼 Consult a Professional</h3>
    <p>
        Before making any investment decision, consult with a <strong>licensed financial advisor</strong> 
        who understands your individual financial situation, goals, and risk tolerance.
    </p>
    
    <h3>📝 Your Responsibility</h3>
    <p>
        By using this tool, you acknowledge that:
    </p>
    <ul>
        <li>You are using it for educational purposes only</li>
        <li>You understand the risks involved in financial markets</li>
        <li>You will not hold the developers liable for any losses</li>
        <li>You agree to conduct your own due diligence</li>
    </ul>
    
    <hr style="border-color: #444; margin: 1.5rem 0;">
    
    <p style="text-align: center; font-size: 0.9rem; color: #888;">
        <strong>If you do not agree to these terms, please do not use this tool.</strong>
    </p>
</div>
"""

# =============================================================================
# SIMULATION DEFAULTS
# =============================================================================
DEFAULT_INITIAL_CAPITAL = 10000
DEFAULT_SIMULATION_YEARS = 7
DEFAULT_TRADING_FEE_PCT = 0.1
DEFAULT_INTEREST_RATE_ANNUAL = 4.0

# =============================================================================
# CHART COLORS FOR PLOTLY (Scientific Heritage Theme)
# =============================================================================
CHART_COLORS = {
    'price': '#2C3E50',      # Midnight Blue
    'sma': '#D35400',        # Ochre
    'volatility': '#C0392B', # Terracotta
    'positive': '#27AE60',   # Moss Green
    'negative': '#C0392B',   # Terracotta
    'neutral': '#95A5A6'     # Stone Grey
}

# =============================================================================
# SCIENTIFIC HERITAGE CSS
# =============================================================================
def get_scientific_heritage_css() -> str:
    """
    Returns CSS for Scientific Heritage design system.
    
    Typography:
        - Merriweather (serif) for headings
        - Lato (sans-serif) for body text
    
    Visual Style:
        - Warm paper background
        - Subtle shadows for depth
        - Earth-tone accent colors
    """
    return """
    <style>
        /* Import Roboto Slab as fallback for Rockwell */
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@300;400;700&family=Roboto+Condensed:wght@300;400;700&display=swap');
        
        /* Import Material Icons for sidebar and UI icons */
        @import url('https://fonts.googleapis.com/css2?family=Material+Icons');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
        
        /* Hide keyboard shortcut tooltips/badges (but not sidebar or essential UI) */
        /* Removed overly broad selectors that were hiding sidebar collapse button */
        [data-testid="stTooltipHoverTarget"]:not([class*="sidebar"]),
        .stTooltipIcon:not([class*="sidebar"]),
        [data-testid="stTooltipIcon"]:not([class*="sidebar"]) {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
        }
        
        /* Plotly Modebar (chart action icons) - Heritage design */
        .modebar {
            background-color: #F9F7F1 !important;
            border: 1px solid #333333 !important;
            border-radius: 4px !important;
            padding: 2px !important;
        }
        
        .modebar-btn {
            font-size: 12px !important;
        }
        
        .modebar-btn svg {
            width: 12px !important;
            height: 12px !important;
        }
        
        .modebar-btn path {
            fill: #333333 !important;
        }
        
        .modebar-btn:hover path {
            fill: #2C3E50 !important;
        }
        
        .modebar-group {
            padding: 2px !important;
        }
        
        /* Global background */
        .stApp {
            background-color: #F9F7F1 !important;
        }
        
        /* Headings and all text in Rockwell Condensed */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Slab', 'Courier New', serif !important;
            color: #2C3E50 !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px !important;
        }
        
        /* Body text also in Rockwell Condensed for consistency */
        p, div, label, span, input, textarea {
            font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Condensed', 'Arial Narrow', sans-serif !important;
            color: #333333 !important;
        }
        
        /* Cards/Containers: like stacked paper */
        div[data-testid="stMetric"], 
        div[data-testid="column"] {
            background-color: #FFFFFF !important;
            border: 1px solid #D1C4E9 !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05) !important;
            padding: 15px !important;
            border-radius: 2px !important;
        }
        
        /* Expander styling - fix overlapping text */
        div[data-testid="stExpander"] {
            background-color: #F9F7F1 !important;
            border: 1px solid #D1C4E9 !important;
            border-radius: 2px !important;
            margin-bottom: 1rem !important;
            position: relative !important;
            z-index: 1 !important;
        }
        
        div[data-testid="stExpander"] summary {
            font-family: 'Merriweather', serif !important;
            color: #2C3E50 !important;
            font-weight: 600 !important;
            padding: 16px 12px !important;
            line-height: 1.8 !important;
            min-height: 56px !important;
            display: flex !important;
            align-items: center !important;
            position: relative !important;
            z-index: 2 !important;
            background: #F9F7F1 !important;
        }
        
        div[data-testid="stExpander"] div[role="button"] {
            line-height: 1.8 !important;
            min-height: 56px !important;
            padding: 16px 12px !important;
            background-color: #F9F7F1 !important;
        }
        
        /* Expander content area */
        div[data-testid="stExpander"] > div:not([data-testid="stExpanderDetails"]) {
            background-color: #F9F7F1 !important;
        }
        
        div[data-testid="stExpanderDetails"] {
            background-color: #F9F7F1 !important;
        }
        
        div[data-testid="stExpander"] summary p {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.8 !important;
            position: relative !important;
            z-index: 3 !important;
        }
        
        /* Allow expander text to show */
        div[data-testid="stExpander"] summary > div {
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
        }
        
        /* Ensure expander label text is visible - REMOVED to fix sidebar icons */
        /* This was hiding sidebar collapse button icons */


        /* 2. Fail-Safe: Stelle sicher, dass der Titel-Text (meistens <p>) sichtbar bleibt */
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary span:not([title*="shortcut"]) {
            font-size: 1rem !important; /* Oder deine gewünschte Größe */
            opacity: 1 !important;
            display: block !important;
            visibility: visible !important;
            color: #2C3E50 !important; /* Midnight Blue */
            }
        
        /* Expander icons - ensure SVG arrows are visible */
        div[data-testid="stExpander"] summary svg {
            display: block !important;
            visibility: visible !important;
            width: 1rem !important;
            height: 1rem !important;
        }

        /* ALL BUTTONS - Cream background, charcoal border & text */
        /* Exclude sidebar collapse button from custom styling */
        .stButton>button:not([class*="collapsedControl"]),
        .stButton button:not([class*="collapsedControl"]),
        button:not([class*="collapsedControl"]):not([data-testid*="collapsedControl"]),
        button[kind="primary"]:not([class*="collapsedControl"]),
        button[kind="secondary"]:not([class*="collapsedControl"]),
        button[type="submit"]:not([class*="collapsedControl"]),
        button[data-testid="baseButton-primary"]:not([class*="collapsedControl"]),
        button[data-testid="baseButton-secondary"]:not([class*="collapsedControl"]),
        div[data-testid="stButton"] button:not([class*="collapsedControl"]),
        div.stButton > button:not([class*="collapsedControl"]) {
            border-radius: 4px !important;
            font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Slab', serif !important;
            font-weight: bold !important;
            transition: all 0.2s ease !important;
            letter-spacing: 0.5px !important;
            border: 1px solid #333333 !important;
            background-color: #F9F7F1 !important;
            background: #F9F7F1 !important;
            color: #333333 !important;
        }
        
        /* Sidebar collapse button - preserve default Streamlit styling */
        button[class*="collapsedControl"],
        button[data-testid*="collapsedControl"],
        section[data-testid="stSidebar"] button[kind="header"] {
            all: revert !important;
        }
        
        /* Preserve icon fonts (Material Icons, etc.) */
        button [class*="material-icons"],
        button [class*="icon"],
        button svg,
        span[class*="material-icons"],
        i[class*="material-icons"] {
            font-family: 'Material Icons', 'Material Icons Extended' !important;
        }
        
        /* Text inside buttons - FORCE charcoal color (but not icons) */
        .stButton>button p:not([class*="icon"]),
        .stButton>button span:not([class*="icon"]):not([class*="material"]),
        .stButton>button div:not([class*="icon"]),
        button:not([class*="collapsedControl"]) p:not([class*="icon"]),
        button:not([class*="collapsedControl"]) span:not([class*="icon"]):not([class*="material"]),
        button:not([class*="collapsedControl"]) div:not([class*="icon"]) {
            color: #333333 !important;
        }
        
        .stButton>button:not([class*="collapsedControl"]):hover,
        .stButton button:not([class*="collapsedControl"]):hover,
        button:not([class*="collapsedControl"]):hover,
        button[kind="primary"]:not([class*="collapsedControl"]):hover,
        button[kind="secondary"]:not([class*="collapsedControl"]):hover,
        button[data-testid="baseButton-primary"]:not([class*="collapsedControl"]):hover,
        button[data-testid="baseButton-secondary"]:not([class*="collapsedControl"]):hover,
        div[data-testid="stButton"] button:not([class*="collapsedControl"]):hover,
        div.stButton > button:not([class*="collapsedControl"]):hover {
            background-color: #E6E1D3 !important;
            background: #E6E1D3 !important;
            border-color: #333333 !important;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.1) !important;
            color: #333333 !important;
        }
        
        .stButton>button:not([class*="collapsedControl"]):hover *:not([class*="icon"]):not([class*="material"]),
        button:not([class*="collapsedControl"]):hover *:not([class*="icon"]):not([class*="material"]) {
            color: #333333 !important;
        }
        
        /* Disabled buttons */
        .stButton>button:disabled,
        button:disabled {
            opacity: 0.4 !important;
            cursor: not-allowed !important;
        }
        
        /* Form submit buttons */
        button[type="submit"] {
            font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Slab', serif !important;
            font-weight: bold !important;
            background-color: #2C3E50 !important;
            border: 2px solid #2C3E50 !important;
            color: #F9F7F1 !important;
        }
        
        /* Input fields */
        input, textarea, select {
            background-color: #FFFFFF !important;
            border: 1px solid #D1C4E9 !important;
            color: #333333 !important;
            font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Condensed', sans-serif !important;
        }
        
        /* Tables */
        table {
            font-family: 'Rockwell Std Condensed', 'Rockwell', 'Roboto Condensed', sans-serif !important;
        }
        
        /* Links */
        a {
            color: #2C3E50 !important;
            text-decoration: underline !important;
        }
        
        /* Sidebar (if used) */
        section[data-testid="stSidebar"] {
            background-color: #E6E1D3 !important;
        }
        
        /* Sidebar collapse button - force default behavior and icon rendering */
        section[data-testid="stSidebar"] button[kind="header"],
        section[data-testid="stSidebar"] button[kind="headerNoPadding"],
        button[class*="collapsedControl"],
        button[data-testid*="baseButton-header"] {
            all: revert !important;
            font-family: inherit !important;
        }
        
        /* Ensure Material Icons render in sidebar button */
        section[data-testid="stSidebar"] button span[class*="material-icons"],
        section[data-testid="stSidebar"] button span[class*="material-symbols"],
        section[data-testid="stSidebar"] button [class*="icon"],
        button[class*="collapsedControl"] span,
        button[class*="collapsedControl"] [class*="icon"],
        button[kind="header"] span,
        button[kind="headerNoPadding"] span {
            font-family: 'Material Symbols Outlined', 'Material Icons', 'Material Icons Extended' !important;
            font-size: 24px !important;
            display: inline-block !important;
            line-height: 1 !important;
            text-transform: none !important;
            letter-spacing: normal !important;
            word-wrap: normal !important;
            white-space: nowrap !important;
            direction: ltr !important;
            -webkit-font-smoothing: antialiased !important;
            text-rendering: optimizeLegibility !important;
            -moz-osx-font-smoothing: grayscale !important;
            font-feature-settings: 'liga' !important;
            font-weight: normal !important;
        }
        
        /* Hide text content in icon-only buttons (sidebar collapse) */
        button[kind="header"] p,
        button[kind="headerNoPadding"] p,
        button[class*="collapsedControl"] p {
            font-size: 0 !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            overflow: hidden !important;
            position: absolute !important;
        }
    </style>
    """

