# Capra Trader

A stock analysis and picker web application backed by a Python Flask API using live market data.

## Overview

Capra Trader provides:
- **Stock Analyzer** — Enter any ticker for real-time price, stop-loss/target, P/E ratio, market cap, 52-week range, volume, and a 6-month price chart
- **Stock Picker** — Momentum-scored picks (top 3) based on holding period and risk tolerance, with custom duration support
- **Portfolio** — Track holdings with live gain/loss tracking, stored in localStorage
- **Market Movers Sidebar** — Live gainers and decliners fetched on page load

## Features

1. **Portfolio tab** — Add stocks with buy price and shares; see live gain/loss per holding and portfolio total. Stored in localStorage.
2. **Expanded quote data** — Market cap, P/E ratio, 52-week high/low with visual range bar, and daily volume from yfinance.
3. **Tooltip popups** — Hover over terms like "Stop Loss", "Target Price", "P/E Ratio", "Market Cap", "Volume", "52-Week Range", and "Algorithm Score" for plain-English definitions.
4. **First-visit onboarding modal** — 3-step walkthrough shown once; dismissal stored in localStorage.
5. **Improved animations** — Cards fade and slide up on load with staggered delays; price/stop-loss/target numbers count up with eased animation.
6. **Mobile responsive** — Fixed bottom navigation bar on screens ≤640px for Analyze, Picks, Portfolio, and Movers tabs. Movers shown in a slide-up sheet on mobile.
7. **Custom holding period** — "Custom duration…" option reveals a text input; parses formats like "45 days", "3 weeks", "2 months" and passes the equivalent day count to the backend.

## Architecture

- **Frontend**: Single-page HTML (`index.html`) — all HTML, CSS, JavaScript in one file
- **Backend**: Python Flask (`main.py`) serving both the HTML and REST API
- **Data source**: `yfinance` for real-time and historical stock data

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/quote?ticker=AAPL` | GET | Price, change, high/low, company name, sector, market cap, P/E, 52w range, volume |
| `/api/candles?ticker=AAPL` | GET | 6-month daily close prices and dates |
| `/api/picks?period=short&risk=moderate&days=0` | GET | Top 3 momentum-scored picks; pass `days=N` for custom period |
| `/api/movers` | GET | Live market gainers and decliners |

### Python Dependencies

- `flask` + `flask-cors` — web server and CORS
- `yfinance` — Yahoo Finance market data

## Development

```bash
python main.py
```

Runs on `0.0.0.0:5000`. Flask serves `index.html` at `/` and the API at `/api/*`.

## Deployment

Configured as **autoscale** deployment running `python main.py`.
