import os
from flask import Flask, request
import telebot
from huggingface_hub import InferenceClient

# ===== ENV =====
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]
APP_URL = os.environ["APP_URL"]

# ===== BOT =====
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ===== MISTRAL CLIENT =====
client = InferenceClient(
    api_key=HF_TOKEN,
)

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai"

# ===== PROMPT شخصیت =====
SYSTEM_PROMPT = """
تو یک ربات روانشناس و همراه هستی.
سبک پاسخ:
- فارسی محاوره‌ای
- کوتاه و ساده
- بدون قضاوت
- آرام و همدلانه
"""

def get_ai_response(user_message):
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return completion.choices[0].message["content"]

    except Exception as e:
        print("ERROR:", e)
        return "الان مشکلی در ارتباط با مدل پیش اومده 😕"

# ===== TELEGRAM HANDLER =====
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print("USER:", message.text)

    reply = get_ai_response(message.text)

    bot.reply_to(message, reply)

# ===== WEBHOOK =====
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(
        request.get_data().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "OK", 200

# ===== SET WEBHOOK =====
@app.route("/set_webhook")
def set_webhook():
    url = f"{APP_URL}/{TELEGRAM_TOKEN}"
    return str(bot.set_webhook(url))

# ===== HEALTH CHECK =====
@app.route("/")
def home():
    return "Bot is running ✅"

# ===== RUN =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
