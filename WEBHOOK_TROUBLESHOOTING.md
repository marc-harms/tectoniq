# 🐛 Webhook Troubleshooting Guide

## Problem: User Not Upgraded After Stripe Payment

**Symptoms:**
- ✅ Stripe checkout works
- ✅ Payment appears in Stripe Dashboard
- ❌ User is not upgraded to Premium
- ❌ User has to login again after redirect
- ❌ Database still shows `subscription_tier = 'free'`

---

## 🔍 Root Cause

The **webhook server** isn't receiving or processing the `checkout.session.completed` event from Stripe.

Webhooks are critical because:
1. User completes payment in Stripe
2. Stripe sends webhook event to your server
3. Webhook server updates database: `subscription_tier = 'premium'`
4. User returns to app and sees Premium status

**If webhook doesn't work** → Database never gets updated.

---

## ✅ Solution: 3-Step Fix

### **Step 1: Start Webhook Server**

**Terminal 2:**
```bash
cd /home/marc/Projects/TECTONIQ
./start_webhook.sh
```

Or manually:
```bash
cd /home/marc/Projects/TECTONIQ
source venv/bin/activate

export STRIPE_SECRET_KEY="your-sk_test-key"
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
export STRIPE_WEBHOOK_SECRET=""  # Will get this from Stripe CLI

python webhook_handler.py
```

You should see:
```
🚀 Starting TECTONIQ Webhook Server...
   Stripe configured: True
   Supabase configured: True

📡 Listening on: http://0.0.0.0:8000
```

---

### **Step 2: Start Stripe CLI**

**Terminal 3:**
```bash
stripe login  # If not already logged in
stripe listen --forward-to localhost:8000/stripe/webhook
```

You'll see:
```
> Ready! Your webhook signing secret is whsec_xxxxx (copy this!)
```

**IMPORTANT:** Copy that `whsec_xxxxx` secret!

Then:
1. Add to `.streamlit/secrets.toml`:
   ```toml
   STRIPE_WEBHOOK_SECRET = "whsec_xxxxx"
   ```

2. Export in Terminal 2:
   ```bash
   export STRIPE_WEBHOOK_SECRET="whsec_xxxxx"
   ```

3. Restart webhook server (Ctrl+C and run again)

---

### **Step 3: Test Payment Again**

1. Go to TECTONIQ app
2. Login as Free user
3. Click "Upgrade to Premium"
4. Use test card: `4242 4242 4242 4242`
5. Complete payment

**Watch Terminal 2** - You should see:
```
📥 Received Stripe event: checkout.session.completed
✅ User e3a2a991-9b79-4e05-b3a2-844a00075e04 upgraded to Premium
   Customer ID: cus_xxxxx
   Subscription ID: sub_xxxxx
```

**Watch Terminal 3** - You should see:
```
2025-12-11 10:30:15  --> checkout.session.completed [evt_xxxxx]
2025-12-11 10:30:15  <-- [200] POST http://localhost:8000/stripe/webhook
```

---

## ✅ Verification Checklist

After payment:

- [ ] Webhook server shows "✅ User upgraded to Premium"
- [ ] Stripe CLI shows `[200]` response
- [ ] Supabase `profiles` table shows `subscription_tier = 'premium'`
- [ ] TECTONIQ sidebar shows "⭐ PREMIUM"
- [ ] Deep Dive charts are unlocked
- [ ] Monte Carlo forecast is unlocked

---

## 🔄 Manual Upgrade (Temporary Workaround)

If webhook still doesn't work, manually upgrade yourself:

1. Open **Supabase Dashboard** → **SQL Editor**
2. Run `manual_upgrade.sql` (in project root)
3. Change email to your email
4. Run query
5. Refresh TECTONIQ app

You should instantly see Premium status.

---

## 🐛 Common Issues

### **Issue 1: "Supabase not initialized" in webhook logs**

**Problem:** Webhook server can't connect to Supabase

