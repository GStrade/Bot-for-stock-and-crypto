import os
import requests
import pandas as pd
import mplfinance as mpf
from pycoingecko import CoinGeckoAPI
from telegram import Bot

TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")
LUNAR_API_KEY = os.getenv("LUNARCRUSH_API")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TOKEN)
cg = CoinGeckoAPI()

# חישוב רמות
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

# גרף נרות
def generate_chart(symbol, prices, entry, stop, target):
    df = pd.DataFrame(prices, columns=["timestamp","price"])
    df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['Open'] = df['price']
    df['High'] = df['price']*1.02
    df['Low'] = df['price']*0.98
    df['Close'] = df['price']
    df.set_index('Date', inplace=True)
    df = df[['Open','High','Low','Close']]

    apds = [
        mpf.make_addplot([entry]*len(df), color='blue', linestyle='--'),
        mpf.make_addplot([stop]*len(df), color='red', linestyle='--'),
        mpf.make_addplot([target]*len(df), color='green', linestyle='--'),
    ]

    filepath = f"{symbol}.png"
    mpf.plot(df, type='candle', style='charles',
             addplot=apds,
             title=f"{symbol} - גרף נרות יומי",
             savefig=filepath)
    return filepath

# ===================== מקורות מידע =====================
def get_trending_gecko():
    return cg.get_search_trending()['coins'][:5]

def get_lunar_trending():
    url = "https://lunarcrush.com/api4/public/coins/list/v1"
    headers = {"Authorization": f"Bearer {LUNAR_API_KEY}"}
    r = requests.get(url, headers=headers, params={"limit": 5, "sort":"social_score"})
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
    for coin in get_trending_gecko():
        try:
            name = coin['item']['name']
            symbol = coin['item']['symbol'].upper()
            coin_id = coin['item']['id']

            hist = cg.get_coin_market_chart_by_id(coin_id, vs_currency='usd', days=7)
            price = hist['prices'][-1][1]
            change = ((hist['prices'][-1][1] - hist['prices'][0][1]) / hist['prices'][0][1]) * 100

            entry, stop, target, style = calculate_levels(price, change)
            chart_path = generate_chart(symbol, hist['prices'], entry, stop, target)

            caption = (
                f"*{name}* ({symbol})\n"
                f"מחיר נוכחי: {round(price,4)}$\n"
                f"כניסה: {entry}$ | סטופ: {stop}$ | טייק: {target}$\n"
                f"סגנון עסקה: {style}\n"
                f"סיבות לכניסה: {'📊 שינוי חד' if abs(change)>5 else 'מגמה מתונה'}, 🔥 נפח מסחר גבוה\n"
                f"אחוז שינוי שבועי: {round(change,2)}%\n"
                f"📌 מקור: CoinGecko"
            )
            bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, 'rb'),
                           caption=caption, parse_mode='Markdown')
        except Exception as e:
            print(f"שגיאה עם {coin}: {e}")

    # LunarCrush
    lunar = get_lunar_trending()
    if lunar:
        hot_list = "\n".join([f"🔥 {c['name']} ({c['symbol']})" for c in lunar])
        bot.send_message(chat_id=CHAT_ID, text=f"🌐 הכי מדובר ב-LunarCrush:\n{hot_list}")

    # CoinMarketCap
    cmc = get_cmc_trending()
    if cmc:
        hot_list = "\n".join([f"🚀 {c['name']} ({c['symbol']})" for c in cmc])
        bot.send_message(chat_id=CHAT_ID, text=f"🌟 המטבעות הטרנדיים ב-CMC:\n{hot_list}")

if __name__ == "__main__":
    send_report()
