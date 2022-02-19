import telebot
from threading import Thread
startdate = dt.now()

from info import TRUSTED_ID, BOT_KEY

bot = telebot.TeleBot(BOT_KEY)

@bot.message_handler(commands=['start', 'pause', 'status', 'kill'])
def handle_commands(message):
    if (dt.now()-startdate).seconds < 2:
        return
    global pause
    if message.from_user.id == TRUSTED_ID:
        if message.text == "/start":
            if pause:
                pause = False
                bot.reply_to(message, "Bot now running.")
            else:
                bot.reply_to(message, "Bot already running.")
        if message.text == "/pause":
            if pause:
                bot.reply_to(message, "Bot already paused.")
            else:
                bot.reply_to(message, "Bot paused.")
                pause = True
                logAll("Bot paused.")
        if message.text == "/status":
            reply = "Actual status:\nRunning = " + ("✅" if not pause else "❌") + "\nEnough balance (>=1 USDT) = " + ("✅" if balance>=1 else "❌")
            bot.reply_to(message, reply)
        if message.text == "/kill":
            global end
            end = True
            bot.reply_to(message, "Killing bot.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.from_user.id == TRUSTED_ID:
        print(message.text)
        bot.reply_to(message, message.text)

def polling():
    bot.polling()

Thread(target=polling).start()