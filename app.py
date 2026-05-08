import os
from flask import Flask, request
import telebot
from huggingface_hub import InferenceClient

# ======================
# ENV
# ======================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]
APP_URL = os.environ["APP_URL"]

# ======================
# TELEGRAM
# ======================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ======================
# FLASK
# ======================

app = Flask(__name__)

# ======================
# HF CLIENT
# ======================

client = InferenceClient(
    token=HF_TOKEN
)

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct:scaleway"

# ======================
# SYSTEM PROMPT
# ======================

SYSTEM_PROMPT = """
تو یک ربات صمیمی و دوستانه فارسی هستی.
کوتاه و طبیعی جواب بده.
"""

# ======================
# AI FUNCTION
# ======================

def get_ai_response(user_message):

    try:

        print("Sending request to HF...")

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
            max_tokens=200,
            temperature=0.7
        )

        print("HF RESPONSE:")
        print(completion)

        reply = completion.choices[0].message.content

        return reply

    except Exception as e:

        print("AI ERROR:")
        print(str(e))

        return f"خطا: {str(e)}"

# ======================
# TELEGRAM HANDLER
# ======================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    try:

        print("NEW MESSAGE")

        user_text = message.text

        print("USER SAID:", user_text)

        reply = get_ai_response(user_text)

        print("BOT REPLY:", reply)

        bot.reply_to(message, reply)

    except Exception as e:

        print("HANDLER ERROR:")
        print(str(e))

# ======================
# WEBHOOK
# ======================

@app.route("/webhook", methods=["POST"])
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

    bot.remove_webhook()

    webhook_url = f"{APP_URL}/webhook"

    result = bot.set_webhook(url=webhook_url)

    return str(result)

# ======================
# HOME
# ======================

@app.route("/")
def home():
    return "Bot Running ✅"

# ======================
# RUN
# ======================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
