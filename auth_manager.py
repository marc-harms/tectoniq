"""
SOC Market Seismograph - Authentication & User Management
==========================================================

Supabase integration for multi-user SaaS functionality.

Handles:
- User authentication (signup, login, logout)
- User profile management (tier: free/premium)
- Portfolio management (per-user asset lists)
- Tier-based feature gating

Author: Market Analysis Team
Version: 8.0 (Supabase Integration)
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

import streamlit as st
from supabase import create_client, Client


# =============================================================================
# SUPABASE CLIENT INITIALIZATION
# =============================================================================

def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client using secrets from Streamlit config.
    If user is authenticated, restores their session to the client.
    
    Returns:
        Configured Supabase client instance (with auth session if logged in)
    
    Raises:
        KeyError: If SUPABASE_URL or SUPABASE_KEY not found in secrets
        ValueError: If secrets are not properly configured
    """
    try:
        # Check if secrets exist
        if not hasattr(st, 'secrets') or 'SUPABASE_URL' not in st.secrets or 'SUPABASE_KEY' not in st.secrets:
            error_msg = """
            🚨 **Supabase Configuration Missing!**
            
            Please create `.streamlit/secrets.toml` with your Supabase credentials:
            
            ```toml
            [default]
            SUPABASE_URL = "https://your-project.supabase.co"
            SUPABASE_KEY = "your-anon-key-here"
            ```
            
            **How to get these:**
            1. Go to your Supabase dashboard
            2. Click: Settings → API
            3. Copy "Project URL" → SUPABASE_URL
            4. Copy "anon public" key → SUPABASE_KEY
            
            See `.streamlit/secrets.toml.template` for an example.
            """
            st.error(error_msg)
            raise ValueError("Supabase credentials not configured")
        
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        
        # Validate they're not template values
        if "your-project" in url.lower() or "your-actual" in key.lower():
            st.error("⚠️ **Please update secrets.toml with your actual Supabase credentials!**")
            raise ValueError("Supabase credentials are still template values")
        
        client = create_client(url, key)
        
        # Restore authenticated session if exists
        if 'supabase_session' in st.session_state:
            try:
                session = st.session_state['supabase_session']
                # Set the session on the client
                client.auth.set_session(session.access_token, session.refresh_token)
            except Exception as e:
                print(f"Warning: Could not restore session: {e}")
        
        return client
        
    except KeyError as e:
        st.error(f"🚨 **Missing Supabase configuration:** {e}")
        st.info("Please create `.streamlit/secrets.toml` with SUPABASE_URL and SUPABASE_KEY")
        raise
    except Exception as e:
        st.error(f"🚨 **Supabase connection error:** {str(e)}")
        raise


# =============================================================================
# AUTHENTICATION FUNCTIONS
# =============================================================================

def signup(email: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Create a new user account with Supabase Auth.
    
    Args:
        email: User's email address
        password: User's password (min 6 characters)
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str], user_data: Optional[Dict])
    
    Example:
        >>> success, error, user = signup("user@example.com", "password123")
        >>> if success:
        >>>     print(f"Welcome {user['email']}!")
    """
    try:
        supabase = get_supabase_client()
        
        # Create auth user
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            # User created successfully
            user_id = response.user.id
            user_email = response.user.email
            
            # Check if email confirmation is required
            if response.session:
                # Auto-login enabled (no email confirmation required)
                st.session_state['supabase_session'] = response.session
            else:
                # Email confirmation required - user must check their inbox
                pass
            
            # Profile is automatically created by database trigger
            # Return user data
            user_data = {
                "id": user_id,
                "email": user_email,
                "tier": "free"
            }
            return True, None, user_data
        else:
            return False, "Failed to create user account", None
            
    except Exception as e:
        # Import traceback for better error logging
        import traceback
        error_msg = str(e)
        
        # Log to console for debugging
        print(f"[SIGNUP] ERROR: {error_msg}")
        print(traceback.format_exc())
        
        # User-friendly error messages
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            return False, "This email is already registered. Please login instead.", None
        elif "password" in error_msg.lower():
            return False, "Password must be at least 6 characters", None
        elif "email" in error_msg.lower() and "invalid" in error_msg.lower():
            return False, "Please enter a valid email address", None
        else:
            # Return the actual error for debugging
            return False, f"Signup error: {error_msg}", None


def login(email: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Authenticate user with Supabase Auth.
    
    Args:
        email: User's email address
        password: User's password
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str], user_data: Optional[Dict])
    
    Example:
        >>> success, error, user = login("user@example.com", "password123")
        >>> if success:
        >>>     st.session_state.user = user
    """
    try:
        supabase = get_supabase_client()
        
        # Authenticate
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user and response.session:
            # Store the authenticated session in session_state
            st.session_state['supabase_session'] = response.session
            
            # Fetch user profile to get tier
            profile = get_user_profile(response.user.id)
            
            user_data = {
                "id": response.user.id,
                "email": response.user.email,
                "tier": profile.get("subscription_tier", "free") if profile else "free"
            }
            return True, None, user_data
        else:
            return False, "Invalid email or password", None
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        
        # Log to console for debugging
        print(f"[LOGIN] ERROR: {error_msg}")
        print(traceback.format_exc())
        
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return False, "Invalid email or password", None
        else:
            return False, f"Login error: {error_msg}", None


