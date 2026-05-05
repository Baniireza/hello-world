import telebot
import os
from telebot import types # توکن از Environment میخونه
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) @bot.message_handler(commands=['start'])
def start_message(message): bot.reply_to(message, "🟢 RavanshenasAVPD آماده!\n/start - شروع\n/help - راهنما") @bot.message_handler(commands=['help'])
def help_message(message): help_text = """
🤖 دستورات:
/start - شروع بات
/help - راهنما """ bot.reply_to(message, help_text) @bot.message_handler(func=lambda message: True)
def echo_all(message): bot.reply_to(message, f"پیام شما: {message.text}") print("بات شروع شد...")
bot.infinity_polling
