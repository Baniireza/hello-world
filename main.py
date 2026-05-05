import telebot
bot = telebot.TeleBot('8686376012:AAEj4x4GDEs-_4E9jbH5MbPrMYJwYEoWCco')
@bot.message_handler(commands=['start'])
def start(message): bot.reply_to(message, 'سلام! بوت کار کرد 🚀')
bot.polling(none_stop=True)
