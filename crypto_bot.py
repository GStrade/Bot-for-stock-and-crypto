import os
import requests
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
from pycoingecko import CoinGeckoAPI
from telegram import Bot

TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")
LUNAR_API_KEY = os.getenv("LUNARCRUSH_API")
CMC_API_KEY = os.getenv("CMC_API_KEY")  # תכניס בגיטהאב

bot = Bot(token=TOKEN)
cg = CoinGeckoAPI()

# ===================== פונקציות עזר =====================

def calculate_levels(price, change):
    if change > 0:
        entry = price
        stop = round(price * 0.92, 4)
        target = round(price * 1.15, 4)
        style = "סווינג (החזק עד שבוע)"
    else:
        entry = price
        stop = round(price * 1.05, 4)
        target = round(price * 0.85, 4)
        style = "עסקה קצרה (Intraday)"
    return entry, stop, target, style

def generate_chart(symbol, prices, entry, stop, target):
    df = pd.DataFrame(prices)
    df['Date'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('Date', inplace=True)
    df = df[['open', 'high', 'low', 'close']]

    apds = [
        mpf.make_addplot([entry]*len(df), color='blue', linestyle='--'),
        mpf.make_addplot([stop]*len(df), color='red', linestyle='--'),
        mpf.make_addplot([target]*len(df), color='green', linestyle='--'),
    ]

    filepath = f"{symbol}.png"
    mpf.plot(df, type='candle', style='charles',
             addplot=apds,
             title=f"{symbol} - גרף יומי",
             savefig=filepath)
    return filepath

# ===================== מקורות מידע =====================

def get_trending_gecko():
    trending = cg.get_search_trending()
    return [coin['item'] for coin in trending['coins'][:5]]

def get_lunar_trending():
    url = "https://lunarcrush.com/api4/public/coins/list/v1"
    params = {"limit": 5, "sort": "social_volume_24h", "desc": True}
    headers = {"Authorization": f"Bearer {LUNAR_API_KEY}"}
    r = requests.get(url, headers=headers)
    return r.json().get("data", [])

def get_cmc_trending():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/trending/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    r = requests.get(url, headers=headers)
    return r.json().get("data", [])

# ===================== שליחת דו"ח =====================

def send_report():
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק הקריפטו התחיל לרוץ!")

    # CoinGecko
    trending = get_trending_gecko()
    if trending:
        for coin in trending:
            name = coin['name']
            symbol = coin['symbol'].upper()
            price = coin.get('price_btc', 0)  # נתון חלקי
            entry, stop, target, style = calculate_levels(price, 5)

            # כאן צריך נתוני גרף אמיתיים (אפשר דרך cg.get_coin_market_chart)
            chart_path = None
            try:
                hist = cg.get_coin_market_chart_by_id(coin['id'], vs_currency='usd', days=7)
                prices = [
                    {"timestamp": int(p[0]/1000), "open": p[1], "high": p[1]*1.02, "low": p[1]*0.98, "close": p[1]}
                    for p in hist['prices']
                ]
                chart_path = generate_chart(symbol, prices, entry, stop, target)
            except:
                pass

            caption = (
                f"*{name}* ({symbol})\n"
                f"מחיר נוכחי: {price}$\n"
                f"כניסה: {entry}$ | סטופ: {stop}$ | טייק: {target}$\n"
                f"סגנון עסקה: {style}\n"
                f"📊 מקור: CoinGecko"
            )

            if chart_path:
                bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, 'rb'),
                               caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(chat_id=CHAT_ID, text=caption, parse_mode='Markdown')

    # LunarCrush
    lunar = get_lunar_trending()
    if lunar:
        hot_list = "\n".join([f"🔥 {c['name']} ({c['symbol']})" for c in lunar])
        bot.send_message(chat_id=CHAT_ID, text=f"🌐 הכי מדובר ב-LunarCrush:\n
