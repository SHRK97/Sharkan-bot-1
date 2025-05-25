
import os
import telebot
from telebot import types
import json
from datetime import datetime, timedelta

# === Ініціалізація ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# === Стан користувачів ===
user_profiles = {}
trial_users = {}

# === Завантаження профілю ===
def load_profiles():
    global user_profiles
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as f:
            user_profiles = json.load(f)
    except FileNotFoundError:
        user_profiles = {}

def save_profiles():
    with open("user_profiles.json", "w", encoding="utf-8") as f:
        json.dump(user_profiles, f, ensure_ascii=False, indent=4)

# === /start ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "step": "lang_select",
            "language": "ua",
            "registered": str(datetime.now()),
            "premium": False
        }
        trial_users[user_id] = datetime.now() + timedelta(days=3)
        save_profiles()
    send_intro(message)

# === Вітання + пояснення ===
def send_intro(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Продовжити")
    markup.add(btn1)
    text = (
        "Ласкаво просимо до SHARKAN BOT!

"
        "Це не просто бот. Це твій особистий наставник.
"
        "Тут ти отримаєш:
"
        "• Персональні плани на день
"
        "• Мотивацію
"
        "• Тренування та челенджі
"
        "• Прогрес і систему рівнів
"
        "• Доступ до Темної Зони

"
        "Перші 3 дні — безкоштовно. Далі — підписка.

"
        "Для кого цей бот:
"
        "• Для тих, хто хоче стати кращим
"
        "• Для чоловіків, жінок і підлітків
"
        "• Для новачків і досвідчених

"
        "Готовий(-а) розпочати?"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

# === Продовження після інтро ===
@bot.message_handler(func=lambda m: m.text == "Продовжити")
def ask_gender(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Чоловік", "Жінка", "Підліток")
    bot.send_message(message.chat.id, "Хто ти?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Чоловік", "Жінка", "Підліток"])
def ask_goal(message):
    user_id = str(message.from_user.id)
    user_profiles[user_id]["gender"] = message.text
    save_profiles()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Схуднути", "Набрати вагу", "Пройти челендж", "Закалити характер")
    bot.send_message(message.chat.id, "Яка твоя мета тут?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Схуднути", "Набрати вагу", "Пройти челендж", "Закалити характер"])
def show_main_menu(message):
    user_id = str(message.from_user.id)
    user_profiles[user_id]["goal"] = message.text
    save_profiles()
    send_main_menu(message)

# === Головне меню ===
def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("План на сьогодні", "Мотивація", "Тренування")
    markup.add("Челенджі", "Темна Зона", "AI-наставник")
    markup.add("Прогрес", "Поради", "SHARKAN Coins")
    markup.add("Допомога", "Контакти")
    bot.send_message(message.chat.id, "Головне меню:", reply_markup=markup)

# === Обробка кнопок ===
@bot.message_handler(func=lambda message: True)
def menu_router(message):
    if message.text == "План на сьогодні":
        bot.send_message(message.chat.id, "Ось твій план: [приклад тексту]")
    elif message.text == "Мотивація":
        bot.send_message(message.chat.id, "Ти не зупинишся. Ти — SHARKAN.")
    elif message.text == "Тренування":
        bot.send_message(message.chat.id, "Обери тип: Набір / Спалення / Shadow Mode.")
    elif message.text == "Челенджі":
        bot.send_message(message.chat.id, "Обери челендж або створи свій.")
    elif message.text == "Темна Зона":
        bot.send_message(message.chat.id, "Доступ відкриється після першого челенджу.")
    elif message.text == "AI-наставник":
        bot.send_message(message.chat.id, "Постав запитання — AI відповість.")
    elif message.text == "Прогрес":
        bot.send_message(message.chat.id, "Ось твоя статистика та рівень.")
    elif message.text == "Поради":
        bot.send_message(message.chat.id, "Поради від тренерів та дієтологів.")
    elif message.text == "SHARKAN Coins":
        bot.send_message(message.chat.id, "Твій баланс: 0 монет.")
    elif message.text == "Допомога":
        bot.send_message(message.chat.id, "Що тебе цікавить? Напиши сюди.")
    elif message.text == "Контакти":
        bot.send_message(message.chat.id, "Зв’язок з автором: @rulya7777")

# === Старт ===
load_profiles()
bot.polling(none_stop=True)
