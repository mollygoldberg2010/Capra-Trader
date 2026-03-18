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
        hist = t.history(period='3mo')
        if hist.empty or len(hist) < 1:
            return jsonify({'error': f'No data found for {ticker}'}), 404

        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        # 1-month and 3-month trend
        price_1mo_ago = float(hist['Close'].iloc[-22]) if len(hist) >= 22 else float(hist['Close'].iloc[0])
        price_3mo_ago = float(hist['Close'].iloc[0])
        trend_1mo = ((current_price - price_1mo_ago) / price_1mo_ago) * 100
        trend_3mo = ((current_price - price_3mo_ago) / price_3mo_ago) * 100

        # 52-week position
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
        company_name = info.get('longName') or info.get('shortName') or NAME_MAP.get(ticker, ticker)
        sector = info.get('sector') or SECTOR_MAP.get(ticker, 'Unknown')
        market_cap = info.get('marketCap')
        pe_raw = info.get('trailingPE') or info.get('forwardPE')
        pe_ratio = round(float(pe_raw), 2) if pe_raw and str(pe_raw) != 'nan' else None
        week52_high = info.get('fiftyTwoWeekHigh') or week52_high_calc
        week52_low  = info.get('fiftyTwoWeekLow')  or week52_low_calc
        volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else info.get('volume')

        # Analyst recommendation
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

        # Revenue growth
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

        # Build outlook signals
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

        # Overall outlook
        if len(signals_positive) >= 2:
            overall = 'bullish'
        elif len(signals_negative) >= 2:
            overall = 'bearish'
        else:
            overall = 'mixed'

        # Build plain-English outlook paragraph
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

        # Beginner-friendly version
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

            # --- Analytics ---
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