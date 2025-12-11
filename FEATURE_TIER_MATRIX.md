# 🎯 TECTONIQ Feature Tier Matrix

## Current Status & Action Plan

This document defines the **correct** feature access for each user tier and identifies what needs to be fixed in the code.

---

## 📊 Tier Definitions

### **1. Public (Unauthenticated)**
- **Goal:** Hook users with basic functionality, encourage signup
- **Strategy:** Generous free tier with gentle friction to drive conversion

### **2. Free (Authenticated, No Payment)**
- **Goal:** Showcase value, build habit, drive premium conversion
- **Strategy:** Full core features, lock advanced analytics

### **3. Premium (Paid Subscription)**
- **Goal:** Power users who need deep analysis and no limits
- **Strategy:** Everything unlocked, no restrictions

---

## ✅ Correct Feature Matrix

| Feature | Public | Free | Premium | Notes |
|---------|--------|------|---------|-------|
| **Ticker Search** | 2/hour | ✅ Unlimited | ✅ Unlimited | Drive signup with limit |
| **Hero Card** | ✅ Yes | ✅ Yes | ✅ Yes | Core value prop (always visible) |
| **Regime Detection** | ✅ Yes | ✅ Yes | ✅ Yes | Core SOC analysis (Hero Card) |
| **Volatility/Risk Metrics** | ✅ Yes | ✅ Yes | ✅ Yes | Part of Hero Card |
| **Statistical Report** | ✅ Yes | ✅ Yes | ✅ Yes | Basic stats (always visible) |
| **Deep Dive (Charts)** | 🔒 Locked | 🔒 Locked | ✅ Full Access | **Premium only** |
| **SOC History Chart** | 🔒 Locked | 🔒 Locked | ✅ Full Access | **Premium only** |
| **Volatility Timeline** | 🔒 Locked | 🔒 Locked | ✅ Full Access | **Premium only** |
| **Returns Distribution** | 🔒 Locked | 🔒 Locked | ✅ Full Access | **Premium only** |
| **Monte Carlo Forecast** | 🔒 Locked | 🔒 Locked | ✅ Full Access | **Premium only** |
| **Portfolio Simulation** | 🔒 Locked | 3/hour | ✅ Unlimited | **Free gets taste** |
| **DCA Backtesting** | 🔒 Locked | 3/hour | ✅ Unlimited | Part of simulation |
| **Portfolio Save/Load** | 🔒 Locked | ✅ Yes | ✅ Yes | Database feature (auth required) |
| **Email Notifications** | 🔒 N/A | 🔒 Future | ✅ Future | Not implemented yet |
| **API Access** | 🔒 N/A | 🔒 N/A | 🔒 Future | Not implemented yet |

---

## 🎯 Recommended Tier Strategy

### **Public → Free Conversion Drivers:**
1. **Search limit** (2/hour) → Forces signup to explore multiple assets
2. **Deep Dive locked** → Teaser of what's possible
3. **Simulation locked** → Can't test strategies without signup

**Value Prop:** "Sign up free to search unlimited tickers and test your strategy (3 simulations/hour)"

---

### **Free → Premium Conversion Drivers:**
1. **Deep Dive locked** → Can't see advanced charts/analytics
2. **Simulation limit** (3/hour) → Power users hit this quickly
3. **No Monte Carlo** → Can't forecast future scenarios

**Value Prop:** "Upgrade to Premium for deep crash analysis, unlimited simulations, and probabilistic forecasting"

---

## 🚨 Issues to Fix

### **Issue 1: Deep Dive is Currently Visible for Free Users**
**Current Behavior:**
```python
# Line 1668 in app.py
if tier == "premium":
    # Show charts
else:
    # Free/Public users see nothing
```

**Problem:** Free users see charts but they're locked. Confusing UX.

**Fix:** Make it consistent - lock for both Public AND Free.

---

### **Issue 2: Monte Carlo is Not Gated**
**Current Status:** Monte Carlo Forecast Engine is shown to all users (no gate).

**Problem:** Premium feature shown to Free users.

**Fix:** Add tier check before `render_monte_carlo_simulation()`.

---

### **Issue 3: Inconsistent Tier Variables**
**Current Code Uses:**
- `st.session_state.tier` (from Supabase)
- `st.session_state.user_tier` (duplicate?)
- `tier` (local variable)

**Problem:** Confusing, error-prone.

**Fix:** Standardize on `st.session_state.tier` everywhere.

---

### **Issue 4: Rate Limiting for Free Simulations**
**Current:**
```python
elif tier == "free":
    if not check_rate_limit('simulation', 3):
        st.warning("Limit reached")
```

**Problem:** Counter doesn't show remaining count clearly.

**Fix:** Show "2/3 simulations remaining this hour" prominently.

---

## 📝 Implementation Checklist

### **Phase 1: Standardize Tier Checks** ✅
- [x] Audit all tier checks in codebase
- [ ] Replace `user_tier` with `tier` everywhere
- [ ] Create helper function `get_user_tier()` in auth_manager.py
- [ ] Update all feature gates to use helper

### **Phase 2: Fix Deep Dive Gate** ✅
- [ ] Lock Deep Dive for Public AND Free users
- [ ] Show upgrade prompt with clear benefits
- [ ] Update UI to indicate "Premium Feature"

### **Phase 3: Gate Monte Carlo** ✅
- [ ] Add tier check before Monte Carlo section
- [ ] Lock for Public and Free
- [ ] Show teaser: "Premium users can forecast 30-day probability cones"

