"""
SOC Market Seismograph - Detail Panel UI Components
===================================================

Deep dive analysis UI components for individual asset analysis.

Contains:
- render_regime_persistence_chart(): Horizontal bar chart showing regime duration
- render_current_regime_outlook(): Historical performance metrics for current regime
- render_detail_panel(): Main detailed analysis panel with charts and metrics

Author: Market Analysis Team
Version: 7.0 (Modularized)
"""

from typing import Dict, Any

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from logic import DataFetcher, SOCAnalyzer
from auth_manager import add_asset_to_portfolio, remove_asset_from_portfolio, get_current_user_id, get_user_portfolio


def render_regime_persistence_chart(current_regime: str, current_duration: int, regime_stats: Dict[str, Any], is_dark: bool = False) -> None:
    """
    Render a horizontal bar chart showing current regime duration vs historical average.
    
    Args:
        current_regime: Name of current regime (e.g., 'STABLE')
        current_duration: Days in current regime
        regime_stats: Historical statistics for this regime
        is_dark: Dark mode flag
    """
    # Get historical stats (using correct keys from logic.py)
    mean_duration = regime_stats.get('avg_duration', 0)  # avg_duration, not mean_duration
    median_duration = regime_stats.get('median_duration', 0)
    max_duration = regime_stats.get('max_duration', 0)
    p95_duration = regime_stats.get('p95_duration', 0)
    
    # Regime colors
    regime_colors = {
        'STABLE': '#00C864',
        'ACTIVE': '#FFCC00',
        'HIGH_ENERGY': '#FF6600',
        'CRITICAL': '#FF4040',
        'DORMANT': '#888888'
    }
    
    regime_color = regime_colors.get(current_regime, '#667eea')
    
    # Handle edge cases
    if max_duration == 0:
        max_duration = max(current_duration * 2, 30)  # Fallback
    if mean_duration == 0:
        mean_duration = current_duration  # Use current as reference
    
    # Theme-aware colors
    text_color = '#FFFFFF' if is_dark else '#1a1a1a'
    axis_color = '#CCCCCC' if is_dark else '#333333'
    grid_color = '#444444' if is_dark else '#E0E0E0'
    bg_color = 'rgba(0,0,0,0)' if is_dark else 'rgba(248,248,248,1)'
    annotation_color = '#FFFFFF' if is_dark else '#333333'
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    # Background range (0 to max)
    fig.add_trace(go.Bar(
        y=['Duration'],
        x=[max_duration],
        orientation='h',
        marker=dict(color='rgba(200,200,200,0.3)' if is_dark else 'rgba(200,200,200,0.5)'),
        name='Max Observed',
        showlegend=False
    ))
    
    # Current duration bar
    fig.add_trace(go.Bar(
        y=['Duration'],
        x=[current_duration],
        orientation='h',
        marker=dict(color=regime_color),
        name='Current',
        showlegend=False
    ))
    
    # Add vertical lines for mean and P95
    fig.add_vline(x=mean_duration, line_dash="dash", line_color="#667eea", line_width=3,
                  annotation_text=f"Avg: {mean_duration:.0f}d", annotation_position="top",
                  annotation=dict(font=dict(color=annotation_color, size=13)))
    
    if p95_duration > 0:
        fig.add_vline(x=p95_duration, line_dash="dot", line_color="#FF6600", line_width=3,
                      annotation_text=f"95th: {p95_duration:.0f}d", annotation_position="bottom",
                      annotation=dict(font=dict(color=annotation_color, size=13)))
    
    # Update layout with explicit colors
    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        paper_bgcolor='rgba(0,0,0,0)' if is_dark else 'rgba(255,255,255,0)',
        plot_bgcolor=bg_color,
        height=180,
        margin=dict(l=80, r=30, t=50, b=50),
        showlegend=False,
        font=dict(color=text_color, size=13)
    )
    
    # Update axes separately (correct Plotly API)
    fig.update_xaxes(
        range=[0, max_duration * 1.1],
        title_text="Days",
        title_font=dict(color=axis_color, size=14),
        tickfont=dict(color=axis_color, size=12),
        gridcolor=grid_color
    )
    
    fig.update_yaxes(
        title_text="",
        tickfont=dict(color=axis_color, size=12)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Interpretation
    if current_duration > p95_duration:
        interpretation = f"⚠️ **Statistical Anomaly:** This regime has lasted {current_duration} days, which is unusually long (above 95th percentile of {p95_duration:.0f} days). Mean reversion probability is elevated."
        st.warning(interpretation)
    elif current_duration > mean_duration:
        interpretation = f"📊 This regime has lasted {current_duration} days, which is **above** the historical average of {mean_duration:.0f} days. Median duration: {median_duration:.0f} days."
        st.info(interpretation)
    else:
        interpretation = f"📊 This regime is still relatively young at {current_duration} days, **below** the historical average of {mean_duration:.0f} days. Median duration: {median_duration:.0f} days."
        st.info(interpretation)


def render_current_regime_outlook(current_regime: str, regime_data: Dict[str, Any]) -> None:
    """
    Render a table showing the historical outlook for the CURRENT regime only.
    
    Args:
        current_regime: Name of current regime
        regime_data: Statistical data for this regime
    """
    regime_display = current_regime.replace('_', ' ').title()
    regime_emojis = {'STABLE': '🟢', 'ACTIVE': '🟡', 'HIGH_ENERGY': '🟠', 'CRITICAL': '🔴', 'DORMANT': '⚪'}
    emoji = regime_emojis.get(current_regime, '📊')
    
    st.markdown(f"##### 🎯 Historical Outlook: {emoji} {regime_display} Regime")
    st.caption("📊 **How to read this:** Shows average price movements following the start of this regime in the past. Use this to understand typical behavior patterns for the current market state.")
    
    # Check if we have data
    phase_count = regime_data.get('phase_count', 0)
    if phase_count == 0:
        st.info("No historical data available for this regime.")
        return
    
    st.markdown(f"*Based on **{phase_count}** historical occurrences of this regime*")
    
    # Build outlook table using available data
    ret_10d = regime_data.get('start_return_10d', 0)
    ret_30d = regime_data.get('avg_return_30d', 0)
    ret_90d = regime_data.get('avg_return_90d', 0)
    dd_10d = regime_data.get('worst_max_dd_10d', 0)
    avg_price_change = regime_data.get('avg_price_change_during', 0)
    
    # Create metrics in columns for better display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("10-Day Avg Return", f"{ret_10d:+.1f}%")
    with col2:
        st.metric("30-Day Avg Return", f"{ret_30d:+.1f}%")
    with col3:
        st.metric("90-Day Avg Return", f"{ret_90d:+.1f}%")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("Avg During Phase", f"{avg_price_change:+.1f}%")
    with col5:
        st.metric("Worst 10d Drawdown", f"{dd_10d:.1f}%" if dd_10d != 0 else "N/A")
    with col6:
        st.metric("Phase Count", f"{phase_count}")
    
    # Add interpretation
    if ret_30d > 5:
        st.success(f"📈 Historically, this regime has shown **positive momentum** with an average 30-day return of {ret_30d:+.1f}%.")
    elif ret_30d < -5:
        st.error(f"📉 Historically, this regime has shown **negative momentum** with an average 30-day return of {ret_30d:+.1f}%.")
    elif ret_30d != 0:
        st.info(f"📊 Historically, this regime has shown **neutral momentum** with an average 30-day return of {ret_30d:+.1f}%.")
    else:
        st.info("📊 Insufficient historical data for return analysis.")


def render_detail_panel(result: Dict[str, Any], get_signal_color_func, get_signal_bg_func) -> None:
    """
    Render detailed analysis panel for a selected asset.
    
    Displays: Header with regime badge, key metrics (price, criticality,
    vol percentile, trend), SOC chart, and VISUAL analysis with:
    - Regime Persistence Visualizer (bar chart)
    - Current Regime Outlook (focused table)
    - Historical data in expander with donut chart
    
    Args:
        result: Dictionary containing asset analysis results
        get_signal_color_func: Function to get signal color
        get_signal_bg_func: Function to get signal background color
    """
    is_dark = st.session_state.get('dark_mode', True)
    symbol = result['symbol']
    signal = result['signal']
    color = get_signal_color_func(signal)
    bg = get_signal_bg_func(signal)
    
    # Active asset card and any portfolio actions are handled in the main app layout
    
    # Explanation of Regime
    st.markdown("""
    <div style="background: rgba(102, 126, 234, 0.1); border-left: 3px solid #667eea; padding: 12px; margin: 12px 0; border-radius: 4px;">
        <strong>📖 What is a "Regime"?</strong><br>
        <span style="font-size: 0.9rem; opacity: 0.9;">
        A <strong>regime</strong> is the asset's current statistical behavior pattern based on price volatility and trend direction. 
        Think of it as the market's "mood" for this asset: <span style="color: #00C864;">🟢 Stable</span> (low volatility, clear trend), 
        <span style="color: #FFB800;">🟡 Transitioning</span> (moderate volatility, changing direction), or 
        <span style="color: #FF4040;">🔴 Volatile</span> (high volatility, unclear direction).
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics row - including new Criticality Score
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Price", f"${result['price']:,.2f}")
    col2.metric("Criticality", f"{result.get('criticality_score', 0)}/100")
    col3.metric("Vol %ile", f"{result.get('vol_percentile', 50):.0f}th")
    col4.metric("Trend", result['trend'])
    
    # Chart
    fetcher = DataFetcher(cache_enabled=True)
    df = fetcher.fetch_data(symbol)
    
    if not df.empty:
        analyzer = SOCAnalyzer(df, symbol, result.get('info'))
        figs = analyzer.get_plotly_figures(dark_mode=is_dark)
        st.plotly_chart(figs['chart3'], width="stretch")
        
        # Historical Signal Analysis
        with st.spinner("🔍 Analyzing historical regime patterns... Mapping stress accumulation trajectories..."):
            analysis = analyzer.get_historical_signal_analysis()
        
        if 'error' in analysis:
            st.warning(analysis['error'])
        else:
                # === INSTABILITY SCORE (Compliance-safe) ===
                stress_data = analysis.get('crash_warning', {})
                if stress_data:
                    score = stress_data.get('score', 0)
                    level = stress_data.get('level', 'BASELINE')
                    level_color = stress_data.get('level_color', '#00CC00')
                    level_emoji = stress_data.get('level_emoji', '📊')
                    interpretation = stress_data.get('interpretation', '')
                    statistical_factors = stress_data.get('risk_factors', [])
                    
                    # Determine background color based on level
                    if level == "ELEVATED":
                        bg_color = "rgba(255, 0, 0, 0.15)"
                        border_color = "#FF0000"
                    elif level == "HEIGHTENED":
                        bg_color = "rgba(255, 102, 0, 0.15)"
                        border_color = "#FF6600"
                    elif level == "MODERATE":
                        bg_color = "rgba(255, 204, 0, 0.15)"
                        border_color = "#FFCC00"
                    else:
                        bg_color = "rgba(0, 204, 0, 0.1)"
                        border_color = "#00CC00"
                    
                    # Build statistical factors HTML
                    factors_html = ""
                    if statistical_factors:
                        factors_html = "<div style='margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.2);'>"
                        factors_html += "<strong>Statistical Indicators:</strong><ul style='margin: 8px 0 0 0; padding-left: 20px;'>"
                        for factor in statistical_factors:
                            factors_html += f"<li style='margin: 4px 0;'>{factor}</li>"
                        factors_html += "</ul></div>"
                    
                    st.markdown(f"""
                    <div style="
                        background: {bg_color};
                        border: 2px solid {border_color};
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 24px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <div style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; margin-bottom: 4px;">
                                    📊 Instability Score
                                </div>
                                <div style="font-size: 42px; font-weight: bold; color: {level_color};">
                                    {score}<span style="font-size: 20px; opacity: 0.7;">/100</span>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="
                                    background: {level_color};
                                    color: {'#000' if level in ['BASELINE', 'MODERATE'] else '#FFF'};
                                    padding: 8px 16px;
                                    border-radius: 20px;
                                    font-weight: bold;
                                    font-size: 14px;
                                ">
                                    {level_emoji} {level}
                                </div>
                            </div>
                        </div>
                        <div style="margin-top: 12px; font-size: 14px; opacity: 0.9;">
                            {interpretation}
                        </div>
                        {factors_html}
                        <div style="margin-top: 12px; font-size: 10px; opacity: 0.6; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                            ⚠️ Purely statistical analysis. Past performance is not indicative of future results.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Explanation of relationship between Regime and Stress Level
                    st.markdown("""
                    <div style="background: rgba(102, 126, 234, 0.1); border-left: 3px solid #667eea; padding: 12px; margin: 12px 0; border-radius: 4px;">
                        <strong>🎯 Regime vs. Instability Score – What's the Difference?</strong><br>
                        <span style="font-size: 0.9rem; opacity: 0.9;">
                        • <strong>Regime</strong> (shown at top) = This asset's individual price behavior pattern<br>
                        • <strong>Instability Score</strong> (shown above) = Overall market-wide risk across volatility, correlations, and trends<br><br>
                        <strong>Why can they differ?</strong> An asset can be in a 🟢 Stable regime (behaving normally) while the broader market shows 🟠 Heightened instability (system-wide risk). 
                        The asset might be insulated now, but elevated instability suggests potential future spillover risk.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Get current regime from analysis
                stats = analysis['signal_stats']
                current_regime_key = analysis.get('current_signal', 'STABLE')  # From historical analysis
                current_regime_data = stats.get(current_regime_key, {})
                current_duration = analysis.get('current_streak_days', 0)  # Days in current regime
                
                st.markdown("---")
                
                # === SECTION A: REGIME PERSISTENCE VISUALIZER ===
                st.markdown("#### ⏱️ Regime Persistence Analysis")
                st.caption("📊 **How to read this:** The colored bar shows how long the asset has been in the current regime. The dashed line shows the historical average duration. If the bar extends beyond the 95th percentile line, the regime may be nearing exhaustion.")
                render_regime_persistence_chart(current_regime_key, current_duration, current_regime_data, is_dark)
                
                st.markdown("---")
                
                # === SECTION B: CURRENT REGIME OUTLOOK ===
                render_current_regime_outlook(current_regime_key, current_regime_data)
                
                st.markdown("---")
                
                # === SECTION C: FULL HISTORICAL DATA (EXPANDER) ===
                with st.expander("View All Historical Regime Data", expanded=False):
                    # Regime Distribution Donut Chart
                    st.markdown("##### Historical Regime Distribution")
                    
                    signal_order = ['STABLE', 'ACTIVE', 'HIGH_ENERGY', 'CRITICAL', 'DORMANT']
                    signal_names = {
                        'STABLE': 'Stable', 'ACTIVE': 'Active', 
                        'HIGH_ENERGY': 'High Energy', 'CRITICAL': 'Critical', 'DORMANT': 'Dormant'
                    }
                    signal_emojis = {'STABLE': '🟢', 'ACTIVE': '🟡', 'HIGH_ENERGY': '🟠', 'CRITICAL': '🔴', 'DORMANT': '⚪'}
                    signal_colors_map = {
                        'STABLE': '#00C864', 'ACTIVE': '#FFCC00', 
                        'HIGH_ENERGY': '#FF6600', 'CRITICAL': '#FF4040', 'DORMANT': '#888888'
                    }
                    
                    # Build donut chart data
                    labels = []
                    values = []
                    colors = []
                    
                    for sig in signal_order:
                        data = stats.get(sig, {})
                        pct = data.get('pct_of_time', 0)
                        if pct > 0:
                            emoji = signal_emojis.get(sig, '')
                            name = signal_names.get(sig, sig)
                            labels.append(f"{emoji} {name}")
                            values.append(pct)
                            colors.append(signal_colors_map.get(sig, '#888888'))
                    
                    # Create donut chart
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.4,
                        marker=dict(colors=colors),
                        textinfo='label+percent',
                        textposition='outside'
                    )])
                    
                    bg_color_chart = 'rgba(0,0,0,0)' if is_dark else 'rgba(255,255,255,0)'
                    text_color_chart = '#FFFFFF' if is_dark else '#333333'
                    
                    fig_donut.update_layout(
                        template="plotly_dark" if is_dark else "plotly_white",
                        paper_bgcolor=bg_color_chart,
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        showlegend=True,
                        legend=dict(font=dict(color=text_color_chart)),
                        font=dict(color=text_color_chart)
                    )
                    
                    st.plotly_chart(fig_donut, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # Full Returns Table (All Regimes)
                    st.markdown("##### Complete Historical Returns by Regime")
                    st.caption("Statistical analysis of price movements following each regime classification")
                    
                    forward_rows = []
                    for sig in signal_order:
                        data = stats.get(sig, {})
                        phase_count = data.get('phase_count', 0)
                        if phase_count > 0:
                            emoji = signal_emojis[sig]
                            forward_rows.append({
                                'Regime': f"{emoji} {signal_names[sig]}",
                                'Periods': str(phase_count),
                                '10d': f"{data.get('start_return_10d', 0):+.1f}%",
                                '30d': f"{data.get('avg_return_30d', 0):+.1f}%",
                                '90d': f"{data.get('avg_return_90d', 0):+.1f}%",
                                'Max DD (10d)': f"{data.get('worst_max_dd_10d', 0):.1f}%"
                            })
                    
                    if forward_rows:
                        st.table(pd.DataFrame(forward_rows))
                    else:
                        st.info("No historical regime data available.")
                    
                    st.markdown("---")
                    
                    # Pre-Regime Conditions Table
                    st.markdown("##### Pre-Regime Market Conditions")
                    st.caption("Historical price movements BEFORE each regime was classified")
                    
                    prior_rows = []
                    for sig in signal_order:
                        data = stats.get(sig, {})
                        phase_count = data.get('phase_count', 0)
                        if phase_count > 0:
                            emoji = signal_emojis[sig]
                            prior_rows.append({
                                'Regime': f"{emoji} {signal_names[sig]}",
                                'Prior 5d': f"{data.get('prior_5d', 0):+.1f}%",
                                'Prior 10d': f"{data.get('prior_10d', 0):+.1f}%",
                                'Prior 30d': f"{data.get('prior_30d', 0):+.1f}%"
                            })
                    
                    if prior_rows:
                        st.table(pd.DataFrame(prior_rows))
                    else:
                        st.info("No historical regime data available.")

