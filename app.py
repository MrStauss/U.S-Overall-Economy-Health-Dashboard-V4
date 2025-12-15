import datetime as dt
from dataclasses import dataclass
from typing import Dict, Optional, List

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from utils.data import get_fred_series, get_yf_history, normalize_index, latest_value, pct_change, get_treasury_debt_to_penny
from utils.score import compute_us_health_score
from utils.news import gdelt_latest

st.set_page_config(page_title="U.S. Overall Economy Health Dashboard", page_icon="📈", layout="wide")

with open("assets/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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

def card_html(title: str, value: str, subtitle: str = "", cls: str = "glass-card"):
    sub_class = "neu"
    s = subtitle.strip()
    if s.startswith("+") or "↑" in s:
        sub_class = "pos"
    if s.startswith("-") or "↓" in s:
        sub_class = "neg"
    return f"""<div class="{cls}">
      <div class="kpi-label">{title}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub {sub_class}">{subtitle}</div>
    </div>"""

def fmt_num(x: Optional[float], kind: str = "") -> str:
    if x is None:
        return "—"
    if kind == "%":
        return f"{x:,.2f}%"
    if kind == "index":
        return f"{x:,.2f}"
    return f"{x:,.0f}" if abs(x) >= 1000 else f"{x:,.2f}"

def plot_line(df: pd.DataFrame, title: str, height: int = 320):
    fig = go.Figure()
    for col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode="lines", name=col))
    fig.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, color="rgba(226,232,240,0.70)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)", color="rgba(226,232,240,0.70)")
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.title("Controls")
today = dt.date.today()
start = st.sidebar.date_input("Start date", value=today - dt.timedelta(days=DEFAULT_LOOKBACK_DAYS))
end = st.sidebar.date_input("End date", value=today)

page = st.sidebar.radio("Page", ["Overview", "Markets", "Jobs", "Debt & BNPL", "News"], index=0)

with st.sidebar.expander("Data sources"):
    st.write("- FRED: macro + jobs + VIX + debt proxies")
    st.write("- Yahoo Finance: GLD, SPY, VTI")
    st.write("- Treasury Fiscal Data API: Debt to the Penny")
    st.write("- GDELT: free news headlines")

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

fred_data = load_fred(list(FRED.keys()), start, end)
prices = load_yf(list(TICKERS.keys()), start, end)

last_updated = dt.datetime.now().strftime("%b %d, %Y %I:%M %p")
st.markdown(
    f"""<div class="header-wrap">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
        <div>
          <div class="header-title">U.S. Overall Economy Health Dashboard</div>
          <div class="header-sub">VIX • GLD • SPY • VTI • Jobs • Debt/BNPL proxies • News</div>
        </div>
        <div style="text-align:right;">
          <div class="header-sub">Last Updated</div>
          <div class="small-mono" style="color:#34d399; font-weight:700;">{last_updated}</div>
        </div>
      </div>
    </div>""",
    unsafe_allow_html=True,
)

score_obj = compute_us_health_score(fred_data, prices)
health_score = int(score_obj.get("score", 50))
score_color = "#10b981" if health_score >= 67 else "#f59e0b" if health_score >= 45 else "#ef4444"
st.markdown(
    f"""<div class="glass-card" style="margin-bottom:14px;">
      <div class="kpi-label">US Economy Health Score</div>
      <div class="kpi-value" style="color:{score_color};">{health_score}/100</div>
      <div class="kpi-sub neu">Composite of jobs, inflation/rates, market risk, and consumer stress proxies.</div>
    </div>""",
    unsafe_allow_html=True,
)

