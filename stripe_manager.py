"""
TECTONIQ Stripe Integration
============================

Handles Stripe Checkout and Customer Portal for Premium subscriptions.

Features:
- Create checkout sessions for Premium upgrade
- Customer portal for subscription management
- Subscription status queries
- Cancellation handling

Author: TECTONIQ Team
Version: 1.0
"""

import streamlit as st
import stripe
from typing import Optional, Tuple, Dict, Any


# =============================================================================
# STRIPE CLIENT INITIALIZATION
# =============================================================================

def get_stripe_client():
    """
    Initialize Stripe client with secret key from Streamlit secrets.
    
    Returns:
        stripe module configured with API key
        
    Raises:
        KeyError: If STRIPE_SECRET_KEY not found in secrets.toml
    """
    try:
        stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
        return stripe
    except KeyError:
        st.error("🚨 **Stripe credentials missing!** Add STRIPE_SECRET_KEY to `.streamlit/secrets.toml`")
        st.stop()


# =============================================================================
# CHECKOUT SESSION
# =============================================================================

def create_checkout_session(user_email: str, user_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Create Stripe Checkout session for Premium subscription.
    
    Args:
        user_email: User's email address (pre-fills checkout form)
        user_id: Supabase user ID (stored in metadata for webhook)
    
    Returns:
        Tuple of (success, error_message, checkout_url)
        
    Example:
        >>> success, error, url = create_checkout_session("user@example.com", "uuid-123")
        >>> if success:
        >>>     st.redirect(url)
    """
    try:
        stripe_client = get_stripe_client()
        price_id = st.secrets.get("STRIPE_PREMIUM_PRICE_ID")
        
        if not price_id:
            return False, "Stripe price ID not configured. Add STRIPE_PREMIUM_PRICE_ID to secrets.toml", None
        
        # Get success/cancel URLs (defaults to localhost for development)
        success_url = st.secrets.get(
            "STRIPE_SUCCESS_URL",
            "http://localhost:8501?payment=success"
        )
        cancel_url = st.secrets.get(
            "STRIPE_CANCEL_URL",
            "http://localhost:8501?payment=cancelled"
        )
        
        # Create checkout session
        session = stripe_client.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user_email,
            client_reference_id=user_id,  # Also store in client_reference_id
            metadata={
                'supabase_user_id': user_id,
                'tier': 'premium',
                'source': 'tectoniq_app'
            },
            subscription_data={
                'metadata': {
                    'supabase_user_id': user_id
                }
            },
            # Optional: Add trial period (7 days free)
            # subscription_data={
            #     'trial_period_days': 7,
            #     'metadata': {'supabase_user_id': user_id}
            # }
        )
        
        return True, None, session.url
        
    except stripe.error.StripeError as e:
        return False, f"Stripe error: {str(e)}", None
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", None


# =============================================================================
# CUSTOMER PORTAL
# =============================================================================

def create_customer_portal_session(customer_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Create Stripe Customer Portal session for subscription management.
    
    Allows users to:
    - Update payment method
    - View invoices
    - Cancel subscription
    - Reactivate subscription
    
    Args:
        customer_id: Stripe customer ID (from profiles table)
    
    Returns:
        Tuple of (success, error_message, portal_url)
    """
    try:
        stripe_client = get_stripe_client()
        
        return_url = st.secrets.get(
            "STRIPE_RETURN_URL",
            "http://localhost:8501"
        )
        
        session = stripe_client.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        
        return True, None, session.url
        
    except stripe.error.StripeError as e:
        return False, f"Stripe error: {str(e)}", None
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", None


# =============================================================================
# SUBSCRIPTION QUERIES
# =============================================================================

def get_subscription_status(subscription_id: str) -> Dict[str, Any]:
    """
    Get subscription status from Stripe.
    
    Args:
        subscription_id: Stripe subscription ID
    
    Returns:
        Dict with subscription details:
        - status: 'active', 'past_due', 'canceled', etc.
        - current_period_end: Unix timestamp
        - cancel_at_period_end: Boolean
    """
    try:
        stripe_client = get_stripe_client()
        subscription = stripe_client.Subscription.retrieve(subscription_id)
        
        return {
            'status': subscription.status,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
        }
        
    except Exception as e:
        print(f"Error fetching subscription: {e}")
        return {}


def cancel_subscription(subscription_id: str, immediate: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Cancel subscription (at period end by default, or immediately).
    
    Args:
        subscription_id: Stripe subscription ID
        immediate: If True, cancel immediately. If False, cancel at period end.
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        stripe_client = get_stripe_client()
        
        if immediate:
            # Cancel immediately
            subscription = stripe_client.Subscription.delete(subscription_id)
        else:
            # Cancel at period end (user keeps access until billing cycle ends)
            subscription = stripe_client.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        
        return True, None
        
    except stripe.error.StripeError as e:
        return False, f"Error canceling subscription: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_currency(amount_cents: int, currency: str = "USD") -> str:
    """
    Format Stripe amount (in cents) to currency string.
    
    Args:
        amount_cents: Amount in cents (e.g., 2900 for $29.00)
        currency: Currency code (default: USD)
    
    Returns:
        Formatted string (e.g., "$29.00")
    """
    amount_dollars = amount_cents / 100
    
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£'
    }
    
    symbol = currency_symbols.get(currency.upper(), currency.upper())
    return f"{symbol}{amount_dollars:.2f}"


def validate_stripe_config() -> Tuple[bool, Optional[str]]:
    """
    Validate that all required Stripe secrets are configured.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_keys = [
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_PREMIUM_PRICE_ID"
    ]
    
    missing = []
    for key in required_keys:
        if key not in st.secrets:
            missing.append(key)
    
    if missing:
        return False, f"Missing Stripe config: {', '.join(missing)}"
    
    return True, None
