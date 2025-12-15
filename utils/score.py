from typing import Dict, Optional, List
import pandas as pd

def zscore_latest(s: Optional[pd.Series], window: int = 252) -> Optional[float]:
    if s is None:
        return None
    x = s.dropna()
    if x.empty:
        return None
    xw = x.iloc[-window:] if len(x) > window else x
    mu = float(xw.mean())
    sig = float(xw.std(ddof=0))
    if sig == 0:
        return None
    return (float(x.iloc[-1]) - mu) / sig

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def compute_us_health_score(fred: Dict[str, Optional[pd.Series]], prices_df: pd.DataFrame) -> Dict[str, object]:
    components: List[dict] = []

    def add_component(name: str, series: Optional[pd.Series], direction: int, weight: float, window: int):
        z = zscore_latest(series, window=window)
        if z is None:
            return
        zc = clamp(direction * z, -2.0, 2.0)
        score = int(round(((zc + 2.0) / 4.0) * 100.0))
        components.append({"name": name, "z": float(z), "score": score, "weight": float(weight)})

    add_component("Unemployment (UNRATE)", fred.get("UNRATE"), direction=-1, weight=0.16, window=60)
    add_component("Payrolls (PAYEMS)", fred.get("PAYEMS"), direction=+1, weight=0.14, window=60)
    add_component("Jobless Claims (ICSA)", fred.get("ICSA"), direction=-1, weight=0.10, window=104)

    add_component("CPI (CPIAUCSL)", fred.get("CPIAUCSL"), direction=-1, weight=0.10, window=60)
    add_component("Fed Funds (FEDFUNDS)", fred.get("FEDFUNDS"), direction=-1, weight=0.06, window=120)

    if "SPY" in prices_df.columns:
        add_component("SPY (price)", prices_df["SPY"], direction=+1, weight=0.10, window=252)
    if "VTI" in prices_df.columns:
        add_component("VTI (price)", prices_df["VTI"], direction=+1, weight=0.08, window=252)
    add_component("VIX (VIXCLS)", fred.get("VIXCLS"), direction=-1, weight=0.10, window=252)

    add_component("CC Delinq. (DRCCLACBS)", fred.get("DRCCLACBS"), direction=-1, weight=0.06, window=80)

    if not components:
        return {"score": 50, "components": []}

    total_w = sum(c["weight"] for c in components)
    score = sum(c["score"] * c["weight"] for c in components) / total_w
    return {"score": int(round(score)), "components": components}
