import os
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from telegram import Bot

# טוקן וצ'אט איידי מתוך Secrets
TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")
bot = Bot(token=TOKEN)


def get_sector(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("sector", "לא ידוע")
    except Exception:
        return "שגיאה"


def generate_chart(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="14d")
    if hist.empty:
        return None
    plt.figure()
    hist['Close'].plot(title=f"{ticker} - גרף יומי")
    filepath = f"{ticker}.png"
    plt.savefig(filepath)
    plt.close()
    return filepath


def calculate_trade_levels(price, volatility, direction):
    """חישוב מחיר כניסה, סטופלוס וטייק פרופיט על בסיס תנודתיות (ATR פשוט)"""
    entry = round(price, 2)
    atr = round(volatility, 2)

    if direction == "לונג":
        stop_loss = round(entry - 1.5 * atr, 2)
        take_profit = round(entry + 2 * atr, 2)
    else:  # שורט
        stop_loss = round(entry + 1.5 * atr, 2)
        take_profit = round(entry - 2 * atr, 2)

    return entry, stop_loss, take_profit


def classify_trade(change, volume_ratio):
    """קובע אם זה סווינג או עסקה יומית"""
    if change > 10 or volume_ratio > 3:
        return "⚡ עסקה יומית (Day Trade)"
    elif 3 < change <= 10:
        return "📊 עסקת סווינג (Swing Trade, 3-7 ימים)"
    else:
        return "🤔 ניטרלי / לא מובהק"


def send_stocks():
    tickers = ['NIO', 'BITF', 'COMP', 'AMC', 'ADT', 'SMWB', 'PGEN', 'GME', 'PLTR', 'RIOT']
    selected = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info

            hist = stock.history(period="7d")
            if hist.empty:
                continue
            price = hist['Close'][-1]

            volume = info.get('volume') or 0
            avg_volume = info.get('averageVolume') or 1
            change = info.get('regularMarketChangePercent') or 0
            sector = get_sector(t)

            # חישוב תנודתיות פשוטה – סטיית תקן יומית
            volatility = hist['Close'].pct_change().std() * price

            reasons = []
            if change and change > 5:
                reasons.append("📈 שינוי יומי חד")
            if volume and avg_volume and volume > 2 * avg_volume:
                reasons.append("🔥 ווליום חריג")

            if reasons:
                direction = "לונג" if change > 0 else "שורט"
                potential = round(abs(change), 2)

                # חישוב רמות מסחר
                entry, stop_loss, take_profit = calculate_trade_levels(price, volatility, direction)
                trade_type = classify_trade(change, volume / avg_volume)

                summary = info.get('longBusinessSummary', '')[:200]
                chart_path = generate_chart(t)

                caption = (
                    f"*{info.get('shortName', t)}* ({t})\n"
                    f"תחום: {sector}\n"
                    f"מחיר נוכחי: {round(price,2)}$\n"
                    f"שינוי יומי: {round(change,2)}%\n"
                    f"סיבה: {', '.join(reasons)}\n"
                    f"כיוון עסקה: {direction}\n"
                    f"סוג עסקה: {trade_type}\n"
                    f"אחוז רווח פוטנציאלי: {potential}%\n\n"
                    f"🎯 מחיר כניסה: {entry}$\n"
                    f"🛑 סטופלוס: {stop_loss}$\n"
                    f"✅ טייק פרופיט: {take_profit}$\n\n"
                    f"{summary}..."
                )

                selected.append((chart_path, caption))
        except Exception as e:
            print(f"שגיאה עם {t}: {e}")

    if not selected:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו מניות מתאימות היום.")
    else:
        for chart_path, caption in selected[:5]:
            if chart_path:
                with open(chart_path, 'rb') as photo:
                    bot.send_photo(chat_id=CHAT_ID, photo=photo,
                                   caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(chat_id=CHAT_ID, text=caption)


if __name__ == "__main__":
    try:
        bot.send_message(chat_id=CHAT_ID, text="🚀 סורק המניות התחיל לרוץ!")
        send_stocks()
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ שגיאה בהרצת הבוט: {e}")
