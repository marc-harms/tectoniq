# 💳 Stripe Integration Guide for TECTONIQ

## 🎯 Goal

Enable users to upgrade from **Free → Premium** tier via Stripe subscription payments.

---

## 📋 Overview

**What We'll Build:**
1. Stripe account setup
2. Product/Price creation in Stripe dashboard
3. Checkout flow (redirect to Stripe hosted page)
4. Webhook to handle successful payment
5. Auto-upgrade user tier in Supabase
6. Subscription management (cancel, reactivate)

---

## 🚀 Phase 1: Stripe Account Setup (5 minutes)

### **Step 1: Create Stripe Account**

1. Go to: https://stripe.com
2. Click "Start now" (or "Sign in" if you have account)
3. Create account:
   - Email
   - Country (important for tax/compliance)
   - Business name: "TECTONIQ" or your legal entity

4. **Activate account:**
   - You'll start in "Test mode" ✅ (perfect for development)
   - Can activate live mode later (requires business verification)

---

### **Step 2: Get API Keys**

1. In Stripe Dashboard, go to: **Developers** → **API keys**
2. You'll see 4 keys:

```
Test Mode:
├─ Publishable key: pk_test_xxxxx (safe to expose in frontend)
└─ Secret key: sk_test_xxxxx (NEVER expose, backend only)

Live Mode: (after activation)
├─ Publishable key: pk_live_xxxxx
└─ Secret key: sk_live_xxxxx
```

3. Copy **Test Mode** keys for now
4. Add to `.streamlit/secrets.toml`:

```toml
[default]
SUPABASE_URL = "..."
SUPABASE_KEY = "..."

# Stripe (Test Mode)
STRIPE_PUBLISHABLE_KEY = "pk_test_xxxxx"
STRIPE_SECRET_KEY = "sk_test_xxxxx"
STRIPE_WEBHOOK_SECRET = ""  # Will get this later
```

---

## 🏷️ Phase 2: Create Product & Price (3 minutes)

### **Step 1: Create Product**

1. In Stripe Dashboard: **Product catalog** → **Add product**
2. Fill in:
   - **Name:** `TECTONIQ Premium`
   - **Description:** `Unlimited simulations, Deep Dive charts, Monte Carlo forecasting`
   - **Image:** (optional, upload logo)
3. Click "Save product"

---

### **Step 2: Create Price**

1. In the product you just created, click **Add price**
2. Configure:
   - **Price:** `29` (or your chosen amount)
   - **Currency:** `USD` (or your currency)
   - **Billing period:** `Recurring` → `Monthly`
   - **Price ID:** Will auto-generate (e.g., `price_xxxxx`) - **copy this!**

3. Click "Save"

---

### **Step 3: Save Price ID**

Add to `secrets.toml`:

```toml
# Stripe Product IDs
STRIPE_PREMIUM_PRICE_ID = "price_xxxxx"  # Monthly subscription
```

---

## 💻 Phase 3: Install Stripe SDK (1 minute)

```bash
cd /home/marc/Projects/TECTONIQ
source venv/bin/activate
pip install stripe
pip freeze > requirements.txt
```

---

## 🛠️ Phase 4: Implement Checkout Flow (Code Changes)

### **File 1: Create `stripe_manager.py`**

