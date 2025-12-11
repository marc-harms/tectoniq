"""
TECTONIQ Stripe Webhook Handler
=================================

FastAPI server to handle Stripe webhook events.

Run as separate server:
    python webhook_handler.py

Events handled:
- checkout.session.completed → Upgrade user to Premium
- customer.subscription.updated → Update subscription status
- customer.subscription.deleted → Downgrade user to Free

Author: TECTONIQ Team
Version: 1.0
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import stripe
import os
from supabase import create_client, Client
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="TECTONIQ Stripe Webhooks")

# Load environment variables (or use Streamlit secrets)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize clients
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    print("⚠️  WARNING: STRIPE_SECRET_KEY not set!")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("⚠️  WARNING: Supabase credentials not set!")
    supabase = None


# =============================================================================
# WEBHOOK ENDPOINT
# =============================================================================

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    
    Stripe will POST events to this endpoint when subscriptions change.
    We verify the signature and process the event.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature header")
    
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Log event
    print(f"📥 Received Stripe event: {event['type']}")
    
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
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)
    
    else:
        print(f"⚠️  Unhandled event type: {event['type']}")
    
    return JSONResponse(content={"status": "success"})


# =============================================================================
# EVENT HANDLERS
# =============================================================================

def handle_checkout_success(session):
    """
    Upgrade user to Premium after successful payment.
    
    Called when user completes checkout.
    """
    if not supabase:
        print("❌ Supabase not initialized")
        return
    
    # Extract user info from metadata
    user_id = session.get('metadata', {}).get('supabase_user_id') or session.get('client_reference_id')
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    
    if not user_id:
        print(f"⚠️  No user_id found in checkout session: {session.get('id')}")
        return
    
    try:
        # Update Supabase profile
        update_data = {
            'subscription_tier': 'premium',
            'stripe_customer_id': customer_id,
            'stripe_subscription_id': subscription_id,
            'subscription_status': 'active',
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('profiles').update(update_data).eq('user_id', user_id).execute()
        
        print(f"✅ User {user_id} upgraded to Premium")
        print(f"   Customer ID: {customer_id}")
        print(f"   Subscription ID: {subscription_id}")
        
    except Exception as e:
        print(f"❌ Error upgrading user: {e}")


def handle_subscription_update(subscription):
    """
    Handle subscription status changes (renewal, past_due, etc.)
    
    Called when subscription status changes.
    """
    if not supabase:
        print("❌ Supabase not initialized")
        return
    
    subscription_id = subscription.get('id')
    status = subscription.get('status')
    customer_id = subscription.get('customer')
    
    # Get user_id from subscription metadata
    user_id = subscription.get('metadata', {}).get('supabase_user_id')
    
    if not user_id:
        # Fallback: Try to find user by subscription_id
        try:
            response = supabase.table('profiles').select('user_id').eq('stripe_subscription_id', subscription_id).execute()
            if response.data and len(response.data) > 0:
                user_id = response.data[0]['user_id']
        except Exception as e:
            print(f"❌ Error finding user for subscription {subscription_id}: {e}")
            return
    
    if not user_id:
        print(f"⚠️  No user found for subscription: {subscription_id}")
        return
    
    try:
        # Update subscription status
        update_data = {
            'subscription_status': status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # If subscription is no longer active, downgrade to free
        if status in ['canceled', 'unpaid', 'past_due']:
            update_data['subscription_tier'] = 'free'
            print(f"⚠️  Downgrading user {user_id} due to status: {status}")
        
        response = supabase.table('profiles').update(update_data).eq('user_id', user_id).execute()
        
        print(f"✅ Subscription {subscription_id} status updated: {status}")
        
    except Exception as e:
        print(f"❌ Error updating subscription: {e}")


def handle_subscription_cancel(subscription):
    """
    Downgrade user to Free when subscription is canceled.
    
    Called when subscription is fully canceled (not just scheduled).
    """
    if not supabase:
        print("❌ Supabase not initialized")
        return
    
    subscription_id = subscription.get('id')
    
    # Get user_id from subscription metadata or lookup
    user_id = subscription.get('metadata', {}).get('supabase_user_id')
    
    if not user_id:
        try:
            response = supabase.table('profiles').select('user_id').eq('stripe_subscription_id', subscription_id).execute()
            if response.data and len(response.data) > 0:
                user_id = response.data[0]['user_id']
        except Exception as e:
            print(f"❌ Error finding user for subscription {subscription_id}: {e}")
            return
    
    if not user_id:
        print(f"⚠️  No user found for subscription: {subscription_id}")
        return
    
    try:
        # Downgrade to free tier
        update_data = {
            'subscription_tier': 'free',
            'subscription_status': 'canceled',
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('profiles').update(update_data).eq('user_id', user_id).execute()
        
        print(f"✅ User {user_id} downgraded to Free (subscription canceled)")
        
    except Exception as e:
        print(f"❌ Error canceling subscription: {e}")


def handle_payment_failed(invoice):
    """
    Handle failed payment (notify user, update status).
    
    Called when payment fails.
    """
    if not supabase:
        print("❌ Supabase not initialized")
        return
    
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    
    print(f"⚠️  Payment failed for customer {customer_id}")
    
    # TODO: Send email notification to user
    # TODO: Update profile with payment_failed flag


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "TECTONIQ Stripe Webhooks",
        "stripe_configured": bool(STRIPE_SECRET_KEY),
        "supabase_configured": bool(supabase)
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "TECTONIQ Stripe Webhook Handler",
        "version": "1.0",
        "endpoints": {
            "webhook": "/stripe/webhook",
            "health": "/health"
        }
    }


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting TECTONIQ Stripe Webhook Server...")
    print(f"   Stripe configured: {bool(STRIPE_SECRET_KEY)}")
    print(f"   Supabase configured: {bool(supabase)}")
    print("")
    print("📡 Listening on: http://0.0.0.0:8000")
    print("📥 Webhook endpoint: http://0.0.0.0:8000/stripe/webhook")
    print("")
    print("💡 For local testing, use Stripe CLI:")
    print("   stripe listen --forward-to localhost:8000/stripe/webhook")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

