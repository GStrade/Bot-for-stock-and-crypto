import os
import yfinance as yf
import matplotlib.pyplot as plt
from telegram import Bot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")
bot = Bot(token=TOKEN)

def get_sector(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("sector", "לא ידוע")
    except:
        return "שגיאה"

def generate_chart(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="7d")
    plt.figure()
    hist['Close'].plot(title=f"{ticker} - גרף יומי")
    filepath = f"{ticker}.png"
    plt.savefig(filepath)
    plt.close()
    return filepath

def send_stocks():
    tickers = ['NIO', 'BITF', 'COMP', 'AMC', 'ADT', 'SMWB', 'PGEN', 'GME', 'PLTR', 'RIOT']
    selected = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            price = stock.history(period="1d")['Close'][0]
            volume = info.get('volume', 0)
            avg_volume = info.get('averageVolume', 1)
            change = info.get('regularMarketChangePercent', 0)
            sector = get_sector(t)

            reasons = []
            if change and change > 5:
                reasons.append("📈 שינוי יומי חד")
            if volume and avg_volume and volume > 2 * avg_volume:
                reasons.append("🔥 ווליום חריג")

            if len(reasons) >= 1:
                direction = "לונג" if change > 0 else "שורט"
                potential = round(abs(change), 2)
                summary = info.get('longBusinessSummary', '')[:200]
                chart_path = generate_chart(t)

                caption = (
                    f"*{info.get('shortName', t)}* ({t})\n"
                    f"תחום: {sector}\n"
                    f"מחיר: {round(price,2)}$\n"
                    f"שינוי יומי: {round(change,2)}%\n"
                    f"סיבה: {', '.join(reasons)}\n"
                    f"כיוון: {direction}\n"
                    f"אחוז רווח פוטנציאלי: {potential}%\n"
                    f"{summary}..."
                )

                selected.append((chart_path, caption))
        except Exception as e:
            print(f"שגיאה עם {t}: {e}")

    if not selected:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו מניות מתאימות היום.")
    else:
        for chart_path, caption in selected[:5]:
            bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, 'rb'),
                           caption=caption, parse_mode='Markdown')

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק המניות התחיל לרוץ!")
    send_stocks()
