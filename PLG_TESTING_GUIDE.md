# PLG System Testing Guide

## 🧪 Quick Test Script

Test all three tiers in 5 minutes!

---

## Test 1: PUBLIC Tier (2-minute test)

### Start Fresh
```bash
streamlit run app.py
```

**Don't login!** Stay as Public user.

### Actions to Test
1. ✅ **Search "AAPL"** → Should work (1/2 used)
2. ✅ **Search "TSLA"** → Should work (2/2 used)
3. ❌ **Search "BTC-USD"** → Should show: "🔒 Search Limit Reached"
4. ✅ **Hero Card visible** → Should display for AAPL/TSLA
5. ❌ **Try Deep Dive** → Should show: "🔒 Premium required"
6. ❌ **Try Simulation** → Should show: "🔒 Not available for Public"
7. ✅ **Check sidebar** → Should show login form with demo credentials

**Expected Result:**
- Search limit enforced ✅
- Hero Card accessible ✅
- Charts locked ✅
- Simulation locked ✅
- Clear upgrade prompts ✅

---

## Test 2: FREE Tier (2-minute test)

### Login
**Sidebar:** Enter `free` / `123` → Click Login

### Actions to Test
1. ✅ **Unlimited searches** → Try 5+ tickers, all should work
2. ✅ **Hero Cards** → All display normally
3. ⚠️ **Deep Dive** → Should show soft gate: "🔒 Premium required"
4. ✅ **Run Simulation #1** → Should work (2/3 remaining shown)
5. ✅ **Run Simulation #2** → Should work (1/3 remaining shown)
6. ✅ **Run Simulation #3** → Should work (0/3 remaining shown)
7. ❌ **Run Simulation #4** → Should show: "⏱️ Limit reached"
8. ✅ **Check sidebar** → Shows "FREE" tier, usage counters

**Expected Result:**
- Unlimited searches ✅
- Simulation limit enforced (3/hour) ✅
- Charts soft-gated ✅
- Upgrade prompts visible ✅

---

## Test 3: PREMIUM Tier (1-minute test)

### Login
**Sidebar:** Logout → Login with `premium` / `123`

### Actions to Test
1. ✅ **Search any ticker** → Unlimited
2. ✅ **Hero Card** → Displays
3. ✅ **Deep Dive charts** → Full access, no locks!
4. ✅ **Run multiple simulations** → No limits
5. ✅ **Statistical analytics** → All visible
6. ✅ **Check sidebar** → Shows "PREMIUM" with gold star ⭐

**Expected Result:**
- Everything unlimited ✅
- No upgrade prompts ✅
- Full feature access ✅

---

## 🎯 Feature Gates to Verify

### Hard Gates (Blocked)
- [ ] Public: 3rd search attempt
- [ ] Public: Simulation access
- [ ] Free: 4th simulation attempt

### Soft Gates (Visible but locked)
- [ ] Public/Free: Deep Dive charts
- [ ] Shows upgrade dialog
- [ ] Lists benefits

---

## 🐛 Common Issues & Fixes

### Issue: "Can't search more than 2 times even after login"
**Fix:** Logout and login again to clear rate limits

### Issue: "Sidebar not showing"
**Fix:** Check `render_sidebar_login()` is called in main()

### Issue: "All features unlocked for Public"
**Fix:** Verify `user_tier` is initialized to "public"

### Issue: "Free user sees 'unlimited' for simulations"
**Fix:** Check gating logic in simulation section

---

## 📊 Rate Limit Testing

### Manual Rate Limit Check
```python
# In Streamlit app, add temporary debug:
if st.button("Debug Rate Limits"):
    st.write("Rate Limits:", st.session_state.get('rate_limits', {}))
    st.write("User Tier:", st.session_state.get('user_tier'))
    st.write("Searches remaining:", get_remaining_actions('search', 2))
    st.write("Simulations remaining:", get_remaining_actions('simulation', 3))
```

### Reset Rate Limits
```python
# Logout and login again
# Or manually: del st.session_state.rate_limits
```

---

## 🎨 UX Verification

### Sidebar Check
- [ ] Login form shows demo credentials
- [ ] Status shows correct tier
- [ ] Usage counters display
- [ ] Logout button works
- [ ] Upgrade prompts appear

### Upgrade Dialogs Check
- [ ] Context-appropriate messaging
- [ ] Lists correct benefits
- [ ] Shows demo credentials
- [ ] Non-intrusive placement

### Rate Limit Messages Check
- [ ] Clear error messages
- [ ] Explains the limit
- [ ] Shows path to upgrade
- [ ] Friendly tone

---

## 🚀 Demo Script for Beta Testers

### Welcome Script
```
"Welcome to TECTONIQ! You're currently using the Public tier.

Try searching for a stock ticker (like AAPL or TSLA).
You have 2 free searches to explore.

Want to try more? Login with:
  Username: free
  Password: 123

This unlocks unlimited searches and 3 simulations per hour!"
```

### Upgrade Script (Free → Premium)
```
"Enjoying TECTONIQ? You're on the Free tier.

To unlock Deep Dive analysis with charts and
unlimited simulations, try our Premium tier.

Demo login:
  Username: premium
  Password: 123"
```

---

## ✅ Testing Checklist

### Functionality
- [ ] Public limited to 2 searches
- [ ] Free has unlimited searches
- [ ] Free limited to 3 simulations
- [ ] Premium has everything unlimited
- [ ] Rate limits reset after 1 hour
- [ ] Login/logout works
- [ ] Tier changes reflect immediately

### UX
- [ ] Sidebar login is intuitive
- [ ] Demo credentials are visible
- [ ] Error messages are helpful
- [ ] Upgrade prompts are clear
- [ ] No confusing gates
- [ ] Smooth tier transitions

### Edge Cases
- [ ] Rapid searches don't break rate limiter
- [ ] Logout clears rate limits
- [ ] Page refresh preserves tier in session
- [ ] Multiple tabs don't share rate limits (session-based)

---

## 📝 Summary

✅ **Three-tier system ready**
✅ **Rate limiting functional**
✅ **Feature gating implemented**
✅ **Upgrade paths clear**
✅ **Demo credentials working**

**Test with the script above to verify all features!** 🎯

---

**Testing Time:** ~5 minutes for complete verification
**Next Step:** Run `streamlit run app.py` and test!

