import os
from telegram import Bot

# טוקן וצ'אט איידי מה־Secrets
TOKEN = os.getenv("TOKEN_CRYPTO")
CHAT_ID = os.getenv("CHAT_ID_CRYPTO")

bot = Bot(token=TOKEN)

if __name__ == "__main__":
    try:
        bot.send_message(chat_id=CHAT_ID, text="✅ בדיקת קריפטו בוט הצליחה! הבוט מחובר 🚀")
        print("הודעת בדיקה נשלחה בהצלחה לטלגרם.")
    except Exception as e:
        print(f"שגיאה בשליחת הודעת בדיקה: {e}")
