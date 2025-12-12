# 🔧 Fix Email Confirmation Error

## Problem: Email Confirmation Link Returns "Connection Error"

When users click the confirmation link in their email, they see:
- ❌ "Page could not be loaded"
- ❌ "Connection error"
- ❌ Can't complete signup

---

## 🎯 Root Cause

Supabase doesn't know where to redirect users after email confirmation. By default, it tries to redirect to a URL that doesn't exist or isn't configured.

---

## ✅ Solution: Configure Redirect URLs in Supabase

### **Step 1: Open Supabase Dashboard**

1. Go to: https://supabase.com/dashboard
2. Select your TECTONIQ project
3. Click **Authentication** (left sidebar)
4. Click **URL Configuration**

---

### **Step 2: Add Redirect URLs**

In the "Site URL" and "Redirect URLs" section:

#### **For Local Development:**

**Site URL:**
```
http://localhost:8501
```

**Redirect URLs** (add all of these):
```
http://localhost:8501
http://localhost:8501/
http://localhost:8501/*
http://127.0.0.1:8501
http://127.0.0.1:8501/
```

Click **Save** at the bottom.

---

### **Step 3: Update Email Templates (Optional but Recommended)**

While in **Authentication** settings:

1. Click **Email Templates** (left sidebar)
2. Select **Confirm signup**
3. Look for the confirmation link - it should look like:

```html
<a href="{{ .ConfirmationURL }}">Confirm your email</a>
```

Make sure it's using `{{ .ConfirmationURL }}` (not a hardcoded URL).

---

### **Step 4: Test Email Confirmation**

Now test the full flow:

1. **Logout** from TECTONIQ (if logged in)
2. Click **"Sign Up"**
3. Enter **new email** (different from previous test)
4. Enter password
5. Submit

You should see:
```
✅ Account created! Please check your email to verify.
```

6. **Check email inbox**
7. Click **"Confirm your email"** link
8. You should be redirected to `http://localhost:8501` and see:

```
✅ Email confirmed! You can now log in.
```

---

## 🔧 Alternative: Disable Email Confirmation (For Testing Only)

If you want to skip email confirmation during development:

1. Go to **Supabase Dashboard** → **Authentication** → **Providers**
2. Click **Email** provider
3. **Uncheck** "Enable email confirmations"
4. Click **Save**

⚠️ **Warning:** Only do this for testing. Re-enable for production!

---

## 🐛 Still Not Working?

### **Issue: "Invalid redirect URL"**

**Problem:** Supabase rejects the redirect

**Fix:**
1. Check Supabase **URL Configuration**
2. Make sure `http://localhost:8501` is in **both** Site URL and Redirect URLs
3. Try adding wildcard: `http://localhost:8501/*`

---

### **Issue: "Email not arriving"**

**Problem:** Emails stuck in spam or not sent

**Fix:**
1. Check **spam folder**
2. Check Supabase Dashboard → **Authentication** → **Logs** for email sending errors
3. If using custom SMTP, verify credentials
4. Try with a different email provider (Gmail, Outlook)

---

### **Issue: "Token expired"**

**Problem:** Confirmation link is old (> 24 hours)

**Fix:**
1. Sign up again with the same email
2. Supabase will send a new confirmation email
3. Use the new link within 24 hours

---

## 🎯 Quick Fix Summary

**In Supabase Dashboard:**
1. **Authentication** → **URL Configuration**
2. Set **Site URL** to: `http://localhost:8501`
3. Add **Redirect URL**: `http://localhost:8501/*`
4. Click **Save**
5. Test signup again with a new email

---

## 🚀 Production Setup

When deploying to production:

1. Update **Site URL** to your production domain:
   ```
   https://tectoniq.app
   ```

2. Update **Redirect URLs**:
   ```
   https://tectoniq.app
   https://tectoniq.app/*
   ```

3. Re-enable email confirmations if disabled

4. Configure custom email templates with branding

5. Consider custom SMTP provider for deliverability

---

## ✅ Success Indicators

Email confirmation works when:

1. ✅ User receives email within 1 minute
2. ✅ Clicking link redirects to TECTONIQ app
3. ✅ User sees confirmation message
4. ✅ User can login immediately
5. ✅ No "connection error" or "invalid redirect"

---

**Next Step:** Configure redirect URLs in Supabase Dashboard, then test signup flow again! 🎯

