import datetime as dt
from typing import List, Optional

import pandas as pd
import requests
import streamlit as st

def _get_fred_client():
    try:
        from fredapi import Fred  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing dependency 'fredapi'. Add it to requirements.txt.") from e
    api_key = st.secrets.get("FRED_API_KEY", None)
    return Fred(api_key=api_key) if api_key else Fred()

def get_fred_series(series_id: str, start: dt.date, end: dt.date) -> Optional[pd.Series]:
    try:
        fred = _get_fred_client()
        s = fred.get_series(series_id, observation_start=start, observation_end=end)
        if s is None or len(s) == 0:
            return None
        s.index = pd.to_datetime(s.index)
        return s.sort_index()
    except Exception as e:
        st.warning(f"FRED series '{series_id}' failed to load: {e}")
        return None

def get_yf_history(tickers: List[str], start: dt.date, end: dt.date) -> pd.DataFrame:
    try:
        import yfinance as yf  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing dependency 'yfinance'. Add it to requirements.txt.") from e
    df = yf.download(
        tickers=tickers,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end) + pd.Timedelta(days=1),
        auto_adjust=False,
        progress=False,
        group_by="ticker",
    )
    out = pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        for t in tickers:
            if (t, "Adj Close") in df.columns:
                out[t] = df[(t, "Adj Close")]
    else:
        if "Adj Close" in df.columns and len(tickers) == 1:
            out[tickers[0]] = df["Adj Close"]
    out.index = pd.to_datetime(out.index)
    return out.dropna(how="all")

def normalize_index(s: pd.Series, base: float = 100.0) -> pd.Series:
    s = s.dropna()
    if s.empty:
        return s
    return (s / float(s.iloc[0])) * base

def latest_value(s: Optional[pd.Series]) -> Optional[float]:
    if s is None:
        return None
    x = s.dropna()
    if x.empty:
        return None
    return float(x.iloc[-1])

def pct_change(s: Optional[pd.Series], periods: int = 1) -> Optional[float]:
    if s is None:
        return None
    x = s.dropna()
    if len(x) <= periods:
        return None
    prev = float(x.iloc[-periods-1])
    cur = float(x.iloc[-1])
    if prev == 0:
        return None
    return (cur / prev - 1.0) * 100.0

def get_treasury_debt_to_penny() -> float:
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    params = {"sort": "-record_date", "page[size]": "1", "fields": "record_date,total_public_debt_outstanding"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    return float(data["data"][0]["total_public_debt_outstanding"])
