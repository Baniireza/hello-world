from flask import Flask, request
import telebot
import os
import requests

# ====== ENV ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
APP_URL = os.environ.get("APP_URL")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ====== مدل HuggingFace ======
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceTB/SmolLM2-1.7B-Instruct"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

PERSONALITY_PROMPT = """
تو یک ربات روانشناس و همراه هستی.
سبک پاسخ:
- خودمونی و فارسی محاوره‌ای
- کوتاه و ساده
- بدون قضاوت
- آرامش‌بخش و حمایتی
"""

def get_ai_response(user_message):
    try:
        payload = {
            "inputs": PERSONALITY_PROMPT + "\n\nکاربر: " + user_message
        }

        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()

        # بعضی وقت‌ها لیست برمیگردونه
        if isinstance(result, list):
            return result[0].get("generated_text", "...")
        
        return "یه مشکلی پیش اومد 😕"
    
    except Exception as e:
        print("ERROR:", e)
        return "خطا در اتصال به مدل 😕"

# ====== Telegram handler ======
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print("MSG:", message.text)
    reply = get_ai_response(message.text)
    bot.reply_to(message, reply)

# ====== Webhook ======
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# ====== set webhook ======
@app.route("/set_webhook")
def set_webhook():
    url = f"{APP_URL}/{TELEGRAM_TOKEN}"
    return str(bot.set_webhook(url))

# ====== test route ======
@app.route("/")
def home():
    return "Bot is alive ✅"

# ====== run ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
