import requests
import pandas as pd
import mplfinance as mpf
from pycoingecko import CoinGeckoAPI
import datetime
import random
import os
import telebot

# ===== הגדרות =====
API_KEY = os.getenv("TELEGRAM_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(API_KEY)

cg = CoinGeckoAPI()

# ===== יצירת גרף נרות =====
def generate_chart(symbol, hist, entry, stop, target):
    prices = hist['prices']
    volumes = hist.get('total_volumes', [])

    data = []
    for i, p in enumerate(prices):
        ts, price = p
        high = price * 1.01
        low = price * 0.99
        close = price
        open_ = price
        volume = volumes[i][1] if i < len(volumes) else 0
        data.append([pd.to_datetime(ts, unit='ms'), open_, high, low, close, volume])

    df = pd.DataFrame(data, columns=["Date","Open","High","Low","Close","Volume"])
    df.set_index("Date", inplace=True)

    mc = mpf.make_marketcolors(up='g', down='r', edge='i', wick='i', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)

    add_lines = [
        mpf.make_addplot([entry]*len(df), color="blue", linestyle="--", linewidth=1),
        mpf.make_addplot([stop]*len(df), color="red", linestyle="--", linewidth=1),
        mpf.make_addplot([target]*len(df), color="green", linestyle="--", linewidth=1),
    ]

    filepath = f"{symbol}.png"
    mpf.plot(df, type="candle", style=s, addplot=add_lines,
             title=f"{symbol.upper()} - גרף נרות", volume=True, savefig=filepath)
    return filepath


# ===== שליחת הודעה עם גרף =====
def send_crypto_signal(coin):
    hist = cg.get_coin_market_chart_by_id(coin['id'], vs_currency='usd', days=30)

    current_price = coin['current_price']
    entry = round(current_price * 0.98, 4)
    stop = round(current_price * 0.95, 4)
    target = round(current_price * 1.15, 4)

    chart = generate_chart(coin['symbol'], hist, entry, stop, target)

    change_24h = round(coin['price_change_percentage_24h'], 2) if coin['price_change_percentage_24h'] else 0
    volume = coin['total_volume']
    market_cap = coin['market_cap']

    msg = f"""
🚀 אות מסחר בקריפטו 🚀

שם מטבע: {coin['name']} ({coin['symbol'].upper()})
מחיר נוכחי: {current_price}$
כניסה: {entry}$
סטופלוס: {stop}$
טייק פרופיט: {target}$

שינוי יומי: {change_24h}%
נפח מסחר: {volume:,}$
שווי שוק: {market_cap:,}$

📝 סיבת כניסה: נפח מסחר חריג, תנודתיות גבוהה, מומנטום חיובי.
📊 מקור נתונים: CoinGecko
    """

    with open(chart, "rb") as photo:
        bot.send_photo(CHAT_ID, photo, caption=msg)


# ===== סורק מטבעות =====
def scan_crypto():
    coins = cg.get_coins_markets(vs_currency='usd', order='volume_desc', per_page=10, page=1)
    selected = random.sample(coins, 3)  # לבחור 3 מטבעות אקראיים מהחמים ביותר
    for coin in selected:
        send_crypto_signal(coin)


if __name__ == "__main__":
    bot.send_message(CHAT_ID, "🚀 סורק הקריפטו התחיל לרוץ!")
    try:
        scan_crypto()
    except Exception as e:
        bot.send_message(CHAT_ID, f"שגיאה בסורק הקריפטו: {e}")
