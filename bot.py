import telebot

TOKEN = "8970077275:AAH1AVCjxSvm9t7Md0osBjdHDYjsiP3Rk9k"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Salom!")

if __name__ == '__main__':
    print("Bot ishga tushdi...")
    bot.infinity_polling()
