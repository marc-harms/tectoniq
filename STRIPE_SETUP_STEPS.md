# 🚀 TECTONIQ Stripe Setup - Quick Start Guide

## ✅ Implementation Complete!

All code is ready. Now follow these steps to activate Stripe payments:

---

## 📋 Step 1: Update Supabase Schema (2 minutes)

1. Open **Supabase Dashboard** → Your project → **SQL Editor**
2. Copy & paste contents of `supabase_stripe_schema.sql`
3. Click **Run**
4. Verify: You should see 4 new columns added to `profiles` table

---

## 🔐 Step 2: Verify Stripe Credentials in secrets.toml (1 minute)

Your `.streamlit/secrets.toml` should have these keys (you mentioned already added):

```toml
[default]
# Supabase
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"

# Stripe (Test Mode keys)
STRIPE_PUBLISHABLE_KEY = "pk_test_xxxxx"
STRIPE_SECRET_KEY = "sk_test_xxxxx"
STRIPE_PREMIUM_PRICE_ID = "price_xxxxx"  # Monthly subscription price ID
STRIPE_WEBHOOK_SECRET = ""  # Will add this later

# Stripe URLs (for local testing)
STRIPE_SUCCESS_URL = "http://localhost:8501?payment=success"
STRIPE_CANCEL_URL = "http://localhost:8501?payment=cancelled"
STRIPE_RETURN_URL = "http://localhost:8501"
```

✅ **You mentioned this is already done!**

---

## 🧪 Step 3: Test the Checkout Flow (5 minutes)

### **Terminal 1: Run Streamlit App**

```bash
cd /home/marc/Projects/TECTONIQ
source venv/bin/activate
streamlit run app.py
```

### **Terminal 2: Run Webhook Server**

```bash
cd /home/marc/Projects/TECTONIQ
source venv/bin/activate

# Set environment variables from secrets
export STRIPE_SECRET_KEY="sk_test_xxxxx"  # Use your actual key
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
export STRIPE_WEBHOOK_SECRET=""  # Empty for now

python webhook_handler.py
```

You should see:
```
🚀 Starting TECTONIQ Stripe Webhook Server...
   Stripe configured: True
   Supabase configured: True

📡 Listening on: http://0.0.0.0:8000
```

### **Terminal 3: Stripe CLI (Forward Webhooks to Local Server)**

```bash
# If you don't have Stripe CLI installed:
# https://stripe.com/docs/stripe-cli

stripe login  # Login to your Stripe account

stripe listen --forward-to localhost:8000/stripe/webhook
```

You'll see output like:
```
> Ready! Your webhook signing secret is whsec_xxxxx
```

**IMPORTANT:** Copy that `whsec_xxxxx` and:
1. Add to `.streamlit/secrets.toml`: `STRIPE_WEBHOOK_SECRET = "whsec_xxxxx"`
2. Export in Terminal 2: `export STRIPE_WEBHOOK_SECRET="whsec_xxxxx"`
3. Restart webhook server (Terminal 2)

---

## 💳 Step 4: Test Payment Flow (3 minutes)

1. **Login** to TECTONIQ as a Free user
2. Click **"Upgrade to Premium"** button (in sidebar or on locked feature)
3. You'll be redirected to **Stripe Checkout**
4. Use **test card**: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits
5. Complete payment
6. You'll be redirected back to TECTONIQ

**Check:**
- ✅ Terminal 2 (webhook server) shows: "✅ User [id] upgraded to Premium"
- ✅ Supabase profiles table shows `subscription_tier = 'premium'`
- ✅ TECTONIQ sidebar shows "⭐ PREMIUM"
- ✅ Deep Dive and Monte Carlo features are now unlocked

---

## 🎉 Success Indicators

If everything works, you should see:

### **In Terminal 2 (Webhook Server):**
```
📥 Received Stripe event: checkout.session.completed
✅ User e3a2a991-9b79-4e05-b3a2-844a00075e04 upgraded to Premium
   Customer ID: cus_xxxxx
   Subscription ID: sub_xxxxx
```

### **In Terminal 3 (Stripe CLI):**
```
2025-12-11 10:30:15  --> checkout.session.completed [evt_xxxxx]
2025-12-11 10:30:15  <-- [200] POST http://localhost:8000/stripe/webhook
```

