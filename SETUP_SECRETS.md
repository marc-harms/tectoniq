# 🔐 Quick Setup: Supabase Credentials

## ⚠️ **Required Before Running App**

Your app needs Supabase credentials to connect to the authentication database.

---

## 📋 **Step-by-Step Setup (2 minutes)**

### **Step 1: Get Your Supabase Credentials**

1. Go to your **Supabase project dashboard**
2. Click: **Settings** (gear icon in sidebar) → **API**
3. You'll see:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon public** key (starts with `eyJhbGciOiJIUzI1NiI...`)

**IMPORTANT:** Use the **anon** key, NOT the **service_role** key!

### **Step 2: Create Secrets File**

1. Copy the template file:
   ```bash
   cd /home/marc/Projects/TECTONIQ/.streamlit
   cp secrets.toml.template secrets.toml
   ```

2. Open `secrets.toml` in your editor

3. Replace the placeholder values with your actual Supabase credentials:
   ```toml
   [default]
   SUPABASE_URL = "https://xxxxx.supabase.co"  # ← Your actual URL
   SUPABASE_KEY = "eyJhbGciOiJIUzI1..."        # ← Your actual anon key
   ```

4. Save the file

### **Step 3: Verify It Works**

Run your app:
```bash
streamlit run app.py
```

If configured correctly:
- ✅ No error messages about missing configuration
- ✅ "Sign Up / Login" button works
- ✅ Signup creates user in Supabase
- ✅ Login authenticates successfully

If you see errors:
- ❌ Double-check URL and key are correct
- ❌ Make sure you used the **anon** key (not service_role)
- ❌ Verify no extra spaces or quotes

---

## 📁 **File Structure**

After setup, you should have:

```
TECTONIQ/
├── .streamlit/
│   ├── secrets.toml           # ← Your actual credentials (DO NOT COMMIT!)
│   └── secrets.toml.template  # ← Template file (safe to commit)
├── .gitignore                 # ← Should include secrets.toml
└── ... (rest of your files)
```

---

## 🔒 **Security Notes**

✅ **DO:**
- Keep `secrets.toml` private
- Use the **anon** key (it's designed for frontend use)
- Add `secrets.toml` to `.gitignore`

❌ **DON'T:**
- Commit `secrets.toml` to git
- Share your secrets file publicly
- Use the service_role key in frontend code

---

## 🐛 **Troubleshooting**

### **"Supabase Configuration Missing" error**
→ You haven't created `secrets.toml` yet. Follow Step 2 above.

### **"Template values" error**
→ You copied the template but didn't replace the placeholder values with real credentials.

### **"Invalid API key" or "Project not found"**
→ Double-check you copied the credentials correctly from Supabase dashboard.

### **Still not working?**
1. Restart Streamlit (Ctrl+C and run again)
2. Check `.streamlit/secrets.toml` exists
3. Verify credentials in Supabase dashboard: **Settings** → **API**
4. Try copying the keys again (no extra spaces)

---

## ✅ **Quick Test**

After setup, test your configuration:

```python
# In Python terminal:
import streamlit as st
from auth_manager import get_supabase_client

# Should work without errors:
client = get_supabase_client()
print("✅ Supabase connected!")
```

---

## 🚀 **Next Steps**

Once credentials are configured:
1. ✅ Run app: `streamlit run app.py`
2. ✅ Click "Sign Up / Login"
3. ✅ Create test account
4. ✅ Check Supabase dashboard for new user

**You're ready to go!** 🎉

