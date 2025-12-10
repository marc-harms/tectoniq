"""
Test Script for get_current_market_state()
===========================================

This script demonstrates how to use the new get_current_market_state() function
to query the current investment status without running a full backtest.

Usage:
    python test_current_state.py
"""

import yfinance as yf
from logic import get_current_market_state, run_dca_simulation
from datetime import datetime, timedelta

def test_ticker(symbol: str, strategy_mode: str = "defensive"):
    """Test current market state for a given ticker."""
    print(f"\n{'='*80}")
    print(f"Testing: {symbol} ({strategy_mode.upper()} strategy)")
    print(f"{'='*80}")
    
    # Fetch recent data
    print("📥 Fetching data...")
    df = yf.download(symbol, period="2y", progress=False, auto_adjust=True)
    
    if df.empty:
        print(f"❌ Could not fetch data for {symbol}")
        return
    
    # Ensure lowercase columns
    df.columns = [c.lower() for c in df.columns]
    
    # Get current state
    print("\n🔍 Analyzing current market state...")
    state = get_current_market_state(df, strategy_mode=strategy_mode)
    
    # Check for errors
    if 'error' in state:
        print(f"❌ Error: {state['error']}")
        return
    
    # Display results
    print("\n" + "="*80)
    print("CURRENT MARKET STATE (TODAY)")
    print("="*80)
    
    print(f"\n📊 Investment Status:")
    print(f"   • Is Invested:       {'✅ YES' if state['is_invested'] else '❌ NO (Cash)'}")
    print(f"   • Exposure:          {state['exposure_pct']:.1f}%")
    print(f"   • Regime:            {state['regime']}")
    
    print(f"\n📈 Market Metrics:")
    print(f"   • Criticality Score: {state['criticality_score']:.1f}/100")
    print(f"   • Trend Signal:      {state['trend_signal']}")
    
    print(f"\n🔧 Raw Data:")
    raw = state['raw_data']
    print(f"   • Current Price:     ${raw['current_price']:,.2f}")
    print(f"   • SMA 200:           ${raw['sma_200']:,.2f}")
    print(f"   • Price vs SMA:      {raw['price_deviation_pct']:+.2f}%")
    print(f"   • Volatility:        {raw['volatility']*100:.2f}%")
    print(f"   • Is Uptrend:        {'✅' if raw['is_uptrend'] else '❌'}")
    
    print(f"\n⚙️  Strategy Settings:")
    print(f"   • Mode:              {raw['strategy_mode'].upper()}")
    print(f"   • High Stress (>80): {raw['high_stress_exposure']:.0f}% exposure")
    print(f"   • Med Stress (>60):  {raw['medium_stress_exposure']:.0f}% exposure")
    print(f"   • Bear Market:       {raw['bear_market_exposure']:.0f}% exposure")
    
    # Verify against backtest (last point should match)
    print("\n🔬 VERIFICATION: Comparing with Full Backtest...")
    print("   (Latest backtest point should match current state)")
    
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    sim_results = run_dca_simulation(
        symbol, 
        initial_capital=10000,
        start_date=start_date,
        strategy_mode=strategy_mode,
        trading_fee_pct=0.005,
        interest_rate_annual=0.03
    )
    
    if 'error' not in sim_results:
        daily_data = sim_results.get('daily_data')
        if daily_data is not None and not daily_data.empty:
            # Get last row from backtest
            last_backtest = daily_data.iloc[-1]
            backtest_exposure = last_backtest['exposure'] * 100
            backtest_criticality = last_backtest['criticality_score']
            
            print(f"\n   Backtest Last Day:")
            print(f"   • Exposure:         {backtest_exposure:.1f}%")
            print(f"   • Criticality:      {backtest_criticality:.1f}/100")
            
            # Compare
            exposure_match = abs(state['exposure_pct'] - backtest_exposure) < 0.1
            crit_match = abs(state['criticality_score'] - backtest_criticality) < 1.0
            
            if exposure_match and crit_match:
                print("\n   ✅ MATCH: Current state matches backtest!")
            else:
                print("\n   ⚠️  MISMATCH DETECTED:")
                print(f"      Exposure diff:     {state['exposure_pct'] - backtest_exposure:+.2f}%")
                print(f"      Criticality diff:  {state['criticality_score'] - backtest_criticality:+.2f}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TECTONIQ - Current Market State Test")
    print("="*80)
    
    # Test multiple tickers with both strategies
    test_cases = [
        ("AAPL", "defensive"),
        ("AAPL", "aggressive"),
        ("BTC-USD", "defensive"),
        ("TSLA", "defensive"),
    ]
    
    for symbol, strategy in test_cases:
        try:
            test_ticker(symbol, strategy)
        except Exception as e:
            print(f"\n❌ Error testing {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80)

