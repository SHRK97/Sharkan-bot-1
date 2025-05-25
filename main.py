import os
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def send_audio(chat_id, filename, caption=""):
    with open(f"audio/{filename}", "rb") as audio:
        bot.send_audio(chat_id, audio, caption=caption)

@bot.message_handler(commands=['start'])
def start(message):
    send_audio(message.chat.id, "welcome.mp3", "Ласкаво просимо до SHARKAN BOT!")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "План на сьогодні", "Мотивація", "Тренування", "Челленджі",
        "Питання до SHARKAN AI", "Shadow Mode", "Темна Зона",
        "Статистика і Прогрес", "SHARKAN Coins", "Вода / Харчування"
    ]
    for b in buttons:
        markup.add(b)
    bot.send_message(message.chat.id, "Обери розділ:", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def menu(m):
    texts = {
        "План на сьогодні": ("plan.mp3", "Ось твій план дій."),
        "Мотивація": ("motivation.mp3", "Слухай і дій."),
        "Тренування": ("training.mp3", "Настав час змінювати тіло."),
        "Челленджі": ("challenge.mp3", "Обери виклик."),
        "Питання до SHARKAN AI": ("ai.mp3", "Став своє питання."),
        "Shadow Mode": ("shadow.mp3", "Режим Самотності активовано."),
        "Темна Зона": ("darkzone.mp3", "Вхід дозволено лише обраним."),
        "Статистика і Прогрес": ("stats.mp3", "Ось твій прогрес."),
        "SHARKAN Coins": ("coins.mp3", "Твій баланс оновлено."),
        "Вода / Харчування": ("water_food.mp3", "Пий воду. Їж правильно.")
    }
    if m.text in texts:
        file, caption = texts[m.text]
        send_audio(m.chat.id, file, caption)
    else:
        bot.send_message(m.chat.id, "Розділ у розробці або невідомий.")

bot.infinity_polling()
