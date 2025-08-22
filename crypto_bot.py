import os, requests
import yfinance as yf
import mplfinance as mpf
from pycoingecko import CoinGeckoAPI
from telegram import Bot

TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")
LUNAR_API_KEY = os.getenv("LUNARCRUSH_API")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TOKEN)
cg = CoinGeckoAPI()

# --- סיווג העסקה (Day / Swing / Watch) ---
def classify_trade(change, volume, market_cap):
    if change and change >= 8 or (volume and market_cap and volume > market_cap * 0.2):
        return "⚡ Day Trade"
    elif change and 3 <= change < 8:
        return "📅 Swing Trade"
    else:
        return "👀 Watchlist"

# --- גרף נרות עם קווים ---
def generate_chart(symbol, entry, stop_loss, take_profit):
    try:
        ticker = f"{symbol.upper()}-USD"
        data = yf.download(ticker, period="7d", interval="1h")
        if data.empty:
            return None

        alines = [
            [data.index[0], entry, data.index[-1], entry],
            [data.index[0], stop_loss, data.index[-1], stop_loss],
            [data.index[0], take_profit, data.index[-1], take_profit]
        ]

        filepath = f"{symbol}.png"
        mpf.plot(data, type="candle", style="charles", volume=True,
                 alines=dict(alines=alines, colors=["blue","red","green"]),
                 savefig=filepath)
        return filepath
    except Exception as e:
        print(f"שגיאה ביצירת גרף עבור {symbol}: {e}")
        return None

# --- CoinGecko Low Caps ---
def get_top_lowcaps():
    coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_asc', per_page=50, page=1)
    return [c for c in coins if c['market_cap'] and c['market_cap']<50_000_000 and c['current_price']<5][:5]

# --- CoinGecko Trending ---
def get_trending_coins():
    trending = cg.get_search_trending()
    return [c['item'] for c in trending['coins'][:5]]

# --- LunarCrush Trending ---
def get_lunar_trending():
    url = "https://lunarcrush.com/api4/public/coins/list/v1"
    headers = {"Authorization": f"Bearer {LUNAR_API_KEY}"}
    r = requests.get(url, headers=headers, params={"limit":5,"sort":"social_volume_24h","desc":True})
    return r.json().get("data", [])

# --- CoinMarketCap Top Movers ---
def get_cmc_movers():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"start": 1, "limit": 10, "sort": "percent_change_24h"}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return []
    data = r.json().get("data", [])
    return data[:5]

# --- שליחת הדו"ח ---
def send_report():
    final_table = []
    charts = []

    # 1. CoinGecko LowCap
    lowcaps = get_top_lowcaps()
    for c in lowcaps:
        entry = round(c['current_price'], 4)
        stop_loss = round(entry * 0.95, 4)
        take_profit = round(entry * 1.1, 4)
        trade_type = classify_trade(c['price_change_percentage_24h'], c['total_volume'], c['market_cap'])
        final_table.append([c['symbol'].upper(), entry, f"{c['price_change_percentage_24h']}%", stop_loss, take_profit, trade_type])
        chart = generate_chart(c['symbol'], entry, stop_loss, take_profit)
        if chart:
            charts.append((chart, c['name']))

    # 2. CoinMarketCap Movers
    cmc = get_cmc_movers()
    for c in cmc:
        entry = round(c['quote']['USD']['price'], 4)
        change = round(c['quote']['USD']['percent_change_24h'], 2)
        stop_loss = round(entry * 0.95, 4)
        take_profit = round(entry * 1.1, 4)
        trade_type = classify_trade(change, c['quote']['USD']['volume_24h'], c['quote']['USD']['market_cap'])
        final_table.append([c['symbol'], entry, f"{change}%", stop_loss, take_profit, trade_type])
        chart = generate_chart(c['symbol'], entry, stop_loss, take_profit)
        if chart:
            charts.append((chart, c['name']))

    # יצירת טבלה Markdown
    if final_table:
        header = "| Symbol | Entry | Change 24h | Stop | Take Profit | Type |\n|--------|-------|------------|------|-------------|------|"
        rows = "\n".join([f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |" for r in final_table])
        bot.send_message(chat_id=CHAT_ID, text="📊 דו\"ח קריפטו יומי:\n\n" + header + "\n" + rows, parse_mode="Markdown")

    # שליחת גרפים
    for chart, name in charts:
        bot.send_photo(chat_id=CHAT_ID, photo=open(chart, 'rb'), caption=f"גרף {name}")

    # Trending (CoinGecko + LunarCrush)
    trending = get_trending_coins()
    if trending:
        hot_list = "\n".join([f"🔥 {c['name']} ({c['symbol']})" for c in trending])
        bot.send_message(chat_id=CHAT_ID, text=f"\n🌟 CoinGecko Trending:\n{hot_list}")

    lunar = get_lunar_trending()
    if lunar:
        lunar_list = "\n".join([f"🌐 {c['name']} ({c['symbol']}) | GalaxyScore: {c.get('galaxy_score','?')}" for c in lunar])
        bot.send_message(chat_id=CHAT_ID, text=f"\n🚀 LunarCrush Trending:\n{lunar_list}")

if __name__ == "__main__":
    send_report()
