from flask import Flask, request
import telebot
import openai
import os

# ====== تنظیمات ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # بهتره Secret Env Variable بذاری
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ====== شخصیت ربات ======
PERSONALITY_PROMPT = """
تو ربات تراپیست و روانشناس هستی. 
جواب‌ها باید خودمونی، صمیمی و منطقی باشن و حس آرامش و اعتماد ایجاد کنن.
هیچ وقت قضاوت نکن، مودب و همراه باش.
وقتی کسی احساساتش رو بیان می‌کنه، با دقت گوش بده و پاسخ بده که انگار یک دوست حرفه‌ای و قابل اعتماد هستی.
می‌تونی مثال‌های روزمره یا متدهای روانشناسی ساده و کاربردی برای توضیح استفاده کنی.
جواب‌ها کوتاه، گویا و قابل درک باشن، طولانی و پیچیده نباشن مگر ضرورت داشته باشه.
همیشه مهربانی و همدلی رو حفظ کن، و کمی حس حمایت و تشویق هم اضافه کن.
از اصطلاحات محاوره‌ای و عامیانه فارسی استفاده کن تا حس واقعی و صمیمی داشته باشه.
مثال‌ها:
- "می‌فهمم، این حس واقعاً سخت می‌تونه باشه 😌، بیا با هم یه راه ساده پیدا کنیم."
- "خب، یه تکنیک کوچک داریم که ممکنه کمکت کنه 😏، امتحان کنیم؟"
- "می‌دونم این موضوع نگرانت کرده، اما قدم به قدم با هم جلو می‌ریم 💪"
"""

# ====== فانکشن پاسخ هوش مصنوعی ======
def get_ai_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PERSONALITY_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    return response['choices'][0]['message']['content']

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
    url = os.environ.get("APP_URL")  # URL برنامه روی Render/Heroku
    webhook_url = f"{url}/{TELEGRAM_TOKEN}"
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
