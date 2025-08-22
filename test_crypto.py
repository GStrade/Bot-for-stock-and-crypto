import os
from telegram import Bot

TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")
bot = Bot(token=TOKEN)

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="✅ בדיקת חיבור: בוט הקריפטו מחובר ועובד!")
