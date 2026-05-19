import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ======================
# ENV
# ======================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
APP_URL = os.environ.get("APP_URL")

# ======================
# AI SETTINGS
# ======================

MODEL_NAME = "openai/gpt-oss-120b:free"

SYSTEM_PROMPT = "تو یک ربات فارسی صمیمی هستی. کوتاه و دوستانه جواب بده."

# ======================
# OPENROUTER
# ======================

def get_ai_response(user_text):

    try:
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
                    {"role": "user", "content": user_text}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            },
            timeout=60
        )

        print("OPENROUTER STATUS:", r.status_code)

        if r.status_code != 200:
            print("ERROR:", r.text)
            return "مشکل در اتصال به AI 😕"

        return r.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI ERROR:", e)
        return "خطا در AI"


# ======================
# WEBHOOK
# ======================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:
        update = request.get_json()

        print("RAW UPDATE:", update)

        message = update.get("message", {})
        text = message.get("text")
        chat_id = message.get("chat", {}).get("id")

        # ignore empty messages
        if not text or not chat_id:
            return "OK", 200

        print("USER:", text)

        reply = get_ai_response(text)

        print("BOT:", reply)

        # send message to Telegram
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": reply
            }
        )

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
        url = f"{APP_URL}/webhook"

        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            params={"url": url}
        )

        return r.text

    except Exception as e:
        return str(e)


# ======================
# HOME
# ======================

@app.route("/")
def home():
    return "Bot is running ✅"


# ======================
# RUN
# ======================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
