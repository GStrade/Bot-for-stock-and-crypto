import os
import telebot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")

print("BOT TOKEN:", TOKEN[:10] + "..." if TOKEN else "❌ ריק")
print("CHAT ID:", CHAT_ID if CHAT_ID else "❌ ריק")

if not TOKEN or not CHAT_ID:
    raise ValueError("חסר TOKEN או CHAT_ID")

bot = telebot.TeleBot(TOKEN)
bot.send_message(CHAT_ID, "✅ בדיקה: הבוט למניות מחובר בהצלחה!")

print("הודעת בדיקה נשלחה לטלגרם")
