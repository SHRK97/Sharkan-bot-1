import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "План на сьогодні", "Мотивація", "Тренування", "Челленджі",
        "Питання до SHARKAN AI", "Темна Зона", "Статистика і Прогрес",
        "Магазин", "Музика", "Поради від топ-тренерів",
        "SHARKAN Coins", "Допомога / FAQ", "Контакти / Співпраця"
    ]
    for btn in buttons:
        markup.add(types.KeyboardButton(btn))

    bot.send_message(message.chat.id,
        "Ласкаво просимо до SHARKAN BOT. Твій шлях починається зараз.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_buttons(message):
    if message.text == "План на сьогодні":
        bot.send_message(message.chat.id, "Формую персональний план на день...")
    elif message.text == "Мотивація":
        bot.send_message(message.chat.id, "Завантажую цитати, голос SHARKAN і відео...")
    elif message.text == "Тренування":
        bot.send_message(message.chat.id, "Обери тип тренування: ціль, рівень, Shadow mode...")
    elif message.text == "Челленджі":
        bot.send_message(message.chat.id, "Ось твій список челленджів...")
    elif message.text == "Питання до SHARKAN AI":
        bot.send_message(message.chat.id, "Запитай мене про харчування, тренування або дисципліну.")
    elif message.text == "Темна Зона":
        bot.send_message(message.chat.id, "Темна Зона заблокована. Пройди хоча б 1 челлендж.")
    elif message.text == "Статистика і Прогрес":
        bot.send_message(message.chat.id, "Завантажую твою статистику...")
    elif message.text == "Магазин":
        bot.send_message(message.chat.id, "SHARKAN одяг скоро буде доступний.")
    elif message.text == "Музика":
        bot.send_message(message.chat.id, "Обери стиль музики: oldschool, техно, французький реп...")
    elif message.text == "Поради від топ-тренерів":
        bot.send_message(message.chat.id, "Поради завантажуються...")
    elif message.text == "SHARKAN Coins":
        bot.send_message(message.chat.id, "У тебе 0 монет. Пройди челленджі, щоб отримати більше!")
    elif message.text == "Допомога / FAQ":
        bot.send_message(message.chat.id, "Тут буде інструкція, як користуватись ботом.")
    elif message.text == "Контакти / Співпраця":
        bot.send_message(message.chat.id, "Звʼяжись із засновником: @rulya7777")
    else:
        bot.send_message(message.chat.id, "Вибач, не розпізнаю команду. Обери з меню.")

bot.infinity_polling()