if page == "Overview":
    unrate = fred_data.get("UNRATE")
    payems = fred_data.get("PAYEMS")
    vix = fred_data.get("VIXCLS")

    unrate_cur = latest_value(unrate)
    unrate_delta = pct_change(unrate, periods=1)
    vix_cur = latest_value(vix)
    vix_delta = pct_change(vix, periods=1)

    payroll_delta = None
    if payems is not None and len(payems.dropna()) > 1:
        payroll_delta = float(payems.dropna().iloc[-1] - payems.dropna().iloc[-2])

    def mk_price_card(label: str, s: Optional[pd.Series], cls="glass-card"):
        if s is None or s.dropna().empty:
            return card_html(label, "—", "No data", cls)
        cur = float(s.dropna().iloc[-1])
        chg = pct_change(s, periods=1)
        sub = f"{chg:+.2f}% day" if chg is not None else "—"
        return card_html(label, f"${cur:,.2f}", sub, cls)

    kpis = [
        card_html("Unemployment", fmt_num(unrate_cur, "%"), f"{unrate_delta:+.2f}% vs last month" if unrate_delta is not None else "—"),
        card_html("VIX", fmt_num(vix_cur, "index"), f"{vix_delta:+.2f}% vs yesterday" if vix_delta is not None else "—"),
        card_html("Payrolls (MoM)", f"{payroll_delta:+,.0f}K" if payroll_delta is not None else "—", "PAYEMS change"),
        card_html("BNPL Proxy (CC Delinq.)", fmt_num(latest_value(fred_data.get("DRCCLACBS")), "%"), "Consumer stress proxy", "bnpl-card"),
        mk_price_card("SPY", prices["SPY"] if "SPY" in prices.columns else None, "metric-card"),
    ]
    st.markdown('<div class="kpi-grid">' + "\n".join(kpis) + "</div>", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    comps = score_obj.get("components", [])
    if comps:
        comp_df = pd.DataFrame(comps).sort_values("weight", ascending=False)
        st.markdown('<div class="section-title">Health Score Breakdown</div>', unsafe_allow_html=True)
        st.dataframe(comp_df[["name","score","weight","z"]], use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div class="section-title">Markets</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Normalized (base=100)</div>', unsafe_allow_html=True)
        if not prices.empty:
            norm = pd.DataFrame({t: normalize_index(prices[t]) for t in prices.columns})
            plot_line(norm.dropna(how="all"), "GLD / SPY / VTI (Normalized)")
    with c2:
        st.markdown('<div class="section-title">Jobs</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">UNRATE + PAYEMS</div>', unsafe_allow_html=True)
        df = pd.DataFrame({"Unemployment (%)": fred_data.get("UNRATE"), "Payrolls (k)": fred_data.get("PAYEMS")}).dropna(how="all")
        if not df.empty:
            plot_line(df, "Labor Signals")

elif page == "Markets":
    st.markdown('<div class="section-title">Markets</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">GLD + SPY + VTI history + quick stats</div>', unsafe_allow_html=True)
    if prices.empty:
        st.warning("No market data returned.")
    else:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            plot_line(prices, "Adj Close Prices")
        with c2:
            norm = pd.DataFrame({t: normalize_index(prices[t]) for t in prices.columns})
            plot_line(norm, "Normalized (base=100)")
        rets = prices.pct_change().dropna(how="all")
        if not rets.empty:
            ann_vol = rets.std() * (252 ** 0.5)
            ann_ret = (1 + rets).prod() ** (252 / len(rets)) - 1
            corr = rets.corr()
            a1, a2, a3 = st.columns(3)
            with a1:
                st.markdown('<div class="section-title">Annualized Return</div>', unsafe_allow_html=True)
                st.dataframe(ann_ret.to_frame("ann_return").style.format("{:.2%}"), use_container_width=True)
            with a2:
                st.markdown('<div class="section-title">Annualized Volatility</div>', unsafe_allow_html=True)
                st.dataframe(ann_vol.to_frame("ann_vol").style.format("{:.2%}"), use_container_width=True)
            with a3:
                st.markdown('<div class="section-title">Correlation</div>', unsafe_allow_html=True)
                st.dataframe(corr.style.format("{:.2f}"), use_container_width=True)

elif page == "Jobs":
    st.markdown('<div class="section-title">Jobs</div>', unsafe_allow_html=True)
    for sid in ["UNRATE","PAYEMS","ICSA","JTSJOL"]:
        s = fred_data.get(sid)
        if s is None or s.dropna().empty:
            st.warning(f"{sid} not available.")
            continue
        plot_line(s.rename(FRED[sid].label).to_frame(), f"{FRED[sid].label} ({sid})")

elif page == "Debt & BNPL":
    st.markdown('<div class="section-title">Debt & BNPL</div>', unsafe_allow_html=True)
    tdsp = latest_value(fred_data.get("TDSP"))
    cc_del = latest_value(fred_data.get("DRCCLACBS"))
    cons_credit = latest_value(fred_data.get("TOTALSL"))
    fed_debt = latest_value(fred_data.get("GFDEBTN"))
    treasury_latest = load_treasury_debt()
    cards = [
        card_html("Debt Service (TDSP)", fmt_num(tdsp, "%"), "Quarterly", "bnpl-card"),
        card_html("CC Delinq. (DRCCLACBS)", fmt_num(cc_del, "%"), "BNPL proxy", "bnpl-card"),
        card_html("Consumer Credit (TOTALSL)", f"${cons_credit:,.0f}B" if cons_credit is not None else "—", "Monthly", "bnpl-card"),
        card_html("Federal Debt (FRED)", f"${(fed_debt/1_000_000):,.2f}T" if fed_debt is not None else "—", "Daily", "glass-card"),
        card_html("Debt to the Penny", f"${(treasury_latest/1e12):,.2f}T" if treasury_latest else "—", "Treasury", "glass-card"),
    ]
    st.markdown('<div class="kpi-grid">' + "\n".join(cards) + "</div>", unsafe_allow_html=True)

elif page == "News":
    st.markdown('<div class="section-title">News Feed</div>', unsafe_allow_html=True)
    q = st.text_input("Query", value="US economy OR inflation OR jobs OR recession OR Federal Reserve OR debt ceiling")
    n = st.slider("Items", 5, 30, 12)
    items = load_news(q, n)
    if not items:
        st.info("No articles returned right now.")
    else:
        for it in items:
            st.markdown(f"- **{it.get('title','')}**  
  {it.get('source','')} · {it.get('seen','')}  
  {it.get('url','')}")
