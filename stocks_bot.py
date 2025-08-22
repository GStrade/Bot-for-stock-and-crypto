import os
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Bot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")
bot = Bot(token=TOKEN)


def generate_advanced_chart(ticker, entry, stop, target):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="3mo", interval="1d")

    # חישוב ממוצעים נעים
    hist['MA20'] = hist['Close'].rolling(window=20).mean()
    hist['MA50'] = hist['Close'].rolling(window=50).mean()

    # חישוב RSI (14 ימים)
    delta = hist['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    hist['RSI'] = 100 - (100 / (1 + rs))

    # קווים לכניסה/סטופ/יעד
    add_lines = [
        mpf.make_addplot([entry] * len(hist), color="blue", width=1.2),
        mpf.make_addplot([stop] * len(hist), color="red", width=1.2),
        mpf.make_addplot([target] * len(hist), color="green", width=1.2),
        mpf.make_addplot(hist['MA20'], color="orange", width=1.0),
        mpf.make_addplot(hist['MA50'], color="purple", width=1.0),
    ]

    # חלון RSI
    ap_rsi = mpf.make_addplot(hist['RSI'], panel=1, color="fuchsia", ylabel='RSI')
    add_lines.append(ap_rsi)

    filepath = f"{ticker}_advanced.png"
    mc = mpf.make_marketcolors(up='g', down='r', edge='i', wick='i', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)

    mpf.plot(
        hist,
        type="candle",
        style=s,
        volume=True,
        addplot=add_lines,
        title=f"{ticker} - גרף נרות מקצועי",
        ylabel="Price",
        ylabel_lower="Volume",
        savefig=filepath
    )
    return filepath


def send_example_signal():
    ticker = "AMC"
    price = 2.95
    entry = 2.94
    stop = 2.80
    target = 3.25

    chart_path = generate_advanced_chart(ticker, entry, stop, target)

    caption = f"""
📊 *AMC Entertainment Holdings (AMC)*

💵 מחיר נוכחי: {price}$
🎯 כניסה: {entry}$
🛑 סטופלוס: {stop}$
✅ טייק פרופיט: {target}$

📐 יחס סיכוי/סיכון: {(target-entry)/(entry-stop):.2f}
⌛ אסטרטגיה: סווינג (3–10 ימים)

🔍 סקירה מלאה:
- סקטור: Communication Services
- סיבה: 📈 שינוי יומי חיובי, 🔥 ווליום חריג
- סנטימנט: חיובי ברשתות
- 🔮 AI Forecast: ↑ +7% (65% הסתברות)

✅ סיכום: איתות חזק, כניסה אפשרית לניהול סיכון.
"""

    with open(chart_path, "rb") as photo:
        bot.send_photo(chat_id=CHAT_ID, photo=photo,
                       caption=caption, parse_mode='Markdown')


if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק המניות (גרסה מקצועית) התחיל לרוץ!")
    send_example_signal()
