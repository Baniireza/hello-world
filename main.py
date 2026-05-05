 import telebot
import os
from telebot import types bot = telebot.TeleBot(os.getenv('BOT_TOKEN')) moods = ['😀 عالی', '😐 معمولی', '😔 بد', '😡 خیلی بد'] @bot.message_handler(commands=['start'])
def start(m): bot.reply_to(m, "🧠 *RavanshenasAVPD*\n/mood حال\n/help راهنما", parse_mode='Markdown') @bot.message_handler(commands=['mood'])
def mood(m): markup = types.InlineKeyboardMarkup(row_width=2) for md in moods: markup.add(types.InlineKeyboardButton(md, callback_data=f"mood_{md}")) bot.send_message(m.chat.id, "💭 حال امروزت؟", reply_markup=markup) @bot.callback_query_handler(func=lambda c: c.data.startswith('mood_'))
def cb(c): bot.answer_callback_query(c.id) bot.send_message(c.message.chat.id, f"✅ ثبت شد: {c.data[5:]}") @bot.message_handler(commands=['help'])
def h(m): bot.reply_to(m, "/start شروع\n/mood حال\n/help راهنما") print("✅ فعال")
bot.infinity_polling (non_stop=True)
