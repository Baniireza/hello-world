import os
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # مثلا: https://yourapp.onrender.com/

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

moods = ['😀 عالی', '😐 معمولی', '😔 بد', '😡 خیلی بد']

# ---------- Handlers ----------
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🧠 سلام! من ربات شخصی تو هستم.\n/mood حال امروزت\n/help راهنما")

@bot.message_handler(commands=['mood'])
def mood_handler(m):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for md in moods:
        markup.add(types.InlineKeyboardButton(md, callback_data=f"mood_{md}"))
    bot.send_message(m.chat.id, "💭 حال امروزت چطوره؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('mood_'))
def cb(c):
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, f"✅ ثبت شد: {c.data[5:]}")

@bot.message_handler(commands=['help'])
def help_handler(m):
    bot.reply_to(m, "/start شروع\n/mood حال\n/help راهنما")

# ---------- Webhook ----------
@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

@app.route('/')
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