### **Phase 4: Improve Rate Limit UX** ✅
- [ ] Show clear counter: "X/3 simulations remaining"
- [ ] Add countdown timer: "Resets in 42 minutes"
- [ ] Upgrade prompt after hitting limit

### **Phase 5: Polish Upgrade Prompts** ✅
- [ ] Make prompts contextual (e.g., "Unlock this chart")
- [ ] Add "See what you're missing" preview images
- [ ] Clear pricing info (placeholder for now)

---

## 💰 Pricing Strategy (To Be Decided)

### **Option A: Monthly Subscription**
```
Free: $0/month
Premium: $29/month
```

### **Option B: Annual Discount**
```
Free: $0
Premium: $29/month ($290/year, save $58)
```

### **Option C: Usage-Based**
```
Free: $0 (3 simulations/hour)
Premium: $49/month (unlimited)
```

**Recommendation:** Start with **Option A** (simple monthly) and iterate based on user feedback.

---

## 🎨 UI/UX Recommendations

### **1. Feature Badges**
Add visual indicators next to features:
```
✅ Available to you
🆓 Free tier
⭐ Premium only
🔒 Upgrade required
```

### **2. Upgrade CTAs**
Replace generic "Upgrade" with specific value:
```
❌ Bad: "Upgrade to Premium"
✅ Good: "Unlock Deep Dive Charts → Premium"
```

### **3. Soft Gates**
Show locked features with blur effect + upgrade prompt (not hide completely).

### **4. Trial Period**
Consider: "Try Premium free for 7 days" (after Stripe integration).

---

## 🔧 Code Locations to Update

### **File: app.py**

#### **Search Rate Limit** (Line 485-493)
✅ **Status:** Working correctly
- Public: 2/hour limit
- Free/Premium: Unlimited

#### **Deep Dive Charts** (Line 1666-1710)
⚠️ **Status:** Needs fix
- Currently only shows for Premium
- Should lock for Free too (or soft-gate with upgrade prompt)

**Current:**
```python
if tier == "premium":
    # Show charts
```

**Should be:**
```python
if tier == "premium":
    # Show charts
else:
    # Show upgrade prompt with benefits
    show_upgrade_dialog("Deep Dive Analytics", tier)
```

#### **Monte Carlo Forecast** (Line ~1550)
⚠️ **Status:** Needs gate
- Currently shown to all users
- Should be Premium only

**Add before rendering:**
```python
# === MONTE CARLO FORECAST (PREMIUM ONLY) ===
if tier == "premium":
    render_monte_carlo_simulation(...)
else:
    st.info("🔮 **Probabilistic Forecasting** is a Premium feature")
    show_upgrade_dialog("Monte Carlo Forecast", tier)
```

#### **Portfolio Simulation** (Line 1714-1750)
✅ **Status:** Working correctly
- Public: Locked
- Free: 3/hour limit
- Premium: Unlimited

---

### **File: auth_manager.py**

#### **Add Helper Function:**
```python
def get_user_tier() -> str:
    """
    Get current user tier (public, free, premium).
    Single source of truth for tier checks.
    
    Returns:
        str: 'public', 'free', or 'premium'
    """
    if is_authenticated():
        return st.session_state.get('tier', 'free')
    else:
        return 'public'
```

---

## 🎯 Success Metrics (To Track After Stripe Integration)

### **Public → Free Conversion**
- Target: 20% of public users sign up
- Track: Search limit hit rate, signup button clicks

### **Free → Premium Conversion**
- Target: 5% of free users upgrade
- Track: Upgrade button clicks, feature gate hits, time to conversion

### **Retention**
- Target: 80% monthly active users (MAU)
- Track: Login frequency, feature usage

---

## 🚀 Next Steps

### **Immediate (Before Stripe):**
1. ✅ Standardize tier checks
2. ✅ Gate Deep Dive for Free users
3. ✅ Gate Monte Carlo for Free users
4. ✅ Improve rate limit messaging

### **After Stripe Integration:**
1. ✅ Add "Upgrade to Premium" button (real payment)
2. ✅ Add pricing page
3. ✅ Add subscription management
4. ✅ Track conversion metrics

---

## 📞 Questions to Decide

1. **Should Free users see Deep Dive charts at all?**
   - Option A: Hide completely (simpler)
   - Option B: Soft-gate with blur/teaser (better for conversion)
   - **Recommendation:** Option B

2. **Simulation limit for Free tier:**
   - Current: 3/hour
   - Alternative: 5/day
   - **Recommendation:** Keep 3/hour (encourages premium for power users)

3. **Monte Carlo visibility:**
   - Option A: Hide from Free users
   - Option B: Show static preview (no interaction)
   - **Recommendation:** Option A (simpler)

---

## ✅ Status Summary

| Component | Status | Priority |
|-----------|--------|----------|
| Search rate limit | ✅ Working | - |
| Hero Card access | ✅ Working | - |
| Deep Dive gate | ⚠️ Needs fix | **HIGH** |
| Monte Carlo gate | ⚠️ Needs gate | **HIGH** |
| Simulation rate limit | ✅ Working | - |
| Tier helper function | ⚠️ Missing | **MEDIUM** |
| Upgrade prompts | ⚠️ Could improve | **MEDIUM** |
| Stripe integration | 🔒 Not started | **HIGH** (Next phase) |

---

**Ready to proceed with fixes?** I can implement these changes before moving to Stripe integration.


