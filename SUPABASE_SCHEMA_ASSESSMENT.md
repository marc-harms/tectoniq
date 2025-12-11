# Supabase Schema Assessment for TECTONIQ Auth System

## Current Implementation Analysis

### Existing Tables (Referenced in Code)

#### 1. **`profiles` Table**
**Purpose:** Store user profile data and subscription tier

**Current Fields Used:**
- `user_id` (UUID, foreign key to auth.users)
- `email` (TEXT)
- `subscription_tier` (TEXT) - values: "free" or "premium"
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Operations:**
- ✅ Read profile by user_id
- ✅ Update subscription tier
- ✅ Auto-created on signup (mentioned: "database trigger")

#### 2. **`portfolios` Table**
**Purpose:** Store user's saved ticker symbols (watchlist)

**Current Fields Used:**
- `user_id` (UUID, foreign key to auth.users)
- `ticker` (TEXT) - asset symbol (e.g., "AAPL", "BTC-USD")
- `added_at` (TIMESTAMP)

**Operations:**
- ✅ Select tickers by user_id
- ✅ Insert new ticker
- ✅ Delete ticker by user_id + ticker

---

## ✅ Schema Sufficiency Assessment

### What You Already Have
The current Supabase tables are **SUFFICIENT** for a basic free/premium user management system with the following features:

✅ **Authentication**
- Email/password login (Supabase Auth handles this automatically)
- User sessions and token management

✅ **User Profiles**
- Store user metadata
- Track subscription tier (free/premium)
- Timestamp tracking

✅ **Portfolio Management**
- Unlimited watchlist for all users
- Per-user ticker storage

---

## 🔧 Recommended Schema (Complete SQL)

Here's the **complete schema** you should have in Supabase:

### 1. Enable RLS (Row Level Security)
```sql
-- Enable RLS on both tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
```

### 2. Profiles Table
```sql
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE NOT NULL,
  email TEXT,
  subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'premium')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);

-- RLS Policies for profiles
CREATE POLICY "Users can read own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = user_id);

-- Trigger to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (user_id, email, subscription_tier)
  VALUES (NEW.id, NEW.email, 'free');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on auth.users table
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3. Portfolios Table
```sql
CREATE TABLE IF NOT EXISTS portfolios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  ticker TEXT NOT NULL,
  added_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, ticker)  -- Prevent duplicate tickers per user
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_ticker ON portfolios(ticker);

-- RLS Policies for portfolios
CREATE POLICY "Users can read own portfolio"
  ON portfolios FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert to own portfolio"
  ON portfolios FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete from own portfolio"
  ON portfolios FOR DELETE
  USING (auth.uid() = user_id);
```

---

## 📊 Optional: Usage Tracking Table (Recommended)

**Purpose:** Track feature usage for rate limiting and analytics

```sql
CREATE TABLE IF NOT EXISTS usage_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  action_type TEXT NOT NULL,  -- 'search', 'simulation', 'deep_dive'
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB  -- Store additional context (ticker, params, etc.)
);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_timestamp 
  ON usage_logs(user_id, timestamp DESC);

-- RLS Policy
CREATE POLICY "Users can read own usage logs"
  ON usage_logs FOR SELECT
  USING (auth.uid() = user_id);

-- Service role can insert (for tracking)
CREATE POLICY "Service can insert usage logs"
  ON usage_logs FOR INSERT
  WITH CHECK (true);
```

---

## 🎯 Current vs. Required: Gap Analysis

| Feature | Current Status | Required | Action Needed |
|---------|----------------|----------|---------------|
| **Auth System** | ✅ Implemented | ✅ Yes | None - Supabase Auth works out of box |
| **Profiles Table** | ⚠️ Partial | ✅ Yes | Add RLS policies, triggers |
| **Portfolios Table** | ⚠️ Partial | ✅ Yes | Add RLS policies, unique constraint |
| **Usage Tracking** | ❌ Missing | 🔶 Optional | Add table if rate limiting needed |
| **Email Verification** | ❌ Not configured | 🔶 Optional | Configure in Supabase dashboard |
| **Password Reset** | ✅ Handled by Supabase | ✅ Yes | None - works automatically |

---

## ⚡ Migration Checklist

To move from demo auth to real Supabase auth:

### Step 1: Database Setup
- [ ] Run SQL to create `profiles` table with all fields
- [ ] Run SQL to create `portfolios` table with unique constraint
- [ ] Create database trigger for auto-profile creation
- [ ] Enable Row Level Security (RLS)
- [ ] Create RLS policies for both tables
- [ ] (Optional) Create `usage_logs` table

### Step 2: Supabase Dashboard Configuration
- [ ] Enable email provider in Authentication settings
- [ ] Configure email templates (optional)
- [ ] Set up password requirements
- [ ] Enable email confirmations (optional but recommended)

### Step 3: Code Changes
- [ ] Remove demo login logic from `app.py` (lines 121-159)
- [ ] Update `ui_auth.py` to use real Supabase auth
- [ ] Test signup flow
- [ ] Test login flow
- [ ] Test tier upgrade/downgrade
- [ ] Test portfolio add/remove

### Step 4: Environment Setup
- [ ] Add `SUPABASE_URL` to `.streamlit/secrets.toml`
- [ ] Add `SUPABASE_KEY` (anon key) to secrets
- [ ] Test connection to Supabase

---

## 🚨 Security Considerations

### ✅ Already Handled by Implementation
- Password hashing (Supabase Auth)
- Session tokens (Supabase Auth)
- HTTPS/TLS (Supabase)

### ⚠️ Need to Add
1. **Row Level Security (RLS)**
   - CRITICAL: Without RLS, any user can read/modify any data
   - Must enable RLS on all custom tables
   - Create policies to restrict access to own data only

2. **API Key Protection**
   - Store Supabase keys in `secrets.toml` (never commit to git)
   - Use anon key (public), not service role key
   - Gitignore `.streamlit/secrets.toml`

3. **Email Verification**
   - Consider enabling to prevent fake signups
   - Configure in Supabase dashboard

---

## 📝 Conclusion

**Answer to your question: "Are the tables sufficient?"**

✅ **YES - The table structure is sufficient**, but needs:

1. **Security hardening** - Add RLS policies (critical)
2. **Database triggers** - Auto-create profile on signup
3. **Constraints** - Add unique constraint on portfolios
4. **Indexes** - Add for performance

The existing `auth_manager.py` code is **well-written and production-ready** once the database is properly configured with the SQL above.

---

## 🔗 Next Steps

1. Copy the SQL schema above into Supabase SQL Editor
2. Run each section to create tables, triggers, and policies
3. Test with a demo signup to verify trigger creates profile
4. Update app.py to remove demo auth and use real Supabase
5. Test end-to-end authentication flow

**Estimated time:** 30-60 minutes to set up and test

