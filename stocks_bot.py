import os
import yfinance as yf
import mplfinance as mpf
import telebot

# ===== הגדרות =====
TOKEN = os.getenv("TOKEN_STOCKS")        # הטוקן של בוט הטלגרם (Secrets בגיטהאב)
CHAT_ID = os.getenv("CHAT_ID_STOCKS")    # הצ'אט ID שלך (Secrets בגיטהאב)
bot = telebot.TeleBot(TOKEN)


# ===== יצירת גרף =====
def generate_chart(ticker, entry, stop, target):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo", interval="1d")

    mc = mpf.make_marketcolors(up='g', down='r', edge='i', wick='i', volume='in')
    s  = mpf.make_mpf_style(marketcolors=mc)

    add_lines = [
        mpf.make_addplot([entry]*len(hist), color="blue", linestyle="--", linewidth=1),
        mpf.make_addplot([stop]*len(hist), color="red", linestyle="--", linewidth=1),
        mpf.make_addplot([target]*len(hist), color="green", linestyle="--", linewidth=1),
    ]

    filepath = f"{ticker}.png"
    mpf.plot(hist, type="candle", style=s, addplot=add_lines,
             title=f"{ticker} - גרף נרות", volume=True, savefig=filepath)
    return filepath


# ===== שליחת מניות =====
def send_stocks():
    tickers = ['NIO', 'TSLA', 'PLTR', 'RIOT', 'AMC']
    selected = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="5d")
            price = round(hist['Close'][-1], 2)
            change = round(info.get('regularMarketChangePercent', 0), 2)
            volume = info.get('volume', 0)
            avg_volume = info.get('averageVolume', 1)
            sector = info.get("sector", "לא ידוע")

            # רמות מסחר
            entry = price * 0.995
            stop  = price * 0.95
            target = price * 1.1
            rr_ratio = round((target - entry) / (entry - stop), 2)

            reasons = []
            if change > 3: reasons.append("📈 שינוי יומי חיובי")
            if volume > 2 * avg_volume: reasons.append("🔥 ווליום חריג")
            if not reasons:
                continue

            caption = f"""
📊 *{info.get('shortName', t)}* ({t})

💵 מחיר נוכחי: {price}$
🎯 כניסה: {round(entry,2)}$  
🛑 סטופלוס: {round(stop,2)}$  
✅ טייק פרופיט: {round(target,2)}$  
📐 יחס סיכוי/סיכון: {rr_ratio}  
⌛ אסטרטגיה: סווינג (3–10 ימים)

🔍 סקירה מלאה:
- סקטור: {sector}
- סיבה: {', '.join(reasons)}
- שינוי יומי: {change}%

✅ סיכום: איתות חזק, כניסה אפשרית לניהול סיכון.
"""

            chart_path = generate_chart(t, entry, stop, target)
            selected.append((chart_path, caption))

        except Exception as e:
            print(f"שגיאה עם {t}: {e}")

    if not selected:
        bot.send_message(CHAT_ID, "❌ לא נמצאו מניות מתאימות היום.")
    else:
        for chart, caption in selected:
            with open(chart, 'rb') as photo:
                bot.send_photo(CHAT_ID, photo, caption=caption, parse_mode='Markdown')


# ===== הרצה =====
if __name__ == "__main__":
    bot.send_message(CHAT_ID, "🚀 סורק המניות התחיל לרוץ!")
    send_stocks()
