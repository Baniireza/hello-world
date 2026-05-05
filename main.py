import telebot
bot = telebot.TeleBot('8686376012:AAFAx_gjj53cuLDRkr3LJsxclca6yhdMeC8')
@bot.message_handler(commands=['start'])
def start(message): bot.reply_to(message, 'سلام! بوت کار کرد 🚀')
bot.polling