def logout() -> None:
    """
    Clear user session data from Streamlit session state.
    
    Note: Supabase tokens are stored client-side, so we just clear session state.
    """
    keys_to_clear = ['user', 'tier', 'portfolio', 'authenticated', 'supabase_session']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


# =============================================================================
# USER PROFILE MANAGEMENT
# =============================================================================

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user profile data from Supabase.
    
    Args:
        user_id: Supabase user UUID
    
    Returns:
        User profile dictionary with keys: user_id, email, subscription_tier, created_at
        Returns None if profile not found
    
    Example:
        >>> profile = get_user_profile("abc-123-def")
        >>> print(f"User tier: {profile['subscription_tier']}")
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching profile: {str(e)}")
        return None


def update_user_tier(user_id: str, new_tier: str) -> bool:
    """
    Update user's subscription tier (for admin use or upgrade flow).
    
    Args:
        user_id: Supabase user UUID
        new_tier: New tier ("free" or "premium")
    
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        supabase.table("profiles").update({
            "subscription_tier": new_tier,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()
        
        # Update session state if current user
        if st.session_state.get('user', {}).get('id') == user_id:
            st.session_state.user['tier'] = new_tier
            st.session_state.tier = new_tier
        
        return True
        
    except Exception as e:
        st.error(f"Error updating tier: {str(e)}")
        return False


# =============================================================================
# PORTFOLIO MANAGEMENT
# =============================================================================

def get_user_portfolio(user_id: str) -> List[str]:
    """
    Fetch user's saved portfolio (list of ticker symbols).
    
    Args:
        user_id: Supabase user UUID
    
    Returns:
        List of ticker symbols (e.g., ["AAPL", "TSLA", "BTC-USD"])
        Empty list if no portfolio found
    
    Example:
        >>> tickers = get_user_portfolio("abc-123-def")
        >>> print(f"User watches: {', '.join(tickers)}")
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("portfolios").select("ticker").eq("user_id", user_id).execute()
        
        if response.data:
            return [item['ticker'] for item in response.data]
        else:
            return []
            
    except Exception as e:
        st.error(f"Error fetching portfolio: {str(e)}")
        return []


