import os
import yfinance as yf
import mplfinance as mpf
from telegram import Bot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")
bot = Bot(token=TOKEN)

# חישוב רמות
def calculate_levels(price, change):
    if change > 0:
        entry = price
        stop = round(price * 0.95, 2)
        target = round(price * 1.10, 2)
        style = "עסקת סווינג (החזק 3–7 ימים)"
    else:
        entry = price
        stop = round(price * 1.05, 2)
        target = round(price * 0.90, 2)
        style = "עסקה יומית (Day Trade)"
    return entry, stop, target, style

# ציור גרף נרות
def generate_chart(ticker, entry, stop, target):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo", interval="1d")

    apds = [
        mpf.make_addplot([entry]*len(hist), color='blue', linestyle='--'),
        mpf.make_addplot([stop]*len(hist), color='red', linestyle='--'),
        mpf.make_addplot([target]*len(hist), color='green', linestyle='--'),
    ]

    filepath = f"{ticker}.png"
    mpf.plot(hist, type='candle', style='charles',
             addplot=apds,
             title=f"{ticker} - גרף נרות יומי",
             savefig=filepath)
    return filepath

# שליחת מניות
def send_stocks():
    tickers = ['NIO', 'BITF', 'AMC', 'PLTR', 'RIOT']
    selected = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            price = stock.history(period="1d")['Close'][0]
            change = info.get('regularMarketChangePercent', 0)

            reasons = []
            if change and abs(change) > 5:
                reasons.append("📈 שינוי יומי חד")
            if info.get('volume', 0) > 2 * info.get('averageVolume', 1):
                reasons.append("🔥 ווליום חריג")
            if info.get('news', None):
                reasons.append("📰 חדשות חמות")
            if price > info.get('fiftyDayAverage', 0):
                reasons.append("🚀 פריצה מעל ממוצע נע 50")

            if len(reasons) >= 2:  # חייב לפחות 2 קריטריונים
                entry, stop, target, style = calculate_levels(price, change)
                chart_path = generate_chart(t, entry, stop, target)

                caption = (
                    f"*{info.get('shortName', t)}* ({t})\n"
                    f"מחיר נוכחי: {round(price,2)}$\n"
                    f"כניסה: {entry}$ | סטופלוס: {stop}$ | טייק פרופיט: {target}$\n"
                    f"סגנון עסקה: {style}\n"
                    f"סיבות לכניסה: {', '.join(reasons)}\n"
                    f"📊 אחוז שינוי יומי: {round(change,2)}%"
                )
                selected.append((chart_path, caption))
        except Exception as e:
            print(f"שגיאה עם {t}: {e}")

    if not selected:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו מניות מתאימות היום.")
    else:
        for chart_path, caption in selected[:3]:
            bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, 'rb'),
                           caption=caption, parse_mode='Markdown')

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק המניות התחיל לרוץ!")
    send_stocks()
