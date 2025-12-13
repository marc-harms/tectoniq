"""
Phase 1: Regime Behavior Validation (External Sanity Check)

This script validates that the market-state engine behaves sensibly, stably,
and defensibly across assets and market conditions.

NO modifications to compute_market_state() - read-only analysis only.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from logic import compute_market_state, MarketState

# Configuration
ASSETS = {
    'SPY': 'Broad Market (S&P 500)',
    'QQQ': 'Tech/Growth (Nasdaq 100)',
    'TSLA': 'High-Volatility Equity',
    'BTC-USD': 'Crypto (Extreme Volatility)',
    'XLP': 'Defensive (Consumer Staples)'
}

YEARS_BACK = 5
MIN_DATA_POINTS = 250  # ~1 year minimum

# Known stress periods for annotation
STRESS_PERIODS = {
    'COVID Crash': ('2020-02-15', '2020-04-15'),
    '2022 Tightening': ('2022-01-01', '2022-10-31'),
    'BTC 2021 Crash': ('2021-11-01', '2022-01-31'),  # BTC only
    'BTC 2022 Low': ('2022-05-01', '2022-07-31'),    # BTC only
}


def fetch_asset_data(symbol: str, years: int = YEARS_BACK) -> pd.DataFrame:
    """Fetch historical OHLCV data for an asset."""
    print(f"  Fetching {symbol}...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365 + 180)  # Extra buffer
    
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        raise ValueError(f"No data for {symbol}")
    
    # Normalize columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    
    print(f"    ✓ {len(df)} rows")
    return df


def compute_all_states(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Compute MarketState for every valid bar."""
    print(f"  Computing market states...")
    
    states = []
    start_idx = 200  # Minimum for SMA200
    
    for idx in range(start_idx, len(df)):
        try:
            state = compute_market_state(df, idx)
            states.append({
                'date': state.date,
                'criticality': state.criticality,
                'regime': state.regime,
                'trend_state': state.trend_state,
                'volatility': state.volatility,
                'volatility_percentile': state.volatility_percentile,
                'volatility_component': state.volatility_component,
                'trend_component': state.trend_component,
                'extension_component': state.extension_component,
                'price': df['close'].iloc[idx]
            })
        except Exception as e:
            print(f"    ⚠️ Warning at index {idx}: {e}")
    
    states_df = pd.DataFrame(states)
    states_df.set_index('date', inplace=True)
    
    print(f"    ✓ {len(states_df)} states computed")
    return states_df


