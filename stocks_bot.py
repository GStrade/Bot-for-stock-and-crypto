import os
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
from telegram import Bot

# --- טוקן וצ'אט איידי מהסודות ---
TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")

bot = Bot(token=TOKEN)


def get_sector(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("sector", "לא ידוע")
    except:
        return "שגיאה"


def generate_chart(ticker, entry, stop_loss, take_profit):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="7d", interval="1h")  # נרות שעתי ל־7 ימים

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
        title=f"{ticker} - גרף נרות יפניים",
        ylabel="מחיר ($)",
        ylabel_lower="Volume",
        volume=True,
        alines=dict(alines=alines, colors=colors, linewidths=[1.2, 1.2, 1.2]),
        savefig=filepath
    )

    # הוספת תוויות מחירים על הגרף
    fig, ax = plt.subplots()
    for line, color, label in zip([entry, stop_loss, take_profit], colors,
                                  ["כניסה", "סטופ לוס", "טייק פרופיט"]):
        ax.axhline(line, color=color, linestyle="--", label=f"{label}: {line}$")
    ax.legend()
    plt.close(fig)

    return filepath


def send_stocks():
    tickers = ['NIO', 'BITF', 'COMP', 'AMC', 'ADT', 'SMWB', 'PGEN', 'GME', 'PLTR', 'RIOT']
    selected = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="1d")

            if hist.empty:
                continue

            price = hist['Close'][-1]
            volume = info.get('volume') or 0
            avg_volume = info.get('averageVolume') or 1
            change = info.get('regularMarketChangePercent') or 0
            sector = get_sector(t)

            reasons = []
            if change and change > 5:
                reasons.append("📈 שינוי יומי חד (מעל 5%)")
            if volume and avg_volume and volume > 2 * avg_volume:
                reasons.append("🔥 ווליום חריג (פי 2 מהממוצע)")
            if price < 20:
                reasons.append("💲 מחיר נמוך יחסית – מתאים לכניסה קטנה")

            if len(reasons) >= 1:
                direction = "לונג" if change > 0 else "שורט"
                potential = round(abs(change), 2)
                summary = info.get('longBusinessSummary', '')[:250]

                # הגדרת רמות טכניות פשוטות
                entry = round(price, 2)
                stop_loss = round(price * 0.9, 2)  # 10% מתחת
                take_profit = round(price * 1.15, 2)  # 15% מעל

                chart_path = generate_chart(t, entry, stop_loss, take_profit)

                caption = (
                    f"*{info.get('shortName', t)}* ({t})\n"
                    f"תחום: {sector}\n"
                    f"מחיר נוכחי: {entry}$\n"
                    f"שינוי יומי: {round(change, 2)}%\n"
                    f"סיבת כניסה:\n- " + "\n- ".join(reasons) + "\n\n"
                    f"💡 אסטרטגיה: {direction}\n"
                    f"🎯 כניסה: {entry}$\n"
                    f"🛑 סטופ לוס: {stop_loss}$\n"
                    f"✅ טייק פרופיט: {take_profit}$\n"
                    f"📊 אחוז רווח פוטנציאלי: {potential}%\n\n"
                    f"ℹ️ תיאור קצר: {summary}..."
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
