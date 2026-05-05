import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get("BOT_TOKEN")  # توکن ربات
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # URL وبهوک

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# مثال دستور ساده
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "سلام! ربات شما آماده است 😎")

# وبهوک برای Render
@app.route("/" + TOKEN, methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# صحت وبهوک
@app.route("/")
def index():
    return "ربات آنلاین است ✅"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