### **In TECTONIQ App:**
- Sidebar shows: **Tier: ⭐ PREMIUM**
- "Manage Subscription" button appears
- Deep Dive charts are visible
- Monte Carlo forecast unlocked
- No simulation limits

---

## 🐛 Troubleshooting

### **"Stripe credentials missing" error:**
→ Check `.streamlit/secrets.toml` has all keys

### **Webhook not receiving events:**
→ Make sure Stripe CLI is running (`stripe listen`)
→ Check Terminal 2 is running webhook server
→ Verify `STRIPE_WEBHOOK_SECRET` matches CLI output

### **User not upgraded after payment:**
→ Check Terminal 2 for errors
→ Verify Supabase credentials in webhook server
→ Check Supabase profiles table manually

### **"No active subscription found" when clicking Manage:**
→ User doesn't have `stripe_customer_id` in profiles
→ Complete a test payment first

---

## 🚀 Going Live (When Ready)

### **1. Activate Stripe Live Mode**
- Complete business verification in Stripe Dashboard
- Switch to "Live mode"
- Get live API keys

### **2. Update secrets.toml (Production)**
```toml
# Replace test keys with live keys
STRIPE_PUBLISHABLE_KEY = "pk_live_xxxxx"
STRIPE_SECRET_KEY = "sk_live_xxxxx"
STRIPE_PREMIUM_PRICE_ID = "price_live_xxxxx"

# Update URLs to production domain
STRIPE_SUCCESS_URL = "https://your-domain.com?payment=success"
STRIPE_CANCEL_URL = "https://your-domain.com?payment=cancelled"
STRIPE_RETURN_URL = "https://your-domain.com"
```

### **3. Deploy Webhook Server**
- Deploy `webhook_handler.py` to your server
- Or use serverless function (Vercel, AWS Lambda, etc.)

### **4. Configure Production Webhook**
- Stripe Dashboard → Webhooks → Add endpoint
- URL: `https://your-domain.com/stripe/webhook`
- Select events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
- Copy signing secret → Add to production secrets

---

## 📊 What Each File Does

| File | Purpose |
|------|---------|
| `stripe_manager.py` | Stripe API wrapper (checkout, portal, queries) |
| `webhook_handler.py` | FastAPI server to handle Stripe webhooks |
| `supabase_stripe_schema.sql` | SQL to add Stripe columns to profiles table |
| `auth_manager.py` | Updated with Stripe helper functions |
| `app.py` | Updated with real Stripe upgrade buttons |

---

## 🎯 Next Steps After Testing

1. **Test cancellation:**
   - Click "Manage Subscription" → Cancel subscription
   - User should downgrade to Free at period end

2. **Test failed payment:**
   - Use test card `4000 0000 0000 0341` (requires authentication)
   - Or `4000 0000 0000 9995` (decline)

3. **Monitor Stripe Dashboard:**
   - Check payments, subscriptions, customers
   - Review webhook event logs

4. **Production deployment:**
   - Follow "Going Live" section above

---

## 💡 Quick Reference

### **Test Cards:**
| Card | Result |
|------|--------|
| `4242 4242 4242 4242` | ✅ Success |
| `4000 0000 0000 9995` | ❌ Decline |
| `4000 0000 0000 0341` | ⚠️ Requires 3D Secure |

### **Webhook Events:**
- `checkout.session.completed` → User upgraded
- `customer.subscription.updated` → Status change
- `customer.subscription.deleted` → User downgraded

### **Useful Commands:**
```bash
# Check webhook server is running
curl http://localhost:8000/health

# View Stripe CLI events
stripe events list --limit 10

# Trigger test webhook
stripe trigger checkout.session.completed
```

---

## ✅ Checklist

- [ ] Supabase schema updated (4 new columns)
- [ ] secrets.toml has all Stripe keys
- [ ] Webhook server runs without errors
- [ ] Stripe CLI forwards webhooks
- [ ] Test payment completes successfully
- [ ] User upgraded to Premium in database
- [ ] App shows Premium features unlocked
- [ ] "Manage Subscription" button works

---

**Ready to test?** Start with Step 3! 🚀

