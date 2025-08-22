import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from pycoingecko import CoinGeckoAPI
from telegram import Bot

# --- סודות ---
TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")
LUNAR_API_KEY = os.getenv("LUNARCRUSH_API")

bot = Bot(token=TOKEN)
cg = CoinGeckoAPI()

# ===================== חישובים =====================
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def get_holding_recommendation(change):
    if change > 15:
        return "Day Trade (עסקה יומית)"
    elif change > 5:
        return "Swing Trade (3–10 ימים)"
    else:
        return "מעקב בלבד"

# ===================== נתוני גרף =====================
def generate_chart(coin_id, entry, stop_loss, take_profit):
    data = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency='usd', days=30, interval='daily')
    prices = pd.DataFrame(data['prices'], columns=['time','price'])
    prices['time'] = pd.to_datetime(prices['time'], unit='ms')
    prices.set_index('time', inplace=True)
    prices['Open'] = prices['price']
    prices['High'] = prices['price']
    prices['Low'] = prices['price']
    prices['Close'] = prices['price']

    alines = [
        [prices.index[0], entry, prices.index[-1], entry],
        [prices.index[0], stop_loss, prices.index[-1], stop_loss],
        [prices.index[0], take_profit, prices.index[-1], take_profit]
    ]
    colors = ["blue", "red", "green"]

    filepath = f"{coin_id}.png"
    mpf.plot(
        prices,
        type="candle",
        style="charles",
        title=f"{coin_id.upper()} - גרף נרות יומיים",
        ylabel="מחיר ($)",
        alines=dict(alines=alines, colors=colors, linewidths=1.2),
        savefig=filepath
    )
    return filepath

# ===================== סורקים =====================
def get_top_lowcaps():
    coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_asc', per_page=100, page=1)
    filtered = []
    for c in coins:
        if not c['market_cap'] or c['market_cap'] > 50_000_000:
            continue
        if c['current_price'] > 5:
            continue
        if c['total_volume'] < c['market_cap'] * 0.1:
            continue
        if c['price_change_percentage_24h'] and c['price_change_percentage_24h'] < 5:
            continue
        filtered.append(c)
    return filtered[:5]

def get_trending_coins():
    trending = cg.get_search_trending()
    return [coin['item'] for coin in trending['coins'][:5]]

def get_lunar_trending():
    url = "https://lunarcrush.com/api4/public/coins/list/v1"
    params = {"limit": 5, "sort": "social_volume_24h", "desc": True}
    headers = {"Authorization": f"Bearer {LUNAR_API_KEY}"}
    r = requests.get(url, headers=headers)
    data = r.json()
    return data.get("data", [])

# ===================== דיווח =====================
def send_report():
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק הקריפטו התחיל לרוץ!")

    coins = get_top_lowcaps()
    if coins:
        for coin in coins:
            entry = coin['current_price']
            stop_loss = round(entry * 0.9, 4)
            take_profit = round(entry * 1.2, 4)
            rr_ratio = round((take_profit - entry) / (entry - stop_loss), 2) if entry > stop_loss else "N/A"

            # RSI
            data = cg.get_coin_market_chart_by_id(id=coin['id'], vs_currency='usd', days=30, interval='daily')
            prices = pd.DataFrame(data['prices'], columns=['time','price'])
            prices['price'] = prices['price'].astype(float)
            rsi = calculate_rsi(prices['price'])

            hold_time = get_holding_recommendation(coin['price_change_percentage_24h'])

            chart_path = generate_chart(coin['id'], entry, stop_loss, take_profit)

            caption = (
                f"*{coin['name']}* ({coin['symbol'].upper()})\n"
                f"💰 שווי שוק: {coin['market_cap']:,}$\n"
                f"💵 מחיר נוכחי: {entry}$\n"
                f"📊 שינוי 24ש': {coin['price_change_percentage_24h']}%\n\n"
                f"סיבת כניסה:\n"
                f"- מחיר מתחת ל-5$\n"
                f"- שווי שוק קטן\n"
                f"- שינוי יומי חיובי\n\n"
                f"💡 אסטרטגיה: לונג\n"
                f"🎯 כניסה: {entry}$\n"
                f"🛑 סטופ לוס: {stop_loss}$\n"
                f"✅ טייק פרופיט: {take_profit}$\n"
                f"📊 יחס סיכון–סיכוי: {rr_ratio}\n"
                f"📆 המלצת זמן אחזקה: {hold_time}\n"
                f"RSI: {round(rsi,2)}\n"
            )

            bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, 'rb'),
                           caption=caption, parse_mode='Markdown')
    else:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו אלטקוינים מתאימים היום.")

    # CoinGecko Trending
    trending = get_trending_coins()
    if trending:
        hot_list = "\n".join([f"🔥 {c['name']} ({c['symbol'].upper()})" for c in trending])
        bot.send_message(chat_id=CHAT_ID, text=f"🌟 המטבעות החמים ב-CoinGecko:\n{hot_list}")

    # LunarCrush Trending
    lunar = get_lunar_trending()
    if lunar:
        msg = "🌐 המטבעות הכי מדוברים (LunarCrush):\n"
        for c in lunar:
            msg += f"🔥 {c['name']} ({c['symbol']}) | GalaxyScore: {c.get('galaxy_score','?')}\n"
        bot.send_message(chat_id=CHAT_ID, text=msg)
    else:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ לא התקבלו נתונים מ-LunarCrush.")

if __name__ == "__main__":
    send_report()
