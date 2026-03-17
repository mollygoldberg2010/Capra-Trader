import random
import requests as req_lib
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

NAME_MAP = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOG": "Alphabet", "AMZN": "Amazon",
    "TSLA": "Tesla", "NVDA": "Nvidia", "META": "Meta", "INTC": "Intel",
    "AMD": "AMD", "CRM": "Salesforce", "ORCL": "Oracle", "ADBE": "Adobe",
    "PYPL": "PayPal", "NFLX": "Netflix", "QCOM": "Qualcomm", "TXN": "Texas Instruments",
    "CSCO": "Cisco", "UBER": "Uber", "JNJ": "Johnson & Johnson", "PFE": "Pfizer",
    "MRNA": "Moderna", "UNH": "UnitedHealth", "ABBV": "AbbVie", "AMGN": "Amgen",
    "TMO": "Thermo Fisher", "JPM": "JPMorgan Chase", "BAC": "Bank of America",
    "GS": "Goldman Sachs", "V": "Visa", "MA": "Mastercard", "XOM": "ExxonMobil",
    "CVX": "Chevron", "CAT": "Caterpillar", "HON": "Honeywell", "GE": "GE Aerospace",
    "LMT": "Lockheed Martin", "BA": "Boeing", "DIS": "Disney", "SBUX": "Starbucks",
    "MCD": "McDonald's", "LLY": "Eli Lilly", "BABA": "Alibaba",
}

SECTOR_MAP = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOG": "Technology",
    "AMZN": "Consumer Cyclical", "TSLA": "Consumer Cyclical", "NVDA": "Technology",
    "META": "Technology", "INTC": "Technology", "AMD": "Technology", "CRM": "Technology",
    "ORCL": "Technology", "ADBE": "Technology", "PYPL": "Financial Services",
    "NFLX": "Communication Services", "QCOM": "Technology", "TXN": "Technology",
    "CSCO": "Technology", "UBER": "Technology", "JNJ": "Healthcare", "PFE": "Healthcare",
    "MRNA": "Healthcare", "UNH": "Healthcare", "ABBV": "Healthcare", "AMGN": "Healthcare",
    "TMO": "Healthcare", "JPM": "Financial Services", "BAC": "Financial Services",
    "GS": "Financial Services", "V": "Financial Services", "MA": "Financial Services",
    "XOM": "Energy", "CVX": "Energy", "CAT": "Industrials", "HON": "Industrials",
    "GE": "Industrials", "LMT": "Industrials", "BA": "Industrials",
    "DIS": "Communication Services", "SBUX": "Consumer Cyclical", "MCD": "Consumer Defensive",
    "LLY": "Healthcare", "BABA": "Consumer Cyclical",
}

