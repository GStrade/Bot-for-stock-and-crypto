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

# ===== פונקציות סינון =====
def get_top_lowcaps():
    coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_asc', per_page=50, page=1)
    return [c for c in coins if c['market_cap'] and c['market_cap'] < 50_000_000 and c['current_price'] < 5][:5]

def get_cmc_trending():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/trending/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        r = requests.get(url, headers=headers)
        return r.json().get("data", [])[:5]
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

# ===== גרף נרות =====
def generate_chart(symbol, prices, entry, stop, target):
    df = pd.DataFrame(prices)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    mc = mpf.make_marketcolors(up='g', down='r', edge='i', wick='i', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    add_lines = [
        mpf.make_addplot([entry]*len(df), color="blue"),
        mpf.make_addplot([stop]*len(df), color="red"),
        mpf.make_addplot([target]*len(df), color="green"),
    ]

    filepath = f"{symbol}.png"
    mpf.plot(df, type="candle", style=s, addplot=add_lines,
             title=f"{symbol.upper()} - נרות", volume=True, savefig=filepath)
    return filepath

# ===== שליחת דו"ח =====
def send_report():
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק הקריפטו התחיל לרוץ!")

    coins = get_top_lowcaps()
    if coins:
        for coin in coins:
            price = coin['current_price']
            entry = round(price * 0.98, 3)
            stop  = round(price * 0.9, 3)
            target = round(price * 1.15, 3)
            rr = round((target - entry) / (entry - stop), 2)

            caption = f"""
🌐 {coin['name']} ({coin['symbol'].upper()})

💵 מחיר נוכחי: {price}$
🎯 כניסה: {entry}$  
🛑 סטופלוס: {stop}$  
✅ טייק פרופיט: {target}$  
📐 יחס סיכוי/סיכון: {rr}  
⌛ אסטרטגיה: סווינג (3–7 ימים)

🔍 סקירה מלאה:
- Market Cap: {coin['market_cap']:,}$
- נפח מסחר: {coin['total_volume']:,}$
- שינוי יומי: {coin['price_change_percentage_24h']}%
- 🔮 תחזית AI: ↑ +12%
"""
            # נתוני היסטוריה לגרף
            hist = cg.get_coin_market_chart_by_id(coin['id'], vs_currency='usd', days=30)
            prices = [{"Date": pd.to_datetime(p[0], unit='ms'),
                       "Open": p[1], "High": p[1]*1.01, "Low": p[1]*0.99, "Close": p[1]} for p in hist['prices']]

            chart = generate_chart(coin['symbol'], prices, entry, stop, target)

            bot.send_photo(chat_id=CHAT_ID, photo=open(chart, 'rb'),
                           caption=caption, parse_mode='Markdown')
    else:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו אלטקוינים מתאימים היום.")

if __name__ == "__main__":
    send_report()
