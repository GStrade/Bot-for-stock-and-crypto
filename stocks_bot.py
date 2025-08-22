import os
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
from telegram import Bot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")
bot = Bot(token=TOKEN)


# ===================== עוזרים =====================
def get_sector(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("sector", "לא ידוע")
    except:
        return "שגיאה"


def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]


def get_holding_recommendation(change, volume_ratio):
    if change > 8:  # שינוי יומי חריג
        return "עסקת Day Trade (חד יומית)"
    elif volume_ratio > 2:
        return "עסקת סווינג (3–10 ימים)"
    else:
        return "מעקב בלבד"


def generate_chart(ticker, entry, stop_loss, take_profit):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="3mo", interval="1d")

    if hist.empty:
        return None

    # קווי עזר למחירים
    alines = [
        [hist.index[0], entry, hist.index[-1], entry],
        [hist.index[0], stop_loss, hist.index[-1], stop_loss],
        [hist.index[0], take_profit, hist.index[-1], take_profit]
    ]
    colors = ["blue", "red", "green"]

    filepath = f"{ticker}.png"
    mpf.plot(
        hist,
        type="candle",
        style="charles",
        title=f"{ticker} - גרף נרות יומיים",
        ylabel="מחיר ($)",
        volume=True,
        mav=(50, 200),  # ממוצעים נעים MA50 MA200
        alines=dict(alines=alines, colors=colors, linewidths=1.2),
        savefig=filepath
    )
    return filepath


# ===================== עיקרי =====================
def send_stocks():
    tickers = ['NIO', 'BITF', 'COMP', 'AMC', 'ADT', 'SMWB', 'PGEN', 'GME', 'PLTR', 'RIOT']
    selected = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="6mo", interval="1d")

            if hist.empty:
                continue

            price = hist['Close'][-1]
            volume = info.get('volume') or 0
            avg_volume = info.get('averageVolume') or 1
            change = info.get('regularMarketChangePercent') or 0
            sector = get_sector(t)

            # ניתוח טכני
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            rsi = calculate_rsi(hist['Close'])
            ma50 = hist['Close'].rolling(50).mean().iloc[-1]
            ma200 = hist['Close'].rolling(200).mean().iloc[-1]

            reasons = []
            if change and change > 5:
                reasons.append("📈 שינוי יומי חד (מעל 5%)")
            if volume_ratio > 2:
                reasons.append(f"🔥 ווליום חריג (פי {round(volume_ratio,1)}) מהממוצע")
            if rsi < 30:
                reasons.append("📉 RSI נמוך (מכירת יתר)")
            elif rsi > 70:
                reasons.append("⚠️ RSI גבוה (קניית יתר)")
            if ma50 > ma200:
                reasons.append("✅ מגמה חיובית (MA50 מעל MA200)")

            if len(reasons) >= 1:
                direction = "לונג" if change > 0 else "שורט"
                potential = round(abs(change), 2)

                entry = round(price, 2)
                stop_loss = round(price * 0.9, 2)
                take_profit = round(price * 1.15, 2)
                rr_ratio = round((take_profit - entry) / (entry - stop_loss), 2) if entry > stop_loss else "N/A"

                hold_time = get_holding_recommendation(change, volume_ratio)

                chart_path = generate_chart(t, entry, stop_loss, take_profit)

                caption = (
                    f"*{info.get('shortName', t)}* ({t})\n"
                    f"תחום: {sector}\n"
                    f"מחיר נוכחי: {entry}$\n"
                    f"שינוי יומי: {round(change,2)}%\n"
                    f"סיבת כניסה:\n- " + "\n- ".join(reasons) + "\n\n"
                    f"💡 אסטרטגיה: {direction}\n"
                    f"🎯 כניסה: {entry}$\n"
                    f"🛑 סטופ לוס: {stop_loss}$\n"
                    f"✅ טייק פרופיט: {take_profit}$\n"
                    f"📊 יחס סיכון–סיכוי: {rr_ratio}\n"
                    f"📆 המלצת זמן אחזקה: {hold_time}\n"
                    f"RSI: {round(rsi,2)} | MA50: {round(ma50,2)} | MA200: {round(ma200,2)}\n\n"
                    f"ℹ️ תיאור קצר: {info.get('longBusinessSummary','')[:250]}..."
                )

                selected.append((chart_path, caption))
        except Exception as e:
            print(f"שגיאה עם {t}: {e}")

    if not selected:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו מניות מתאימות היום.")
    else:
        for chart_path, caption in selected[:5]:
            if chart_path:
                bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, 'rb'),
                               caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(chat_id=CHAT_ID, text=caption)


if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק המניות התחיל לרוץ!")
    send_stocks()
