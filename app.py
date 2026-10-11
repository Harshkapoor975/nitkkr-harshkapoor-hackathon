import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Ensure project root imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from store.db import load_signals, load_latest_weights
    from config import TICKERS, EVENT_TYPES
    from scripts.rebalancer import TacticalRebalancer, MOCK_INDEX_UNIVERSE, run_tactical_rebalance
except ImportError:
    from src.store.db import load_signals, load_latest_weights
    from src.config import TICKERS, EVENT_TYPES
    from src.rebalancer import TacticalRebalancer, MOCK_INDEX_UNIVERSE, run_tactical_rebalance

# -----------------------------------------------------------------------------
# Page Configuration & Theming
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="S&P AI Risk Engine & Tactical Rebalancer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Institutional Polish
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-size: 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("🏛️ S&P Global AI Risk Engine & Tactical Rebalancer")
st.caption("Campus Hackathon 2026 Deliverable | Core NLP Risk Intelligence Engine + Module A: Tactical Index Rebalancing")

# -----------------------------------------------------------------------------
# Data Loading & Caching
# -----------------------------------------------------------------------------
@st.cache_data(ttl=15)
def fetch_data():
    signals = load_signals()
    df = pd.DataFrame(signals)
    if not df.empty:
        df['dt'] = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce', utc=True)
        df = df.dropna(subset=['dt']).sort_values(by='dt', ascending=False)
    return df

df_signals = fetch_data()

# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
st.sidebar.header("⚙️ Rebalancer Controls")
alpha_param = st.sidebar.slider(
    "Sentiment Sensitivity (α)",
    min_value=0.1,
    max_value=2.0,
    value=0.75,
    step=0.05,
    help="Higher alpha tilts portfolio weights more aggressively in response to sentiment."
)

max_weight_param = st.sidebar.slider(
    "Max Single-Asset Cap (%)",
    min_value=15,
    max_value=35,
    value=25,
    step=1,
    help="Institutional concentration constraint (e.g. UCITS 25% single stock cap)."
) / 100.0

half_life_param = st.sidebar.slider(
    "Signal Half-Life (Hours)",
    min_value=6,
    max_value=120,
    value=48,
    step=6,
    help="Exponential decay rate. Older signals gradually lose impact."
)