```python
"""
Stripe integration for TECTONIQ Premium subscriptions.
"""

import streamlit as st
import stripe
from typing import Optional, Tuple, Dict, Any

# Initialize Stripe
def get_stripe_client():
    """Initialize Stripe client with secret key."""
    try:
        stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
        return stripe
    except KeyError:
        st.error("Stripe credentials missing! Add to secrets.toml")
        st.stop()


def create_checkout_session(user_email: str, user_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Create Stripe Checkout session for Premium subscription.
    
    Args:
        user_email: User's email address
        user_id: Supabase user ID (stored in metadata)
    
    Returns:
        Tuple of (success, error_message, checkout_url)
    """
    try:
        stripe_client = get_stripe_client()
        price_id = st.secrets["STRIPE_PREMIUM_PRICE_ID"]
        
        # Create checkout session
        session = stripe_client.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=st.secrets.get(
                "STRIPE_SUCCESS_URL",
                "http://localhost:8501?payment=success"
            ),
            cancel_url=st.secrets.get(
                "STRIPE_CANCEL_URL",
                "http://localhost:8501?payment=cancelled"
            ),
            customer_email=user_email,
            metadata={
                'supabase_user_id': user_id,
                'tier': 'premium'
            },
            subscription_data={
                'metadata': {
                    'supabase_user_id': user_id
                }
            }
        )
        
        return True, None, session.url
        
    except Exception as e:
        return False, f"Stripe error: {str(e)}", None


def create_customer_portal_session(customer_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Create Stripe Customer Portal session for subscription management.
    
    Args:
        customer_id: Stripe customer ID
    
    Returns:
        Tuple of (success, error_message, portal_url)
    """
    try:
        stripe_client = get_stripe_client()
        
        session = stripe_client.billing_portal.Session.create(
            customer=customer_id,
            return_url=st.secrets.get(
                "STRIPE_RETURN_URL",
                "http://localhost:8501"
            ),
        )
        
        return True, None, session.url
        
    except Exception as e:
        return False, f"Stripe error: {str(e)}", None


def get_subscription_status(subscription_id: str) -> Dict[str, Any]:
    """
    Get subscription status from Stripe.
    
    Args:
        subscription_id: Stripe subscription ID
    
    Returns:
        Dict with subscription details
    """
    try:
        stripe_client = get_stripe_client()
        subscription = stripe_client.Subscription.retrieve(subscription_id)
        
        return {
            'status': subscription.status,  # active, past_due, canceled, etc.
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
        }
        
    except Exception as e:
        print(f"Error fetching subscription: {e}")
        return {}


def cancel_subscription(subscription_id: str) -> Tuple[bool, Optional[str]]:
    """
    Cancel subscription at period end (no immediate termination).
    
    Args:
        subscription_id: Stripe subscription ID
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        stripe_client = get_stripe_client()
        
        # Cancel at period end (user keeps access until billing cycle ends)
        subscription = stripe_client.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        
        return True, None
        
    except Exception as e:
        return False, f"Error canceling subscription: {str(e)}"
```

---

### **File 2: Update `auth_manager.py`**

Add these functions:

```python
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
            'subscription_tier': new_tier
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
    except:
        return None
```

---

### **File 3: Update Supabase `profiles` Table**

Add Stripe fields to profiles table:

```sql
-- In Supabase SQL Editor:

ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'free',
ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMPTZ;

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_customer 
ON profiles(stripe_customer_id);
```

---

### **File 4: Update `app.py` - Add Upgrade Button**

Replace the placeholder upgrade button:

```python
# Around line 248 (in show_upgrade_dialog function)

if tier == "free":
    st.markdown("""
    **Upgrade to Premium to unlock:**
    - ✅ Full Deep Dive analysis with charts
    - ✅ Unlimited simulations
    - ✅ Monte Carlo forecasting
    - ✅ Advanced crash detection
    """)
    
    st.markdown("**💰 Only $29/month** - Cancel anytime")
    
    if st.button("⭐ Upgrade to Premium Now", use_container_width=True, type="primary"):
        # Import Stripe manager
        from stripe_manager import create_checkout_session
        from auth_manager import get_current_user_id, get_current_user_email
        
        user_id = get_current_user_id()
        user_email = get_current_user_email()
        
        with st.spinner("🔄 Redirecting to secure checkout..."):
            success, error, checkout_url = create_checkout_session(user_email, user_id)
            
            if success:
                st.success("✅ Redirecting to Stripe...")
                st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)
                st.markdown(f"[Click here if not redirected automatically]({checkout_url})")
            else:
                st.error(f"❌ {error}")
```

---

## 🎣 Phase 5: Handle Stripe Webhooks (Critical!)

**Why Webhooks?**
- Stripe sends events when payment succeeds/fails
- We need to upgrade user tier automatically
- Can't rely on redirect alone (user might close browser)

---

### **Step 1: Create Webhook Endpoint**

Create `webhook_handler.py`:

