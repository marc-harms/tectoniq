import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf # Nur für den Test-Daten-Download nötig

class MarketForensics:
    """
    Die reine Logik-Einheit für statistische Auswertungen.
    Trennt Mathe von UI.
    """

    @staticmethod
    def get_regime_stats(df: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet Regime-Statistiken basierend auf ZUSAMMENHÄNGENDEN BLÖCKEN (Events),
        nicht auf einzelnen Tages-Zeilen. Löst das 'Median=1' Problem.
        """
        # Kopie um Warnungen zu vermeiden
        work_df = df.copy()

        # 1. Block-ID erstellen (Run-Length Encoding)
        # Ändert sich nur, wenn das Regime wechselt
        work_df['block_id'] = (work_df['Regime'] != work_df['Regime'].shift(1)).cumsum()

        # 2. Aggregation: Dauer pro Block berechnen
        # Ergebnis: Eine Liste von Events (z.B. "Stable: 45 Tage", "Critical: 12 Tage")
        block_stats = work_df.groupby(['Regime', 'block_id']).size().reset_index(name='duration_days')

        # 3. Statistik über die Blöcke berechnen
        stats = block_stats.groupby('Regime')['duration_days'].agg(
            Count_Events='count',          # Wie oft kam diese Phase vor?
            Min_Duration_Days='min',       # Kürzeste Phase
            Avg_Duration_Days='mean',      # Mittlere Dauer
            Median_Duration_Days='median', # Median (robust gegen Ausreißer)
            Max_Duration_Days='max'        # Längste Phase jemals
        ).reset_index()

        # 4. Frequenz basierend auf ZEIT (Total Days) hinzufügen
        total_days = len(work_df)
        days_per_regime = work_df['Regime'].value_counts()
        stats['Frequency_Pct'] = stats['Regime'].map(lambda x: (days_per_regime.get(x, 0) / total_days) * 100)

        return stats.round(1).set_index('Regime')

    @staticmethod
    def get_crash_metrics(df: pd.DataFrame) -> dict:
        """
        Forensische Analyse: Findet 'Echte Crashs' (Ground Truth) und prüft,
        ob das Signal gewarnt hat.
        """
        work_df = df.copy()
        
        # Pick price column robustly
        if 'Close' in work_df.columns:
            price_col = 'Close'
        elif 'close' in work_df.columns:
            price_col = 'close'
        elif 'Adj Close' in work_df.columns:
            price_col = 'Adj Close'
        else:
            # Return empty metrics if no price column
            return {
                'total_crashes_5y': 0,
                'avg_crash_depth': 0,
                'detected_count': 0,
                'detection_rate': 0,
                'false_alarm_rate': 0,
                'avg_lead_time_days': 0,
                'crash_list_preview': [],
                'crash_list_full': [],
                'total_signals': 0,
                'justified_signals': 0,
                'false_alarms': 0,
                'lead_times': []
            }

        # Normalize regime labels (strip emojis/whitespace, uppercase)
        if 'Regime' in work_df.columns:
            work_df['Regime_Clean'] = (
                work_df['Regime']
                .astype(str)
                .str.replace('[^\\w\\s]', '', regex=True)
                .str.strip()
                .str.upper()
            )
        else:
            work_df['Regime'] = 'UNKNOWN'
            work_df['Regime_Clean'] = 'UNKNOWN'

        # --- SCHRITT 1: DEFINITION "ECHTER CRASH" (GROUND TRUTH) ---
        
        # Drawdown vom 90-Tage Hoch (mittelfristiger Trend)
        rolling_peak = work_df[price_col].rolling(window=90, min_periods=1).max()
        work_df['drawdown'] = (work_df[price_col] - rolling_peak) / rolling_peak

        # Harte Definition: Crash ist nur, wenn Drawdown < -20%
        # (Für Tech/Krypto evtl auf -25% anpassen, für SAP reichen -20%)
        CRASH_THRESHOLD = -0.20
        work_df['is_crash_day'] = work_df['drawdown'] < CRASH_THRESHOLD

        # Gruppieren: Zusammenhängende Crash-Tage sind 1 Event
        work_df['crash_block'] = (work_df['is_crash_day'] != work_df['is_crash_day'].shift(1)).cumsum()

        # Nur die Blöcke filtern, die wirklich Crashs sind
        crash_groups = work_df[work_df['is_crash_day']].groupby('crash_block')
        
        true_crashes = []
        for _, block in crash_groups:
            start_date = block.index[0]
            end_date = block.index[-1]
            max_loss = block['drawdown'].min()
            duration = (end_date - start_date).days
            
            # De-Bouncing: Ignoriere Mini-Dips unter 5 Tagen Dauer (Rauschen)
            if duration >= 5:
                true_crashes.append({
                    'start_date': start_date,
                    'end_date': end_date,
                    'max_loss': max_loss,
                    'duration': duration
                })

        # Merge crashes that occur within 90 days of each other (single bear market event)
        MERGE_GAP_DAYS = 90
        merged_crashes = []
        for crash in sorted(true_crashes, key=lambda c: c['start_date']):
            if not merged_crashes:
                merged_crashes.append(crash)
                continue
            
            prev = merged_crashes[-1]
            gap_days = (crash['start_date'] - prev['end_date']).days
            if gap_days <= MERGE_GAP_DAYS:
                prev['end_date'] = max(prev['end_date'], crash['end_date'])
                prev['max_loss'] = min(prev['max_loss'], crash['max_loss'])
                prev['duration'] = (prev['end_date'] - prev['start_date']).days
            else:
                merged_crashes.append(crash)

        crashes = merged_crashes
        total_crashes = len(crashes)

        # --- SCHRITT 2: ERKENNUNGSPRÜFUNG (RECALL) ---
        
        detected_count = 0
        lead_times = []

        # Wir suchen nach Warnsignalen: "Critical" oder "High Energy"
        WARNING_SIGNALS = {'CRITICAL', 'HIGH_ENERGY', 'HIGH ENERGY'}

        for crash in crashes:
            c_start = crash['start_date']
            
            # Analyse-Fenster: 21 Tage VOR bis 7 Tage NACH dem Crash-Start
            lookback_start = c_start - pd.Timedelta(days=21)
            lookahead_end = c_start + pd.Timedelta(days=7)
            window = work_df.loc[lookback_start : lookahead_end]
            
            # Gab es IRGENDEIN Warnsignal in diesem Fenster?
            has_warning = window['Regime_Clean'].isin(WARNING_SIGNALS).any()
            
            if has_warning:
                detected_count += 1
                # Lead Time berechnen: Tage vom ersten Warnsignal bis zum Crash
                first_warning_date = window[window['Regime_Clean'].isin(WARNING_SIGNALS)].index[0]
                lead_time = max((c_start - first_warning_date).days, 0)
                lead_times.append(lead_time)

        avg_lead_time = np.mean(lead_times) if lead_times else 0

        # --- SCHRITT 3: FALSE ALARMS (PRECISION) ---
        
        # Identifiziere Signal-Blöcke (Warnung > 3 Tage am Stück)
        work_df['is_signal'] = work_df['Regime_Clean'].isin(WARNING_SIGNALS)
        work_df['signal_block'] = (work_df['is_signal'] != work_df['is_signal'].shift(1)).cumsum()
        
        signal_groups = work_df[work_df['is_signal']].groupby('signal_block')
        
        total_signals = 0
        false_alarms = 0
        
        for _, block in signal_groups:
            # Ignoriere kurzes Flackern (< 3 Tage)
            if len(block) < 3:
                continue
            
            total_signals += 1
            sig_start = block.index[0]
            
            # Schau 30 Tage in die Zukunft: Kam ein Crash?
            lookahead_end = sig_start + pd.Timedelta(days=30)
            
            crash_followed = False
            for crash in crashes:
                # Liegt ein Crash-Start in diesem Fenster?
                if sig_start <= crash['start_date'] <= lookahead_end:
                    crash_followed = True
                    break
            
            if not crash_followed:
                false_alarms += 1

        # Simplified mapping: each detected crash corresponds to one justified signal event
        justified_signals = detected_count
        false_alarms = max(total_signals - justified_signals, 0)
        false_alarm_rate = (false_alarms / total_signals * 100) if total_signals > 0 else 0

        return {
            'total_crashes_5y': total_crashes,
            'avg_crash_depth': np.mean([c['max_loss'] for c in crashes]) if crashes else 0,
            'detected_count': detected_count,
            'detection_rate': (detected_count / total_crashes * 100) if total_crashes > 0 else 0,
            'false_alarm_rate': false_alarm_rate,
            'avg_lead_time_days': avg_lead_time,
            'lead_times': lead_times,
            'crash_list_preview': crashes[-3:],
            'crash_list_full': crashes,
            'total_signals': total_signals,
            'justified_signals': justified_signals,
            'false_alarms': false_alarms
        }


# =============================================================================
# MONTE CARLO FORECAST ENGINE
# =============================================================================

def get_sim_params(regime_name):
    """
    Physics Engine: Translates market regime into AGGRESSIVE simulation parameters.
    
    Each regime produces visually distinct forecast shapes:
    - CRASH/DECLINE: Strong downward drift (cone points down)
    - CRITICAL: Extreme volatility with downside skew (fat fan drags down)
    - MANIA/HIGH_ENERGY: Strong upward drift (cone points up)
    - DORMANT: Minimal drift and volatility (narrow flat tube)
    
    Args:
        regime_name: String containing regime name (e.g., "CRITICAL INSTABILITY", "HIGH ENERGY MANIA")
        
    Returns:
        tuple: (drift_adj, vola_mult, shock_prob, downside_skew)
    """
    # Defaults (Organic Growth / Stable)
    drift_adj = 0.0008      # Slight upward bias
    vola_mult = 1.0         # Normal volatility
    shock_prob = 0.005      # 0.5% probability of shock per day
    downside_skew = False   # No asymmetric skew by default
    
    regime_upper = regime_name.upper()
    
    # STRUCTURAL DECLINE (Slate) - The cone points DOWN
    if "CRASH" in regime_upper or "DECLINE" in regime_upper:
        drift_adj = -0.0015     # Strong NEGATIVE drift (-0.15% daily = -4.5% monthly)
        vola_mult = 1.8         # High volatility
        shock_prob = 0.06       # Frequent shocks
        downside_skew = False   # Already going down
    
    # CRITICAL INSTABILITY (Magma) - Fat fan drags downwards
    elif "CRITICAL" in regime_upper:
        drift_adj = -0.0008     # Slight negative (gravity effect)
        vola_mult = 2.5         # EXTREME volatility (2.5x)
        shock_prob = 0.10       # Very high crash risk
        downside_skew = True    # Asymmetric: downside moves magnified
    
    # HIGH ENERGY MANIA (Pyrite/Gold) - The cone points UP
    elif "MANIA" in regime_upper or "HIGH_ENERGY" in regime_upper or "HIGH ENERGY" in regime_upper:
        drift_adj = 0.0012      # Strong POSITIVE drift (+0.12% daily = +3.6% monthly)
        vola_mult = 1.4         # Elevated volatility (nervous momentum)
        shock_prob = 0.03       # Some risk of reversal
        downside_skew = False   # Momentum carries upward
    
    # DORMANT (Moss) - Narrow flat tube
    elif "DORMANT" in regime_upper:
        drift_adj = 0.0         # No drift
        vola_mult = 0.4         # Very LOW volatility
        shock_prob = 0.0        # No shocks
        downside_skew = False
    
    # GROWTH/STABLE/ACTIVE - Normal behavior
    elif "GROWTH" in regime_upper or "STABLE" in regime_upper or "ACTIVE" in regime_upper:
        # Keep defaults (slight upward bias, normal vol)
        pass
        
    return drift_adj, vola_mult, shock_prob, downside_skew


def run_monte_carlo_simulation(start_price, hist_vola, regime_obj, days=30, runs=1000):
    """
    Run Monte Carlo simulation with AGGRESSIVE regime-specific physics.
    
    Implements:
    - Directional drift (regimes have clear up/down bias)
    - Asymmetric downside skew for critical regimes
    - Sample path extraction for texture visualization
    
    Args:
        start_price: Current asset price
        hist_vola: Historical volatility (daily)
        regime_obj: Dict with 'name' and 'color' keys
        days: Forecast horizon (default 30)
        runs: Number of simulation paths (default 1000)
        
    Returns:
        tuple: (quantiles_df, sample_paths)
            - quantiles_df: DataFrame with day, p05, p25, p50, p75, p95
            - sample_paths: List of 3 random simulation paths for texture
    """
    regime_name = regime_obj.get('name', 'STABLE')
    drift_adj, vola_mult, shock_prob, downside_skew = get_sim_params(regime_name)
    
    # Adjust parameters
    sim_vola = hist_vola * vola_mult
    mu = drift_adj 
    
    # Vectorized simulation (faster than loops)
    # 1. Calculate shocks (Yes/No matrix)
    shock_matrix = np.random.choice([0, 1], size=(runs, days), p=[1-shock_prob, shock_prob])
    
    # 2. Shock magnitude (Random between 0% and -5%)
    shock_values = np.random.uniform(0, -0.05, size=(runs, days)) * shock_matrix
    
    # 3. Daily returns (Geometric Brownian Motion + Shocks)
    daily_returns = np.random.normal(mu, sim_vola, (runs, days)) + shock_values
    
    # 4. Apply DOWNSIDE SKEW if enabled (for CRITICAL regime)
    # Amplify negative moves, dampen positive moves
    if downside_skew:
        daily_returns = np.where(
            daily_returns < 0,
            daily_returns * 1.5,  # Magnify downside by 50%
            daily_returns * 0.5   # Dampen upside by 50%
        )
    
    # 5. Cumulative price paths
    price_paths = np.zeros((runs, days + 1))
    price_paths[:, 0] = start_price
    
    for t in range(1, days + 1):
        price_paths[:, t] = price_paths[:, t-1] * (1 + daily_returns[:, t-1])
    
    # 6. Extract 3 random sample paths for texture visualization
    sample_indices = np.random.choice(runs, size=3, replace=False)
    day_array = np.arange(days + 1)  # Convert to numpy array for plotly compatibility
    sample_paths = [
        {'day': day_array, 'price': price_paths[idx, :]} 
        for idx in sample_indices
    ]
        
    # 7. Extract detailed quantiles for multi-layer fan chart
    quantiles_df = pd.DataFrame({
        'day': day_array,  # Use same numpy array for consistency
        'p05': np.percentile(price_paths, 5, axis=0),   # Worst Case (Extreme)
        'p25': np.percentile(price_paths, 25, axis=0),  # Lower Band (Likely)
        'p50': np.percentile(price_paths, 50, axis=0),  # Median
        'p75': np.percentile(price_paths, 75, axis=0),  # Upper Band (Likely)
        'p95': np.percentile(price_paths, 95, axis=0)   # Best Case (Extreme)
    })
    
    return quantiles_df, sample_paths


def hex_to_rgba(hex_color, opacity):
    """
    Convert hex color to RGBA string with specified opacity.
    
    This helper ensures precise control over transparency in the fan chart layers.
    
    Args:
        hex_color: Hex color string (e.g., "#C0392B" or "C0392B")
        opacity: Float between 0.0 and 1.0
        
    Returns:
        String in format "rgba(r, g, b, a)"
        
    Example:
        >>> hex_to_rgba("#C0392B", 0.1)
        "rgba(192, 57, 43, 0.1)"
    """
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert hex to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    return f"rgba({r}, {g}, {b}, {opacity})"


def plot_forecast(sim_df, regime_color, sample_paths=None, is_dark=False):
    """
    Create a proper 'Fan Chart' (Probabilistic Cone) for Monte Carlo forecast.
    
    Uses RGBA colors for precise transparency control to prevent solid block appearance.
    Creates four distinct visual layers with graduated opacity + texture.
    
    Visual Strategy:
    - Layer 1: Outer extreme band (p05-p95) - Very faint background
    - Layer 2: Inner likely band (p25-p75) - Slightly darker, overlays Layer 1
    - Layer 3: Sample paths (texture) - Thin chaotic lines showing individual simulations
    - Layer 4: Median projection - Bold dashed line
    
    Args:
        sim_df: DataFrame with day, p05, p25, p50, p75, p95 columns
        regime_color: Hex color code for the regime (e.g., "#C0392B")
        sample_paths: List of dicts with 'day' and 'price' keys (for texture)
        is_dark: Boolean for dark mode styling
        
    Returns:
        Plotly Figure object with proper fan chart rendering
    """
    fig = go.Figure()
    
    # Background colors
    bg_color = 'rgba(0,0,0,0)' if not is_dark else 'rgba(20,20,20,0.8)'
    text_color = '#2C3E50' if not is_dark else '#E0E0E0'
    grid_color = '#F2F3F4' if not is_dark else '#3A3A3A'
    
    # Convert regime color to RGBA with specific opacities
    outer_fill = hex_to_rgba(regime_color, 0.1)   # 10% opacity for outer band
    inner_fill = hex_to_rgba(regime_color, 0.25)  # 25% opacity for inner band (will overlay)
    
    # =============================================================================
    # Layer 1: OUTER EXTREME BAND (p05 - p95)
    # =============================================================================
    # This is the background layer showing extreme possibilities
    
    # Trace A: Upper bound (p95) - invisible anchor line
    fig.add_trace(go.Scatter(
        x=sim_df['day'], 
        y=sim_df['p95'],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Trace B: Lower bound (p05) - fills up to p95 with very light color
    fig.add_trace(go.Scatter(
        x=sim_df['day'], 
        y=sim_df['p05'],
        mode='lines',
        line=dict(width=0),
        fill='tonexty',
        fillcolor=outer_fill,  # RGBA with 10% opacity
        name='90% Range (Extreme)',
        hoverinfo='skip',
        showlegend=True
    ))
    
    # =============================================================================
    # Layer 2: INNER LIKELY BAND (p25 - p75)
    # =============================================================================
    # This overlays Layer 1, creating darker center to show likely outcomes
    
    # Trace C: Upper bound (p75) - invisible anchor line
    fig.add_trace(go.Scatter(
        x=sim_df['day'], 
        y=sim_df['p75'],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Trace D: Lower bound (p25) - fills up to p75 with darker color
    fig.add_trace(go.Scatter(
        x=sim_df['day'], 
        y=sim_df['p25'],
        mode='lines',
        line=dict(width=0),  # No visible line, just fill
        fill='tonexty',
        fillcolor=inner_fill,  # RGBA with 25% opacity
        name='50% Range (Likely)',
        hoverinfo='skip',
        showlegend=True
    ))
    
    # =============================================================================
    # Layer 3: SAMPLE PATHS (Texture)
    # =============================================================================
    # Add 3 random individual simulation paths to show chaotic nature
    # This prevents the chart from looking like a geometric shape
    
    if sample_paths:
        path_color_rgba = hex_to_rgba(regime_color, 0.3)  # 30% opacity for texture
        
        for i, path in enumerate(sample_paths):
            fig.add_trace(go.Scatter(
                x=path['day'],
                y=path['price'],
                mode='lines',
                line=dict(
                    color=path_color_rgba,
                    width=1  # Very thin lines
                ),
                showlegend=False,  # Don't clutter legend
                hoverinfo='skip'
            ))
    
    # =============================================================================
    # Layer 4: MEDIAN PROJECTION LINE
    # =============================================================================
    # Bold dashed line showing the expected path
    
    fig.add_trace(go.Scatter(
        x=sim_df['day'], 
        y=sim_df['p50'],
        mode='lines',
        line=dict(
            color=regime_color, 
            width=2.5, 
            dash='longdash'  # Professional dashed style
        ),
        name='Median Projection',
        hovertemplate='Day %{x}<br>Median: %{y:.2f}<extra></extra>',
        showlegend=True
    ))
    
    # =============================================================================
    # Layout Styling - Scientific Heritage Theme
    # =============================================================================
    fig.update_layout(
        title="Probabilistic Path Projection (30 Days) - Experimental",
        title_font=dict(
            family="Merriweather, serif",
            size=16,
            color=text_color
        ),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        font=dict(family="Roboto, sans-serif", color=text_color, size=12),
        height=400,
        margin=dict(l=20, r=20, t=60, b=40),
        xaxis=dict(
            title="Days Forward",
            title_font=dict(size=13),
            showgrid=True, 
            gridcolor=grid_color, 
            gridwidth=1,
            zeroline=False
        ),
        yaxis=dict(
            title="Projected Price", 
            title_font=dict(size=13),
            showgrid=True, 
            gridcolor=grid_color,
            gridwidth=1,
            zeroline=False
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            bgcolor='rgba(255,255,255,0.8)'
        )
    )
    
    return fig


# --- TEST BEREICH (Wird nur im Terminal ausgeführt) ---
if __name__ == "__main__":
    print("🚀 Starte Analytics Engine Test...\n")
    
    tickers = ["SAP", "NVDA"]
    
    for ticker in tickers:
        print(f"--- ANALYSE FÜR: {ticker} ---")
        
        # 1. Daten holen (Letzte 5 Jahre)
        data = yf.download(ticker, period="5y", progress=False)
        # Flatten MultiIndex if necessary (yfinance update quirk)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        df = pd.DataFrame(index=data.index)
        df['Close'] = data['Close']
        
        # 2. MOCK REGIME GENERATOR (Nur für diesen Test!)
        # Wir simulieren hier deine SOC Logik vereinfacht, damit das Script läuft.
        # Hohe Vola = Critical, Niedrige Vola = Stable.
        df['Returns'] = df['Close'].pct_change()
        df['Vol_30'] = df['Returns'].rolling(30).std()
        
        conditions = [
            (df['Vol_30'] > df['Vol_30'].quantile(0.90)), # Top 10% Vola -> Critical
            (df['Vol_30'] > df['Vol_30'].quantile(0.70)), # Top 30% -> High Energy
            (df['Vol_30'] < df['Vol_30'].quantile(0.30))  # Low Vola -> Stable
        ]
        choices = ['CRITICAL', 'HIGH_ENERGY', 'STABLE']
        df['Regime'] = np.select(conditions, choices, default='ACTIVE')
        
        # 3. Teste Regime Stats
        print("\n[A] Regime Profile (Median > 1?):")
        stats = MarketForensics.get_regime_stats(df)
        print(stats[['Frequency_Pct', 'Median_Duration_Days', 'Avg_Duration_Days']])
        
        # 4. Teste Crash Logic
        print("\n[B] Crash Forensics (Realistische Anzahl?):")
        metrics = MarketForensics.get_crash_metrics(df)
        
        print(f"Total True Crashes (5Y): {metrics['total_crashes_5y']}")
        print(f"Detected: {metrics['detected_count']} ({metrics['detection_rate']:.1f}%)")
        print(f"False Alarm Rate: {metrics['false_alarm_rate']:.1f}%")
        print(f"Ø Lead Time: {metrics['avg_lead_time_days']:.1f} Days")
        print(f"Sample Crashes: {metrics['crash_list_preview']}")
        print("-" * 40 + "\n")