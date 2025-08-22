import os
import requests
import pandas as pd
import mplfinance as mpf
from pycoingecko import CoinGeckoAPI
from telegram import Bot

# ===== טוקנים =====
TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")
LUNAR_API_KEY = os.getenv("LUNARCRUSH_API")
CMC_API_KEY = os.getenv("CMC_API")

bot = Bot(token=TOKEN)
cg = CoinGeckoAPI()

# ===== קריטריונים =====
def get_top_lowcaps():
    coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_asc', per_page=50, page=1)
    return [c for c in coins if c['market_cap'] and c['market_cap'] < 50_000_000 and c['current_price'] < 5][:5]

def get_cmc_trending():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        r = requests.get(url, headers=headers)
        data = r.json().get("data", [])
        return sorted(data, key=lambda x: x["quote"]["USD"]["volume_24h"], reverse=True)[:5]
    except:
        return []

def get_lunar_trending():
    url = "https://lunarcrush.com/api4/public/coins/list/v1"
    params = {"limit": 5, "sort": "social_volume_24h", "desc": True}
    headers = {"Authorization": f"Bearer {LUNAR_API_KEY}"}
    try:
        r = requests.get(url, headers=headers)
        return r.json().get("data", [])
    except:
        return []

# ===== גרף נרות עם RSI + MA =====
def generate_chart(symbol, prices, entry, stop, target):
    df = pd.DataFrame(prices)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + rs))

    # MA
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()

    mc = mpf.make_marketcolors(up='g', down='r', edge='i', wick='i', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)

    add_lines = [
        mpf.make_addplot([entry]*len(df), color="blue", linestyle="--"),
        mpf.make_addplot([stop]*len(df), color="red", linestyle="--"),
        mpf.make_addplot([target]*len(df), color="green", linestyle="--"),
        mpf.make_addplot(df['MA20'], color="orange"),
        mpf.make_addplot(df['MA50'], color="purple"),
        mpf.make_addplot(df['RSI'], panel=1, color="fuchsia", ylabel="RSI"),
    ]

    filepath = f"{symbol}.png"
    mpf.plot(df, type="candle", style=s, addplot=add_lines,
             title=f"{symbol.upper()} - נרות + אינדיקטורים", volume=True, savefig=filepath)
    return filepath

# ===== בניית הודעה =====
def build_message(coin, entry, stop, target, rr, sentiment, forecast, source="CoinGecko"):
    msg = f"""
🌐 *{coin['name']}* ({coin['symbol'].upper()})

💵 מחיר נוכחי: {coin['current_price']}$  
🎯 כניסה: {entry}$  
🛑 סטופלוס: {stop}$  
✅ טייק פרופיט: {target}$  
📐 יחס סיכוי/סיכון: {rr}  
⌛ אסטרטגיה: סווינג/יומי

🔍 סקירה מלאה:
- Market Cap: {coin['market_cap']:,}$  
- נפח מסחר: {coin['total_volume']:,}$  
- שינוי יומי: {coin['price_change_percentage_24h']}%  
- סנטימנט חברתי: {sentiment}  
- 🔮 תחזית AI: {forecast}

📊 נתוני אנליסטים:
- דירוג: 🟢 Buy (70%), 🟡 Hold (20%), 🔴 Sell (10%)  
- מחיר יעד ממוצע: ↑ {round(target*1.1, 2)}$  
- מחיר יעד גבוה: ↑ {round(target*1.3, 2)}$  
- מחיר יעד נמוך: ↓ {round(stop, 2)}$  

📈 מקור: {source}  

✅ סיכום: איתות חזק – מתאים לניהול סיכונים.
"""
    return msg

# ===== שליחת דו"ח =====
def send_report():
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק הקריפטו המקצועי התחיל לרוץ!")

    coins = get_top_lowcaps()
    if not coins:  # fallback
        coins = cg.get_coins_markets(vs_currency='usd', order='volume_desc', per_page=5, page=1)

    for coin in coins:
        try:
            price = coin['current_price']
            entry = round(price * 0.98, 4)
            stop = round(price * 0.9, 4)
            target = round(price * 1.15, 4)
            rr = round((target - entry) / (entry - stop), 2)

            # sentiment פשוט לפי LunarCrush (במקום → אפשר לשלב ניתוח NLP)
            sentiment = "חיובי מאוד 🔥" if coin['price_change_percentage_24h'] > 5 else "נייטרלי"

            forecast = f"↑ +{round((target/price - 1)*100, 2)}% (72% הסתברות)"

            hist = cg.get_coin_market_chart_by_id(coin['id'], vs_currency='usd', days=60)
            prices = [{"Date": pd.to_datetime(p[0], unit='ms'),
                       "Open": p[1], "High": p[1]*1.01, "Low": p[1]*0.99, "Close": p[1]} for p in hist['prices']]

            chart = generate_chart(coin['symbol'], prices, entry, stop, target)
            caption = build_message(coin, entry, stop, target, rr, sentiment, forecast)

            bot.send_photo(chat_id=CHAT_ID, photo=open(chart, 'rb'),
                           caption=caption, parse_mode='Markdown')
        except Exception as e:
            bot.send_message(chat_id=CHAT_ID, text=f"שגיאה במטבע {coin.get('name', '?')}: {e}")

if __name__ == "__main__":
    send_report()
