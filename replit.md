# Capra Trader

A stock analysis and picker web application backed by a Python Flask API using live market data.

## Overview

Capra Trader provides:
- **Stock Analyzer** — Enter any ticker for real-time price, stop-loss/target, P/E ratio, market cap, 52-week range, volume, and a 6-month price chart
- **Stock Picker** — Momentum-scored picks (top 3) based on holding period and risk tolerance, with custom duration support
- **Portfolio** — Track holdings with live gain/loss tracking, stored in localStorage
- **Market Movers Sidebar** — Live gainers and decliners fetched on page load

## Features

1. **Three experience modes** — Beginner, Intermediate, and Pro, each delivering a tailored UI. Chosen on first visit via a full-screen modal; stored in `localStorage` as `capra_mode`. A clickable pill in the header lets users switch at any time. Results re-render immediately when the mode changes.
2. **Portfolio tab** — Add stocks with buy price and shares; see live gain/loss per holding and portfolio total. Stored in localStorage.
3. **Expanded quote data** — Market cap, P/E ratio, 52-week high/low with visual range bar, and daily volume from yfinance.
4. **Tooltip popups** — Hover over terms for plain-English definitions (hidden in Pro mode).
5. **Autocomplete search** — Typing 2+ characters in the analyzer calls `/api/search` → Yahoo Finance symbol search; dropdown shows company name + ticker. Beginner mode shows company name prominently; Intermediate/Pro show ticker first.
6. **Improved animations** — Cards fade and slide up; numbers count up with eased animation.
7. **Mobile responsive** — Fixed bottom navigation bar on screens ≤640px; Movers in a slide-up sheet.
8. **Custom holding period** — Parses "45 days", "3 weeks", "2 months" etc.

## Mode Details

### 🌱 Beginner
- Intro paragraph explaining what a stock is shown above the search bar
- Search label reads "Company Name"; autocomplete shows company name large, ticker small/gray
- Results show plain-English narrative: "Right now, one share of Apple costs $X…"
- Only 3 metric cards: Current Price, Safety Net Price (Stop Loss), Goal Price (Target) — each with a one-sentence explanation directly underneath
- No P/E, market cap, volume, or volatility
- Picker intro uses plain language; results include a "How did we pick these?" section
- Glossary panel accessible via "What does this mean?" button (10 terms, plain English)

### 📈 Intermediate
- Standard labels with one-line explanations under each metric card
- Shows: price, stop loss, target, company size (market cap), 52-week range
- "Explain these results to me" toggle reveals a plain-English narrative
- Picker shows algorithm score + rationale per card
- Tooltips on hover for unfamiliar terms

### 💼 Pro
- Compact layout with all 6 metrics: price, stop loss, target, P/E, market cap, volume
- No explanations under metrics
- Strategy Insight box with concise technical summary
- Picker cards show full algorithm breakdown: return %, volatility level, risk sensitivity, final score
- No tooltips, no glossary, no plain-English walkthrough

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
