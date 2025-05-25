import os
import json
import telebot
from telebot import types

# === Ініціалізація ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
user_profiles = {}

# === Завантаження профілю ===
def load_profiles():
    global user_profiles
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as f:
            user_profiles = json.load(f)
    except FileNotFoundError:
        user_profiles = {}

# === Збереження профілю ===
def save_profiles():
    with open("user_profiles.json", "w", encoding="utf-8") as f:
        json.dump(user_profiles, f, indent=4, ensure_ascii=False)

# === Команда /start ===
@bot.message_handler(commands=["start"])
def start_command(message):
    load_profiles()
    user_id = str(message.from_user.id)
    if user_id not in user_profiles:
        user_profiles[user_id] = {"імʼя": message.from_user.first_name, "вага": "", "ріст": "", "ціль": ""}
        save_profiles()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Мій профіль", "План на сьогодні", "Мотивація")
    bot.send_message(message.chat.id, "Ласкаво просимо до SHARKAN BOT!", reply_markup=markup)

# === Обробка тексту ===
@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    user_id = str(message.from_user.id)
    if message.text == "Мій профіль":
        profile = user_profiles.get(user_id, {})
        response = f"Твій профіль:\nІмʼя: {profile.get('імʼя')}\nВага: {profile.get('вага')}\nРіст: {profile.get('ріст')}\nЦіль: {profile.get('ціль')}"
        bot.send_message(message.chat.id, response)
    elif message.text == "Мотивація":
        bot.send_message(message.chat.id, "Памʼятай, дисципліна — це твоя сила. SHARKAN з тобою.")
    elif message.text == "План на сьогодні":
        bot.send_message(message.chat.id, "Сьогодні тренування на все тіло, пий воду та не зупиняйся!")

load_profiles()
bot.infinity_polling()
