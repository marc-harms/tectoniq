-- =====================================================================
-- TECTONIQ: Manual Premium Upgrade (For Testing/Debugging)
-- =====================================================================
-- 
-- If webhook isn't working, use this to manually upgrade yourself
-- 
-- Instructions:
-- 1. Open Supabase Dashboard → SQL Editor
-- 2. Replace 'your-email@example.com' with YOUR actual email
-- 3. Run this script
-- 4. Refresh TECTONIQ app
-- 
-- =====================================================================

-- Find your user and upgrade to premium
UPDATE profiles
SET 
    subscription_tier = 'premium',
    updated_at = NOW()
WHERE email = 'moin@moin.de';  -- CHANGE THIS TO YOUR EMAIL!

-- Verify the update
SELECT 
    email,
    subscription_tier,
    updated_at
FROM profiles
WHERE email = 'moin@moin.de';  -- CHANGE THIS TO YOUR EMAIL!

