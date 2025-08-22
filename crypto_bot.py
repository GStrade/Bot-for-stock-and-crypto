import os
import requests
import pandas as pd
import mplfinance as mpf
from pycoingecko import CoinGeckoAPI
from telegram import Bot

# --- Tokens ---
TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")
LUNAR_API_KEY = os.getenv("LUNARCRUSH_API")
CMC_API_KEY = os.getenv("CMC_API")

bot = Bot(token=TOKEN)
cg = CoinGeckoAPI()

# ---------------- LowCaps Filter ----------------
def get_top_lowcaps():
    coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_asc', per_page=100, page=1)
    filtered = []
    for c in coins:
        if not c['market_cap']: 
            continue
        if c['market_cap'] > 200_000_000:  # ריכוך: עד 200M
            continue
        if c['current_price'] > 10:        # ריכוך: עד 10$
            continue
        if c['total_volume'] < c['market_cap'] * 0.02:  # ריכוך ווליום
            continue
        filtered.append(c)
    return filtered[:5]

# ---------------- CoinGecko Trending ----------------
def get_trending_coins():
    trending = cg.get_search_trending()
    return [coin['item'] for coin in trending['coins'][:5]]

# ---------------- LunarCrush Trending ----------------
def get_lunar_trending():
    try:
        url = "https://lunarcrush.com/api4/public/coins/list/v1"
        params = {"limit": 5, "sort": "social_volume_24h", "desc": True}
        headers = {"Authorization": f"Bearer {LUNAR_API_KEY}"}
        r = requests.get(url, headers=headers, timeout=10)
        return r.json().get("data", [])
    except:
        return []

# ---------------- CoinMarketCap Trending ----------------
def get_cmc_trending():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/trending/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        return r.json().get("data", [])[:5]
    except:
        return []

# ---------------- Chart Generator ----------------
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
             title=f"{symbol} - גרף נרות", volume=True, savefig=filepath)
    return filepath

# ---------------- Report ----------------
def send_report():
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק הקריפטו התחיל להריץ סריקה...")

    # --- LowCaps ---
    coins = get_top_lowcaps()
    if not coins:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ לא נמצאו LowCaps מתאימים, מציג מטבעות טרנדינג במקום.")
        coins = get_trending_coins()

    for coin in coins:
        try:
            price = coin.get('current_price') or coin.get('price_btc', 0)
            if not price: 
                continue
            entry = price * 0.98
            stop  = price * 0.9
            target = price * 1.15
            rr = round((target - entry) / (entry - stop), 2)

            caption = f"""
🌐 {coin['name']} ({coin['symbol'].upper()})

💵 מחיר נוכחי: {round(price,3)}$
🎯 כניסה: {round(entry,3)}$  
🛑 סטופלוס: {round(stop,3)}$  
✅ טייק פרופיט: {round(target,3)}$  
📐 יחס סיכוי/סיכון: {rr}  
⌛ אסטרטגיה: סווינג (3–7 ימים)

🔍 סקירה מלאה:
- Market Cap: {coin.get('market_cap','?')}
- Volume: {coin.get('total_volume','?')}
- שינוי 24ש: {coin.get('price_change_percentage_24h','?')}%
"""

            # גרף מ־CoinGecko אם אפשר
            if "id" in coin:
                hist = cg.get_coin_market_chart_by_id(coin['id'], vs_currency='usd', days=30)
                prices = [{"Date": pd.to_datetime(p[0], unit='ms'),
                           "Open": p[1], "High": p[1]*1.01, "Low": p[1]*0.99, "Close": p[1]} for p in hist['prices']]
                chart = generate_chart(coin['symbol'], prices, entry, stop, target)
                bot.send_photo(chat_id=CHAT_ID, photo=open(chart, 'rb'),
                               caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(chat_id=CHAT_ID, text=caption)
        except Exception as e:
            bot.send_message(chat_id=CHAT_ID, text=f"שגיאה עם {coin.get('name','?')}: {e}")

    # --- LunarCrush ---
    lunar = get_lunar_trending()
    if lunar:
        msg = "🌐 מטבעות הכי מדוברים (LunarCrush):\n"
        for c in lunar:
            msg += f"🔥 {c['name']} ({c['symbol']}) | GalaxyScore: {c.get('galaxy_score','?')}\n"
        bot.send_message(chat_id=CHAT_ID, text=msg)

    # --- CoinMarketCap ---
    cmc = get_cmc_trending()
    if cmc:
        msg = "📊 Trending ב-CoinMarketCap:\n"
        for c in cmc:
            msg += f"⭐ {c['name']} ({c['symbol']})\n"
        bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    send_report()
