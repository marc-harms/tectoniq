# ✅ Enable Email Verification (Anti-Spam Protection)

## 🎯 Quick Setup (2 Minutes)

Your authentication is working! Now enable email verification to prevent spam signups.

---

## 📋 **Step-by-Step**

### **Step 1: Enable Email Confirmations**

1. Go to your **Supabase dashboard**
2. Navigate to: **Authentication** → **Providers** → **Email**
3. Scroll down to **"Email Confirmations"** section
4. **Toggle ON**: "Enable email confirmations"
5. **Click "Save"**

**That's it!** Email verification is now enabled.

---

### **Step 2: Configure Site URL (Important!)**

Still in Authentication settings:

1. Go to: **Authentication** → **URL Configuration**
2. Set **Site URL**:
   - For local testing: `http://localhost:8501`
   - For production: `https://your-domain.com`
3. Add to **Redirect URLs**:
   - `http://localhost:8501/**`
   - `https://your-domain.com/**` (when you deploy)
4. **Click "Save"**

---

### **Step 3: (Optional) Customize Email Template**

Make the confirmation email match TECTONIQ branding:

1. Go to: **Authentication** → **Email Templates**
2. Select: **"Confirm signup"**
3. Replace with this template:

```html
<h2 style="color: #2C3E50; font-family: 'Rockwell', serif;">Welcome to TECTONIQ!</h2>

<p style="color: #333; font-size: 1rem; line-height: 1.6;">
  Thanks for signing up. Please confirm your email address by clicking the button below:
</p>

<div style="text-align: center; margin: 30px 0;">
  <a href="{{ .ConfirmationURL }}" 
     style="background-color: #2C3E50; color: white; padding: 12px 30px; 
            text-decoration: none; border-radius: 4px; font-weight: bold; 
            display: inline-block;">
    Confirm Your Email
  </a>
</div>

<p style="color: #666; font-size: 0.9rem;">
  Or copy this link: <a href="{{ .ConfirmationURL }}">{{ .ConfirmationURL }}</a>
</p>

<p style="color: #666; font-size: 0.9rem;">
  This link will expire in 24 hours.
</p>

<hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

<p style="color: #999; font-size: 0.85rem;">
  If you didn't create an account with TECTONIQ, you can safely ignore this email.
</p>

<p style="color: #999; font-size: 0.85rem;">
  — The TECTONIQ Team<br>
  Market crashes aren't random—they are physics.
</p>
```

4. **Click "Save"**

---

## 🧪 **How Email Verification Works**

### **Before Enabling (Current State):**
1. User signs up → Immediately logged in ✅
2. No email sent
3. Any email works (even fake ones)

### **After Enabling:**
1. User signs up → Account created
2. **Email sent** with confirmation link 📧
3. User **must click link** to verify email
4. Then user can log in ✅
5. Fake/typo emails won't work

---

## 🔍 **Test It**

After enabling:

1. **Sign up** with a new email address (use a real one you can access)
2. **Check your inbox** for "Confirm your signup" email
3. **Click the link** in the email
4. **Return to app** and log in
5. **Should work!** ✅

**Check Spam Folder** if you don't see the email within 2 minutes.

---

## 📊 **Verify Email Confirmations**

Check in Supabase dashboard:

1. Go to: **Authentication** → **Users**
2. Look at the **"Email Confirmed At"** column
3. Users with confirmed emails show a timestamp
4. Unconfirmed users show blank

---

## 🚨 **Important: Existing Users**

Users who signed up **before** you enabled email verification:
- ✅ Already confirmed (grandfathered in)
- ✅ Can log in normally
- ✅ No action needed

**Only new signups** after enabling will require email confirmation.

---

## 🔐 **Security Benefits**

With email verification:
- ✅ Prevents throwaway/fake emails
- ✅ Reduces bot signups
- ✅ Verifies users own their email
- ✅ Enables password reset functionality
- ✅ Better user data quality

---

## ⚙️ **Advanced: Rate Limit Confirmation Emails**

To prevent abuse of the signup endpoint:

1. Go to: **Authentication** → **Rate Limits**
2. Set limits:
   - **Email signups per hour**: 10-20 (per IP)
   - **Email confirmations per hour**: 5 (per email)

---

## 📞 **Troubleshooting**

### **"Email not received"**
- Check spam/junk folder
- Wait 2-3 minutes (sometimes delayed)
- Check Supabase logs: **Authentication** → **Logs**
- Verify email provider is enabled

### **"Link expired"**
- Links expire after 24 hours
- User can request new link by trying to log in
- Or manually resend from dashboard

### **"Can't log in after confirming"**
- Verify email was actually confirmed
- Check: **Authentication** → **Users** → "Email Confirmed At" column
- Try password reset if needed

---

## ✅ **You're Done!**

After enabling email verification:
- New signups require email confirmation
- Existing users work normally  
- Spam signups prevented
- Your authentication is production-ready! 🎉

---

**Current Status:**
- ✅ Authentication working (tested with moin@moin.de)
- ✅ Supabase connected
- ✅ Login/logout flows working
- ⏳ Email verification (enable in dashboard per steps above)

**Time to enable:** ~2 minutes

