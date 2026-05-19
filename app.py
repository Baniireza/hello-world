import os
import requests
from flask import Flask, request
import telebot

# ======================
# ENV
# ======================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
APP_URL = os.environ.get("APP_URL")

# ======================
# TELEGRAM
# ======================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ======================
# FLASK
# ======================

app = Flask(__name__)

# ======================
# MODEL
# ======================

MODEL_NAME = "inclusionai/ring-2.6-1t:free"

SYSTEM_PROMPT = """
تو یک ربات فارسی صمیمی و طبیعی هستی.
کوتاه و دوستانه جواب بده.
"""

# ======================
# AI FUNCTION
# ======================

def get_ai_response(user_message):

    try:

        print("Sending request to OpenRouter...")

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.7
            },
            timeout=60
        )

        print("STATUS CODE:")
        print(response.status_code)

        print("RAW RESPONSE:")
        print(response.text)

        data = response.json()

        reply = data["choices"][0]["message"]["content"]

        return reply

    except Exception as e:

        print("AI ERROR:")
        print(str(e))

        return f"خطا: {str(e)}"

# ======================
# MESSAGE HANDLER
# ======================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    try:

        print("NEW MESSAGE RECEIVED")

        user_text = message.text

        print("USER:", user_text)

        reply = get_ai_response(user_text)

        print("BOT:", reply)

        bot.reply_to(message, reply)

    except Exception as e:

        print("HANDLER ERROR:")
        print(str(e))

# ======================
# WEBHOOK
# ======================

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():

    try:

        json_str = request.get_data().decode("utf-8")

        update = telebot.types.Update.de_json(json_str)

        bot.process_new_updates([update])

        return "OK", 200

    except Exception as e:

        print("WEBHOOK ERROR:")
        print(str(e))

        return "ERROR", 500

# ======================
# SET WEBHOOK
# ======================

@app.route("/set_webhook")
def set_webhook():

    try:

        bot.remove_webhook()

        webhook_url = f"{APP_URL}/{TELEGRAM_TOKEN}"

        result = bot.set_webhook(url=webhook_url)

        return str(result)

    except Exception as e:

        return str(e)

# ======================
# HOME
# ======================

@app.route("/")
def home():
    return "Psycho Bot Running ✅"

# ======================
# RUN
# ======================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
