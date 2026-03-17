# Capra Trader

A stock analysis and picker web application backed by a Python Flask API using live market data.

## Overview

Capra Trader provides:
- **Stock Analyzer**: Enter any ticker to get real-time price, stop-loss/target levels, and a 6-month price chart
- **Stock Picker**: Get 3 AI-scored stock picks based on holding period and risk tolerance
- **Market Movers Sidebar**: Live gainers and decliners fetched on page load

## Architecture

- **Frontend**: Single-page HTML app (`index.html`) — all HTML, CSS, and JavaScript in one file
- **Backend**: Python Flask (`main.py`) serving both the HTML and REST API endpoints
- **Data source**: `yfinance` for real-time and historical stock market data

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/quote?ticker=AAPL` | GET | Current price, change, high/low, company name, sector |
| `/api/candles?ticker=AAPL` | GET | 6-month daily close prices and dates |
| `/api/picks?period=short&risk=moderate` | GET | Top 3 scored stock picks |
| `/api/movers` | GET | Live market gainers and decliners |

### External Dependencies (CDN)

- Chart.js 4.4.1 — price history and mini charts

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
