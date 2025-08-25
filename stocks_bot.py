import os
import yfinance as yf
import mplfinance as mpf
import requests
import pandas as pd
from telegram import Bot
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# === משתנים מהסביבה ===
TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")
bot = Bot(token=TOKEN)

CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'Arial'

# ===== ניקוי גרפים ישנים =====
def clean_old_charts(days=7):
    now = datetime.now()
    for file in os.listdir(CHARTS_DIR):
        path = os.path.join(CHARTS_DIR, file)
        if os.path.isfile(path):
            modified = datetime.fromtimestamp(os.path.getmtime(path))
            if now - modified > timedelta(days=days):
                os.remove(path)

# ===== כתיבה ללוג =====
def write_log(text):
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")

# ===== חדשות =====
def get_news(ticker):
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}"
    try:
        r = requests.get(url).json()
        if "news" in r and r["news"]:
            return r["news"][0]["title"]
    except:
        return "אין חדשות זמינות"
    return "אין חדשות זמינות"

# ===== חוות דעת אנליסטים =====
def get_analyst_opinion(ticker):
    try:
        stock = yf.Ticker(ticker)
        recs = stock.recommendations_summary
        if recs is None or recs.empty:
            return "אין נתוני אנליסטים"

        last = recs.iloc[-1].to_dict()
        buy = last.get("buy", 0)
        hold = last.get("hold", 0)
        sell = last.get("sell", 0)
        total = buy + hold + sell
        if total == 0:
            return "אין נתוני אנליסטים"

        buy_pct = round(buy/total*100)
        hold_pct = round(hold/total*100)
        sell_pct = round(sell/total*100)

        return f"קנייה: {buy_pct}% | החזקה: {hold_pct}% | מכירה: {sell_pct}%"
    except:
        return "אין נתוני אנליסטים"

# ===== גרף נרות =====
def generate_chart(ticker, entry, stop, tps):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="3mo", interval="1d")
    if hist.empty:
        return None

    # חישוב אינדיקטורים
    hist['MA20'] = hist['Close'].rolling(20).mean()
    hist['MA50'] = hist['Close'].rolling(50).mean()
    delta = hist['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    hist['RSI'] = 100 - (100 / (1 + rs))

    add_lines = [
        mpf.make_addplot([entry]*len(hist), color="blue", linestyle="--"),
        mpf.make_addplot([stop]*len(hist), color="red", linestyle="--"),
        mpf.make_addplot(hist['MA20'], color="orange"),
        mpf.make_addplot(hist['MA50'], color="purple"),
        mpf.make_addplot(hist['RSI'], panel=1, color="fuchsia", ylabel='RSI'),
    ]
    for i, tp in enumerate(tps):
        add_lines.append(mpf.make_addplot([tp]*len(hist), color="green", linestyle="--"))

    filepath = os.path.join(CHARTS_DIR, f"{ticker}.png")
    mpf.plot(hist, type="candle", style="yahoo",
             addplot=add_lines, volume=True,
             title=f"{ticker} - נרות + אינדיקטורים",
             ylabel="Price", ylabel_lower="Volume",
             savefig=filepath)
    return filepath

# ===== סורק מניות =====
def scan_stocks(limit=4, strict=True):
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)[0]
    tickers = table['Symbol'].tolist()

    selected = []
    for t in tickers:
        try:
            if "." in t: t = t.replace(".", "-")
            stock = yf.Ticker(t)
            hist = stock.history(period="10d", interval="1d")
            if len(hist) < 2: continue

            today, yesterday = hist.iloc[-1], hist.iloc[-2]
            change = (today['Close'] - yesterday['Close']) / yesterday['Close'] * 100
            avg_vol = hist['Volume'].tail(5).mean()
            unusual_vol = today['Volume'] > (2 * avg_vol if strict else 1.2 * avg_vol)

            if abs(change) >= (3 if strict else 2) and unusual_vol:
                entry = today['Close']
                stop = entry * 0.97
                tps = [entry*1.03, entry*1.05, entry*1.07, entry*1.1]
                selected.append({"ticker": t, "entry": round(entry,2), "stop": round(stop,2), "tps": [round(tp,2) for tp in tps], "change": round(change,2)})
        except:
            continue

    return selected[:limit]

# ===== שליחת דו"ח =====
def send_report():
    clean_old_charts(days=7)
    stocks = scan_stocks()
    if not stocks:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ לא נמצאו מניות בקריטריונים קשוחים – מחפש חלופיים...")
        stocks = scan_stocks(strict=False)

    if not stocks:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו מניות גם בקריטריונים חלופיים.")
        return

    for s in stocks:
        info = yf.Ticker(s['ticker']).info
        sector = info.get("sector", "N/A")
        market_cap = info.get("marketCap", "N/A")
        pe = info.get("trailingPE", "N/A")
        eps = info.get("trailingEps", "N/A")

        news = get_news(s['ticker'])
        analysts = get_analyst_opinion(s['ticker'])
        chart = generate_chart(s['ticker'], s['entry'], s['stop'], s['tps'])

        msg = f"""
📊 {info.get('shortName', s['ticker'])} ({s['ticker']})

💵 מחיר נוכחי: {s['entry']}$
🎯 כניסה: {s['entry']}$
🛑 סטופלוס: {s['stop']}$
✅ יעדים:
- TP1: {s['tps'][0]}$
- TP2: {s['tps'][1]}$
- TP3: {s['tps'][2]}$
- TP4: {s['tps'][3]}$

📐 שינוי יומי: {s['change']}%
🏷️ סקטור: {sector}
📰 חדשות: {news}
📊 אנליסטים: {analysts}

📈 פיננסים:
- Market Cap: {market_cap}
- EPS: {eps}
- P/E: {pe}

🔗 TradingView: https://www.tradingview.com/symbols/{s['ticker']}/

✅ סיכום: איתות מקצועי – מתאים לניהול סווינג.
"""
        bot.send_photo(chat_id=CHAT_ID, photo=open(chart, "rb"), caption=msg, parse_mode="Markdown")
        write_log(f"נשלח איתות עבור {s['ticker']}")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק מניות מקצועי התחיל לרוץ!")
    send_report()
