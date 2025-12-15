import datetime as dt
from dataclasses import dataclass
from typing import Dict, Optional, List
import json

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from utils.data import get_fred_series, get_yf_history, normalize_index, latest_value, pct_change, get_treasury_debt_to_penny
from utils.score import compute_us_health_score
from utils.news import gdelt_latest

st.set_page_config(
    page_title="U.S. Economy Health Dashboard", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with animations and modern design
ENHANCED_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

* { font-family: 'Inter', sans-serif; }
.mono { font-family: 'JetBrains Mono', monospace; }

.stApp { 
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #e2e8f0; 
}

.block-container { 
    padding-top: 1rem; 
    padding-bottom: 3rem; 
    max-width: 1400px; 
}

/* Animated Header */
.hero-header {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}

.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
    animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    position: relative;
    z-index: 1;
}

.hero-subtitle {
    font-size: 1.1rem;
    color: rgba(226, 232, 240, 0.8);
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

/* Score Gauge Container */
.score-container {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
    backdrop-filter: blur(16px);
    border: 2px solid rgba(148, 163, 184, 0.2);
    border-radius: 24px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    position: relative;
    overflow: hidden;
}

.score-container::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 60%);
    animation: rotate 10s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.score-label {
    text-align: center;
    font-size: 0.95rem;
    color: rgba(226, 232, 240, 0.7);
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 1rem;
    position: relative;
    z-index: 1;
}

.score-value {
    text-align: center;
    font-size: 5rem;
    font-weight: 800;
    margin: 1rem 0;
    position: relative;
    z-index: 1;
    animation: fadeIn 1s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1); }
}

.score-description {
    text-align: center;
    font-size: 0.95rem;
    color: rgba(226, 232, 240, 0.7);
    position: relative;
    z-index: 1;
}

/* KPI Grid */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.25rem;
    margin-bottom: 2rem;
}

/* Enhanced Cards */
.metric-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(59, 130, 246, 0.4);
    box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15);
}

.metric-card:hover::before {
    opacity: 1;
}

.metric-label {
    font-size: 0.85rem;
    color: rgba(226, 232, 240, 0.7);
    font-weight: 600;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.5rem;
    font-feature-settings: 'tnum';
}

.metric-change {
    font-size: 0.9rem;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    border-radius: 8px;
}

.metric-change.positive {
    color: #10b981;
    background: rgba(16, 185, 129, 0.1);
}

.metric-change.negative {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
}

.metric-change.neutral {
    color: #f59e0b;
    background: rgba(245, 158, 11, 0.1);
}

