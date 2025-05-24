
import os
import json
import telebot
from telebot import types

# === Инициализация ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
user_profiles = {}

# === Загрузка профилей ===
def load_profiles():
    global user_profiles
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as f:
            user_profiles = json.load(f)
    except FileNotFoundError:
        user_profiles = {}

# === Сохранение профилей ===
def save_profiles():
    with open("user_profiles.json", "w", encoding="utf-8") as f:
        json.dump(user_profiles, f, ensure_ascii=False, indent=4)

# === Команда /start ===
@bot.message_handler(commands=["start"])
def start_command(message):
    user_id = str(message.from_user.id)
    load_profiles()
    if user_id not in user_profiles:
        user_profiles[user_id] = {}
        save_profiles()
    bot.send_message(message.chat.id, "Ласкаво просимо до SHARKAN BOT. Введіть /профіль щоб почати.")

# === Команда /профіль ===
@bot.message_handler(commands=["профіль"])
def ask_profile(message):
    user_id = str(message.from_user.id)
    msg = bot.send_message(message.chat.id, "Введи свій ріст у см (наприклад 180):")
    bot.register_next_step_handler(msg, get_height)

def get_height(message):
    user_id = str(message.from_user.id)
    user_profiles[user_id] = {"height": message.text}
    msg = bot.send_message(message.chat.id, "Введи свою вагу у кг (наприклад 75):")
    bot.register_next_step_handler(msg, get_weight)

def get_weight(message):
    user_id = str(message.from_user.id)
    user_profiles[user_id]["weight"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Схуднення", "Набір ваги", "Підтримка форми")
    msg = bot.send_message(message.chat.id, "Яка твоя ціль?", reply_markup=markup)
    bot.register_next_step_handler(msg, get_goal)

def get_goal(message):
    user_id = str(message.from_user.id)
    user_profiles[user_id]["goal"] = message.text
    save_profiles()
    bot.send_message(message.chat.id, "Профіль збережено! Введи /мійпрофіль щоб побачити свої дані.")

# === Команда /мійпрофіль ===
@bot.message_handler(commands=["мійпрофіль"])
def show_profile(message):
    user_id = str(message.from_user.id)
    load_profiles()
    if user_id in user_profiles:
        profile = user_profiles[user_id]
        text = f"Ріст: {profile.get('height')} см
Вага: {profile.get('weight')} кг
Ціль: {profile.get('goal')}"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "Профіль не знайдено. Введи /профіль щоб створити.")

# === Запуск ===
if __name__ == "__main__":
    load_profiles()
    bot.polling(none_stop=True)
