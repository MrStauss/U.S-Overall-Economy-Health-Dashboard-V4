from typing import List, Dict
import requests

def gdelt_latest(query: str = "US economy OR recession OR inflation OR jobs OR Federal Reserve", max_records: int = 12) -> List[Dict]:
    """Free, no-key headline pull from GDELT 2.1 DOC API."""
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "formatdatetime": "true",
        "maxrecords": str(max_records),
        "sort": "HybridRel",
        "sourcelang": "english",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    arts = data.get("articles", []) or []
    out: List[Dict] = []
    for a in arts:
        out.append({
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "source": a.get("sourceCountry", "") or a.get("source", ""),
            "seen": a.get("seendate", ""),
        })
    return out
