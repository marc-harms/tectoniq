"""
Test for look-ahead bias in compute_market_state().

This test verifies that historical market states remain unchanged
when new data is appended to the dataframe.

Expected: Zero changes in historical states
If this fails: There is look-ahead bias (data leakage)
"""

import pandas as pd
import yfinance as yf
from logic import compute_market_state, MarketState


def test_lookahead_bias():
    """
    Test that historical states don't change when future data is added.
    
    Steps:
    1. Compute market state for last N=300 bars
    2. Append new data
    3. Recompute past N bars
    4. Verify: Zero changes in historical states
    """
    print("=" * 70)
    print("LOOK-AHEAD BIAS TEST")
    print("=" * 70)
    print("\nObjective: Verify historical states remain unchanged when new data is added")
    print("Expected: Zero differences in criticality, regime, or trend")
    print()
    
    # Fetch data with enough history
    print("Step 1: Fetching test data (2 years)...")
    df = yf.download("AAPL", period="2y", progress=False)
    
    if df.empty:
        print("❌ FAILED: Could not fetch data")
        return False
    
    # Normalize columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    
    print(f"✓ Fetched {len(df)} rows")
    
    # Split into historical and future
    N = 300
    if len(df) < N + 50:
        print(f"❌ FAILED: Not enough data (need {N+50}, got {len(df)})")
        return False
    
    # Historical window: [end-N-50 : end-50]
    # Future window: [end-50 : end]
    historical_end = len(df) - 50
    historical_start = historical_end - N
    
    df_historical = df.iloc[:historical_end].copy()
    df_full = df.copy()
    
    print(f"\nStep 2: Computing states for last {N} bars (historical window)...")
    print(f"  Historical data: rows 0-{historical_end} ({len(df_historical)} total)")
    print(f"  Test window: rows {historical_start}-{historical_end}")
    
    # Compute states for the test window using only historical data
    historical_states = []
    for i in range(historical_start, historical_end):
        try:
            state = compute_market_state(df_historical, i)
            historical_states.append({
                'idx': i,
                'date': state.date,
                'criticality': state.criticality,
                'regime': state.regime,
                'trend_state': state.trend_state,
                'volatility_percentile': state.volatility_percentile
            })
        except Exception as e:
            print(f"⚠️  Warning: Could not compute state at index {i}: {e}")
    
    print(f"✓ Computed {len(historical_states)} historical states")
    
    # Now append future data
    print(f"\nStep 3: Appending future data...")
    print(f"  Full data: {len(df_full)} rows (added {len(df_full) - len(df_historical)} rows)")
    
    # Recompute the same indices using full data
    print(f"\nStep 4: Recomputing same {N} bars with full data...")
    recomputed_states = []
    for i in range(historical_start, historical_end):
        try:
            state = compute_market_state(df_full, i)
            recomputed_states.append({
                'idx': i,
                'date': state.date,
                'criticality': state.criticality,
                'regime': state.regime,
                'trend_state': state.trend_state,
                'volatility_percentile': state.volatility_percentile
            })
        except Exception as e:
            print(f"⚠️  Warning: Could not compute state at index {i}: {e}")
    
    print(f"✓ Recomputed {len(recomputed_states)} states")
    
    # Compare states
    print(f"\nStep 5: Comparing historical vs recomputed states...")
    print("=" * 70)
    
    differences = []
    for hist, recomp in zip(historical_states, recomputed_states):
        crit_diff = abs(hist['criticality'] - recomp['criticality'])
        regime_diff = (hist['regime'] != recomp['regime'])
        trend_diff = (hist['trend_state'] != recomp['trend_state'])
        vol_diff = abs(hist['volatility_percentile'] - recomp['volatility_percentile'])
        
        if crit_diff > 0 or regime_diff or trend_diff or vol_diff > 0.1:
            differences.append({
                'idx': hist['idx'],
                'date': hist['date'],
                'crit_before': hist['criticality'],
                'crit_after': recomp['criticality'],
                'crit_diff': crit_diff,
                'regime_before': hist['regime'],
                'regime_after': recomp['regime'],
                'regime_changed': regime_diff,
                'trend_before': hist['trend_state'],
                'trend_after': recomp['trend_state'],
                'trend_changed': trend_diff,
                'vol_pct_diff': vol_diff
            })
    
    # Report results
    if len(differences) == 0:
        print("\n✅ TEST PASSED: ZERO CHANGES DETECTED")
        print(f"   All {len(historical_states)} historical states remained unchanged")
        print("   No look-ahead bias detected")
        return True
    else:
        print(f"\n❌ TEST FAILED: {len(differences)} CHANGES DETECTED")
        print(f"   {len(differences)}/{len(historical_states)} states changed when future data was added")
        print("\n🚨 LOOK-AHEAD BIAS DETECTED (DATA LEAKAGE)")
        print("\nFirst 10 differences:")
        print("-" * 70)
        
        for i, diff in enumerate(differences[:10]):
            print(f"\nIndex {diff['idx']} ({diff['date'].date()}):")
            print(f"  Criticality: {diff['crit_before']} → {diff['crit_after']} (Δ{diff['crit_diff']:+d})")
            if diff['regime_changed']:
                print(f"  Regime: {diff['regime_before']} → {diff['regime_after']} ❌")
            if diff['trend_changed']:
                print(f"  Trend: {diff['trend_before']} → {diff['trend_after']} ❌")
            if diff['vol_pct_diff'] > 0.1:
                print(f"  Vol %ile: Δ{diff['vol_pct_diff']:.2f}")
        
        if len(differences) > 10:
            print(f"\n... and {len(differences) - 10} more differences")
        
        print("\n⚠️  STOP: Fix look-ahead bias before proceeding")
        return False


def main():
    """Run the look-ahead bias test."""
    success = test_lookahead_bias()
    
    print("\n" + "=" * 70)
    if success:
        print("RESULT: ✅ NO LOOK-AHEAD BIAS")
        print("Historical states are stable and point-in-time")
        return 0
    else:
        print("RESULT: ❌ LOOK-AHEAD BIAS DETECTED")
        print("Implementation uses future data - must be fixed")
        return 1


if __name__ == "__main__":
    exit(main())

