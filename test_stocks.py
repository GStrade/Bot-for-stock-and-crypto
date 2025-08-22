import os
from telegram import Bot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")

if not TOKEN or not CHAT_ID:
    raise ValueError("❌ חסר TOKEN_STOCKS או CHAT_ID_STOCKS")

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text="✅ בדיקת בוט מניות הצליחה!")
