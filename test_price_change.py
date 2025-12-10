#!/usr/bin/env python3
"""
Test Script - Verify 24h Price Change Fix
==========================================

This script verifies that the price_change_1d field is now
correctly calculated and returned by get_market_phase().

Usage:
    python test_price_change.py
"""

import yfinance as yf
from logic import SOCAnalyzer, DataFetcher

def test_price_change(ticker: str):
    """Test that price_change_1d is calculated correctly."""
    print(f"\n{'='*60}")
    print(f"Testing: {ticker}")
    print(f"{'='*60}")
    
    # Fetch data
    print("📥 Fetching data...")
    fetcher = DataFetcher(cache_enabled=True)
    df = fetcher.fetch_data(ticker)
    
    if df.empty:
        print(f"❌ Could not fetch data for {ticker}")
        return False
    
    # Get market phase
    print("🔍 Analyzing market phase...")
    analyzer = SOCAnalyzer(df, ticker)
    phase = analyzer.get_market_phase()
    
    # Check if price_change_1d exists
    if 'price_change_1d' not in phase:
        print("❌ FAIL: price_change_1d field missing!")
        return False
    
    price_change = phase['price_change_1d']
    current_price = phase['price']
    
    # Verify it's not zero (unless market is truly flat)
    print(f"\n📊 Results:")
    print(f"   Current Price:     ${current_price:,.2f}")
    print(f"   24h Change:        {price_change:+.2f}%")
    
    if price_change == 0.0:
        print(f"\n⚠️  WARNING: Price change is exactly 0.00%")
        print(f"   This could be normal if market is flat, or indicate an issue.")
        
        # Double-check by calculating manually
        if len(df) >= 2:
            prev_price = df['close'].iloc[-2]
            curr_price = df['close'].iloc[-1]
            manual_change = ((curr_price - prev_price) / prev_price) * 100
            print(f"\n   Manual calculation:")
            print(f"   Previous close: ${prev_price:,.2f}")
            print(f"   Current close:  ${curr_price:,.2f}")
            print(f"   Change:         {manual_change:+.2f}%")
            
            if abs(manual_change) < 0.01:
                print(f"\n   ✅ Confirmed: Market is genuinely flat (< 0.01% move)")
                return True
            else:
                print(f"\n   ❌ ISSUE: Manual calc shows {manual_change:+.2f}% but phase shows 0.00%")
                return False
    else:
        print(f"\n✅ SUCCESS: Price change is non-zero ({price_change:+.2f}%)")
        return True
    
    return True


def main():
    """Test multiple tickers."""
    print("\n" + "="*60)
    print("24h Price Change Fix Verification")
    print("="*60)
    
    # Test with multiple popular tickers
    test_tickers = ['AAPL', 'TSLA', 'BTC-USD', 'MSFT']
    
    results = {}
    for ticker in test_tickers:
        try:
            success = test_price_change(ticker)
            results[ticker] = "✅ PASS" if success else "❌ FAIL"
        except Exception as e:
            print(f"\n❌ Error testing {ticker}: {str(e)}")
            results[ticker] = "❌ ERROR"
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for ticker, result in results.items():
        print(f"{ticker:10s} {result}")
    
    # Overall status
    all_passed = all("✅" in r for r in results.values())
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Fix is working!")
    else:
        print("⚠️  Some tests failed - review output above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

