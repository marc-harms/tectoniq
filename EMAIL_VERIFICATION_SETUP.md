# Email Verification Setup Guide for TECTONIQ

## 🎯 Purpose

Enable email verification to:
- ✅ Prevent spam signups
- ✅ Verify real email addresses
- ✅ Improve security
- ✅ Reduce fake accounts

---

## 📋 Step-by-Step Configuration

### Step 1: Access Supabase Authentication Settings

1. Go to your Supabase project dashboard
2. Navigate to: **Authentication** → **Providers** (left sidebar)
3. Click on **Email** provider

### Step 2: Enable Email Confirmation

In the Email provider settings:

1. **Enable Email Confirmations**
   - Toggle ON: **"Enable email confirmations"**
   - This requires users to confirm their email before they can log in

2. **Confirm Email Template** (Optional but Recommended)
   - Customize the confirmation email to match TECTONIQ branding
   - Go to: **Authentication** → **Email Templates** → **Confirm signup**
   
   **Sample Custom Template:**
   ```html
   <h2>Welcome to TECTONIQ!</h2>
   <p>Thanks for signing up. Please confirm your email address by clicking the link below:</p>
   <p><a href="{{ .ConfirmationURL }}">Confirm your email</a></p>
   <p>This link will expire in 24 hours.</p>
   <br>
   <p style="color: #666;">If you didn't create an account, you can safely ignore this email.</p>
   <p style="color: #666;">— The TECTONIQ Team</p>
   ```

3. **Set Redirect URL** (Important!)
   - Go to: **Authentication** → **URL Configuration**
   - Set **Site URL** to your app's URL:
     - Local development: `http://localhost:8501`
     - Production: `https://your-domain.com`
   - Add to **Redirect URLs**:
     - `http://localhost:8501`
     - `https://your-domain.com`

### Step 3: Configure Email Settings (Optional)

By default, Supabase sends emails from their domain. For production, consider custom SMTP:

1. Go to: **Project Settings** → **Auth** → **SMTP Settings**
2. Enable **Custom SMTP**
3. Configure your email provider:
   - **Host**: `smtp.gmail.com` (or your provider)
   - **Port**: `587` (TLS) or `465` (SSL)
   - **Username**: Your email address
   - **Password**: App-specific password (not your regular password)
   - **Sender email**: `noreply@your-domain.com`
   - **Sender name**: `TECTONIQ`

**Recommended Providers:**
- Gmail (free for low volume)
- SendGrid (better deliverability)
- AWS SES (production scale)
- Postmark (transactional emails)

---

## 🔧 Update Your Code

### No Code Changes Needed! ✅

Your existing `auth_manager.py` already handles email verification correctly:

```python
# In signup function
response = supabase.auth.sign_up({
    "email": email,
    "password": password
})

# Supabase automatically:
# 1. Sends confirmation email
# 2. Creates user in auth.users (but email_confirmed = false)
# 3. Returns session only after email is confirmed
```

### What Happens to Users

**Before Email Verification is Enabled:**
1. User signs up → Immediately logged in → Can use app

**After Email Verification is Enabled:**
1. User signs up → Sees success message
2. User receives confirmation email
3. User clicks link in email → Email confirmed
4. User can now log in → Full access

### Update Signup Success Message

Update `ui_auth.py` to inform users about email verification:

```python
if success:
    st.session_state.user = user_data
    st.session_state.tier = user_data['tier']
    st.session_state.authenticated = True
    st.success(f"🎉 Account created! **Check your email** to confirm your address.")
    st.info("📧 We sent a confirmation link to {email}. Click it to activate your account.")
    st.balloons()
    # Don't auto-login - wait for email confirmation
```

---

## 🧪 Testing Email Verification

### Test Flow:

1. **Sign up with a real email** (one you can access)
2. **Check your inbox** for "Confirm your signup" email
3. **Click the confirmation link**
4. **You'll be redirected** back to your app
5. **Log in** with your email/password
6. **Should work!** ✅

### Troubleshooting:

**Email not received?**
- Check spam folder
- Wait 2-3 minutes (sometimes delayed)
- Check Supabase logs: **Authentication** → **Logs**
- Verify SMTP settings if using custom email

**Link doesn't work?**
- Check Redirect URLs are configured correctly
- Ensure Site URL matches your app URL
- Link expires after 24 hours

**Can't log in after confirming?**
- Go to Supabase dashboard → **Authentication** → **Users**
- Check if `email_confirmed_at` has a timestamp
- If not, the confirmation didn't work - resend manually

---

## 🚀 Production Checklist

Before going live:

- [ ] Email confirmation enabled in Supabase
- [ ] Custom email template configured (branded)
- [ ] Site URL set to production domain
- [ ] Redirect URLs include production domain
- [ ] SMTP configured with custom domain (recommended)
- [ ] Test signup flow end-to-end
- [ ] Test email deliverability (check spam score)
- [ ] Update Terms of Service to mention email verification
- [ ] Add "Resend confirmation email" feature (optional)

---

## 📊 Monitoring

Track email verification in Supabase:

1. **Authentication** → **Users** table
   - `email_confirmed_at` column shows verification timestamp
   - Filter by unconfirmed users: `email_confirmed_at IS NULL`

2. **Authentication** → **Logs**
   - See email send events
   - Track confirmation clicks
   - Debug delivery issues

3. **Consider Adding:**
   - Automated reminder emails (if not confirmed after 24h)
   - Admin dashboard to see unconfirmed users
   - Rate limiting on resend confirmation

---

## 🔐 Security Benefits

With email verification enabled:

✅ **Prevents:**
- Fake email signups
- Throwaway email abuse
- Bot registrations
- Email typos causing issues

✅ **Enables:**
- Password reset functionality (requires verified email)
- Trusted communication channel
- Better user data quality
- Compliance with anti-spam laws

---

## ⚡ Quick Start (TL;DR)

1. Supabase dashboard → **Authentication** → **Providers** → **Email**
2. Toggle ON: **"Enable email confirmations"**
3. Set **Site URL**: Your app URL
4. Save changes
5. Test signup → Check email → Click link → Works! ✅

**That's it!** Your auth system now requires email verification.

---

## 📞 Support

If you encounter issues:
- Check Supabase docs: https://supabase.com/docs/guides/auth
- Supabase Discord: https://discord.supabase.com
- Or contact: support@tectoniq.app


