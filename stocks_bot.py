import os
import yfinance as yf
import mplfinance as mpf
from telegram import Bot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")
bot = Bot(token=TOKEN)

def classify_trade(change, volume, avg_volume):
    if change >= 6 or (avg_volume and volume > 3 * avg_volume):
        return "⚡ Day Trade (עסקה יומית – לנצל תנודתיות גבוהה)"
    elif 2 <= change < 6:
        return "📅 Swing Trade (החזקה של ימים עד שבועות)"
    else:
        return "👀 למעקב בלבד"

def generate_chart(ticker, entry, stop_loss, take_profit):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="7d", interval="1h")
    if hist.empty:
        return None
    alines = [
        [hist.index[0], entry, hist.index[-1], entry],
        [hist.index[0], stop_loss, hist.index[-1], stop_loss],
        [hist.index[0], take_profit, hist.index[-1], take_profit]
    ]
    filepath = f"{ticker}.png"
    mpf.plot(hist, type="candle", style="charles", volume=True,
             alines=dict(alines=alines, colors=["blue","red","green"]),
             savefig=filepath)
    return filepath

def send_stocks():
    tickers = ['NIO','BITF','COMP','AMC','ADT','SMWB','PGEN','GME','PLTR','RIOT']
    report_lines = []
    charts = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="1d")
            if hist.empty:
                continue
            price = hist['Close'][0]
            change = info.get('regularMarketChangePercent', 0)
            volume, avg_volume = info.get('volume',0), info.get('averageVolume',1)
            if not change:
                continue

            reasons = []
            if change > 5: reasons.append("📈 שינוי יומי חד")
            if volume and avg_volume and volume > 2 * avg_volume:
                reasons.append("🔥 ווליום חריג")

            trade_type = classify_trade(change, volume, avg_volume)
            if len(reasons) >= 1:
                entry = round(price,2)
                stop_loss = round(entry*0.95,2)
                take_profit = round(entry*1.1,2)
                chart_path = generate_chart(t, entry, stop_loss, take_profit)
                charts.append((chart_path, t))

                report_lines.append(
                    f"*{info.get('shortName',t)}* ({t})\n"
                    f"מחיר: {entry}$ | שינוי: {round(change,2)}%\n"
                    f"כניסה: {entry}$ | סטופלוס: {stop_loss}$ | טייק: {take_profit}$\n"
                    f"סיבה: {', '.join(reasons)}\n"
                    f"סוג עסקה: {trade_type}\n"
                    "----------------------------------"
                )
        except Exception as e:
            print(f"שגיאה עם {t}: {e}")

    if report_lines:
        bot.send_message(chat_id=CHAT_ID, text="📊 דו\"ח מניות להיום:\n\n" + "\n\n".join(report_lines), parse_mode="Markdown")
        for chart_path, t in charts:
            if chart_path:
                bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path,'rb'), caption=f"גרף {t}")
    else:
        bot.send_message(chat_id=CHAT_ID, text="❌ לא נמצאו מניות מתאימות להיום.")

if __name__=="__main__":
    send_stocks()