def calculate_regime_distribution(states_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate percentage of time in each regime."""
    total = len(states_df)
    green_pct = (states_df['regime'] == 'GREEN').sum() / total * 100
    yellow_pct = (states_df['regime'] == 'YELLOW').sum() / total * 100
    red_pct = (states_df['regime'] == 'RED').sum() / total * 100
    
    return {
        'GREEN': green_pct,
        'YELLOW': yellow_pct,
        'RED': red_pct
    }


def calculate_regime_persistence(states_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Calculate mean/median duration of each regime."""
    regime_durations = {'GREEN': [], 'YELLOW': [], 'RED': []}
    
    current_regime = None
    duration = 0
    
    for regime in states_df['regime']:
        if regime == current_regime:
            duration += 1
        else:
            if current_regime is not None:
                regime_durations[current_regime].append(duration)
            current_regime = regime
            duration = 1
    
    # Add last streak
    if current_regime is not None:
        regime_durations[current_regime].append(duration)
    
    results = {}
    for regime in ['GREEN', 'YELLOW', 'RED']:
        durations = regime_durations[regime]
        if durations:
            results[regime] = {
                'mean': np.mean(durations),
                'median': np.median(durations),
                'max': np.max(durations),
                'count': len(durations)
            }
        else:
            results[regime] = {
                'mean': 0,
                'median': 0,
                'max': 0,
                'count': 0
            }
    
    return results


def calculate_transition_matrix(states_df: pd.DataFrame) -> Dict[Tuple[str, str], int]:
    """Calculate regime transition counts."""
    transitions = {}
    prev_regime = None
    
    for regime in states_df['regime']:
        if prev_regime is not None and prev_regime != regime:
            key = (prev_regime, regime)
            transitions[key] = transitions.get(key, 0) + 1
        prev_regime = regime
    
    return transitions


def calculate_transitions_per_year(states_df: pd.DataFrame) -> float:
    """Calculate average number of regime changes per year."""
    years = (states_df.index[-1] - states_df.index[0]).days / 365.25
    
    changes = 0
    prev_regime = None
    for regime in states_df['regime']:
        if prev_regime is not None and prev_regime != regime:
            changes += 1
        prev_regime = regime
    
    return changes / years if years > 0 else 0


def plot_price_with_regimes(states_df: pd.DataFrame, symbol: str, asset_name: str, 
                            stress_periods: Dict[str, Tuple[str, str]]) -> None:
    """Plot price chart with regime background shading."""
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Plot price
    ax.plot(states_df.index, states_df['price'], color='black', linewidth=1.5, label='Price')
    
    # Add regime shading
    regime_colors = {'GREEN': '#27AE6020', 'YELLOW': '#F39C1220', 'RED': '#C0392B20'}
    
    current_regime = None
    start_idx = 0
    
    for i, (date, row) in enumerate(states_df.iterrows()):
        if row['regime'] != current_regime:
            if current_regime is not None:
                ax.axvspan(states_df.index[start_idx], date, 
                          facecolor=regime_colors[current_regime], alpha=0.3)
            current_regime = row['regime']
            start_idx = i
    
    # Add last segment
    if current_regime is not None:
        ax.axvspan(states_df.index[start_idx], states_df.index[-1], 
                  facecolor=regime_colors[current_regime], alpha=0.3)
    
    # Annotate stress periods
    relevant_periods = {k: v for k, v in stress_periods.items() 
                       if 'BTC' not in k or 'BTC' in symbol}
    
    for period_name, (start, end) in relevant_periods.items():
        try:
            start_date = pd.Timestamp(start)
            end_date = pd.Timestamp(end)
            if start_date >= states_df.index[0] and end_date <= states_df.index[-1]:
                ax.axvspan(start_date, end_date, color='red', alpha=0.1, linestyle='--')
                mid_date = start_date + (end_date - start_date) / 2
                ax.text(mid_date, ax.get_ylim()[1] * 0.95, period_name, 
                       ha='center', va='top', fontsize=9, rotation=0, 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.2))
        except:
            pass
    
    ax.set_title(f'{symbol} - {asset_name}\nPrice with Regime Background', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price ($)')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Add regime legend
    green_patch = mpatches.Patch(color='#27AE60', alpha=0.3, label='GREEN')
    yellow_patch = mpatches.Patch(color='#F39C12', alpha=0.3, label='YELLOW')
    red_patch = mpatches.Patch(color='#C0392B', alpha=0.3, label='RED')
    ax.legend(handles=[green_patch, yellow_patch, red_patch], loc='upper right')
    
    plt.tight_layout()
    plt.savefig(f'validation_{symbol}_price_regimes.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"    ✓ Saved validation_{symbol}_price_regimes.png")


def plot_criticality_timeseries(states_df: pd.DataFrame, symbol: str, asset_name: str) -> None:
    """Plot criticality time series with regime thresholds."""
    fig, ax = plt.subplots(figsize=(16, 6))
    
    # Plot criticality
    ax.plot(states_df.index, states_df['criticality'], color='navy', linewidth=1, label='Criticality')
    
    # Add regime threshold lines
    ax.axhline(y=40, color='#27AE60', linestyle='--', linewidth=2, label='GREEN threshold (40)')
    ax.axhline(y=70, color='#C0392B', linestyle='--', linewidth=2, label='RED threshold (70)')
    
    # Shade regime zones
    ax.axhspan(0, 40, facecolor='#27AE60', alpha=0.1)
    ax.axhspan(40, 70, facecolor='#F39C12', alpha=0.1)
    ax.axhspan(70, 100, facecolor='#C0392B', alpha=0.1)
    
    ax.set_title(f'{symbol} - {asset_name}\nCriticality Score Over Time', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Criticality (0-100)')
    ax.set_ylim(0, 100)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'validation_{symbol}_criticality.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"    ✓ Saved validation_{symbol}_criticality.png")


def interpret_asset_behavior(symbol: str, asset_name: str, states_df: pd.DataFrame,
                             distribution: Dict[str, float], persistence: Dict[str, Dict],
                             transitions: Dict[Tuple[str, str], int]) -> List[str]:
    """Generate interpretation bullet points for an asset."""
    observations = []
    
    # Check regime distribution
    if distribution['RED'] > 25:
        observations.append(f"⚠️ RED regime {distribution['RED']:.1f}% of time (>25% = alarm fatigue risk)")
    elif distribution['RED'] < 5:
        observations.append(f"✓ RED regime {distribution['RED']:.1f}% of time (rare, as expected)")
    else:
        observations.append(f"✓ RED regime {distribution['RED']:.1f}% of time (reasonable)")
    
    # Check RED persistence
    red_median = persistence['RED']['median']
    if red_median < 3:
        observations.append(f"⚠️ Median RED duration {red_median:.1f} days (< 3 = flickering)")
    else:
        observations.append(f"✓ Median RED duration {red_median:.1f} days (stable)")
    
    # Check for direct GREEN→RED jumps
    green_to_red = transitions.get(('GREEN', 'RED'), 0)
    total_transitions = sum(transitions.values())
    if total_transitions > 0:
        green_red_pct = green_to_red / total_transitions * 100
        if green_red_pct > 10:
            observations.append(f"⚠️ GREEN→RED jumps: {green_to_red} ({green_red_pct:.1f}% of transitions)")
        else:
            observations.append(f"✓ GREEN→RED jumps: {green_to_red} ({green_red_pct:.1f}%, rare as expected)")
    
    # Check criticality clustering
    crit_values = states_df['criticality'].values
    near_40 = ((crit_values >= 38) & (crit_values <= 42)).sum() / len(crit_values) * 100
    near_70 = ((crit_values >= 68) & (crit_values <= 72)).sum() / len(crit_values) * 100
    
    if near_40 > 15 or near_70 > 15:
        observations.append(f"⚠️ Criticality clusters near thresholds (40: {near_40:.1f}%, 70: {near_70:.1f}%)")
    else:
        observations.append(f"✓ Criticality distribution smooth (no excessive threshold clustering)")
    
    return observations


def validate_asset(symbol: str, asset_name: str) -> Dict[str, Any]:
    """Run full validation for a single asset."""
    print(f"\n{'='*70}")
    print(f"Validating {symbol} - {asset_name}")
    print('='*70)
    
    try:
        # Fetch data
        df = fetch_asset_data(symbol, YEARS_BACK)
        
        if len(df) < MIN_DATA_POINTS:
            print(f"  ⚠️ Insufficient data ({len(df)} rows, need {MIN_DATA_POINTS})")
            return None
        
        # Compute all states
        states_df = compute_all_states(df, symbol)
        
        if len(states_df) < 100:
            print(f"  ⚠️ Too few valid states ({len(states_df)})")
            return None
        
        # Calculate metrics
        print(f"  Calculating metrics...")
        distribution = calculate_regime_distribution(states_df)
        persistence = calculate_regime_persistence(states_df)
        transitions = calculate_transition_matrix(states_df)
        transitions_per_year = calculate_transitions_per_year(states_df)
        
        # Criticality stats
        crit_stats = {
            'mean': states_df['criticality'].mean(),
            'median': states_df['criticality'].median(),
            'std': states_df['criticality'].std(),
            'min': states_df['criticality'].min(),
            'max': states_df['criticality'].max()
        }
        
        # Generate visuals
        print(f"  Generating visualizations...")
        plot_price_with_regimes(states_df, symbol, asset_name, STRESS_PERIODS)
        plot_criticality_timeseries(states_df, symbol, asset_name)
        
        # Interpret behavior
        observations = interpret_asset_behavior(symbol, asset_name, states_df,
                                               distribution, persistence, transitions)
        
        return {
            'symbol': symbol,
            'name': asset_name,
            'data_points': len(states_df),
            'date_range': (states_df.index[0].date(), states_df.index[-1].date()),
            'distribution': distribution,
            'persistence': persistence,
            'transitions': transitions,
            'transitions_per_year': transitions_per_year,
            'criticality_stats': crit_stats,
            'observations': observations
        }
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_asset_summary(result: Dict[str, Any]) -> None:
    """Print formatted summary for an asset."""
    print(f"\n{'='*70}")
    print(f"{result['symbol']} - {result['name']}")
    print('='*70)
    
    print(f"\n📊 Data Range: {result['date_range'][0]} to {result['date_range'][1]}")
    print(f"   Total bars: {result['data_points']}")
    
    print(f"\n🎨 Regime Distribution:")
    for regime in ['GREEN', 'YELLOW', 'RED']:
        pct = result['distribution'][regime]
        print(f"   {regime:7s}: {pct:5.1f}%")
    
    print(f"\n⏱️  Regime Persistence (days):")
    for regime in ['GREEN', 'YELLOW', 'RED']:
        pers = result['persistence'][regime]
        print(f"   {regime:7s}: Mean={pers['mean']:5.1f}, Median={pers['median']:5.1f}, Max={pers['max']:3.0f}, Count={pers['count']:3d}")
    
    print(f"\n🔄 Transition Analysis:")
    print(f"   Transitions per year: {result['transitions_per_year']:.1f}")
    print(f"   Transition matrix:")
    for (from_regime, to_regime), count in sorted(result['transitions'].items()):
        print(f"      {from_regime:7s} → {to_regime:7s}: {count:3d}")
    
    print(f"\n📈 Criticality Statistics:")
    crit = result['criticality_stats']
    print(f"   Mean: {crit['mean']:.1f}, Median: {crit['median']:.1f}, Std: {crit['std']:.1f}")
    print(f"   Range: [{crit['min']:.0f}, {crit['max']:.0f}]")
    
    print(f"\n💡 Observations:")
    for obs in result['observations']:
        print(f"   {obs}")


def generate_overall_verdict(results: List[Dict[str, Any]]) -> str:
    """Generate overall verdict based on all asset validations."""
    concerns = []
    
    for result in results:
        if result is None:
            continue
        
        # Check for alarm fatigue
        if result['distribution']['RED'] > 25:
            concerns.append(f"{result['symbol']}: RED > 25% (alarm fatigue)")
        
        # Check for flickering
        if result['persistence']['RED']['median'] < 3:
            concerns.append(f"{result['symbol']}: RED median < 3 days (flickering)")
        
        # Check for excessive GREEN→RED
        green_red = result['transitions'].get(('GREEN', 'RED'), 0)
        total_trans = sum(result['transitions'].values())
        if total_trans > 0 and (green_red / total_trans) > 0.15:
            concerns.append(f"{result['symbol']}: >15% GREEN→RED jumps")
    
    if len(concerns) == 0:
        return "✅ BEHAVIOR ACCEPTABLE - Model behaves as a sane instability detector"
    elif len(concerns) <= 2:
        return f"⚠️ MINOR CONCERNS ({len(concerns)}) - Review before production use:\n   " + "\n   ".join(concerns)
    else:
        return f"❌ THRESHOLD RECALIBRATION REQUIRED - {len(concerns)} concerns detected:\n   " + "\n   ".join(concerns)


def main():
    """Run full validation suite."""
    print("\n" + "="*70)
    print("PHASE 1: REGIME BEHAVIOR VALIDATION")
    print("="*70)
    print("\nObjective: Validate regime behavior across asset classes")
    print("Method: Read-only analysis (NO parameter tuning)")
    print()
    
    results = []
    
    for symbol, asset_name in ASSETS.items():
        result = validate_asset(symbol, asset_name)
        if result is not None:
            results.append(result)
            print_asset_summary(result)
    
    # Overall verdict
    print("\n" + "="*70)
    print("OVERALL VERDICT")
    print("="*70)
    verdict = generate_overall_verdict(results)
    print(f"\n{verdict}\n")
    
    # Summary table
    print("="*70)
    print("SUMMARY TABLE")
    print("="*70)
    print(f"\n{'Asset':<10} {'GREEN%':>8} {'YELLOW%':>8} {'RED%':>8} {'RED Med':>8} {'Trans/Yr':>9}")
    print("-"*70)
    for result in results:
        print(f"{result['symbol']:<10} "
              f"{result['distribution']['GREEN']:>7.1f}% "
              f"{result['distribution']['YELLOW']:>7.1f}% "
              f"{result['distribution']['RED']:>7.1f}% "
              f"{result['persistence']['RED']['median']:>7.1f}d "
              f"{result['transitions_per_year']:>8.1f}")
    
    print("\n" + "="*70)
    print("Validation complete. Review charts and observations above.")
    print("="*70)
    
    return 0 if "ACCEPTABLE" in verdict else 1


if __name__ == "__main__":
    exit(main())

