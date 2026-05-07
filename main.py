from flask import Flask, request
import telebot
import os
import google.generativeai as genai

# ====== تنظیمات ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
APP_URL = os.environ.get("APP_URL")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ====== تنظیم Gemini ======
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ====== شخصیت ربات ======
PERSONALITY_PROMPT = """
تو یک ربات تراپیست و روانشناس هستی.
جواب‌ها باید:
- خودمونی و صمیمی باشن
- کوتاه و قابل فهم باشن
- قضاوت نکنن
- حس آرامش و امنیت بدن

سبک صحبت:
- محاوره‌ای فارسی
- مهربان و همراه
- کمی انگیزشی

مثال:
- "می‌فهمم، این حس واقعاً می‌تونه سخت باشه 😌"
- "بیا یه راه ساده با هم امتحان کنیم 💪"
"""

# ====== فانکشن پاسخ ======
def get_ai_response(user_message):
    try:
        response = model.generate_content(
            PERSONALITY_PROMPT + "\n\nکاربر: " + user_message
        )
        return response.text
    except Exception as e:
        print("ERROR:", e)
        return "یه مشکلی پیش اومد 😕 دوباره امتحان کن"

# ====== webhook ======
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# ====== هندل پیام ======
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print("پیام دریافت شد:", message.text)  # ← اضافه کن
    reply = get_ai_response(message.text)
    bot.reply_to(message, reply))

# ====== ست کردن webhook ======
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    webhook_url = f"{APP_URL}/{TELEGRAM_TOKEN}"
    success = bot.set_webhook(webhook_url)
    return f"Webhook set: {success}"

# ====== صفحه تست ======
@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است ✅"

# ====== اجرا ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    print("BOT STARTED")