MOVER_TICKERS = ["NVDA", "META", "AMZN", "LLY", "MSFT", "TSLA", "INTC", "PYPL", "DIS", "PFE"]


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/quote')
def quote():
    ticker = request.args.get('ticker', '').upper().strip()
    if not ticker:
        return jsonify({'error': 'ticker is required'}), 400
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period='5d')
        if hist.empty or len(hist) < 1:
            return jsonify({'error': f'No data found for {ticker}'}), 404

        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        info = t.info
        company_name = info.get('longName') or info.get('shortName') or NAME_MAP.get(ticker, ticker)
        sector = info.get('sector') or SECTOR_MAP.get(ticker, 'Unknown')

        market_cap = info.get('marketCap')
        pe_raw = info.get('trailingPE') or info.get('forwardPE')
        pe_ratio = round(float(pe_raw), 2) if pe_raw and str(pe_raw) != 'nan' else None
        week52_high = info.get('fiftyTwoWeekHigh')
        week52_low = info.get('fiftyTwoWeekLow')
        volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else info.get('volume')

        return jsonify({
            'price': round(current_price, 2),
            'change': round(change, 2),
            'changePct': round(change_pct, 2),
            'high': round(float(hist['High'].iloc[-1]), 2),
            'low': round(float(hist['Low'].iloc[-1]), 2),
            'companyName': company_name,
            'sector': sector,
            'marketCap': int(market_cap) if market_cap else None,
            'peRatio': pe_ratio,
            'week52High': round(float(week52_high), 2) if week52_high else None,
            'week52Low': round(float(week52_low), 2) if week52_low else None,
            'volume': int(volume) if volume else None,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/candles')
def candles():
    ticker = request.args.get('ticker', '').upper().strip()
    if not ticker:
        return jsonify({'error': 'ticker is required'}), 400
    try:
        hist = yf.Ticker(ticker).history(period='6mo', interval='1d')
        if hist.empty:
            return jsonify({'error': f'No candle data for {ticker}'}), 404

        dates = [d.strftime('%-m/%-d') for d in hist.index]
        closes = [round(float(c), 2) for c in hist['Close']]
        return jsonify({'dates': dates, 'closes': closes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/picks')
def picks():
    period = request.args.get('period', 'medium')
    risk = request.args.get('risk', 'moderate')
    custom_days = request.args.get('days', type=int, default=0)

    risk_sensitivity = {'conservative': 2.0, 'moderate': 1.2, 'aggressive': 0.6}.get(risk, 1.2)
    stop_pct = {'conservative': 0.02, 'moderate': 0.05, 'aggressive': 0.10}.get(risk, 0.05)
    target_pct = {'conservative': 0.04, 'moderate': 0.10, 'aggressive': 0.20}.get(risk, 0.10)

    effective_days = custom_days if custom_days > 0 else 0

    if period == 'short' or (0 < effective_days <= 30):
        pool = ["AAPL", "MSFT", "NVDA", "META", "AMZN", "TSLA", "AMD", "CRM", "NFLX", "QCOM"]
    elif period == 'long' or (effective_days > 90):
        pool = ["AAPL", "MSFT", "JNJ", "UNH", "V", "MA", "JPM", "XOM", "HON", "LLY"]
    else:
        pool = ["AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOG", "V", "JPM", "UNH", "ADBE"]

    if effective_days > 0:
        if effective_days <= 30:
            yf_period = '1mo'
        elif effective_days <= 90:
            yf_period = '3mo'
        elif effective_days <= 180:
            yf_period = '6mo'
        elif effective_days <= 365:
            yf_period = '1y'
        else:
            yf_period = '2y'
        lookback_default = effective_days
    else:
        yf_period = '3mo'
        lookback_default = 22

    sample = random.sample(pool, min(8, len(pool)))

    try:
        data = yf.download(sample, period=yf_period, interval='1d', progress=False, auto_adjust=True)
        if data.empty:
            return jsonify({'error': 'Could not fetch market data'}), 500

        closes = data['Close'] if 'Close' in data.columns else data

        scored = []
        for ticker in sample:
            try:
                if ticker not in closes.columns:
                    continue
                prices = closes[ticker].dropna()
                if len(prices) < 5:
                    continue
                current_price = float(prices.iloc[-1])
                lb = min(lookback_default, len(prices) - 1)
                ret = float((prices.iloc[-1] / prices.iloc[-lb] - 1) * 100)
                vol = float(prices.pct_change().std() * 100)
                score = ret - (vol * risk_sensitivity)
                scored.append((ticker, current_price, ret, vol, score, lb))
            except Exception:
                continue

        if not scored:
            return jsonify({'error': 'Could not score stocks'}), 500

        scored.sort(key=lambda x: x[4], reverse=True)
        top3 = scored[:3]

        result_picks = []
        for ticker, price, ret, vol, raw_score, lb in top3:
            stop = round(price * (1 - stop_pct), 2)
            target = round(price * (1 + target_pct), 2)
            normalized = min(99, max(45, int(60 + raw_score * 1.5)))
            result_picks.append({
                'ticker': ticker,
                'companyName': NAME_MAP.get(ticker, ticker),
                'sector': SECTOR_MAP.get(ticker, 'Unknown'),
                'price': round(price, 2),
                'changePct': round(ret / max(lb, 1), 2),
                'stopLoss': stop,
                'targetPrice': target,
                'score': normalized,
                'rationale': (
                    f"{round(ret, 1)}% return over the past {lb} trading days with "
                    f"{round(vol, 2)}% daily volatility — a "
                    f"{'strong' if raw_score > 5 else 'solid'} fit for a {risk} strategy."
                ),
            })

        return jsonify({'picks': result_picks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []})
    try:
        url = (
            f'https://query2.finance.yahoo.com/v1/finance/search'
            f'?q={q}&quotesCount=8&newsCount=0&enableFuzzyQuery=false'
        )
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; CapraTrader/1.0)'}
        resp = req_lib.get(url, headers=headers, timeout=5)
        data = resp.json()
        quotes = data.get('quotes', [])
        results = []
        for item in quotes:
            symbol = item.get('symbol', '')
            name = item.get('longname') or item.get('shortname') or ''
            exchange = item.get('exchange', '')
            q_type = item.get('quoteType', '')
            if symbol and q_type in ('EQUITY', 'ETF', 'INDEX'):
                results.append({
                    'ticker': symbol,
                    'name': name,
                    'exchange': exchange,
                    'type': q_type,
                })
        return jsonify({'results': results[:7]})
    except Exception as e:
        return jsonify({'results': [], 'error': str(e)})


@app.route('/api/movers')
def movers():
    try:
        data = yf.download(MOVER_TICKERS, period='5d', interval='1d', progress=False, auto_adjust=True)
        if data.empty:
            return jsonify({'up': [], 'down': []}), 200

        closes = data['Close'] if 'Close' in data.columns else data

        changes = {}
        for t in MOVER_TICKERS:
            try:
                if t not in closes.columns:
                    continue
                prices = closes[t].dropna()
                if len(prices) >= 2:
                    chg = (float(prices.iloc[-1]) / float(prices.iloc[-2]) - 1) * 100
                    changes[t] = round(chg, 2)
            except Exception:
                continue

        sorted_items = sorted(changes.items(), key=lambda x: x[1], reverse=True)
        up = [
            {'t': t, 'n': NAME_MAP.get(t, t), 'c': f'+{v:.2f}%'}
            for t, v in sorted_items if v >= 0
        ][:5]
        down = [
            {'t': t, 'n': NAME_MAP.get(t, t), 'c': f'{v:.2f}%'}
            for t, v in sorted_items if v < 0
        ][:5]

        return jsonify({'up': up, 'down': down})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
