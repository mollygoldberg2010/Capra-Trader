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
    "MCD": "McDonald's", "LLY": "Eli Lilly", "BABA": "Alibaba","MS": "Morgan Stanley", "COP": "ConocoPhillips", "NKE": "Nike",
    "WMT": "Walmart", "COST": "Costco", "COIN": "Coinbase",
    "SQ": "Block", "SHOP": "Shopify", "SNAP": "Snap",
    "RBLX": "Roblox", "PLTR": "Palantir", "RIVN": "Rivian",
    "LCID": "Lucid Motors", "MRK": "Merck", "BRK-B": "Berkshire Hathaway",
    "SPOT": "Spotify",
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
    "LLY": "Healthcare", "BABA": "Consumer Cyclical","MS": "Financial Services", "COP": "Energy", "NKE": "Consumer Cyclical",
    "WMT": "Consumer Defensive", "COST": "Consumer Defensive",
    "COIN": "Financial Services", "SQ": "Financial Services",
    "SHOP": "Consumer Cyclical", "SNAP": "Communication Services",
    "RBLX": "Communication Services", "PLTR": "Technology",
    "RIVN": "Consumer Cyclical", "LCID": "Consumer Cyclical",
    "MRK": "Healthcare", "BRK-B": "Financial Services",
    "SPOT": "Communication Services",
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
        hist = t.history(period='3mo')
        if hist.empty or len(hist) < 1:
            return jsonify({'error': f'No data found for {ticker}'}), 404

        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        price_1mo_ago = float(hist['Close'].iloc[-22]) if len(hist) >= 22 else float(hist['Close'].iloc[0])
        price_3mo_ago = float(hist['Close'].iloc[0])
        trend_1mo = ((current_price - price_1mo_ago) / price_1mo_ago) * 100
        trend_3mo = ((current_price - price_3mo_ago) / price_3mo_ago) * 100

        hist_1y = t.history(period='1y')
        week52_high_calc = float(hist_1y['High'].max()) if not hist_1y.empty else current_price
        week52_low_calc  = float(hist_1y['Low'].min())  if not hist_1y.empty else current_price
        w52_range = week52_high_calc - week52_low_calc
        w52_position = ((current_price - week52_low_calc) / w52_range * 100) if w52_range > 0 else 50
        if w52_position > 80:
            w52_label = 'near its 52-week high'
        elif w52_position < 20:
            w52_label = 'near its 52-week low'
        else:
            w52_label = 'in the middle of its 52-week range'

        info = t.info
        # Fetch recent news
        try:
            news_items = t.news or []
            news = []
            for item in news_items[:3]:
                title = item.get('title', '')
                if title:
                    news.append(title)
        except Exception:
            news = []
        company_name = info.get('longName') or info.get('shortName') or NAME_MAP.get(ticker, ticker)
        sector = info.get('sector') or SECTOR_MAP.get(ticker, 'Unknown')
        market_cap = info.get('marketCap')
        pe_raw = info.get('trailingPE') or info.get('forwardPE')
        pe_ratio = round(float(pe_raw), 2) if pe_raw and str(pe_raw) != 'nan' else None
        week52_high = info.get('fiftyTwoWeekHigh') or week52_high_calc
        week52_low  = info.get('fiftyTwoWeekLow')  or week52_low_calc
        volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else info.get('volume')

        rec_key = info.get('recommendationKey', '').lower()
        if rec_key in ('strong_buy', 'buy'):
            analyst_text = 'Most Wall Street analysts rate it a Buy'
            analyst_signal = 'positive'
        elif rec_key in ('sell', 'strong_sell', 'underperform'):
            analyst_text = 'Most Wall Street analysts rate it a Sell'
            analyst_signal = 'negative'
        elif rec_key in ('hold', 'neutral'):
            analyst_text = 'Most Wall Street analysts rate it a Hold'
            analyst_signal = 'neutral'
        else:
            analyst_text = None
            analyst_signal = 'neutral'

        rev_growth = info.get('revenueGrowth')
        if rev_growth and rev_growth > 0.05:
            rev_text = f'The company has shown strong revenue growth of {round(rev_growth*100,1)}% recently'
            rev_signal = 'positive'
        elif rev_growth and rev_growth < -0.05:
            rev_text = f'Revenue has been declining by {abs(round(rev_growth*100,1))}% recently'
            rev_signal = 'negative'
        else:
            rev_text = None
            rev_signal = 'neutral'

        signals_positive = []
        signals_negative = []
        signals_neutral  = []

        if trend_1mo > 3:
            signals_positive.append(f'up {round(trend_1mo,1)}% over the past month')
        elif trend_1mo < -3:
            signals_negative.append(f'down {abs(round(trend_1mo,1))}% over the past month')
        else:
            signals_neutral.append(f'roughly flat over the past month ({round(trend_1mo,1)}%)')

        if trend_3mo > 5:
            signals_positive.append(f'up {round(trend_3mo,1)}% over 3 months')
        elif trend_3mo < -5:
            signals_negative.append(f'down {abs(round(trend_3mo,1))}% over 3 months')

        if analyst_signal == 'positive' and analyst_text:
            signals_positive.append(analyst_text)
        elif analyst_signal == 'negative' and analyst_text:
            signals_negative.append(analyst_text)

        if rev_signal == 'positive' and rev_text:
            signals_positive.append(rev_text)
        elif rev_signal == 'negative' and rev_text:
            signals_negative.append(rev_text)

        if len(signals_positive) >= 2:
            overall = 'bullish'
        elif len(signals_negative) >= 2:
            overall = 'bearish'
        else:
            overall = 'mixed'

        all_signals = signals_positive + signals_negative + signals_neutral
        if all_signals:
            outlook_para = f"{company_name} has been {', '.join(all_signals[:2])}. "
        else:
            outlook_para = f"{company_name} is currently {w52_label}. "

        if analyst_text and analyst_text not in outlook_para:
            outlook_para += f"{analyst_text}. "
        if rev_text and rev_text not in outlook_para:
            outlook_para += f"{rev_text}. "
        outlook_para += f"The stock is currently {w52_label}."
        if overall == 'bullish':
            outlook_para += ' These signals suggest positive momentum overall.'
        elif overall == 'bearish':
            outlook_para += ' These signals suggest caution is warranted.'
        else:
            outlook_para += ' The overall picture is mixed — worth watching closely.'

        if trend_1mo > 3:
            beginner_trend = f"its price has been going up lately — {round(trend_1mo,1)}% higher than a month ago"
        elif trend_1mo < -3:
            beginner_trend = f"its price has been falling lately — down {abs(round(trend_1mo,1))}% from a month ago"
        else:
            beginner_trend = "its price has been fairly stable over the past month"

        if analyst_signal == 'positive':
            beginner_analyst = "Professional investors who study this stock for a living mostly recommend buying it"
        elif analyst_signal == 'negative':
            beginner_analyst = "Professional investors who study this stock mostly recommend selling it"
        else:
            beginner_analyst = "Professional investors are split — some say buy, some say wait"

        if w52_position > 80:
            beginner_w52 = "It is near its highest price of the past year, which means it has been doing well but may have less room to grow"
        elif w52_position < 20:
            beginner_w52 = "It is near its lowest price of the past year — it has dropped a lot, which could be a risk or an opportunity depending on why"
        else:
            beginner_w52 = "Its price is somewhere in the middle compared to the past year — not unusually high or low"

        beginner_outlook = f"Here is what the data says about why this stock might go up or down: {beginner_trend}. {beginner_analyst}. {beginner_w52}."

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
            'trend1mo': round(trend_1mo, 1),
            'trend3mo': round(trend_3mo, 1),
            'outlookPara': outlook_para,
            'beginnerOutlook': beginner_outlook,
            'overallOutlook': overall,
            'analystText': analyst_text,
            'w52Label': w52_label,
            'news': news,
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
                daily_rets = prices.pct_change().dropna()
                ret = float((prices.iloc[-1] / prices.iloc[-lb] - 1) * 100)
                vol = float(daily_rets.std() * 100)
                score = ret - (vol * risk_sensitivity)
                scored.append((ticker, current_price, ret, vol, score, lb, daily_rets))
            except Exception:
                continue

        if not scored:
            return jsonify({'error': 'Could not score stocks'}), 500

        scored.sort(key=lambda x: x[4], reverse=True)
        top3 = scored[:3]
        result_picks = []
        for ticker, price, ret, vol, raw_score, lb, daily_rets in top3:
            stop = round(price * (1 - stop_pct), 2)
            target = round(price * (1 + target_pct), 2)
            normalized = min(99, max(45, int(60 + raw_score * 1.5)))
            avg_daily = float(daily_rets.mean() * 100)
            avg_weekly = round(avg_daily * 5, 2)
            lb_rets = daily_rets.iloc[-lb:] if len(daily_rets) >= lb else daily_rets
            pct_positive = float((lb_rets > 0).mean() * 100)
            vol_label = 'Low' if vol < 1.5 else ('Medium' if vol < 3.0 else 'High')
            trend = 'Rising' if ret > 5 else ('Falling' if ret < -5 else 'Flat')
            confidence = 'Strong' if pct_positive > 56 else ('Moderate' if pct_positive >= 50 else 'Weak')
            weeks = max(1, lb // 5)
            period_str = f"{weeks} week{'s' if weeks != 1 else ''}"
            move_word  = 'grew' if ret > 0 else 'declined'
            swing_word = 'low' if vol_label == 'Low' else ('moderate' if vol_label == 'Medium' else 'elevated')
            trend_word = 'rising' if trend == 'Rising' else ('flat' if trend == 'Flat' else 'declining')
            fit_word   = 'strong' if raw_score > 5 else ('solid' if raw_score > 0 else 'speculative')
            company = NAME_MAP.get(ticker, ticker)
            rationale = (
                f"{company} {move_word} {abs(round(ret, 1))}% over the past {period_str} with "
                f"{swing_word} price swings ({round(vol, 1)}% daily volatility). "
                f"Its price trend has been {trend_word}, with {round(pct_positive, 0):.0f}% of "
                f"trading days moving positively — making it a {fit_word} fit for a {risk} strategy."
            )
            result_picks.append({
                'ticker': ticker,
                'companyName': company,
                'sector': SECTOR_MAP.get(ticker, 'Unknown'),
                'price': round(price, 2),
                'changePct': round(ret / max(lb, 1), 2),
                'stopLoss': stop,
                'targetPrice': target,
                'score': normalized,
                'rationale': rationale,
                'avgWeeklyReturn': avg_weekly,
                'volatility': round(vol, 2),
                'volatilityLabel': vol_label,
                'trendDirection': trend,
                'consistency': round(pct_positive, 1),
                'confidence': confidence,
                'totalReturn': round(ret, 1),
                'lookbackDays': lb,
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
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; BloomStocks/1.0)'}
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
        up = [{'t': t, 'n': NAME_MAP.get(t, t), 'c': f'+{v:.2f}%'} for t, v in sorted_items if v >= 0][:5]
        down = [{'t': t, 'n': NAME_MAP.get(t, t), 'c': f'{v:.2f}%'} for t, v in sorted_items if v < 0][:5]
        return jsonify({'up': up, 'down': down})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/heatmap')
def heatmap():
    tickers = [
        {"t": "AAPL", "n": "Apple", "s": "Technology"},
        {"t": "MSFT", "n": "Microsoft", "s": "Technology"},
        {"t": "NVDA", "n": "Nvidia", "s": "Technology"},
        {"t": "META", "n": "Meta", "s": "Technology"},
        {"t": "GOOG", "n": "Alphabet", "s": "Technology"},
        {"t": "AMD", "n": "AMD", "s": "Technology"},
        {"t": "ADBE", "n": "Adobe", "s": "Technology"},
        {"t": "CRM", "n": "Salesforce", "s": "Technology"},
        {"t": "ORCL", "n": "Oracle", "s": "Technology"},
        {"t": "INTC", "n": "Intel", "s": "Technology"},
        {"t": "QCOM", "n": "Qualcomm", "s": "Technology"},
        {"t": "CSCO", "n": "Cisco", "s": "Technology"},
        {"t": "AMZN", "n": "Amazon", "s": "Consumer"},
        {"t": "TSLA", "n": "Tesla", "s": "Consumer"},
        {"t": "MCD", "n": "McDonald's", "s": "Consumer"},
        {"t": "SBUX", "n": "Starbucks", "s": "Consumer"},
        {"t": "NKE", "n": "Nike", "s": "Consumer"},
        {"t": "TGT", "n": "Target", "s": "Consumer"},
        {"t": "WMT", "n": "Walmart", "s": "Consumer"},
        {"t": "COST", "n": "Costco", "s": "Consumer"},
        {"t": "JNJ", "n": "J&J", "s": "Healthcare"},
        {"t": "UNH", "n": "UnitedHealth", "s": "Healthcare"},
        {"t": "PFE", "n": "Pfizer", "s": "Healthcare"},
        {"t": "ABBV", "n": "AbbVie", "s": "Healthcare"},
        {"t": "MRK", "n": "Merck", "s": "Healthcare"},
        {"t": "LLY", "n": "Eli Lilly", "s": "Healthcare"},
        {"t": "AMGN", "n": "Amgen", "s": "Healthcare"},
        {"t": "MRNA", "n": "Moderna", "s": "Healthcare"},
        {"t": "JPM", "n": "JPMorgan", "s": "Finance"},
        {"t": "BAC", "n": "Bank of America", "s": "Finance"},
        {"t": "GS", "n": "Goldman Sachs", "s": "Finance"},
        {"t": "V", "n": "Visa", "s": "Finance"},
        {"t": "MA", "n": "Mastercard", "s": "Finance"},
        {"t": "PYPL", "n": "PayPal", "s": "Finance"},
        {"t": "MS", "n": "Morgan Stanley", "s": "Finance"},
        {"t": "XOM", "n": "ExxonMobil", "s": "Energy"},
        {"t": "CVX", "n": "Chevron", "s": "Energy"},
        {"t": "COP", "n": "ConocoPhillips", "s": "Energy"},
        {"t": "CAT", "n": "Caterpillar", "s": "Industrials"},
        {"t": "HON", "n": "Honeywell", "s": "Industrials"},
        {"t": "BA", "n": "Boeing", "s": "Industrials"},
        {"t": "GE", "n": "GE Aerospace", "s": "Industrials"},
        {"t": "LMT", "n": "Lockheed Martin", "s": "Industrials"},
        {"t": "NFLX", "n": "Netflix", "s": "Communication"},
        {"t": "DIS", "n": "Disney", "s": "Communication"},
        {"t": "UBER", "n": "Uber", "s": "Communication"},
        {"t": "SPOT", "n": "Spotify", "s": "Communication"},
        {"t": "BRK-B", "n": "Berkshire", "s": "Finance"},
        {"t": "TMO", "n": "Thermo Fisher", "s": "Healthcare"},
        {"t": "TXN", "n": "Texas Instruments", "s": "Technology"},
    ]
    ticker_list = [t["t"] for t in tickers]
    try:
        data = yf.download(ticker_list, period="2d", interval="1d", progress=False, auto_adjust=True)
        closes = data["Close"] if "Close" in data.columns else data
        results = []
        for item in tickers:
            t = item["t"]
            try:
                prices = closes[t].dropna()
                if len(prices) >= 2:
                    chg = ((float(prices.iloc[-1]) / float(prices.iloc[-2])) - 1) * 100
                    price = float(prices.iloc[-1])
                elif len(prices) == 1:
                    chg = 0
                    price = float(prices.iloc[-1])
                else:
                    continue
                MC_WEIGHTS = {
                    "AAPL": 100, "MSFT": 95, "NVDA": 90, "AMZN": 85, "GOOG": 80,
                    "META": 75, "TSLA": 60, "BRK-B": 70, "LLY": 65, "V": 62,
                    "JPM": 60, "UNH": 58, "MA": 55, "XOM": 52, "ORCL": 50,
                    "JNJ": 48, "COST": 47, "WMT": 46, "ABBV": 44, "NFLX": 43,
                    "CRM": 42, "BAC": 41, "MRK": 40, "ADBE": 39, "GS": 38,
                    "AMD": 37, "QCOM": 36, "TXN": 35, "HON": 34, "CAT": 33,
                    "MS": 32, "TMO": 31, "GE": 30, "LMT": 29, "CVX": 28,
                    "CSCO": 27, "AMGN": 26, "INTC": 25, "BA": 24, "DIS": 23,
                    "UBER": 22, "SBUX": 21, "MCD": 20, "PFE": 19, "COP": 18,
                    "MRNA": 17, "NKE": 16, "TGT": 15, "SPOT": 14, "PYPL": 13,
                }
                weight = MC_WEIGHTS.get(t, 20)
                results.append({
                    "ticker": t,
                    "name": item["n"],
                    "sector": item["s"],
                    "price": round(price, 2),
                    "changePct": round(chg, 2),
                    "weight": weight,
                })
            except Exception:
                continue
        return jsonify({"stocks": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/daytrading')
def daytrading():
    SCAN_TICKERS = [
        "AAPL", "MSFT", "NVDA", "META", "AMZN", "TSLA", "GOOG", "AMD",
        "NFLX", "CRM", "ADBE", "UBER", "PYPL", "INTC", "QCOM", "CSCO",
        "JPM", "BAC", "GS", "V", "MA", "MS",
        "JNJ", "PFE", "LLY", "ABBV", "UNH", "MRNA", "AMGN",
        "XOM", "CVX", "COP",
        "CAT", "HON", "GE", "BA", "LMT",
        "DIS", "NFLX", "SPOT",
        "WMT", "COST", "TGT", "NKE", "SBUX", "MCD",
        "COIN", "SQ", "SHOP", "SNAP", "RBLX", "PLTR", "RIVN", "LCID",
    ]

    try:
        data = yf.download(SCAN_TICKERS, period="10d", interval="1d", progress=False, auto_adjust=True)
        closes = data["Close"] if "Close" in data.columns else data
        volumes = data["Volume"] if "Volume" in data.columns else None

        results = []
        for ticker in SCAN_TICKERS:
            try:
                if ticker not in closes.columns:
                    continue
                prices = closes[ticker].dropna()
                if len(prices) < 5:
                    continue

                current = float(prices.iloc[-1])
                prev    = float(prices.iloc[-2])
                overnight_chg = ((current - prev) / prev) * 100

                # Multi-day winning streak
                streak = 0
                for i in range(len(prices) - 1, 0, -1):
                    if prices.iloc[i] > prices.iloc[i - 1]:
                        streak += 1
                    else:
                        break

                # 5-day return
                ret_5d = ((current - float(prices.iloc[-5])) / float(prices.iloc[-5])) * 100

                # Volume spike
                vol_spike_ratio = None
                if volumes is not None and ticker in volumes.columns:
                    vols = volumes[ticker].dropna()
                    if len(vols) >= 5:
                        avg_vol = float(vols.iloc[-6:-1].mean())
                        today_vol = float(vols.iloc[-1])
                        if avg_vol > 0:
                            vol_spike_ratio = round(today_vol / avg_vol, 2)

                # Scoring: weight overnight move, streak, volume
                score = 0
                if overnight_chg > 1:   score += overnight_chg * 2
                if streak >= 3:          score += streak * 3
                if vol_spike_ratio and vol_spike_ratio > 1.5: score += (vol_spike_ratio - 1) * 5
                if ret_5d > 5:           score += ret_5d * 0.5

                # Only include if positive momentum
                if overnight_chg < 0.3 and streak < 2:
                    continue

                company = NAME_MAP.get(ticker, ticker)

                # Signal explanations
                signals = []
                beginner_signals = []

                if overnight_chg >= 2:
                    signals.append(f"jumped +{round(overnight_chg,1)}% overnight")
                    beginner_signals.append(f"its price jumped {round(overnight_chg,1)}% since yesterday — a big overnight move that day traders watch closely")
                elif overnight_chg >= 0.5:
                    signals.append(f"up +{round(overnight_chg,1)}% from yesterday")
                    beginner_signals.append(f"it rose {round(overnight_chg,1)}% since yesterday's close — a positive start")

                if streak >= 4:
                    signals.append(f"{streak}-day winning streak")
                    beginner_signals.append(f"it has gone up {streak} days in a row — that kind of consistent momentum is what day traders look for")
                elif streak >= 2:
                    signals.append(f"up {streak} days in a row")
                    beginner_signals.append(f"it has risen for {streak} straight days, showing consistent upward pressure")

                if vol_spike_ratio and vol_spike_ratio >= 2:
                    signals.append(f"volume {round(vol_spike_ratio,1)}x above average")
                    beginner_signals.append(f"it is being traded {round(vol_spike_ratio,1)}x more than usual today — heavy trading activity often means something important is happening")
                elif vol_spike_ratio and vol_spike_ratio >= 1.4:
                    signals.append(f"volume {round(vol_spike_ratio,1)}x normal")
                    beginner_signals.append(f"more people than usual are buying and selling it today — elevated activity can signal a move is building")

                if ret_5d >= 8:
                    signals.append(f"+{round(ret_5d,1)}% over 5 days")
                    beginner_signals.append(f"it has climbed {round(ret_5d,1)}% over the past week — strong recent momentum")

                if not signals:
                    continue

                results.append({
                    "ticker": ticker,
                    "companyName": company,
                    "sector": SECTOR_MAP.get(ticker, "Unknown"),
                    "price": round(current, 2),
                    "overnightChg": round(overnight_chg, 2),
                    "streak": streak,
                    "ret5d": round(ret_5d, 1),
                    "volSpikeRatio": vol_spike_ratio,
                    "score": round(score, 1),
                    "signals": signals,
                    "beginnerSignals": beginner_signals,
                })
            except Exception:
                continue

        results.sort(key=lambda x: x["score"], reverse=True)
        return jsonify({"picks": results[:8]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)