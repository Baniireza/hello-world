from flask import Flask, request
import telebot
import openai
import os

# ====== تنظیمات ======
TELEGRAM_TOKEN = "توکن_ربات_تو"  # از BotFather بگیر
OPENAI_API_KEY = "کلید_API_تو"

openai.api_key = OPENAI_API_KEY

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ====== شخصیت ربات ======
PERSONALITY_PROMPT = """
تو یه کلانتر باحال و باهوش و منطقی هستی. 
جواب‌ها باید خودمونی، بامزه و محترمانه باشه.
هیچ وقت جواب تند یا توهین‌آمیز نده.
"""

# ====== فانکشن پاسخ هوش مصنوعی ======
def get_ai_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": PERSONALITY_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    return response['choices'][0]['message']['content']

# ====== هندل پیام‌ها ======
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    ai_reply = get_ai_response(user_text)
    bot.reply_to(message, ai_reply)

# ====== فلکس وب‌هوک ساده ======
@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است ✅"

# ====== اجرا ======
if __name__ == "__main__":
    # اجرای همزمان Flask و Telebot
    from threading import Thread

    # اجرای ربات تلگرام در یک thread
    def run_bot():
        bot.infinity_polling()

    Thread(target=run_bot).start()

    # اجرای فلکس
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
