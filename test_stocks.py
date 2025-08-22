test_stocks.pyimport os
from telegram import Bot

TOKEN = os.getenv("TOKEN_STOCKS")
CHAT_ID = os.getenv("CHAT_ID_STOCKS")
bot = Bot(token=TOKEN)

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="✅ בדיקת חיבור: בוט המניות מחובר ועובד!")
