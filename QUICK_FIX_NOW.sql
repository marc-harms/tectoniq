-- =====================================================================
-- TECTONIQ: Quick Fix - Upgrade to Premium NOW
-- =====================================================================
-- 
-- Run this in Supabase SQL Editor to:
-- 1. Add missing Stripe columns (if not done)
-- 2. Upgrade your account to Premium
-- 
-- =====================================================================

-- Step 1: Add Stripe columns (will skip if already exist)
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'free',
ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMPTZ;

-- Step 2: Create indexes (will skip if already exist)
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_customer 
ON profiles(stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_profiles_stripe_subscription 
ON profiles(stripe_subscription_id);

-- Step 3: Upgrade YOUR account to Premium
UPDATE profiles
SET 
    subscription_tier = 'premium',
    subscription_status = 'active',
    updated_at = NOW()
WHERE email = 'moin@moin.de';  -- CHANGE THIS TO YOUR EMAIL!

-- Step 4: Verify everything worked
SELECT 
    email,
    subscription_tier,
    subscription_status,
    stripe_customer_id,
    stripe_subscription_id,
    created_at,
    updated_at
FROM profiles
WHERE email = 'moin@moin.de'  -- CHANGE THIS TO YOUR EMAIL!
ORDER BY created_at DESC;

-- Expected result:
-- email: moin@moin.de
-- subscription_tier: premium
-- subscription_status: active
-- stripe_customer_id: NULL (will be filled by future webhook)
-- stripe_subscription_id: NULL (will be filled by future webhook)

