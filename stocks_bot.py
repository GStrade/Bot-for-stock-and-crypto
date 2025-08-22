import os
import yfinance as yf
import mplfinance as mpf
from telegram import Bot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")

bot = Bot(token=TOKEN)

# --- סיווג העסקה ---
def classify_trade(change, volume, avg_volume):
    if change and change >= 7 or (volume and avg_volume and volume > 3 * avg_volume):
        return "⚡ Day Trade"
    elif change and 3 <= change < 7:
        return "📅 Swing Trade"
    else:
        return "👀 Watchlist"

# --- גרף נרות עם קווי SL/TP ---
def generate_chart(ticker, entry, stop_loss, take_profit):
    try:
        data = yf.download(ticker, period="7d", interval="1h")
        if data.empty:
            return None

        alines = [
            [data.index[0], entry, data.index[-1], entry],
            [data.index[0], stop_loss, data.index[-1], stop_loss],
            [data.index[0], take_profit, data.index[-1], take_profit]
        ]

        filepath = f"{ticker}.png"
        mpf.plot(data, type="candle", style="charles", volume=True,
                 alines=dict(alines=alines, colors=["blue","red","green"]),
                 savefig=filepath)
        return filepath
    except Exception as e:
        print(f"שגיאה בגרף עבור {ticker}: {e}")
        return None

# --- שליחת מניות ---
def send_stocks():
    tickers = ['NIO', 'BITF', 'COMP', 'AMC', 'ADT', 'SMWB', 'PGEN', 'GME', 'PLTR', 'RIOT']
    final_table = []
    charts = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="1d")
            if hist.empty:
                continue

            price = round(hist['Close'][0], 2)
            info = stock.info
            change = info.get('regularMarketChangePercent', 0)
            volume = info.get('volume', 0)
            avg_volume = info.get('averageVolume', 1)
            sector = info.get('sector', 'לא ידוע')

            # קריטריונים
            reasons = []
            if change and change > 5:
                reasons.append("📈 שינוי יומי חד")
            if volume and avg_volume and volume > 2 * avg_volume:
                reasons.append("🔥 ווליום חריג")

            if not reasons:
                continue

            # חישוב SL/TP
            entry = price
            stop_loss = round(entry * 0.95, 2)
            take_profit = round(entry * 1.1, 2)
            trade_type = classify_trade(change, volume, avg_volume)

            # טבלה
            final_table.append([t, entry, f"{round(change,2)}%", stop_loss, take_profit, trade_type])

            # גרף
            chart = generate_chart(t, entry, stop_loss, take_profit)
            if chart:
                charts.append((chart, info.get('shortName', t), ", ".join(reasons), sector))

        except Exception as e:
            print(f"שגיאה עם {t}: {e}")

    # שליחת טבלה
    if final_table:
        header = "| Symbol | Entry | Change  | Stop | Take Profit | Type |\n|--------|-------|---------|------|-------------|------|"
        rows = "\n".join([f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |" for r in final_table])
        bot.send_message(chat_id=CHAT_ID, text="📊 דו\"ח מניות יומי:\n\n" + header + "\n" + rows, parse_mode="Markdown")

    # שליחת גרפים עם סיבה
    for chart, name, reasons, sector in charts:
        caption = f"*{name}*\nסקטור: {sector}\nסיבת בחירה: {reasons}"
        bot.send_photo(chat_id=CHAT_ID, photo=open(chart, 'rb'), caption=caption, parse_mode="Markdown")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="🚀 סורק המניות התחיל לרוץ!")
    send_stocks()                    f"מחיר: {entry}$ | שינוי: {round(change,2)}%\n"
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
