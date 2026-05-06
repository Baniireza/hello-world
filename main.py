from flask import Flask, request
import telebot
from openai import OpenAI
import os

# ====== تنظیمات ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GAPGPT_API_KEY = os.environ.get("GAPGPT_API_KEY")
APP_URL = os.environ.get("APP_URL")  # URL برنامه روی Render

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ====== ایجاد کلاینت GapGPT ======
# نسخه‌ای از OpenAI که با GapGPT سازگار است
client = OpenAI(
    api_key=GAPGPT_API_KEY,
    base_url="https://api.gapgpt.app/v1"
)

# ====== شخصیت ربات ======
PERSONALITY_PROMPT = """
تو یه تراپیست و روانشناس باحال و منطقی هستی.
جواب‌ها باید خودمونی، مهربان و صمیمی باشن.
هیچ وقت قضاوت نکن و مودب باش.
وقتی کسی احساساتش رو بیان می‌کنه، با دقت گوش بده و پاسخ بده که انگار یک دوست حرفه‌ای و قابل اعتماد هستی.
مثال‌ها:
- "می‌فهمم، این حس واقعاً سخت می‌تونه باشه 😌، بیا با هم یه راه ساده پیدا کنیم."
- "می‌دونم این موضوع نگرانت کرده، اما قدم به قدم با هم جلو می‌ریم 💪"
"""

# ====== فانکشن پاسخ هوش مصنوعی ======
def get_ai_response(user_message):
    response = client.chat.completions.create(
        model="gpt-4o",  # مدل GapGPT
        messages=[
            {"role": "system", "content": PERSONALITY_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content

# ====== هندل پیام‌های تلگرام از طریق وب‌هوک ======
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    ai_reply = get_ai_response(message.text)
    bot.reply_to(message, ai_reply)

# ====== فعال کردن وب‌هوک ======
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    webhook_url = f"{APP_URL}/{TELEGRAM_TOKEN}"
    success = bot.set_webhook(webhook_url)
    return f"Webhook set: {success}"

# ====== صفحه اصلی ======
@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است ✅"

# ====== اجرا ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
