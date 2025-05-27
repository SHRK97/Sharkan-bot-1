import os
import json
import logging
from datetime import datetime
from telebot import TeleBot, types

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)
ADMIN_ID = 693609628
VERSION = "SHARKAN BOT v1.0 — MULTILANG + GENDER"

logging.basicConfig(
    level=logging.INFO,
    filename="bot.log",
    filemode="a",
    format="%(asctime)s — %(levelname)s — %(message)s"
)

USER_PROFILE_FILE = "user_profiles.json"
if os.path.exists(USER_PROFILE_FILE):
    with open(USER_PROFILE_FILE, "r") as f:
        user_profiles = json.load(f)
else:
    user_profiles = {}

def save_profiles():
    try:
        with open(USER_PROFILE_FILE, "w") as f:
            json.dump(user_profiles, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"[SAVE_PROFILE_ERROR] {e}")

LANGUAGES = {'ua': 'Українська', 'ru': 'Русский', 'en': 'English'}
user_lang = {}

@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    for code, name in LANGUAGES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"lang_{code}"))
    bot.send_message(message.chat.id, "👋 Обери мову / Choose your language / Выберите язык:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    chat_id = call.message.chat.id
    user_id = str(call.from_user.id)
    lang = call.data.split("_")[1]

    user_profiles[user_id] = user_profiles.get(user_id, {})
    user_profiles[user_id]["language"] = lang
    user_lang[user_id] = lang
    save_profiles()

    if lang == "ua":
        text = "✅ Твоя мова — українська. Вітаємо в SHARKAN BOT!"
"👤 Обери свою стать:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Я — чоловік", callback_data="gender_male"),
            types.InlineKeyboardButton("Я — жінка", callback_data="gender_female")
        )
    elif lang == "ru":
        text = "✅ Ваш язык — русский. Добро пожаловать в SHARKAN BOT!"
"👤 Выбери свой пол:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Я — мужчина", callback_data="gender_male"),
            types.InlineKeyboardButton("Я — женщина", callback_data="gender_female")
        )
    else:
        text = "✅ Your language is English. Welcome to SHARKAN BOT!"
"👤 Select your gender:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("I am a man", callback_data="gender_male"),
            types.InlineKeyboardButton("I am a woman", callback_data="gender_female")
        )

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender(call):
    chat_id = call.message.chat.id
    user_id = str(call.from_user.id)
    gender = call.data.split("_")[1]  # male or female

    user_profiles[user_id]["gender"] = gender
    save_profiles()

    lang = user_lang.get(user_id, "ua")
    confirm = {
        "ua": "✅ Стать збережено.",
        "ru": "✅ Пол сохранён.",
        "en": "✅ Gender saved."
    }

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id)
    bot.send_message(chat_id, confirm.get(lang, "✅ Done."))
    menu_from_id(chat_id, user_id)

def menu_from_id(chat_id, user_id):
    lang = user_lang.get(user_id, "ua")
    gender = user_profiles.get(user_id, {}).get("gender", "male")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    if lang == "ua":
        if gender == "female":
            buttons = [
                "🔥 Мій план", "🏋️ Тренування", "💖 Натхнення",
                "⚔️ Shadow Mode", "👑 Мій шлях", "📊 Мій прогрес",
                "🌟 Виклик", "💎 SHRK COINS", "⚙️ Налаштування"
            ]
        else:
            buttons = [
                "🔥 План на сьогодні", "🏋️ Тренування", "🧠 Мотивація",
                "⚔️ Shadow Mode", "👤 Мій профіль", "📊 Мої результати",
                "🥇 Виклик", "🪙 SHRK COINS", "⚙️ Налаштування"
            ]
    elif lang == "ru":
        if gender == "female":
            buttons = [
                "🔥 Мой план", "🏋️ Тренировка", "💖 Вдохновение",
                "⚔️ Shadow Mode", "👑 Мой путь", "📊 Мой прогресс",
                "🌟 Вызов", "💎 SHRK COINS", "⚙️ Настройки"
            ]
        else:
            buttons = [
                "🔥 План на сегодня", "🏋️ Тренировка", "🧠 Мотивация",
                "⚔️ Shadow Mode", "👤 Мой профиль", "📊 Мои результаты",
                "🥇 Вызов", "🪙 SHRK COINS", "⚙️ Настройки"
            ]
    else:
        if gender == "female":
            buttons = [
                "🔥 My Plan", "🏋️ Workout", "💖 Inspiration",
                "⚔️ Shadow Mode", "👑 My Path", "📊 My Progress",
                "🌟 Challenge", "💎 SHRK COINS", "⚙️ Settings"
            ]
        else:
            buttons = [
                "🔥 Today’s Plan", "🏋️ Workout", "🧠 Motivation",
                "⚔️ Shadow Mode", "👤 My Profile", "📊 My Results",
                "🥇 Challenge", "🪙 SHRK COINS", "⚙️ Settings"
            ]

    markup.add(*buttons)
    bot.send_message(chat_id, "📋 Меню активовано:" if lang == "ua" else "📋 Меню активировано:" if lang == "ru" else "📋 Menu activated:", reply_markup=markup)

print(f"{VERSION} запущено.")
bot.infinity_polling()
