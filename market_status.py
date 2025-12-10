#!/usr/bin/env python3
"""
TECTONIQ Market Status CLI
==========================

Quick command-line tool to check current investment status for any ticker.

Usage:
    python market_status.py AAPL
    python market_status.py BTC-USD --strategy aggressive
    python market_status.py TSLA --verbose
"""

import argparse
import sys
import yfinance as yf
from logic import get_current_market_state


def format_status(state: dict, verbose: bool = False) -> str:
    """Format market state for terminal display."""
    
    # Check for errors
    if 'error' in state:
        return f"❌ Error: {state['error']}"
    
    # Status emoji
    if state['is_invested']:
        status_emoji = "✅"
        if state['exposure_pct'] >= 100:
            status_text = "FULL EXPOSURE"
        elif state['exposure_pct'] >= 50:
            status_text = "PARTIAL EXPOSURE"
        else:
            status_text = "MINIMAL EXPOSURE"
    else:
        status_emoji = "❌"
        status_text = "CASH (RISK OFF)"
    
    # Trend emoji
    trend_emoji = "📈" if state['trend_signal'] == "BULL" else "📉"
    
    # Criticality color
    crit_score = state['criticality_score']
    if crit_score > 80:
        crit_label = "🔴 CRITICAL"
    elif crit_score > 60:
        crit_label = "🟠 HIGH ENERGY"
    else:
        crit_label = "🟢 STABLE"
    
    # Build output
    lines = [
        "",
        "="*60,
        f"MARKET STATUS: {state_emoji_status(state)}",
        "="*60,
        f"Status:       {status_emoji} {status_text}",
        f"Exposure:     {state['exposure_pct']:.1f}%",
        f"Regime:       {state['regime']}",
        f"",
        f"Criticality:  {crit_score:.1f}/100 {crit_label}",
        f"Trend:        {trend_emoji} {state['trend_signal']}",
    ]
    
    if verbose:
        raw = state['raw_data']
        lines.extend([
            "",
            "-"*60,
            "DETAILED METRICS",
            "-"*60,
            f"Current Price:     ${raw['current_price']:,.2f}",
            f"SMA 200:           ${raw['sma_200']:,.2f}",
            f"Price vs SMA:      {raw['price_deviation_pct']:+.2f}%",
            f"Volatility:        {raw['volatility']*100:.2f}%",
            f"Is Uptrend:        {'✅ Yes' if raw['is_uptrend'] else '❌ No'}",
            "",
            "Strategy Settings:",
            f"  Mode:            {raw['strategy_mode'].upper()}",
            f"  High Stress:     {raw['high_stress_exposure']:.0f}% (>80)",
            f"  Medium Stress:   {raw['medium_stress_exposure']:.0f}% (>60)",
            f"  Bear Market:     {raw['bear_market_exposure']:.0f}%",
        ])
    
    lines.append("="*60)
    lines.append("")
    
    return "\n".join(lines)


def state_emoji_status(state: dict) -> str:
    """Get emoji representation of state."""
    if not state['is_invested']:
        return "💰 CASH"
    elif state['exposure_pct'] >= 100:
        return "🚀 FULL"
    elif state['exposure_pct'] >= 50:
        return "⚡ PARTIAL"
    else:
        return "🔍 MINIMAL"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='TECTONIQ Market Status - Check current investment status',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python market_status.py AAPL
  python market_status.py BTC-USD --strategy aggressive
  python market_status.py TSLA --verbose
  python market_status.py SPY --period 5y
        """
    )
    
    parser.add_argument(
        'ticker',
        type=str,
        help='Ticker symbol (e.g., AAPL, BTC-USD, TSLA)'
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        choices=['defensive', 'aggressive'],
        default='defensive',
        help='Strategy mode (default: defensive)'
    )
    
    parser.add_argument(
        '--period',
        type=str,
        default='2y',
        help='Data period to fetch (default: 2y)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed metrics'
    )
    
    args = parser.parse_args()
    
    # Display header
    print("\n" + "="*60)
    print(f"TECTONIQ - Market Status Check")
    print("="*60)
    print(f"Ticker:    {args.ticker}")
    print(f"Strategy:  {args.strategy.upper()}")
    print(f"Period:    {args.period}")
    print("="*60)
    
    # Fetch data
    print("\n📥 Fetching market data...")
    try:
        df = yf.download(args.ticker, period=args.period, progress=False, auto_adjust=True)
        
        if df.empty:
            print(f"❌ Could not fetch data for {args.ticker}")
            print("   - Check if ticker symbol is correct")
            print("   - Verify internet connection")
            return 1
        
        # Ensure lowercase columns
        df.columns = [c.lower() for c in df.columns]
        
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        return 1
    
    # Get current state
    print("🔍 Analyzing current market state...")
    try:
        state = get_current_market_state(df, strategy_mode=args.strategy)
    except Exception as e:
        print(f"❌ Error analyzing data: {str(e)}")
        return 1
    
    # Display results
    print(format_status(state, verbose=args.verbose))
    
    # Interpretation
    if state['is_invested']:
        print("💡 Interpretation:")
        if state['exposure_pct'] >= 100:
            print("   The model suggests FULL exposure to this asset.")
            print("   Market conditions appear stable with manageable volatility.")
        elif state['exposure_pct'] >= 50:
            print("   The model suggests PARTIAL exposure to this asset.")
            print("   Volatility is elevated - position sizing reduces risk.")
        else:
            print("   The model suggests MINIMAL exposure to this asset.")
            print("   Market is showing critical stress levels.")
    else:
        print("💡 Interpretation:")
        print("   The model suggests staying in CASH for this asset.")
        if state['trend_signal'] == 'BEAR':
            print("   Price is below SMA200 (bearish trend).")
        else:
            print("   Volatility is extremely high (critical conditions).")
    
    print("\n⚠️  Disclaimer:")
    print("   This is a statistical analysis tool for educational purposes only.")
    print("   Not financial advice. Consult a professional before investing.")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

