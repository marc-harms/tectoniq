"""
SOC Market Seismograph - Simulation UI Components
=================================================

Portfolio simulation and backtesting UI rendering functions.

Contains:
- render_dca_simulation(): Main simulation interface with strategy comparison

Author: Market Analysis Team
Version: 7.0 (Modularized)
"""

from typing import List
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from logic import run_dca_simulation, calculate_audit_metrics


def render_dca_simulation(tickers: List[str]) -> None:
    """
    Render Lump Sum Investment Simulation comparing all three strategies:
    Buy & Hold, Defensive SOC, and Aggressive SOC.
    
    Shows combined equity curves, drawdown comparison, and metrics table.
    
    Args:
        tickers: List of ticker symbols to simulate (uses selected asset from session state)
    """
    is_dark = st.session_state.get('dark_mode', True)
    
    st.markdown("### Portfolio Simulation")
    st.caption("Compare Buy & Hold vs. Defensive vs. Aggressive SOC Strategies")
    
    # Get selected asset from Analysis Results section
    selected_idx = st.session_state.get('selected_asset', 0)
    if tickers and selected_idx < len(tickers):
        sim_ticker = tickers[selected_idx]
    else:
        sim_ticker = tickers[0] if tickers else 'BTC-USD'
    
    # Show currently selected asset
    st.markdown(f"""
    <div style="background: rgba(102, 126, 234, 0.1); border: 1px solid #667eea; 
                border-radius: 8px; padding: 12px; margin-bottom: 1rem; text-align: center;">
        <span style="color: #888; font-size: 0.85rem;">Simulating for:</span>
        <span style="color: #667eea; font-weight: 600; font-size: 1.1rem; margin-left: 8px;">{sim_ticker}</span>
        <span style="color: #666; font-size: 0.8rem; margin-left: 8px;">(change in Asset Selection above)</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Parameters row
    col1, col2 = st.columns(2)
    
    with col1:
        initial_capital = st.number_input(
            "Initial Capital (€):",
            min_value=1000,
            max_value=1000000,
            value=10000,
            step=1000
        )
    
    with col2:
        years_back = st.slider(
            "Simulation Period (Years):",
            min_value=1,
            max_value=10,
            value=7,
            step=1,
            format="%d Years"
        )
    
    # Reality Settings (Fees & Interest) - Always visible
    st.markdown("#### Reality Settings")
    st.caption("Adjust trading costs and cash interest for realistic simulation")
    
        col_fee, col_interest = st.columns(2)
        
        with col_fee:
            trading_fee_pct = st.slider(
                "Trading Fee & Slippage (%):",
                min_value=0.0, max_value=2.0, value=0.5, step=0.1,
                format="%.1f%%"
            )
        
        with col_interest:
            interest_rate_annual = st.slider(
                "Interest on Cash (% p.a.):",
                min_value=0.0, max_value=5.0, value=3.0, step=0.5,
                format="%.1f%%"
            )
    
    # Run simulation button - centered and smaller
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    col_left, col_btn, col_right = st.columns([1, 1, 1])
    with col_btn:
        run_clicked = st.button("Run Simulation", use_container_width=True)
    
    if run_clicked:
        # Set flag for PLG rate limiting (registered in app.py)
        st.session_state.simulation_running = True
        
        start_date = (datetime.now() - timedelta(days=years_back * 365)).strftime('%Y-%m-%d')
        
        # === RUN BOTH SIMULATIONS ===
        with st.spinner(f"⚙️ Reconstructing {years_back}-year tectonic timeline for {sim_ticker}... Simulating phase transitions..."):
            # Run Defensive simulation
            results_def = run_dca_simulation(
                sim_ticker, 
                initial_capital=initial_capital, 
                start_date=start_date, 
                years_back=years_back,
                strategy_mode="defensive",
                trading_fee_pct=trading_fee_pct / 100,
                interest_rate_annual=interest_rate_annual / 100
            )
            
            # Run Aggressive simulation
            results_agg = run_dca_simulation(
                sim_ticker, 
                initial_capital=initial_capital, 
                start_date=start_date, 
                years_back=years_back,
                strategy_mode="aggressive",
                trading_fee_pct=trading_fee_pct / 100,
                interest_rate_annual=interest_rate_annual / 100
            )
        
        # Check for errors
        if 'error' in results_def:
            st.error(f"Defensive simulation error: {results_def['error']}")
            return
        if 'error' in results_agg:
            st.error(f"Aggressive simulation error: {results_agg['error']}")
            return
        
        # Store in session state for theme persistence
        st.session_state.sim_results_def = results_def
        st.session_state.sim_results_agg = results_agg
        st.session_state.sim_initial_capital = initial_capital
        st.session_state.sim_years_back = years_back
        st.session_state.sim_ticker = sim_ticker
        st.session_state.sim_trading_fee_pct = trading_fee_pct
        st.session_state.sim_interest_rate_annual = interest_rate_annual
    
    # Display results if available in session state
    if 'sim_results_def' not in st.session_state:
        return
    
    results_def = st.session_state.sim_results_def
    results_agg = st.session_state.sim_results_agg
    initial_capital = st.session_state.sim_initial_capital
    years_back = st.session_state.sim_years_back
    trading_fee_pct = st.session_state.sim_trading_fee_pct
    interest_rate_annual = st.session_state.sim_interest_rate_annual
    
    sum_def = results_def.get('summary', {})
    sum_agg = results_agg.get('summary', {})
    
    # Results header
    st.markdown("---")
    st.markdown("#### Strategy Comparison Results")
    
    # Strategy explanations
    st.markdown("""
    <div style="background: rgba(102, 126, 234, 0.1); border-left: 3px solid #667eea; padding: 14px; margin: 16px 0; border-radius: 4px;">
        <strong>📚 Strategy Overview:</strong><br>
        <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 0.9rem; line-height: 1.6;">
            <li><strong>Buy & Hold:</strong> Remains 100% invested at all times, regardless of market conditions (baseline strategy)</li>
            <li><strong>Defensive SOC:</strong> Exits to cash during Volatile/Transitioning regimes to preserve capital and avoid drawdowns</li>
            <li><strong>Aggressive SOC:</strong> Stays invested during all regimes except extreme volatility, maximizing market exposure for higher returns</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # === COMPARISON TABLE ===
    st.markdown("##### Performance Overview")
    
    # Build comparison data
    bh_final = sum_def.get('buyhold_final', 0)
    bh_return = sum_def.get('buyhold_return_pct', 0)
    bh_dd = sum_def.get('max_dd_buyhold', 0)
    
    def_final = sum_def.get('soc_final', 0)
    def_return = sum_def.get('soc_return_pct', 0)
    def_dd = sum_def.get('max_dd_soc', 0)
    def_trades = sum_def.get('trade_count', 0)
    def_exposure = sum_def.get('avg_exposure', 100)
    
    agg_final = sum_agg.get('soc_final', 0)
    agg_return = sum_agg.get('soc_return_pct', 0)
    agg_dd = sum_agg.get('max_dd_soc', 0)
    agg_trades = sum_agg.get('trade_count', 0)
    agg_exposure = sum_agg.get('avg_exposure', 100)
    
    # Calculate trades per month
    def_trades_per_month = def_trades / (years_back * 12) if years_back > 0 else 0
    agg_trades_per_month = agg_trades / (years_back * 12) if years_back > 0 else 0
    
    # Determine if trade frequency is high (warning indicator)
    def_high_trades = def_trades_per_month > 2
    agg_high_trades = agg_trades_per_month > 2
    
    # Build styled HTML table
    def_trades_bg = "background: rgba(255, 100, 100, 0.2);" if def_high_trades else ""
    agg_trades_bg = "background: rgba(255, 100, 100, 0.2);" if agg_high_trades else ""
    
    table_html = f"""
    <style>
        .perf-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}
        .perf-table th {{
            background: rgba(102, 126, 234, 0.3);
            padding: 12px 10px;
            text-align: center;
            font-weight: 700;
            border-bottom: 2px solid #667eea;
        }}
        .perf-table td {{
            padding: 10px;
            text-align: center;
            border-bottom: 1px solid #444;
        }}
        .perf-table tr:hover {{
            background: rgba(102, 126, 234, 0.05);
        }}
        .row-highlight {{
            background: rgba(102, 126, 234, 0.15);
            font-weight: 600;
        }}
        .row-bold {{
            font-weight: 600;
        }}
        .metric-label {{
            text-align: left;
            padding-left: 15px;
        }}
    </style>
    <table class="perf-table">
        <thead>
            <tr>
                <th class="metric-label">Metric</th>
                <th>Buy & Hold</th>
                <th>Defensive</th>
                <th>Aggressive</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-highlight">
                <td class="metric-label"><b>Final Value</b></td>
                <td><b>€{bh_final:,.0f}</b></td>
                <td><b>€{def_final:,.0f}</b></td>
                <td><b>€{agg_final:,.0f}</b></td>
            </tr>
            <tr>
                <td class="metric-label">Total Return</td>
                <td>{bh_return:+.1f}%</td>
                <td>{def_return:+.1f}%</td>
                <td>{agg_return:+.1f}%</td>
            </tr>
            <tr>
                <td class="metric-label">Max Drawdown</td>
                <td>{bh_dd:.1f}%</td>
                <td>{def_dd:.1f}%</td>
                <td>{agg_dd:.1f}%</td>
            </tr>
            <tr>
                <td class="metric-label">Avg. Exposure</td>
                <td>100%</td>
                <td>{def_exposure:.0f}%</td>
                <td>{agg_exposure:.0f}%</td>
            </tr>
            <tr>
                <td class="metric-label">Total Trades</td>
                <td>0</td>
                <td style="{def_trades_bg}">{def_trades}</td>
                <td style="{agg_trades_bg}">{agg_trades}</td>
            </tr>
            <tr>
                <td class="metric-label">Trades/Month (Ø)</td>
                <td>0</td>
                <td style="{def_trades_bg}">{def_trades_per_month:.1f}</td>
                <td style="{agg_trades_bg}">{agg_trades_per_month:.1f}</td>
            </tr>
            <tr class="row-highlight">
                <td class="metric-label"><b>vs. Buy & Hold</b></td>
                <td><b>—</b></td>
                <td><b>{def_return - bh_return:+.1f}%</b></td>
                <td><b>{agg_return - bh_return:+.1f}%</b></td>
            </tr>
        </tbody>
    </table>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Key insight callout
    best_return = max(bh_return, def_return, agg_return)
    best_dd = max(bh_dd, def_dd, agg_dd)  # Less negative is better
    
    if def_return == best_return:
        winner_return = "Defensive"
    elif agg_return == best_return:
        winner_return = "Aggressive"
    else:
        winner_return = "Buy & Hold"
    
    if def_dd == best_dd:
        winner_dd = "Defensive"
    elif agg_dd == best_dd:
        winner_dd = "Aggressive"
    else:
        winner_dd = "Buy & Hold"
    
    col_insight1, col_insight2 = st.columns(2)
    with col_insight1:
        st.success(f"**Best Return:** {winner_return} ({best_return:+.1f}%)")
    with col_insight2:
        st.info(f"**Lowest Drawdown:** {winner_dd} ({best_dd:.1f}%)")
    
    # === EQUITY CURVES (3 lines) ===
    st.markdown("#### Equity Curves Comparison")
    
    equity_def = results_def.get('equity_curve', pd.DataFrame())
    equity_agg = results_agg.get('equity_curve', pd.DataFrame())
    
    if not equity_def.empty:
        fig = go.Figure()
        
        # Scientific Heritage colors - ink tones
        legend_color = '#333333'
        
        # Buy & Hold - Asbestos Grey (dashed, thinner)
        fig.add_trace(go.Scatter(
            x=equity_def['date'],
            y=equity_def['buyhold_value'],
            name='Buy & Hold',
            line=dict(color='#7F8C8D', width=1.5, dash='dash'),
            mode='lines'
        ))
        
        # Defensive SOC - Midnight Blue Ink (solid, thicker)
        fig.add_trace(go.Scatter(
            x=equity_def['date'],
            y=equity_def['soc_value'],
            name='Defensive',
            line=dict(color='#2C3E50', width=2),
            mode='lines'
        ))
        
        # Aggressive SOC - Ochre/Pumpkin
        if not equity_agg.empty:
            fig.add_trace(go.Scatter(
                x=equity_agg['date'],
                y=equity_agg['soc_value'],
                name='Aggressive',
                line=dict(color='#D35400', width=2),
                mode='lines'
            ))
        
        # Initial capital line (very subtle)
        fig.add_trace(go.Scatter(
            x=equity_def['date'],
            y=[initial_capital] * len(equity_def),
            name='Initial Capital',
            line=dict(color='#BDC3C7', width=0.8, dash='dot'),
            mode='lines'
        ))
        
        # Scientific Journal style
        axis_color = '#333333'
        grid_color = '#E6E1D3'
        
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent
            plot_bgcolor='rgba(0,0,0,0)',    # Transparent
            height=400,
            margin=dict(t=20, b=50, l=60, r=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(family="Merriweather, serif", color=legend_color, size=13)
            ),
            font=dict(family="Merriweather, serif", size=13, color=axis_color),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Merriweather, serif",
                font_color="#333333"
            ),
            # Add watermark
            annotations=[
                dict(
                    text="TECTONIQ.APP (Beta)",
                    xref="paper", yref="paper",
                    x=0.98, y=0.02,
                    xanchor="right", yanchor="bottom",
                    font=dict(size=9, color="#95A5A6", family="Merriweather, serif"),
                    showarrow=False,
                    opacity=0.5
                )
            ]
        )
        fig.update_xaxes(
            title_text="Date",
            title_font=dict(family="Merriweather, serif", color=axis_color, size=14),
            tickfont=dict(family="Merriweather, serif", color=axis_color, size=12),
            gridcolor=grid_color,
            gridwidth=0.5,
            griddash='dot'
        )
        fig.update_yaxes(
            title_text="Portfolio Value (€)",
            title_font=dict(family="Merriweather, serif", color=axis_color, size=14),
            tickfont=dict(family="Merriweather, serif", color=axis_color, size=12),
            gridcolor=grid_color,
            gridwidth=0.5,
            griddash='dot',
            zerolinecolor='#BDC3C7',
            zerolinewidth=0.8
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # === DRAWDOWN COMPARISON (3 areas) ===
    daily_def = results_def.get('daily_data', pd.DataFrame())
    daily_agg = results_agg.get('daily_data', pd.DataFrame())
    
    if not daily_def.empty and 'buyhold_drawdown' in daily_def.columns:
        st.markdown("#### Drawdown Comparison")
        
        # Heritage colors for drawdown chart
        legend_color_dd = '#333333'
        
        fig_dd = go.Figure()
        
        # Buy & Hold - Terracotta tones (earth red)
        fig_dd.add_trace(go.Scatter(
            x=daily_def.index,
            y=daily_def['buyhold_drawdown'],
            name='Buy & Hold',
            fill='tozeroy',
            line=dict(color='rgba(192,57,43,0.8)', width=1.2),  # #C0392B with opacity
            fillcolor='rgba(192,57,43,0.2)'
        ))
        
        # Defensive - Midnight Blue
        fig_dd.add_trace(go.Scatter(
            x=daily_def.index,
            y=daily_def['soc_drawdown'],
            name='Defensive',
            fill='tozeroy',
            line=dict(color='rgba(44,62,80,0.8)', width=1.2),  # #2C3E50 with opacity
            fillcolor='rgba(44,62,80,0.2)'
        ))
        
        # Aggressive - Ochre/Pumpkin
        if not daily_agg.empty and 'soc_drawdown' in daily_agg.columns:
            fig_dd.add_trace(go.Scatter(
                x=daily_agg.index,
                y=daily_agg['soc_drawdown'],
                name='Aggressive',
                fill='tozeroy',
                line=dict(color='rgba(211,84,0,0.8)', width=1.2),  # #D35400 with opacity
                fillcolor='rgba(211,84,0,0.2)'
            ))
        
        # Scientific Journal style for drawdown
        axis_color_dd = '#333333'
        grid_color_dd = '#E6E1D3'
        
        fig_dd.update_layout(
            template="plotly_white",
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent
            plot_bgcolor='rgba(0,0,0,0)',    # Transparent
            height=280,
            margin=dict(t=20, b=50, l=60, r=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(family="Merriweather, serif", color=legend_color_dd, size=13)
            ),
            font=dict(family="Merriweather, serif", size=13, color=axis_color_dd),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Merriweather, serif",
                font_color="#333333"
            ),
            # Add watermark
            annotations=[
                dict(
                    text="TECTONIQ.APP (Beta)",
                    xref="paper", yref="paper",
                    x=0.98, y=0.02,
                    xanchor="right", yanchor="bottom",
                    font=dict(size=9, color="#95A5A6", family="Merriweather, serif"),
                    showarrow=False,
                    opacity=0.5
                )
            ]
        )
        fig_dd.update_xaxes(
            title_text="Date",
            title_font=dict(family="Merriweather, serif", color=axis_color_dd, size=14),
            tickfont=dict(family="Merriweather, serif", color=axis_color_dd, size=12),
            gridcolor=grid_color_dd,
            gridwidth=0.5,
            griddash='dot'
        )
        fig_dd.update_yaxes(
            title_text="Drawdown (%)",
            title_font=dict(family="Merriweather, serif", color=axis_color_dd, size=14),
            tickfont=dict(family="Merriweather, serif", color=axis_color_dd, size=12),
            gridcolor=grid_color_dd,
            gridwidth=0.5,
            griddash='dot',
            zerolinecolor='#BDC3C7',
            zerolinewidth=0.8
        )
        
        st.plotly_chart(fig_dd, use_container_width=True)
    
    # === MODEL AUDIT & STRESS TEST ===
    st.markdown("---")
    st.markdown("#### Strategy Audit & Stress Test")
    
    # Calculate audit metrics for both strategies
    audit_def = calculate_audit_metrics(daily_def, strategy_mode="defensive") if not daily_def.empty else None
    audit_agg = calculate_audit_metrics(daily_agg, strategy_mode="aggressive") if not daily_agg.empty else None
    
    if audit_def and 'error' not in audit_def:
        crash_stats_def = audit_def.get('crash_stats', {})
        protection_def = audit_def.get('protection_stats', {})
        big_short_def = audit_def.get('big_short', {})
        false_alarms_def = audit_def.get('false_alarms', {})
        
        crash_stats_agg = audit_agg.get('crash_stats', {}) if audit_agg else {}
        protection_agg = audit_agg.get('protection_stats', {}) if audit_agg else {}
        big_short_agg = audit_agg.get('big_short', {}) if audit_agg else {}
        false_alarms_agg = audit_agg.get('false_alarms', {}) if audit_agg else {}
        
        # === AUDIT COMPARISON TABLE ===
        st.markdown("##### Crash Detection & Protection Overview")
        
        # Extract metrics for both strategies
        def_crash_count = crash_stats_def.get('crash_count', 0)
        def_days_defensive = crash_stats_def.get('total_defensive_days', 0)
        def_pct_defensive = crash_stats_def.get('pct_time_defensive', 0)
        def_protection_eff = protection_def.get('protection_efficiency', 0)
        def_protection_delta = protection_def.get('protection_delta', 0)
        def_true_alerts = false_alarms_def.get('true_alerts', 0)
        def_false_alarms = false_alarms_def.get('false_alarms', 0)
        def_accuracy = false_alarms_def.get('true_alert_rate', 0)
        def_insurance_cost = false_alarms_def.get('insurance_cost_pct', 0)
        
        agg_crash_count = crash_stats_agg.get('crash_count', 0)
        agg_days_defensive = crash_stats_agg.get('total_defensive_days', 0)
        agg_pct_defensive = crash_stats_agg.get('pct_time_defensive', 0)
        agg_protection_eff = protection_agg.get('protection_efficiency', 0)
        agg_protection_delta = protection_agg.get('protection_delta', 0)
        agg_true_alerts = false_alarms_agg.get('true_alerts', 0)
        agg_false_alarms = false_alarms_agg.get('false_alarms', 0)
        agg_accuracy = false_alarms_agg.get('true_alert_rate', 0)
        agg_insurance_cost = false_alarms_agg.get('insurance_cost_pct', 0)
        
        # Build comparison table HTML
        audit_table = '<table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">'
        audit_table += '<thead><tr style="background: rgba(102, 126, 234, 0.3); border-bottom: 2px solid #667eea;"><th style="padding: 12px 10px; text-align: left; font-weight: 700;">Metric</th><th style="padding: 12px 10px; text-align: center; font-weight: 700;">Defensive</th><th style="padding: 12px 10px; text-align: center; font-weight: 700;">Aggressive</th></tr></thead>'
        audit_table += '<tbody>'
        
        # Crash Phases Detected
        audit_table += f'<tr><td style="padding: 10px; border-bottom: 1px solid #444;">Crash Phases Detected</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{def_crash_count}</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{agg_crash_count}</td></tr>'
        
        # Days in Defense
        audit_table += f'<tr><td style="padding: 10px; border-bottom: 1px solid #444;">Days in Defense</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{def_days_defensive} ({def_pct_defensive:.1f}%)</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{agg_days_defensive} ({agg_pct_defensive:.1f}%)</td></tr>'
        
        # Protection Efficiency (highlight row)
        audit_table += f'<tr style="background: rgba(102, 126, 234, 0.15);"><td style="padding: 10px; border-bottom: 1px solid #444;"><b>Protection Efficiency</b></td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;"><b>{def_protection_eff:.0f}%</b></td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;"><b>{agg_protection_eff:.0f}%</b></td></tr>'
        
        # Protection Delta
        audit_table += f'<tr><td style="padding: 10px; border-bottom: 1px solid #444;">Protection Delta vs B&H</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{def_protection_delta:+.1f}%</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{agg_protection_delta:+.1f}%</td></tr>'
        
        # True Alerts
        audit_table += f'<tr><td style="padding: 10px; border-bottom: 1px solid #444;">True Alerts (Justified)</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{def_true_alerts}</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{agg_true_alerts}</td></tr>'
        
        # False Alarms
        audit_table += f'<tr><td style="padding: 10px; border-bottom: 1px solid #444;">False Alarms</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{def_false_alarms}</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{agg_false_alarms}</td></tr>'
        
        # Signal Accuracy (highlight row)
        audit_table += f'<tr style="background: rgba(102, 126, 234, 0.15);"><td style="padding: 10px; border-bottom: 1px solid #444;"><b>Signal Accuracy</b></td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;"><b>{def_accuracy:.0f}%</b></td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;"><b>{agg_accuracy:.0f}%</b></td></tr>'
        
        # Insurance Cost
        audit_table += f'<tr><td style="padding: 10px; border-bottom: 1px solid #444;">Insurance Cost (Opportunity)</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{def_insurance_cost:+.1f}%</td><td style="padding: 10px; text-align: center; border-bottom: 1px solid #444;">{agg_insurance_cost:+.1f}%</td></tr>'
        
        audit_table += '</tbody></table>'
        
        st.markdown(audit_table, unsafe_allow_html=True)
        
        # Key insights
        col_ins1, col_ins2 = st.columns(2)
        with col_ins1:
            better_protection = "Defensive" if def_protection_eff >= agg_protection_eff else "Aggressive"
            st.success(f"**Best Protection:** {better_protection} ({max(def_protection_eff, agg_protection_eff):.0f}%)")
        with col_ins2:
            better_accuracy = "Defensive" if def_accuracy >= agg_accuracy else "Aggressive"
            st.info(f"**Best Accuracy:** {better_accuracy} ({max(def_accuracy, agg_accuracy):.0f}%)")
        
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        # === THE BIG SHORT CHECK (Side by Side) ===
        st.markdown("##### The Big Short Check (Top 5 Historical Crashes)")
        
        big_short_events_def = big_short_def.get('events', [])
        big_short_events_agg = big_short_agg.get('events', [])
        
        if big_short_events_def:
            # Build comparison table showing how each strategy responded
            crash_rows_list = []
            
            # Create a map of aggressive events by date for matching
            agg_events_map = {e.get('date'): e for e in big_short_events_agg}
            
            for event_def in big_short_events_def:
                date = event_def.get('date', 'N/A')
                dd = event_def.get('drawdown', 0)
                
                # Defensive status
                def_emoji = event_def.get('emoji', '❓')
                def_prior = event_def.get('prior_exposure', 0)
                def_trough = event_def.get('trough_exposure', 0)
                
                # Aggressive status (match by date)
                event_agg = agg_events_map.get(date, {})
                agg_emoji = event_agg.get('emoji', '❓') if event_agg else '❓'
                agg_prior = event_agg.get('prior_exposure', 0) if event_agg else 0
                agg_trough = event_agg.get('trough_exposure', 0) if event_agg else 0
                
                # Color code row based on defensive status
                status = event_def.get('status', '')
                if status == 'protected':
                    bg_color = 'rgba(0, 200, 100, 0.1)'
                elif status == 'late':
                    bg_color = 'rgba(255, 165, 0, 0.1)'
                else:
                    bg_color = 'rgba(255, 80, 80, 0.1)'
                
                row_html = f'<tr style="background: {bg_color};"><td style="padding: 8px;">{date}</td><td style="padding: 8px; text-align: center;"><b>{dd:.1f}%</b></td><td style="padding: 8px; text-align: center; font-size: 1.1rem;">{def_emoji}</td><td style="padding: 8px; text-align: center;">{def_prior:.0f}% → {def_trough:.0f}%</td><td style="padding: 8px; text-align: center; font-size: 1.1rem;">{agg_emoji}</td><td style="padding: 8px; text-align: center;">{agg_prior:.0f}% → {agg_trough:.0f}%</td></tr>'
                crash_rows_list.append(row_html)
            
            crash_rows = "".join(crash_rows_list)
            
            crash_table = '<table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;"><thead><tr style="background: rgba(102, 126, 234, 0.2); border-bottom: 2px solid #667eea;"><th style="padding: 10px;">Date</th><th style="padding: 10px; text-align: center;">Drawdown</th><th style="padding: 10px; text-align: center;">Def. Status</th><th style="padding: 10px; text-align: center;">Def. Exposure</th><th style="padding: 10px; text-align: center;">Agg. Status</th><th style="padding: 10px; text-align: center;">Agg. Exposure</th></tr></thead><tbody>' + crash_rows + '</tbody></table>'
            
            st.markdown(crash_table, unsafe_allow_html=True)
            
            # Summary for both
            def_protected = big_short_def.get('protected_count', 0)
            def_late = big_short_def.get('late_count', 0)
            def_missed = big_short_def.get('missed_count', 0)
            
            agg_protected = big_short_agg.get('protected_count', 0)
            agg_late = big_short_agg.get('late_count', 0)
            agg_missed = big_short_agg.get('missed_count', 0)
            
            total_events = len(big_short_events_def)
            
            summary_html = f'<div style="margin-top: 0.5rem; font-size: 0.9rem;"><b>Defensive:</b> ✅ {def_protected}/{total_events} | ⚠️ {def_late}/{total_events} | ❌ {def_missed}/{total_events} &nbsp;&nbsp;&nbsp; <b>Aggressive:</b> ✅ {agg_protected}/{total_events} | ⚠️ {agg_late}/{total_events} | ❌ {agg_missed}/{total_events}</div>'
            st.markdown(summary_html, unsafe_allow_html=True)
            
            # Legend
            legend_html = '<div style="margin-top: 0.5rem; font-size: 0.8rem; color: #888;">✅ Protected = Defensive before crash | ⚠️ Late = Switched during crash | ❌ Missed = Stayed invested</div>'
            st.markdown(legend_html, unsafe_allow_html=True)
        else:
            st.info("No significant crash events detected in this period.")
    
    else:
        st.warning("Could not calculate audit metrics. Insufficient data.")