```python
"""
Stripe webhook handler for TECTONIQ.
This file should be run as a separate FastAPI server.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import stripe
import os
from supabase import create_client, Client

# Initialize
app = FastAPI()

# Load secrets (use environment variables in production)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

stripe.api_key = STRIPE_SECRET_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_success(session)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_update(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancel(subscription)
    
    return JSONResponse(content={"status": "success"})


def handle_checkout_success(session):
    """
    Upgrade user to Premium after successful payment.
    """
    user_id = session['metadata']['supabase_user_id']
    customer_id = session['customer']
    subscription_id = session['subscription']
    
    try:
        # Update Supabase profile
        supabase.table('profiles').update({
            'subscription_tier': 'premium',
            'stripe_customer_id': customer_id,
            'stripe_subscription_id': subscription_id,
            'subscription_status': 'active'
        }).eq('user_id', user_id).execute()
        
        print(f"✅ User {user_id} upgraded to Premium")
    except Exception as e:
        print(f"❌ Error upgrading user: {e}")


def handle_subscription_update(subscription):
    """
    Handle subscription status changes (renewal, past_due, etc.)
    """
    subscription_id = subscription['id']
    status = subscription['status']
    
    try:
        # Update subscription status in Supabase
        supabase.table('profiles').update({
            'subscription_status': status
        }).eq('stripe_subscription_id', subscription_id).execute()
        
        # If subscription is no longer active, downgrade to free
        if status in ['canceled', 'unpaid', 'past_due']:
            supabase.table('profiles').update({
                'subscription_tier': 'free'
            }).eq('stripe_subscription_id', subscription_id).execute()
            
        print(f"✅ Subscription {subscription_id} status: {status}")
    except Exception as e:
        print(f"❌ Error updating subscription: {e}")


def handle_subscription_cancel(subscription):
    """
    Downgrade user to Free when subscription is canceled.
    """
    subscription_id = subscription['id']
    
    try:
        supabase.table('profiles').update({
            'subscription_tier': 'free',
            'subscription_status': 'canceled'
        }).eq('stripe_subscription_id', subscription_id).execute()
        
        print(f"✅ Subscription {subscription_id} canceled")
    except Exception as e:
        print(f"❌ Error canceling subscription: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### **Step 2: Install FastAPI**

```bash
pip install fastapi uvicorn python-multipart
pip freeze > requirements.txt
```

---

### **Step 3: Run Webhook Server Locally (Testing)**

Terminal 1 (Streamlit app):
```bash
streamlit run app.py
```

Terminal 2 (Webhook server):
```bash
python webhook_handler.py
```

Terminal 3 (Stripe CLI - forwards webhooks to local server):
```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli
stripe login
stripe listen --forward-to localhost:8000/stripe/webhook
```

The Stripe CLI will output a webhook secret:
```
> Ready! Your webhook signing secret is whsec_xxxxx
```

Copy this to `secrets.toml`:
```toml
STRIPE_WEBHOOK_SECRET = "whsec_xxxxx"
```

---

### **Step 4: Configure Webhook in Stripe Dashboard (Production)**

1. Go to: **Developers** → **Webhooks**
2. Click "Add endpoint"
3. Enter URL: `https://your-domain.com/stripe/webhook`
4. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Click "Add endpoint"
6. Copy **Signing secret** → Add to production secrets

---

## 🧪 Phase 6: Testing the Flow

### **Test Checkout (Test Mode):**

1. Login as Free user
2. Click "Upgrade to Premium"
3. Redirected to Stripe Checkout
4. Use test card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits
5. Complete payment
6. Redirected back to app
7. **Check:** User tier should be "premium" ✅

---

### **Test Card Numbers:**

| Card Number | Scenario |
|-------------|----------|
| `4242 4242 4242 4242` | ✅ Success |
| `4000 0000 0000 9995` | ❌ Decline (insufficient funds) |
| `4000 0000 0000 0341` | ⚠️ Requires authentication (3D Secure) |

Full list: https://stripe.com/docs/testing

---

## 🚀 Phase 7: Deployment (Production)

### **1. Activate Stripe Live Mode**

1. Complete business verification in Stripe
2. Switch to "Live mode" in dashboard
3. Get live API keys:
   - `pk_live_xxxxx`
   - `sk_live_xxxxx`

---

### **2. Update Secrets (Production)**

```toml
[production]
SUPABASE_URL = "https://your-prod-project.supabase.co"
SUPABASE_KEY = "your-prod-anon-key"

# Stripe LIVE keys
STRIPE_PUBLISHABLE_KEY = "pk_live_xxxxx"
STRIPE_SECRET_KEY = "sk_live_xxxxx"
STRIPE_WEBHOOK_SECRET = "whsec_live_xxxxx"
STRIPE_PREMIUM_PRICE_ID = "price_live_xxxxx"

# Production URLs
STRIPE_SUCCESS_URL = "https://tectoniq.app?payment=success"
STRIPE_CANCEL_URL = "https://tectoniq.app?payment=cancelled"
STRIPE_RETURN_URL = "https://tectoniq.app"
```

---

### **3. Deploy Webhook Handler**

**Option A: Same Server as Streamlit**
```bash
# Run both with supervisor or systemd
streamlit run app.py --server.port 8501
uvicorn webhook_handler:app --host 0.0.0.0 --port 8000
```

**Option B: Separate Service (Recommended)**
- Deploy webhook handler to: Railway, Render, Fly.io
- Advantages: Independent scaling, easier monitoring

