import os
import requests
from flask import Flask, request
import telebot
import logging

logging.basicConfig(level=logging.INFO)
telebot.logger.setLevel(logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
APP_URL = os.environ.get("APP_URL")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

MODEL_NAME = "openai/gpt-oss-120b:free"

SYSTEM_PROMPT = "تو یک ربات فارسی صمیمی هستی. کوتاه و دوستانه جواب بده."


# ======================
# AI FUNCTION (FIXED)
# ======================

def get_ai_response(user_message):

    try:
        print("➡️ Sending request to OpenRouter...")

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            },
            timeout=60
        )

        print("STATUS:", r.status_code)

        # 🔥 اگر خطا بود
        if r.status_code != 200:
            print("OPENROUTER ERROR:", r.text)
            return "مشکل در اتصال به AI 😕"

        data = r.json()

        reply = data["choices"][0]["message"]["content"]

        return reply

    except Exception as e:
        print("AI ERROR:", str(e))
        return "خطا در پردازش AI"


# ======================
# MESSAGE HANDLER (FIXED)
# ======================

@bot.message_handler(func=lambda m: True)
def handle_message(message):

    try:
        print("NEW MESSAGE")

        # 🔥 FIX: جلوگیری از None
        user_text = message.text or ""

        if not user_text.strip():
            bot.reply_to(message, "فقط متن بفرست 🙂")
            return

        print("USER:", user_text)

        reply = get_ai_response(user_text)

        print("BOT:", reply)

        bot.send_message(message.chat.id, reply)

    except Exception as e:
        print("HANDLER ERROR:", str(e))


# ======================
# WEBHOOK (SIMPLIFIED)
# ======================

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_str = request.get_json(force=True)

        print("RAW UPDATE:", json_str)

        update = telebot.types.Update.de_json(json_str)

        print("PARSED")

        bot.process_new_updates([update])

        print("PROCESSED")

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "ERROR", 500


# ======================
# SET WEBHOOK
# ======================

@app.route("/set_webhook")
def set_webhook():

    try:
        bot.remove_webhook()

        webhook_url = f"{APP_URL}/webhook"

        return str(bot.set_webhook(url=webhook_url))

    except Exception as e:
        return str(e)


@app.route("/")
def home():
    return "Bot Running ✅"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
