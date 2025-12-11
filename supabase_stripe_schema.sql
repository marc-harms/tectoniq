-- =====================================================================
-- TECTONIQ: Add Stripe Fields to Profiles Table
-- =====================================================================
-- 
-- Run this in Supabase SQL Editor to add Stripe integration columns
--
-- This enables:
-- - Storing Stripe customer IDs
-- - Storing Stripe subscription IDs
-- - Tracking subscription status
-- - Storing subscription end dates
--
-- =====================================================================

-- Add Stripe-related columns to profiles table
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'free',
ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMPTZ;

-- Add comments for documentation
COMMENT ON COLUMN profiles.stripe_customer_id IS 'Stripe customer ID (cus_xxxxx)';
COMMENT ON COLUMN profiles.stripe_subscription_id IS 'Stripe subscription ID (sub_xxxxx)';
COMMENT ON COLUMN profiles.subscription_status IS 'Subscription status: free, active, past_due, canceled, etc.';
COMMENT ON COLUMN profiles.subscription_ends_at IS 'When subscription ends (for cancellations)';

-- Create index for faster Stripe lookups
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_customer 
ON profiles(stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_profiles_stripe_subscription 
ON profiles(stripe_subscription_id);

-- Verify changes
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'profiles' 
  AND column_name IN (
      'stripe_customer_id', 
      'stripe_subscription_id', 
      'subscription_status', 
      'subscription_ends_at'
  )
ORDER BY ordinal_position;