def add_asset_to_portfolio(user_id: str, ticker: str) -> Tuple[bool, Optional[str]]:
    """
    Add a ticker to user's portfolio.
    
    Args:
        user_id: Supabase user UUID
        ticker: Ticker symbol to add (e.g., "AAPL")
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    
    Constraints:
        - No limitations on number of assets
        - No duplicates allowed
    
    Example:
        >>> success, error = add_asset_to_portfolio("abc-123", "AAPL")
        >>> if not success:
        >>>     st.error(error)
    """
    try:
        supabase = get_supabase_client()
        
        # Get current portfolio
        current_portfolio = get_user_portfolio(user_id)
        
        # Check for duplicates only
        if ticker in current_portfolio:
            return False, f"{ticker} is already in your portfolio"
        
        # No tier limits - all users have unlimited portfolio
        
        # Add to portfolio
        portfolio_data = {
            "user_id": user_id,
            "ticker": ticker,
            "added_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("portfolios").insert(portfolio_data).execute()
        
        # Update session state cache
        if 'portfolio' in st.session_state:
            st.session_state.portfolio.append(ticker)
        
        return True, None
        
    except Exception as e:
        return False, f"Error adding asset: {str(e)}"


def remove_asset_from_portfolio(user_id: str, ticker: str) -> Tuple[bool, Optional[str]]:
    """
    Remove a ticker from user's portfolio.
    
    Args:
        user_id: Supabase user UUID
        ticker: Ticker symbol to remove (e.g., "AAPL")
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    
    Example:
        >>> success, error = remove_asset_from_portfolio("abc-123", "AAPL")
        >>> if success:
        >>>     st.success("Asset removed!")
    """
    try:
        supabase = get_supabase_client()
        
        supabase.table("portfolios").delete().eq("user_id", user_id).eq("ticker", ticker).execute()
        
        # Update session state cache
        if 'portfolio' in st.session_state and ticker in st.session_state.portfolio:
            st.session_state.portfolio.remove(ticker)
        
        return True, None
        
    except Exception as e:
        return False, f"Error removing asset: {str(e)}"


# =============================================================================
# TIER-BASED FEATURE GATING
# =============================================================================

def can_access_simulation() -> bool:
    """
    Check if current user can access Simulation feature.
    
    Simulation is now FREE for all users with daily limits:
    - Free tier: 5 simulations per day
    - Premium tier: Unlimited simulations
    
    Returns:
        True (simulation available to all users with limits)
    """
    # Simulation is now free for everyone (with daily limits)
    return True


def get_simulation_count_today() -> int:
    """
    Get number of simulations run by current user today.
    
    Returns:
        Count of simulations run today (0 if not tracked)
    """
    user_id = get_current_user_id()
    if not user_id:
        return 0
    
    from datetime import date
    today = str(date.today())
    
    # Initialize tracking dict if not exists
    if 'simulation_usage' not in st.session_state:
        st.session_state.simulation_usage = {}
    
    # Get today's count
    key = f"{user_id}_{today}"
    return st.session_state.simulation_usage.get(key, 0)


def increment_simulation_count() -> None:
    """
    Increment simulation count for current user today.
    """
    user_id = get_current_user_id()
    if not user_id:
        return
    
    from datetime import date
    today = str(date.today())
    
    # Initialize tracking dict if not exists
    if 'simulation_usage' not in st.session_state:
        st.session_state.simulation_usage = {}
    
    # Increment count
    key = f"{user_id}_{today}"
    st.session_state.simulation_usage[key] = st.session_state.simulation_usage.get(key, 0) + 1


def can_run_simulation() -> tuple[bool, str]:
    """
    Check if user can run another simulation today.
    
    Returns:
        Tuple of (can_run: bool, message: str)
        - All users now have unlimited simulations
    """
    # No limits - all users have unlimited simulations
    return True, ""


def can_access_instant_alerts() -> bool:
    """
    Check if current user can access Instant Alerts feature.
    
    Returns:
        True if user is Premium, False otherwise
    """
    tier = st.session_state.get('tier', 'free')
    return tier == 'premium'


def get_portfolio_limit() -> int:
    """
    Get maximum number of assets user can save to portfolio.
    
    Returns:
        999 (unlimited for all users)
    """
    return 999  # No limits - all users have unlimited portfolio


def show_upgrade_prompt(feature_name: str = "this feature") -> None:
    """
    Display a friendly upgrade prompt for premium features.
    
    Args:
        feature_name: Name of the gated feature
    """
    st.warning(f"🔒 **Premium Feature:** {feature_name} is only available on the Premium tier.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⭐ Upgrade to Premium", use_container_width=True):
            st.info("💡 **Contact:** Upgrade options coming soon! Email support@socseismograph.com")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def is_authenticated() -> bool:
    """
    Check if a user is currently authenticated.
    
    Returns:
        True if user is logged in, False otherwise
    """
    return 'user' in st.session_state and st.session_state.user is not None


def get_current_user_id() -> Optional[str]:
    """
    Get the current authenticated user's ID.
    
    Returns:
        User ID string, or None if not authenticated
    """
    if is_authenticated():
        return st.session_state.user.get('id')
    return None


def get_current_user_email() -> Optional[str]:
    """
    Get the current authenticated user's email.
    
    Returns:
        User email string, or None if not authenticated
    """
    if is_authenticated():
        return st.session_state.user.get('email')
    return None


def get_user_tier() -> str:
    """
    Get current user's subscription tier.
    Single source of truth for tier checks throughout the app.
    
    Returns:
        str: 'public' (not authenticated), 'free', or 'premium'
    """
    if is_authenticated():
        # Get tier from session state (loaded from Supabase profile)
        return st.session_state.get('tier', 'free')
    else:
        # Not logged in
        return 'public'


# =============================================================================
# STRIPE INTEGRATION
# =============================================================================

def update_user_tier(user_id: str, new_tier: str, stripe_customer_id: Optional[str] = None, 
                     stripe_subscription_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Update user's subscription tier in Supabase.
    
    Args:
        user_id: Supabase user ID
        new_tier: 'free' or 'premium'
        stripe_customer_id: Stripe customer ID (optional)
        stripe_subscription_id: Stripe subscription ID (optional)
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        supabase = get_supabase_client()
        
        update_data = {
            'subscription_tier': new_tier,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if stripe_customer_id:
            update_data['stripe_customer_id'] = stripe_customer_id
        
        if stripe_subscription_id:
            update_data['stripe_subscription_id'] = stripe_subscription_id
        
        response = supabase.table('profiles').update(update_data).eq('user_id', user_id).execute()
        
        # Update session state
        st.session_state.tier = new_tier
        
        return True, None
        
    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_stripe_customer_id(user_id: str) -> Optional[str]:
    """
    Get Stripe customer ID for user.
    
    Args:
        user_id: Supabase user ID
    
    Returns:
        Stripe customer ID or None
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('profiles').select('stripe_customer_id').eq('user_id', user_id).single().execute()
        return response.data.get('stripe_customer_id') if response.data else None
    except Exception as e:
        print(f"Error fetching Stripe customer ID: {e}")
        return None


def get_stripe_subscription_id(user_id: str) -> Optional[str]:
    """
    Get Stripe subscription ID for user.
    
    Args:
        user_id: Supabase user ID
    
    Returns:
        Stripe subscription ID or None
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('profiles').select('stripe_subscription_id').eq('user_id', user_id).single().execute()
        return response.data.get('stripe_subscription_id') if response.data else None
    except Exception as e:
        print(f"Error fetching Stripe subscription ID: {e}")
        return None

