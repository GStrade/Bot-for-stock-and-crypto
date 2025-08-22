import os
import requests
from pycoingecko import CoinGeckoAPI
from telegram import Bot

# טעינת הסודות מ-GitHub Secrets
TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")
LUNAR_API_KEY = os.getenv("LUNARCRUSH_API")

# בדיקה שהסודות קיימים
if not TOKEN or not CHAT_ID:
    raise ValueError("❌ חסר TOKEN_CRYPTO או CHAT_ID_CRYPTO ב-Secrets")

bot = Bot(token=TOKEN)
cg = CoinGeckoAPI()

def get_top_lowcaps():
    coins = cg.get_coins_markets(
        vs_currency='usd',
        order='market_cap_asc',
        per_page=100,
        page=1
    )
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
    if not LUNAR_API_KEY:
        print("⚠️ לא הוזן API של LunarCrush")
        return []
    url = "https://lunarcrush.com/api4/public/coins/list/v1"
    params = {"limit": 5, "sort": "social_volume_24h", "desc": True}
    headers = {"Authorization": f"Bearer {LUNAR_API_KEY}"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data.get("data", [])
    except Exception as e:
        print(f"שגיאה מ-LunarCrush: {e}")
        return []

def send_report():
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק הקריפטו התחיל לרוץ!")

    # Low caps
    coins = get_top_lowcaps()
    if coins:
        for coin in coins:
            msg = f"""
💎 {coin['name']} ({coin['symbol'].upper()})
💰 שווי שוק: {coin['market_cap']:,}$
💵 מחיר: {coin['current_price']}$
📈 שינוי 24ש': {coin['price_change_percentage_24h']}%
"""
            bot.send_message(chat_id=CHAT_ID, text=msg)
    else:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו אלטקוינים מסוננים היום.")

    # Trending CoinGecko
    trending = get_trending_coins()
    if trending:
        hot_list = "\n".join([f"🔥 {c['name']} ({c['symbol'].upper()})" for c in trending])
        bot.send_message(chat_id=CHAT_ID, text=f"🌟 המטבעות החמים ב-CoinGecko:\n{hot_list}")

    # LunarCrush
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