---

### **4. Configure Production Webhook**

1. Stripe Dashboard → Webhooks → Add endpoint
2. URL: `https://your-domain.com/stripe/webhook`
3. Select same events as test mode
4. Copy signing secret → Production secrets

---

## 📊 Phase 8: Subscription Management UI

Add to sidebar for Premium users:

```python
# In render_sidebar_login() function (app.py)

if tier == "premium":
    st.markdown("---")
    st.markdown("### 🎟️ Manage Subscription")
    
    if st.button("📋 View Subscription Details", use_container_width=True):
        from stripe_manager import create_customer_portal_session
        from auth_manager import get_stripe_customer_id, get_current_user_id
        
        customer_id = get_stripe_customer_id(get_current_user_id())
        
        if customer_id:
            success, error, portal_url = create_customer_portal_session(customer_id)
            if success:
                st.markdown(f'<meta http-equiv="refresh" content="0; url={portal_url}">', unsafe_allow_html=True)
                st.markdown(f"[Manage Subscription →]({portal_url})")
            else:
                st.error(f"❌ {error}")
        else:
            st.error("No active subscription found")
```

**Stripe Customer Portal includes:**
- Update payment method
- View invoices
- Cancel subscription
- Reactivate subscription

---

## 💰 Pricing & Business Logic

### **Recommended Setup:**

```python
# Monthly subscription
PREMIUM_PRICE = "$29/month"
TRIAL_PERIOD_DAYS = 7  # Optional: 7-day free trial

# Stripe Price IDs (create in dashboard)
PRICE_MONTHLY = "price_xxxxx"
PRICE_ANNUAL = "price_xxxxx"  # Optional: discounted annual plan
```

### **Cancellation Policy:**
- User keeps Premium until end of billing period
- No immediate downgrade (good UX)
- Auto-downgrade to Free when subscription expires

---

## 🛡️ Security Checklist

- [ ] **Never** expose `STRIPE_SECRET_KEY` in frontend
- [ ] **Always** verify webhook signatures
- [ ] Use HTTPS in production (required by Stripe)
- [ ] Rate limit checkout endpoint (prevent spam)
- [ ] Log all Stripe events for audit trail
- [ ] Handle failed payments gracefully
- [ ] Test with Stripe test cards before going live

---

## 🐛 Troubleshooting

### **Webhook not receiving events:**
1. Check webhook URL is publicly accessible
2. Verify webhook secret matches
3. Check Stripe Dashboard → Webhooks → Logs
4. Use Stripe CLI for local testing

### **Checkout not redirecting:**
1. Check success/cancel URLs are correct
2. Verify Stripe publishable key is correct
3. Check browser console for errors

### **User not upgraded after payment:**
1. Check webhook received event
2. Verify user_id in metadata is correct
3. Check Supabase profile updated
4. Look for errors in webhook server logs

---

## 📚 Resources

- **Stripe Docs:** https://stripe.com/docs
- **Stripe Testing:** https://stripe.com/docs/testing
- **Webhook Guide:** https://stripe.com/docs/webhooks
- **Customer Portal:** https://stripe.com/docs/billing/subscriptions/customer-portal

---

## ✅ Implementation Checklist

### **Before Coding:**
- [ ] Create Stripe account
- [ ] Get API keys (test mode)
- [ ] Create Premium product
- [ ] Create price ($29/month)
- [ ] Copy price ID

### **Coding:**
- [ ] Install stripe SDK
- [ ] Create `stripe_manager.py`
- [ ] Update `auth_manager.py`
- [ ] Add Stripe fields to Supabase profiles table
- [ ] Update upgrade button in `app.py`
- [ ] Create `webhook_handler.py`
- [ ] Install FastAPI

### **Testing:**
- [ ] Run webhook server locally
- [ ] Use Stripe CLI to forward webhooks
- [ ] Test checkout with test card
- [ ] Verify user upgraded in Supabase
- [ ] Test subscription cancellation

### **Production:**
- [ ] Activate Stripe live mode
- [ ] Update secrets with live keys
- [ ] Deploy webhook handler
- [ ] Configure production webhook
- [ ] Test with real (small) payment

---

## 🎯 Next Steps

**Ready to start?** Let me know and I can:

1. ✅ Implement the code files (`stripe_manager.py`, `webhook_handler.py`)
2. ✅ Update `app.py` with real upgrade buttons
3. ✅ Update Supabase schema with Stripe fields
4. ✅ Walk you through Stripe dashboard setup
5. ✅ Help with testing

Let's get you monetized! 💰


