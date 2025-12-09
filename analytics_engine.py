import pandas as pd
import numpy as np
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