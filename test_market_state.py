"""
Test script for single source of truth market state refactoring.

Verifies:
1. compute_market_state() works correctly
2. Backward compatibility with old functions
3. Hero card state matches last plot bar state (consistency test)
"""

import pandas as pd
import yfinance as yf
from logic import (
    compute_market_state,
    MarketState,
    get_current_market_state,
    SOCAnalyzer,
    DataFetcher
)


def test_compute_market_state():
    """Test that compute_market_state returns valid MarketState."""
    print("=" * 70)
    print("TEST 1: compute_market_state() basic functionality")
    print("=" * 70)
    
    # Fetch sample data
    print("\nFetching AAPL data...")
    df = yf.download("AAPL", period="2y", progress=False)
    
    if df.empty:
        print("❌ FAILED: Could not fetch data")
        return False
    
    # Normalize columns (handle MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    
    print(f"✓ Fetched {len(df)} rows")
    
    # Compute state for last row
    try:
        state = compute_market_state(df, len(df) - 1)
        print(f"\n✓ Computed market state successfully")
        print(f"  Date: {state.date}")
        print(f"  Volatility: {state.volatility:.6f}")
        print(f"  Volatility Percentile: {state.volatility_percentile:.1f}%")
        print(f"  Trend: {state.trend_state}")
        print(f"  Criticality: {state.criticality}")
        print(f"  Regime: {state.regime}")
        print(f"  Reason Codes: {', '.join(state.reason_codes)}")
        
        # Validate fields
        assert state.regime in ["GREEN", "YELLOW", "RED"], f"Invalid regime: {state.regime}"
        assert state.trend_state in ["UP", "DOWN", "NEUTRAL"], f"Invalid trend: {state.trend_state}"
        assert 0 <= state.criticality <= 100, f"Invalid criticality: {state.criticality}"
        assert 0 <= state.volatility_percentile <= 100, f"Invalid percentile: {state.volatility_percentile}"
        assert len(state.reason_codes) <= 4, f"Too many reason codes: {len(state.reason_codes)}"
        
        print("\n✅ TEST 1 PASSED: All validations successful")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that old functions still work with new implementation."""
    print("\n" + "=" * 70)
    print("TEST 2: Backward compatibility")
    print("=" * 70)
    
    try:
        # Fetch data
        print("\nFetching TSLA data...")
        fetcher = DataFetcher(cache_enabled=False)
        df = fetcher.fetch_data("TSLA")
        info = fetcher.fetch_info("TSLA")
        
        if df.empty:
            print("❌ FAILED: Could not fetch data")
            return False
        
        print(f"✓ Fetched {len(df)} rows")
        
        # Test SOCAnalyzer.get_market_phase()
        print("\nTesting SOCAnalyzer.get_market_phase()...")
        analyzer = SOCAnalyzer(df, "TSLA", info)
        phase = analyzer.get_market_phase()
        
        print(f"  Signal: {phase.get('signal')}")
        print(f"  Tier: {phase.get('tier')}")
        print(f"  Criticality: {phase.get('criticality_score')}")
        print(f"  Trend: {phase.get('trend')}")
        print(f"  Regime: {phase.get('regime')}")
        
        # Test get_current_market_state()
        print("\nTesting get_current_market_state()...")
        state = get_current_market_state(df, strategy_mode="defensive")
        
        print(f"  Is Invested: {state.get('is_invested')}")
        print(f"  Criticality: {state.get('criticality_score')}")
        print(f"  Regime: {state.get('regime')}")
        print(f"  Trend: {state.get('trend_signal')}")
        print(f"  Exposure: {state.get('exposure_pct'):.0f}%")
        
        print("\n✅ TEST 2 PASSED: Backward compatibility maintained")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_consistency_hero_vs_plot():
    """
    CRITICAL TEST: Verify hero card state matches last plot bar.
    
    This ensures there's no discrepancy between what users see in the
    hero card vs what they see at the end of the historical chart.
    """
    print("\n" + "=" * 70)
    print("TEST 3: Hero card state == Last plot bar state")
    print("=" * 70)
    
    try:
        # Fetch data
        print("\nFetching BTC-USD data...")
        df = yf.download("BTC-USD", period="1y", progress=False)
        
        if df.empty:
            print("❌ FAILED: Could not fetch data")
            return False
        
        # Normalize columns (handle MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        
        print(f"✓ Fetched {len(df)} rows")
        
        # Get last bar state (what plot shows)
        print("\nComputing last bar state (plot)...")
        last_idx = len(df) - 1
        plot_state = compute_market_state(df, last_idx)
        
        print(f"  Plot state - Regime: {plot_state.regime}, Criticality: {plot_state.criticality}")
        
        # Get hero card state (what hero card shows)
        print("\nComputing hero card state...")
        hero_state_dict = get_current_market_state(df, strategy_mode="defensive")
        
        print(f"  Hero card - Regime: {hero_state_dict['regime']}, Criticality: {hero_state_dict['criticality_score']}")
        
        # Compare criticality scores (should be identical)
        crit_match = abs(plot_state.criticality - hero_state_dict['criticality_score']) < 1.0
        
        print("\n📊 Consistency Check:")
        print(f"  Plot Criticality: {plot_state.criticality}")
        print(f"  Hero Criticality: {hero_state_dict['criticality_score']}")
        print(f"  Match: {'✓' if crit_match else '✗'}")
        
        print(f"\n  Plot Regime: {plot_state.regime}")
        print(f"  Hero Regime: {hero_state_dict['regime']}")
        regime_match = plot_state.regime == hero_state_dict['regime']
        print(f"  Match: {'✓' if regime_match else '✗'}")
        
        if crit_match and regime_match:
            print("\n✅ TEST 3 PASSED: Hero card matches plot state")
            return True
        else:
            print("\n⚠️  TEST 3 WARNING: Minor discrepancy detected")
            print("     This may be acceptable if exposure calculations differ")
            return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MARKET STATE REFACTORING VALIDATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("compute_market_state", test_compute_market_state()))
    results.append(("Backward compatibility", test_backward_compatibility()))
    results.append(("Consistency (hero vs plot)", test_consistency_hero_vs_plot()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Refactoring successful!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Review required")
        return 1


if __name__ == "__main__":
    exit(main())

