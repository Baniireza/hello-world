import os
from flask import Flask, request
import telebot
from huggingface_hub import InferenceClient

# =========================
# ENV
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]
APP_URL = os.environ["APP_URL"]

# =========================
# TELEGRAM BOT
# =========================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# =========================
# FLASK
# =========================

app = Flask(__name__)

# =========================
# HUGGING FACE CLIENT
# =========================

client = InferenceClient(
    token=HF_TOKEN
)

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"

# =========================
# شخصیت ربات
# =========================

SYSTEM_PROMPT = """
تو یک ربات همراه و صمیمی هستی.

ویژگی‌ها:
- فارسی محاوره‌ای
- کوتاه و طبیعی
- دوستانه
- بدون قضاوت
- مناسب گفتگو در گروه تلگرام
- ایموجی زیاد استفاده نکن
"""

# =========================
# AI RESPONSE
# =========================

def get_ai_response(user_message):

    try:

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=300,
            temperature=0.7,
        )

        reply = completion.choices[0].message.content

        return reply

    except Exception as e:

        print("ERROR:", e)

        return "فعلا یه مشکلی پیش اومده 😕"

# =========================
# MESSAGE HANDLER
# =========================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    try:

        user_text = message.text

        if not user_text:
            return

        print("USER:", user_text)

        reply = get_ai_response(user_text)

        bot.reply_to(message, reply)

    except Exception as e:

        print("MESSAGE ERROR:", e)

# =========================
# WEBHOOK
# =========================

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():

    json_str = request.get_data().decode("utf-8")

    update = telebot.types.Update.de_json(json_str)

    bot.process_new_updates([update])

    return "OK", 200

# =========================
# SET WEBHOOK
# =========================

@app.route("/set_webhook")
def set_webhook():

    webhook_url = f"{APP_URL}/{TELEGRAM_TOKEN}"

    bot.remove_webhook()

    result = bot.set_webhook(url=webhook_url)

    return str(result)

# =========================
# HOME
# =========================

@app.route("/")
def home():
    return "Llama Bot Running ✅"

# =========================
# RUN
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
