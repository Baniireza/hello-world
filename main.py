from flask import Flask, request
import telebot
import os
import requests

# =========================
# ENV VARIABLES
# =========================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
APP_URL = os.environ.get("APP_URL")

# =========================
# TELEGRAM BOT
# =========================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# =========================
# FLASK
# =========================

app = Flask(__name__)

# =========================
# HUGGING FACE MODEL
# =========================

API_URL = "https://api-inference.huggingface.co/models/google/gemma-4-31B-it"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# =========================
# AI RESPONSE
# =========================

def get_ai_response(user_message):
    try:

        prompt = f"""
تو یک همراه روانشناس مهربان هستی.

ویژگی پاسخ‌ها:
- فارسی
- کوتاه
- آرامش‌بخش
- دوستانه
- بدون قضاوت
- خودمونی

کاربر:
{user_message}

پاسخ:
"""

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 120,
                "temperature": 0.7,
                "return_full_text": False
            }
        }

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("RAW:", response.text)

        result = response.json()

        # موفق
        if isinstance(result, list):
            return result[0].get("generated_text", "🤍")

        # خطای مدل
        if "error" in result:
            return "خطای مدل:\n" + result["error"]

        return "یه مشکلی پیش اومد 😕"

    except Exception as e:
        print("ERROR:", e)
        return "ارتباط با AI برقرار نشد 😕"

# =========================
# TELEGRAM MESSAGE HANDLER
# =========================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    print("MESSAGE:", message.text)

    reply = get_ai_response(message.text)

    bot.reply_to(message, reply)

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

    bot.remove_webhook()

    webhook_url = f"{APP_URL}/{TELEGRAM_TOKEN}"

    success = bot.set_webhook(url=webhook_url)

    return {
        "success": success,
        "webhook_url": webhook_url
    }

# =========================
# HOME
# =========================

@app.route("/")
def home():
    return "Bot is alive ✅"

# =========================
# RUN
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
