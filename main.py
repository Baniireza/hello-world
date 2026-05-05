# main.py
import os
from flask import Flask, request
import telebot
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# --- توکن و وبهوک ---
TOKEN = os.environ.get("BOT_TOKEN")  # توکن ربات
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # URL وبهوک

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- مدل AI سبک ---
model_name = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def ai_reply(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    # محدودیت max_length برای RAM پایین
    outputs = model.generate(**inputs, max_length=50, do_sample=True, top_k=50)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# --- Mood دکمه‌ها ---
from telebot import types
moods = ['😀 عالی','😐 معمولی','😔 بد','😡 خیلی بد']

@bot.message_handler(commands=['mood'])
def mood_handler(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for md in moods:
        markup.add(types.InlineKeyboardButton(md, callback_data=f"mood_{md}"))
    bot.send_message(message.chat.id, "💭 حال امروزت؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('mood_'))
def cb(c):
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, f"✅ ثبت شد: {c.data[5:]}")

# --- دستور شروع ---
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "سلام! ربات AI شما آماده است 😎\n\n/mood حال\n/help راهنما")

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.reply_to(message, "/start شروع\n/mood حال\n/help راهنما")

# --- پاسخ به همه پیام‌ها با AI ---
@bot.message_handler(func=lambda m: True)
def all_messages(message):
    try:
        reply = ai_reply(message.text)
    except Exception as e:
        reply = "❌ خطا در پاسخ دادن! هنوز سرور سنگینه 😅"
    bot.reply_to(message, reply)

# --- وبهوک برای Render ---
@app.route("/" + TOKEN, methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# --- تست آنلاین ---
@app.route("/")
def index():
    return "ربات آنلاین است ✅"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