/* Section Headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 2.5rem 0 1.5rem 0;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid rgba(148, 163, 184, 0.2);
}

.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
}

.section-subtitle {
    font-size: 0.9rem;
    color: rgba(226, 232, 240, 0.6);
    margin: 0;
}

/* Chart Container */
.chart-container {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

/* Status Badge */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.status-healthy {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-moderate {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-warning {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Insight Card */
.insight-card {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.insight-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.insight-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #60a5fa;
    margin-bottom: 0.75rem;
}

.insight-text {
    font-size: 0.95rem;
    color: rgba(226, 232, 240, 0.85);
    line-height: 1.6;
}

/* Loading Animation */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.skeleton {
    background: linear-gradient(90deg, rgba(148, 163, 184, 0.1) 0%, rgba(148, 163, 184, 0.2) 50%, rgba(148, 163, 184, 0.1) 100%);
    background-size: 1000px 100%;
    animation: shimmer 2s infinite;
    border-radius: 8px;
}

/* Responsive */
@media (max-width: 768px) {
    .hero-title { font-size: 1.75rem; }
    .score-value { font-size: 3.5rem; }
    .kpi-grid { grid-template-columns: 1fr; }
}
</style>
"""

st.markdown(ENHANCED_CSS, unsafe_allow_html=True)

@dataclass(frozen=True)
class SeriesSpec:
    id: str
    label: str
    units: str
    freq_hint: str

FRED: Dict[str, SeriesSpec] = {
    "UNRATE": SeriesSpec("UNRATE", "Unemployment Rate", "%", "monthly"),
    "PAYEMS": SeriesSpec("PAYEMS", "Nonfarm Payrolls", "thousands", "monthly"),
    "ICSA": SeriesSpec("ICSA", "Initial Jobless Claims", "claims", "weekly"),
    "JTSJOL": SeriesSpec("JTSJOL", "Job Openings (JOLTS)", "thousands", "monthly"),
    "VIXCLS": SeriesSpec("VIXCLS", "VIX (CBOE)", "index", "daily"),
    "CPIAUCSL": SeriesSpec("CPIAUCSL", "CPI (All Urban Consumers)", "index", "monthly"),
    "FEDFUNDS": SeriesSpec("FEDFUNDS", "Effective Fed Funds Rate", "%", "monthly"),
    "TDSP": SeriesSpec("TDSP", "Household Debt Service Ratio", "%", "quarterly"),
    "DRCCLACBS": SeriesSpec("DRCCLACBS", "Credit Card Delinquency Rate", "%", "quarterly"),
    "TOTALSL": SeriesSpec("TOTALSL", "Total Consumer Credit", "USD (billions)", "monthly"),
    "GFDEBTN": SeriesSpec("GFDEBTN", "Federal Debt: Total Public Debt", "USD (millions)", "daily"),
}

TICKERS = {"GLD": "Gold (GLD)", "SPY": "S&P 500 (SPY)", "VTI": "Total Market (VTI)"}
DEFAULT_LOOKBACK_DAYS = 365 * 5

# Caching functions
@st.cache_data(ttl=60 * 60, show_spinner=False)
def load_fred(ids: List[str], start_dt: dt.date, end_dt: dt.date):
    return {sid: get_fred_series(sid, start_dt, end_dt) for sid in ids}

@st.cache_data(ttl=15 * 60, show_spinner=False)
def load_yf(tickers: List[str], start_dt: dt.date, end_dt: dt.date) -> pd.DataFrame:
    return get_yf_history(tickers, start_dt, end_dt)

@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def load_treasury_debt() -> Optional[float]:
    try:
        return get_treasury_debt_to_penny()
    except Exception:
        return None

@st.cache_data(ttl=10 * 60, show_spinner=False)
def load_news(q: str, n: int):
    try:
        return gdelt_latest(query=q, max_records=n)
    except Exception:
        return []

def create_gauge_chart(score: int, title: str = "Economy Health Score") -> go.Figure:
    """Create an animated gauge chart for the health score"""
    color = "#10b981" if score >= 67 else "#f59e0b" if score >= 45 else "#ef4444"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20, 'color': '#e2e8f0'}},
        number={'font': {'size': 60, 'color': color}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': "#94a3b8"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "rgba(30, 41, 59, 0.3)",
            'borderwidth': 2,
            'bordercolor': "rgba(148, 163, 184, 0.3)",
            'steps': [
                {'range': [0, 33], 'color': 'rgba(239, 68, 68, 0.2)'},
                {'range': [33, 67], 'color': 'rgba(245, 158, 11, 0.2)'},
                {'range': [67, 100], 'color': 'rgba(16, 185, 129, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "#ffffff", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "#e2e8f0", 'family': "Inter"},
        height=300,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig

def create_enhanced_line_chart(df: pd.DataFrame, title: str, height: int = 400) -> go.Figure:
    """Create enhanced line chart with modern styling"""
    fig = go.Figure()
    
    colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']
    
    for idx, col in enumerate(df.columns):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col],
            mode='lines',
            name=col,
            line=dict(width=3, color=colors[idx % len(colors)]),
            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:,.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title={
            'text': title,
            'font': {'size': 18, 'color': '#ffffff', 'family': 'Inter'}
        },
        margin=dict(l=10, r=10, t=50, b=10),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", family="Inter"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(30, 41, 59, 0.6)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
        hovermode='x unified',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(148, 163, 184, 0.1)',
            color='rgba(226, 232, 240, 0.7)'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(148, 163, 184, 0.1)',
            color='rgba(226, 232, 240, 0.7)'
        )
    )
    
    return fig

def create_sparkline(series: pd.Series, color: str = '#3b82f6') -> go.Figure:
    """Create minimal sparkline chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=series.index,
        y=series.values,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)',
        hovertemplate='%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=60,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        hovermode='x'
    )
    
    return fig

def format_number(value: Optional[float], format_type: str = "number") -> str:
    """Format numbers with appropriate styling"""
    if value is None:
        return "—"
    
    if format_type == "percent":
        return f"{value:.2f}%"
    elif format_type == "currency":
        if abs(value) >= 1e12:
            return f"${value/1e12:.2f}T"
        elif abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        else:
            return f"${value:,.0f}"
    elif format_type == "large":
        if abs(value) >= 1e6:
            return f"{value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.1f}K"
        else:
            return f"{value:,.0f}"
    else:
        return f"{value:,.2f}"

def generate_insight(score: int, components: List[dict]) -> str:
    """Generate AI-style insight based on score and components"""
    if score >= 75:
        status = "strong and resilient"
        trend = "positive momentum across multiple indicators"
    elif score >= 60:
        status = "moderately healthy"
        trend = "stable conditions with some areas of strength"
    elif score >= 45:
        status = "showing mixed signals"
        trend = "diverging indicators requiring attention"
    else:
        status = "facing headwinds"
        trend = "concerning trends across key metrics"
    
    # Find strongest and weakest components
    sorted_comps = sorted(components, key=lambda x: x['score'], reverse=True)
    strongest = sorted_comps[0]['name'] if sorted_comps else "markets"
    weakest = sorted_comps[-1]['name'] if sorted_comps else "employment"
    
    return f"""The U.S. economy is currently **{status}** with a health score of **{score}/100**. 
    Analysis shows {trend}. **{strongest}** is performing well, while **{weakest}** warrants monitoring. 
    This composite score reflects real-time data across employment, inflation, market risk, and consumer stress indicators."""

# Sidebar
st.sidebar.title("⚙️ Dashboard Controls")

today = dt.date.today()
start = st.sidebar.date_input("📅 Start Date", value=today - dt.timedelta(days=DEFAULT_LOOKBACK_DAYS))
end = st.sidebar.date_input("📅 End Date", value=today)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "📊 Navigate",
    ["🏠 Overview", "📈 Markets", "💼 Jobs & Employment", "💳 Debt & Credit", "📰 News Feed"],
    index=0
)

st.sidebar.markdown("---")

with st.sidebar.expander("ℹ️ Data Sources"):
    st.markdown("""
    **Economic Data:**
    - FRED (Federal Reserve Economic Data)
    - Treasury Fiscal Data API
    
    **Market Data:**
    - Yahoo Finance (Real-time)
    
    **News:**
    - GDELT Project
    """)

with st.sidebar.expander("📖 About the Score"):
    st.markdown("""
    The **Economy Health Score** is a composite metric (0-100) that synthesizes:
    
    - **Employment** (40%): Unemployment, payrolls, job openings
    - **Inflation & Rates** (16%): CPI, Fed Funds Rate
    - **Market Risk** (28%): VIX, SPY, VTI performance
    - **Consumer Stress** (16%): Credit card delinquencies, debt service
    
    Scores are normalized using z-scores over rolling windows.
    """)

# Load data
with st.spinner("🔄 Loading economic data..."):
    fred_data = load_fred(list(FRED.keys()), start, end)
    prices = load_yf(list(TICKERS.keys()), start, end)
    treasury_debt = load_treasury_debt()

# Calculate score
score_obj = compute_us_health_score(fred_data, prices)
health_score = int(score_obj.get("score", 50))
components = score_obj.get("components", [])

# Hero Header
last_updated = dt.datetime.now().strftime("%B %d, %Y at %I:%M %p")
st.markdown(f"""
<div class="hero-header">
    <div class="hero-title">🇺🇸 U.S. Economy Health Dashboard</div>
    <div class="hero-subtitle">Real-time economic intelligence • Last updated: {last_updated}</div>
</div>
""", unsafe_allow_html=True)

# Main Score Display
score_status = "status-healthy" if health_score >= 67 else "status-moderate" if health_score >= 45 else "status-warning"
score_label = "Healthy" if health_score >= 67 else "Moderate" if health_score >= 45 else "Warning"
score_emoji = "✅" if health_score >= 67 else "⚠️" if health_score >= 45 else "🚨"

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(f"""
    <div class="score-container">
        <div class="score-label">U.S. Economy Health Score</div>
        <div class="score-value" style="color: {'#10b981' if health_score >= 67 else '#f59e0b' if health_score >= 45 else '#ef4444'};">
            {health_score}<span style="font-size: 2.5rem; color: rgba(226, 232, 240, 0.5);">/100</span>
        </div>
        <div style="text-align: center; margin: 1rem 0;">
            <span class="{score_status} status-badge">{score_emoji} {score_label}</span>
        </div>
        <div class="score-description">
            Composite metric synthesizing employment, inflation, market risk, and consumer stress indicators
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    gauge_fig = create_gauge_chart(health_score)
    st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})

# AI Insight
insight_text = generate_insight(health_score, components)
st.markdown(f"""
<div class="insight-card">
    <div class="insight-icon">💡</div>
    <div class="insight-title">Economic Snapshot</div>
    <div class="insight-text">{insight_text}</div>
</div>
""", unsafe_allow_html=True)

# PAGE ROUTING
if page == "🏠 Overview":
    # Key Metrics Grid
    st.markdown('<div class="section-header"><div class="section-title">📊 Key Economic Indicators</div></div>', unsafe_allow_html=True)
    
    unrate = fred_data.get("UNRATE")
    payems = fred_data.get("PAYEMS")
    vix = fred_data.get("VIXCLS")
    cpi = fred_data.get("CPIAUCSL")
    
    unrate_cur = latest_value(unrate)
    unrate_delta = pct_change(unrate, periods=1)
    
    vix_cur = latest_value(vix)
    vix_delta = pct_change(vix, periods=1)
    
    cpi_cur = latest_value(cpi)
    cpi_delta = pct_change(cpi, periods=12)
    
    payroll_delta = None
    if payems is not None and len(payems.dropna()) > 1:
        payroll_delta = float(payems.dropna().iloc[-1] - payems.dropna().iloc[-2])
    
    spy_price = None
    spy_delta = None
    if "SPY" in prices.columns:
        spy_price = latest_value(prices["SPY"])
        spy_delta = pct_change(prices["SPY"], periods=1)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        change_class = "negative" if unrate_delta and unrate_delta > 0 else "positive" if unrate_delta and unrate_delta < 0 else "neutral"
        arrow = "↑" if unrate_delta and unrate_delta > 0 else "↓" if unrate_delta and unrate_delta < 0 else "→"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Unemployment Rate</div>
            <div class="metric-value">{format_number(unrate_cur, 'percent')}</div>
            <span class="metric-change {change_class}">{arrow} {abs(unrate_delta) if unrate_delta else 0:.2f}% MoM</span>
        </div>
        """, unsafe_allow_html=True)
        if unrate is not None and not unrate.dropna().empty:
            st.plotly_chart(create_sparkline(unrate.dropna().tail(30), '#ef4444' if unrate_delta and unrate_delta > 0 else '#10b981'), 
                          use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        change_class = "positive" if payroll_delta and payroll_delta > 0 else "negative" if payroll_delta and payroll_delta < 0 else "neutral"
        arrow = "↑" if payroll_delta and payroll_delta > 0 else "↓" if payroll_delta and payroll_delta < 0 else "→"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Payroll Change (MoM)</div>
            <div class="metric-value">{arrow}{format_number(payroll_delta, 'large')}</div>
            <span class="metric-change {change_class}">PAYEMS</span>
        </div>
        """, unsafe_allow_html=True)
        if payems is not None and not payems.dropna().empty:
            st.plotly_chart(create_sparkline(payems.dropna().tail(30), '#10b981' if payroll_delta and payroll_delta > 0 else '#ef4444'), 
                          use_container_width=True, config={'displayModeBar': False})
    
    with col3:
        change_class = "negative" if vix_delta and vix_delta > 0 else "positive" if vix_delta and vix_delta < 0 else "neutral"
        arrow = "↑" if vix_delta and vix_delta > 0 else "↓" if vix_delta and vix_delta < 0 else "→"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">VIX (Market Volatility)</div>
            <div class="metric-value">{format_number(vix_cur, 'number')}</div>
            <span class="metric-change {change_class}">{arrow} {abs(vix_delta) if vix_delta else 0:.2f}% Daily</span>
        </div>
        """, unsafe_allow_html=True)
        if vix is not None and not vix.dropna().empty:
            st.plotly_chart(create_sparkline(vix.dropna().tail(60), '#ef4444' if vix_cur and vix_cur > 20 else '#10b981'), 
                          use_container_width=True, config={'displayModeBar': False})
    
    with col4:
        change_class = "positive" if spy_delta and spy_delta > 0 else "negative" if spy_delta and spy_delta < 0 else "neutral"
        arrow = "↑" if spy_delta and spy_delta > 0 else "↓" if spy_delta and spy_delta < 0 else "→"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">S&P 500 (SPY)</div>
            <div class="metric-value">{format_number(spy_price, 'currency') if spy_price else '—'}</div>
            <span class="metric-change {change_class}">{arrow} {abs(spy_delta) if spy_delta else 0:.2f}% Daily</span>
        </div>
        """, unsafe_allow_html=True)
        if "SPY" in prices.columns and not prices["SPY"].dropna().empty:
            st.plotly_chart(create_sparkline(prices["SPY"].dropna().tail(60), '#10b981' if spy_delta and spy_delta > 0 else '#ef4444'), 
                          use_container_width=True, config={'displayModeBar': False})
    
    # Score Breakdown
    st.markdown('<div class="section-header"><div class="section-title">🔍 Health Score Components</div></div>', unsafe_allow_html=True)
    
    if components:
        comp_df = pd.DataFrame(components).sort_values("weight", ascending=False)
        
        # Create visual breakdown
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=comp_df['name'],
            y=comp_df['score'],
            marker=dict(
                color=comp_df['score'],
                colorscale=[[0, '#ef4444'], [0.5, '#f59e0b'], [1, '#10b981']],
                line=dict(color='rgba(148, 163, 184, 0.3)', width=1)
            ),
            text=comp_df['score'].apply(lambda x: f"{x}"),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Score: %{y}<br>Weight: %{customdata:.1%}<extra></extra>',
            customdata=comp_df['weight']
        ))
        
        fig.update_layout(
            title="Component Scores (Weighted)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0", family="Inter"),
            height=400,
            showlegend=False,
            xaxis=dict(
                tickangle=-45,
                showgrid=False,
                color='rgba(226, 232, 240, 0.7)'
            ),
            yaxis=dict(
                title="Score (0-100)",
                showgrid=True,
                gridcolor='rgba(148, 163, 184, 0.1)',
                color='rgba(226, 232, 240, 0.7)',
                range=[0, 100]
            ),
            margin=dict(l=60, r=20, t=60, b=120)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        with st.expander("📋 View Detailed Component Data"):
            display_df = comp_df[["name", "score", "weight", "z"]].copy()
            display_df.columns = ["Indicator", "Score", "Weight", "Z-Score"]
            display_df["Weight"] = display_df["Weight"].apply(lambda x: f"{x:.1%}")
            display_df["Z-Score"] = display_df["Z-Score"].apply(lambda x: f"{x:.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Charts Section
    st.markdown('<div class="section-header"><div class="section-title">📈 Market Performance</div></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not prices.empty:
            norm = pd.DataFrame({t: normalize_index(prices[t]) for t in prices.columns})
            fig = create_enhanced_line_chart(norm.dropna(how="all"), "Normalized Performance (Base=100)")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if unrate is not None and payems is not None:
            df = pd.DataFrame({
                "Unemployment (%)": unrate,
                "Payrolls (Thousands)": payems / 1000  # Scale for visibility
            }).dropna(how="all")
            if not df.empty:
                fig = create_enhanced_line_chart(df, "Employment Indicators")
                st.plotly_chart(fig, use_container_width=True)

elif page == "📈 Markets":
    st.markdown('<div class="section-header"><div class="section-title">📈 Market Analysis</div></div>', unsafe_allow_html=True)
    
    if prices.empty:
        st.warning("⚠️ No market data available for the selected period.")
    else:
        # Price charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_enhanced_line_chart(prices, "Adjusted Close Prices")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            norm = pd.DataFrame({t: normalize_index(prices[t]) for t in prices.columns})
            fig = create_enhanced_line_chart(norm, "Normalized Performance (Base=100)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        st.markdown('<div class="section-header"><div class="section-title">📊 Market Statistics</div></div>', unsafe_allow_html=True)
        
        rets = prices.pct_change().dropna(how="all")
        
        if not rets.empty:
            ann_vol = rets.std() * (252 ** 0.5)
            ann_ret = (1 + rets).prod() ** (252 / len(rets)) - 1
            sharpe = (ann_ret / ann_vol) if not ann_vol.isna().all() else pd.Series()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Annualized Return**")
                for ticker in ann_ret.index:
                    val = ann_ret[ticker]
                    color = "#10b981" if val > 0 else "#ef4444"
                    st.markdown(f"""
                    <div style="margin: 0.5rem 0;">
                        <span style="color: #94a3b8;">{ticker}:</span>
                        <span style="color: {color}; font-weight: 600; margin-left: 0.5rem;">{val*100:.2f}%</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Annualized Volatility**")
                for ticker in ann_vol.index:
                    val = ann_vol[ticker]
                    st.markdown(f"""
                    <div style="margin: 0.5rem 0;">
                        <span style="color: #94a3b8;">{ticker}:</span>
                        <span style="color: #60a5fa; font-weight: 600; margin-left: 0.5rem;">{val*100:.2f}%</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("**Sharpe Ratio**")
                for ticker in sharpe.index:
                    val = sharpe[ticker]
                    color = "#10b981" if val > 1 else "#f59e0b" if val > 0.5 else "#ef4444"
                    st.markdown(f"""
                    <div style="margin: 0.5rem 0;">
                        <span style="color: #94a3b8;">{ticker}:</span>
                        <span style="color: {color}; font-weight: 600; margin-left: 0.5rem;">{val:.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Correlation heatmap
            st.markdown('<div class="section-header"><div class="section-title">🔗 Asset Correlations</div></div>', unsafe_allow_html=True)
            
            corr = rets.corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.index,
                colorscale='RdBu',
                zmid=0,
                text=corr.values,
                texttemplate='%{text:.2f}',
                textfont={"size": 12},
                colorbar=dict(title="Correlation")
            ))
            
            fig.update_layout(
                title="Return Correlations",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0", family="Inter"),
                height=400,
                xaxis=dict(side='bottom'),
                yaxis=dict(side='left')
            )
            
            st.plotly_chart(fig, use_container_width=True)

elif page == "💼 Jobs & Employment":
    st.markdown('<div class="section-header"><div class="section-title">💼 Employment Indicators</div></div>', unsafe_allow_html=True)
    
    job_metrics = ["UNRATE", "PAYEMS", "ICSA", "JTSJOL"]
    
    for sid in job_metrics:
        s = fred_data.get(sid)
        if s is None or s.dropna().empty:
            st.warning(f"⚠️ {FRED[sid].label} data not available.")
            continue
        
        spec = FRED[sid]
        latest = latest_value(s)
        change = pct_change(s, periods=1)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            change_class = "positive" if change and change > 0 else "negative" if change and change < 0 else "neutral"
            if sid == "UNRATE" or sid == "ICSA":
                change_class = "negative" if change and change > 0 else "positive" if change and change < 0 else "neutral"
            
            arrow = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{spec.label}</div>
                <div class="metric-value">{format_number(latest, 'percent' if spec.units == '%' else 'large')}</div>
                <span class="metric-change {change_class}">{arrow} {abs(change) if change else 0:.2f}%</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            fig = create_enhanced_line_chart(s.rename(spec.label).to_frame(), f"{spec.label} - {spec.freq_hint.title()}")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")

elif page == "💳 Debt & Credit":
    st.markdown('<div class="section-header"><div class="section-title">💳 Consumer Debt & Credit Indicators</div></div>', unsafe_allow_html=True)
    
    # Key metrics
    tdsp = latest_value(fred_data.get("TDSP"))
    cc_del = latest_value(fred_data.get("DRCCLACBS"))
    cons_credit = latest_value(fred_data.get("TOTALSL"))
    fed_debt = latest_value(fred_data.get("GFDEBTN"))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Debt Service Ratio</div>
            <div class="metric-value">{format_number(tdsp, 'percent')}</div>
            <span class="metric-change neutral">Quarterly</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        status = "negative" if cc_del and cc_del > 2.5 else "neutral"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">CC Delinquency Rate</div>
            <div class="metric-value">{format_number(cc_del, 'percent')}</div>
            <span class="metric-change {status}">BNPL Proxy</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Consumer Credit</div>
            <div class="metric-value">{format_number(cons_credit, 'currency')}</div>
            <span class="metric-change neutral">Monthly</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        debt_val = (fed_debt / 1_000_000) if fed_debt else None
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Federal Debt</div>
            <div class="metric-value">{format_number(debt_val, 'currency')}</div>
            <span class="metric-change neutral">FRED Daily</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Treasury debt
    if treasury_debt:
        st.markdown(f"""
        <div class="insight-card" style="margin-top: 1.5rem;">
            <div class="insight-icon">🏛️</div>
            <div class="insight-title">U.S. Treasury - Debt to the Penny</div>
            <div class="insight-text">
                Current total public debt outstanding: <strong>{format_number(treasury_debt, 'currency')}</strong>
                <br><small>Source: Treasury Fiscal Data API (Daily Update)</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    st.markdown('<div class="section-header"><div class="section-title">📊 Debt Trends</div></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        tdsp_series = fred_data.get("TDSP")
        if tdsp_series is not None and not tdsp_series.dropna().empty:
            fig = create_enhanced_line_chart(tdsp_series.rename("Debt Service Ratio (%)").to_frame(), 
                                           "Household Debt Service Ratio")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        cc_series = fred_data.get("DRCCLACBS")
        if cc_series is not None and not cc_series.dropna().empty:
            fig = create_enhanced_line_chart(cc_series.rename("Delinquency Rate (%)").to_frame(), 
                                           "Credit Card Delinquency Rate")
            st.plotly_chart(fig, use_container_width=True)

elif page == "📰 News Feed":
    st.markdown('<div class="section-header"><div class="section-title">📰 Latest Economic News</div></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        q = st.text_input("🔍 Search Query", 
                         value="US economy OR inflation OR jobs OR recession OR Federal Reserve OR debt ceiling",
                         help="Use OR, AND, NOT for boolean search")
    
    with col2:
        n = st.slider("📊 Articles", 5, 30, 15)
    
    with st.spinner("📡 Fetching latest news..."):
        items = load_news(q, n)
    
    if not items:
        st.info("ℹ️ No articles found. Try adjusting your search query.")
    else:
        st.markdown(f"<p style='color: #94a3b8; margin-bottom: 1rem;'>Found {len(items)} articles</p>", 
                   unsafe_allow_html=True)
        
        for idx, item in enumerate(items, 1):
            title = item.get('title', 'Untitled')
            source = item.get('source', 'Unknown')
            seen = item.get('seen', '')
            url = item.get('url', '#')
            
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                    <span style="color: #94a3b8; font-size: 0.85rem; font-weight: 600;">#{idx}</span>
                    <span style="color: #64748b; font-size: 0.75rem;">{seen}</span>
                </div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.5rem;">
                    {title}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8; font-size: 0.85rem;">📍 {source}</span>
                    <a href="{url}" target="_blank" style="color: #3b82f6; text-decoration: none; font-size: 0.85rem; font-weight: 500;">
                        Read More →
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(148, 163, 184, 0.7); font-size: 0.85rem; padding: 2rem 0 1rem 0;">
    <p><strong>U.S. Economy Health Dashboard</strong> | Data updated in real-time</p>
    <p style="margin-top: 0.5rem;">Built with Streamlit • Data from FRED, Yahoo Finance, Treasury.gov, GDELT</p>
    <p style="margin-top: 0.5rem; font-size: 0.75rem;">
        ⚠️ <em>For informational purposes only. Not financial advice.</em>
    </p>
</div>
""", unsafe_allow_html=True)