**Fix:**
```bash
# Verify environment variables are set
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Should NOT be empty
# If empty, export them and restart webhook server
```

---

### **Issue 2: "No user_id found in checkout session"**

**Problem:** Stripe metadata missing user_id

**Fix:** Check `stripe_manager.py` line 75:
```python
metadata={
    'supabase_user_id': user_id,  # Must be set
    'tier': 'premium',
    'source': 'tectoniq_app'
}
```

---

### **Issue 3: Stripe CLI not forwarding events**

**Problem:** Stripe CLI not running or wrong endpoint

**Fix:**
```bash
# Check if Stripe CLI is running
ps aux | grep stripe

# If not running, start it:
stripe listen --forward-to localhost:8000/stripe/webhook

# Verify endpoint is correct (should be /stripe/webhook, not /webhook)
```

---

### **Issue 4: Webhook server not running**

**Problem:** Forgot to start Terminal 2

**Fix:**
```bash
# Start webhook server
cd /home/marc/Projects/TECTONIQ
./start_webhook.sh

# Keep this terminal open!
```

---

## 📊 Debug: Check What Happened

### **Check Supabase Database:**
```sql
SELECT 
    email,
    subscription_tier,
    stripe_customer_id,
    stripe_subscription_id,
    subscription_status,
    updated_at
FROM profiles
WHERE email = 'your-email@example.com';
```

**If `stripe_customer_id` is NULL** → Webhook never fired

---

### **Check Stripe Dashboard:**

1. Go to: https://dashboard.stripe.com/test/events
2. Find `checkout.session.completed` event
3. Click on it
4. Check "Webhook attempts"
5. If 0 attempts → Webhook not configured
6. If failed attempts → Check error message

---

### **Check Webhook Server Logs:**

Look at Terminal 2 output for errors:

**Good:**
```
✅ User [id] upgraded to Premium
```

**Bad:**
```
❌ Error upgrading user: [error message]
⚠️  No user_id found in checkout session
```

---

## 🎯 Testing Commands

### **Trigger Test Webhook (Without Real Payment):**
```bash
# In Terminal 3 (Stripe CLI):
stripe trigger checkout.session.completed

# Should trigger webhook and upgrade a test user
```

### **Check Webhook Health:**
```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "service": "TECTONIQ Stripe Webhooks",
  "stripe_configured": true,
  "supabase_configured": true
}
```

### **List Recent Stripe Events:**
```bash
stripe events list --limit 10
```

---

## 🚀 Production Checklist

Before going live:

- [ ] Deploy webhook server to production server
- [ ] Get production domain (e.g., `https://api.tectoniq.app`)
- [ ] Configure webhook in Stripe Dashboard (not CLI)
- [ ] Test with live mode keys
- [ ] Test with real (small) payment

---

## 📞 Still Not Working?

If nothing works:

1. **Check all 3 terminals are running:**
   - Terminal 1: `streamlit run app.py`
   - Terminal 2: `python webhook_handler.py`
   - Terminal 3: `stripe listen --forward-to ...`

2. **Verify secrets are correct:**
   - Check `.streamlit/secrets.toml`
   - Check environment variables in Terminal 2

3. **Check Supabase schema:**
   - Run `supabase_stripe_schema.sql` if not done
   - Verify columns exist

4. **Manual upgrade as workaround:**
   - Use `manual_upgrade.sql`
   - Continue debugging webhook for future users

---

## ✅ Success Indicators

Everything is working when:

1. **Terminal 2** shows: `✅ User upgraded to Premium`
2. **Terminal 3** shows: `[200] POST http://localhost:8000/stripe/webhook`
3. **Supabase** shows: `subscription_tier = 'premium'`
4. **TECTONIQ** shows: "⭐ PREMIUM" in sidebar
5. **Features** unlocked: Deep Dive + Monte Carlo

---

**Quick Fix:** Use `manual_upgrade.sql` to upgrade yourself now, then debug webhook for automation.