rebalance_btn = st.sidebar.button("⚡ Run Tactical Rebalance Now", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Live Multi-Source Ingestion")

# 1. Background Autonomous Crawler Toggle
bg_crawler_enabled = st.sidebar.toggle(
    "🟢 Background Autonomous Crawler", 
    value=True, 
    help="Autonomous background thread continuously scanning RSS feeds and Yahoo Finance."
)
if bg_crawler_enabled:
    try:
        from src.crawlers.daemon import GLOBAL_DAEMON
        if not GLOBAL_DAEMON.is_running:
            GLOBAL_DAEMON.start_background()
    except Exception as e:
        pass

# 2. On-Demand Live Scrape & Rebalance Trigger
if st.sidebar.button("🕷️ Crawl Live News & Scrape Now", use_container_width=True):
    with st.spinner("🌐 Crawling RSS feeds & Yahoo Finance..."):
        try:
            from src.crawlers.daemon import GLOBAL_DAEMON
            res = GLOBAL_DAEMON.single_crawl_cycle()
            st.toast(f"✅ Ingested {res['total_new']} signals & updated rebalancing!", icon="🚀")
            st.rerun()
        except Exception as e:
            st.error(f"Error crawling live intelligence: {e}")

# 3. Live Auto-Refresh Streaming Mode
auto_refresh = st.sidebar.checkbox(
    "🔄 Live Streaming Auto-Refresh (15s)", 
    value=False, 
    help="Periodically refreshes the dashboard so dynamic background signals update live."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Database Intelligence Status")
total_signals = len(df_signals)
st.sidebar.metric("Total Ingested Signals", total_signals)
if not df_signals.empty:
    latest_time = df_signals['dt'].max().strftime('%b %d, %H:%M UTC')
    st.sidebar.info(f"Latest Signal: **{latest_time}**")

# -----------------------------------------------------------------------------
# Execute Rebalancing Engine
# -----------------------------------------------------------------------------
rebalancer = TacticalRebalancer(
    universe=MOCK_INDEX_UNIVERSE,
    alpha=alpha_param,
    half_life_hours=half_life_param,
    min_weight=0.02,
    max_weight=max_weight_param
)

if df_signals.empty:
    st.warning("⚠️ No signals found in database. Run `python scripts/custom_nlp_engine.py` or `python scripts/live_risk_daemon.py` to ingest news.")
    st.stop()

# Compute live allocation
sentiments = rebalancer.compute_smoothed_sentiments(df_signals)
weights_df = rebalancer.rebalance(sentiments)
history_df = rebalancer.compute_historical_weight_trajectory(df_signals, num_steps=20)
perf_df = rebalancer.simulate_performance(history_df)

# -----------------------------------------------------------------------------
# Main Navigation Tabs
# -----------------------------------------------------------------------------
tab_module_a, tab_risk_engine, tab_ticker_drill = st.tabs([
    "⚖️ Module A: Tactical Index Rebalancer",
    "🧠 AI/NLP Risk Engine (Live Firehose)",
    "🔬 Single-Asset Deep Dive"
])

# =============================================================================
# TAB 1: MODULE A - TACTICAL INDEX REBALANCING (PRIMARY DELIVERABLE)
# =============================================================================
with tab_module_a:
    st.markdown("### 📊 Dynamic Mock Index Rebalancer (S&P 100 Universe)")
    st.markdown(
        "Subscribes to real-time sentiment scores from the AI Risk Engine and tactically tilts "
        "stock allocations away from the **Equal-Weighted Benchmark (10.0%)** toward high-conviction positive sentiment assets."
    )

    # Top KPI Metrics
    latest_perf = perf_df.iloc[-1] if not perf_df.empty else None
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    portfolio_val = latest_perf['Tactical_Portfolio'] if latest_perf is not None else 100000.0
    benchmark_val = latest_perf['Equal_Weight_Benchmark'] if latest_perf is not None else 100000.0
    alpha_pct = latest_perf['Alpha_Pct'] if latest_perf is not None else 0.0

    col_kpi1.metric(
        "Tactical Portfolio Value",
        f"${portfolio_val:,.2f}",
        delta=f"{alpha_pct:+.2f}% Alpha",
        delta_color="normal"
    )
    col_kpi2.metric(
        "Equal-Weight Benchmark",
        f"${benchmark_val:,.2f}",
        help="Passive 10% Equal-Weight allocation across 10 stocks."
    )
    active_share = (weights_df['active_tilt_pct'].abs().sum() / 2.0)
    col_kpi3.metric(
        "Active Share",
        f"{active_share:.1f}%",
        help="Percentage of the portfolio that differs from the passive benchmark."
    )
    top_winner = weights_df.iloc[0]
    col_kpi4.metric(
        "Top Overweight Asset",
        f"{top_winner['ticker']} ({top_winner['weight_pct']:.1f}%)",
        delta=f"{top_winner['active_tilt_pct']:+.1f}% vs Bench"
    )

    st.markdown("---")

    # Chart Row 1: Current Allocation vs Benchmark & Alpha Curve
    col_alloc, col_alpha = st.columns([1, 1])

    with col_alloc:
        st.subheader("⚖️ Current Allocation vs. Benchmark (10%)")
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Equal-Weight Benchmark (10%)",
            x=weights_df['ticker'],
            y=weights_df['benchmark_pct'],
            marker_color="#94a3b8"
        ))
        # Color tactical bars green if overweight, red if underweight
        colors = ['#10b981' if t >= 0 else '#ef4444' for t in weights_df['active_tilt_pct']]
        fig_bar.add_trace(go.Bar(
            name="Tactical Sentiment Weight",
            x=weights_df['ticker'],
            y=weights_df['weight_pct'],
            marker_color=colors,
            text=[f"{w:.1f}% ({t:+.1f}%)" for w, t in zip(weights_df['weight_pct'], weights_df['active_tilt_pct'])],
            textposition='outside'
        ))
        fig_bar.update_layout(
            barmode='group',
            yaxis_title="Weight Percentage (%)",
            xaxis_title="Index Constituent",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20),
            height=380
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_alpha:
        st.subheader("📈 Cumulative Alpha Backtest Simulation")
        if not perf_df.empty:
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Scatter(
                x=perf_df['timestamp'],
                y=perf_df['Tactical_Portfolio'],
                mode='lines+markers',
                name='Tactical Sentiment Index',
                line=dict(color='#2563eb', width=3)
            ))
            fig_perf.add_trace(go.Scatter(
                x=perf_df['timestamp'],
                y=perf_df['Equal_Weight_Benchmark'],
                mode='lines',
                name='Benchmark (Equal Weight)',
                line=dict(color='#64748b', width=2, dash='dot')
            ))
            fig_perf.update_layout(
                yaxis_title="Portfolio Equity ($)",
                xaxis_title="Time",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=40, b=20),
                height=380
            )
            st.plotly_chart(fig_perf, use_container_width=True)
        else:
            st.info("Performance curve will populate as multiple timestamps are recorded.")

    # Chart Row 2: Dynamic Weight Evolution Over Time (Stacked Area Chart)
    st.subheader("🌊 Dynamic Weight Evolution Over Time")
    st.caption("Visualizes how individual stock allocations dynamically expanded or contracted as news broke.")

    if not history_df.empty:
        fig_area = px.area(
            history_df,
            x="timestamp",
            y="weight_pct",
            color="ticker",
            labels={"weight_pct": "Allocation (%)", "timestamp": "Timestamp", "ticker": "Asset"},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_area.update_layout(
            yaxis_range=[0, 100],
            yaxis_title="Total Portfolio Allocation (%)",
            margin=dict(l=20, r=20, t=20, b=20),
            height=420
        )
        st.plotly_chart(fig_area, use_container_width=True)
    else:
        st.info("Gathering historical data points...")

    # Section 3: Trade Decision Log & Sentiment Attribution
    st.subheader("📜 Rebalancing Attribution & Trade Decision Log")
    st.caption("Traceable lineage connecting the NLP Risk Engine's sentiment scores to exact portfolio weight shifts.")

    alloc_display = weights_df[[
        'ticker', 'weight_pct', 'benchmark_pct', 'active_tilt_pct', 
        'smoothed_sentiment', 'signal_count', 'top_signal_text'
    ]].copy()

    st.dataframe(
        alloc_display,
        column_config={
            "ticker": "Ticker",
            "weight_pct": st.column_config.NumberColumn("Tactical Weight", format="%.2f%%"),
            "benchmark_pct": st.column_config.NumberColumn("Benchmark", format="%.2f%%"),
            "active_tilt_pct": st.column_config.NumberColumn("Active Tilt (Δ)", format="%+.2f%%"),
            "smoothed_sentiment": st.column_config.NumberColumn("Decayed Sentiment", format="%+.3f"),
            "signal_count": st.column_config.NumberColumn("Signals Logged", format="%d"),
            "top_signal_text": "Key Driver Headline"
        },
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# TAB 2: AI/NLP RISK ENGINE (LIVE PIPELINE)
# =============================================================================
with tab_risk_engine:
    st.subheader("🧠 Real-Time NLP Intelligence & Signal Ingestion")
    st.caption("Live extraction of Sentiment (-1 to +1), Event Classification, and Impact Severity (1 to 10).")

    # Filters
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        selected_tickers = st.multiselect(
            "Filter Tickers",
            options=sorted(df_signals['ticker'].unique()),
            default=[]
        )
    with col_f2:
        min_impact = st.slider("Min Impact Severity", min_value=1, max_value=10, value=1)
    with col_f3:
        selected_events = st.multiselect(
            "Filter Event Categories",
            options=sorted(df_signals['event_type'].unique()),
            default=[]
        )

    # Filter signals
    filtered = df_signals.copy()
    if selected_tickers:
        filtered = filtered[filtered['ticker'].isin(selected_tickers)]
    if selected_events:
        filtered = filtered[filtered['event_type'].isin(selected_events)]
    filtered = filtered[filtered['impact'] >= min_impact]

    # Visualizations
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.subheader("Event Categories Distribution")
        ev_counts = filtered['event_type'].value_counts().reset_index()
        ev_counts.columns = ['Event Category', 'Count']
        fig_pie = px.pie(
            ev_counts,
            names='Event Category',
            values='Count',
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_c2:
        st.subheader("Average Sentiment by Asset")
        avg_sent = filtered.groupby('ticker')['sentiment'].mean().reset_index()
        avg_sent['Tone'] = avg_sent['sentiment'].apply(lambda x: 'Bullish' if x > 0.05 else ('Bearish' if x < -0.05 else 'Neutral'))
        fig_sent = px.bar(
            avg_sent,
            x='ticker',
            y='sentiment',
            color='Tone',
            color_discrete_map={'Bullish': '#10b981', 'Bearish': '#ef4444', 'Neutral': '#94a3b8'}
        )
        fig_sent.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
        st.plotly_chart(fig_sent, use_container_width=True)

    # Live Feed Table
    st.subheader("🚨 Live Ingested Signals Feed")
    feed_df = filtered[['dt', 'ticker', 'source', 'event_type', 'impact', 'sentiment', 'rationale', 'text']].copy()
    feed_df['Time'] = feed_df['dt'].dt.strftime('%b %d, %H:%M')

    st.dataframe(
        feed_df[['Time', 'ticker', 'source', 'event_type', 'impact', 'sentiment', 'rationale', 'text']],
        column_config={
            "Time": "Timestamp",
            "ticker": "Asset",
            "source": "Source",
            "event_type": "Event Category",
            "impact": st.column_config.ProgressColumn("Impact (1-10)", min_value=1, max_value=10, format="%d"),
            "sentiment": st.column_config.NumberColumn("Sentiment", format="%+.2f"),
            "rationale": "Explainable AI (XAI) Rationale",
            "text": "Extracted Headline"
        },
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# TAB 3: SINGLE ASSET DEEP DIVE
# =============================================================================
with tab_ticker_drill:
    st.subheader("🔬 Single Asset Sentiment & Allocation Analysis")
    target_ticker = st.selectbox("Select Asset to Inspect", options=MOCK_INDEX_UNIVERSE, index=0)

    ticker_signals = df_signals[df_signals['ticker'] == target_ticker]
    ticker_alloc = weights_df[weights_df['ticker'] == target_ticker]

    if not ticker_alloc.empty:
        alloc_row = ticker_alloc.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Allocation", f"{alloc_row['weight_pct']:.2f}%")
        c2.metric("Benchmark Weight", f"{alloc_row['benchmark_pct']:.2f}%")
        c3.metric("Active Tilt", f"{alloc_row['active_tilt_pct']:+.2f}%")
        c4.metric("Decayed Sentiment", f"{alloc_row['smoothed_sentiment']:+.3f}")

    if not ticker_signals.empty:
        st.markdown(f"#### Sentiment Trajectory for {target_ticker}")
        fig_ts = px.scatter(
            ticker_signals,
            x='dt',
            y='sentiment',
            size='impact',
            color='event_type',
            hover_data=['text', 'impact'],
            labels={'dt': 'Time', 'sentiment': 'Sentiment Score (-1 to 1)'}
        )
        fig_ts.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_ts.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_ts, use_container_width=True)

        st.markdown(f"#### Recent Intelligence for {target_ticker}")
        st.dataframe(
            ticker_signals[['dt', 'event_type', 'impact', 'sentiment', 'text', 'rationale']].head(10),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"No specific news signals recorded for {target_ticker} yet.")

# -----------------------------------------------------------------------------
# Streaming Auto-Refresh Hook
# -----------------------------------------------------------------------------
if auto_refresh:
    import time
    time.sleep(15)
    st.rerun()
