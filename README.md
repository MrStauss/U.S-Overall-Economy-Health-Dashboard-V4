# U.S. Overall Economy Health Dashboard (Streamlit)

## Features
- Dark/glass UI (CSS in `assets/style.css`)
- SPY, VTI, GLD market tracking + simple analytics
- US Economy Health Score (0-100)
- Jobs + inflation + rates + debt proxies via FRED
- Treasury “Debt to the Penny” snapshot
- Live-ish News feed via GDELT (no key)

## Setup
Add Streamlit secrets:

```toml
FRED_API_KEY = "YOUR_FRED_KEY"
```

## Versioning best practice
- Use Git tags: v0.1.0, v0.2.0...
- Use branches: main (stable), dev (work)
- Use GitHub Releases for changelog
