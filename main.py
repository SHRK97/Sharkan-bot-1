import os
import json
import logging
import random
from datetime import datetime
from telebot import TeleBot, types

# === Загрузка мотиваций ===
try:
    with open("motivations.json", "r", encoding="utf-8") as f:
        motivation_data = json.load(f)
except Exception as e:
    motivation_data = {"ua": [], "ru": [], "en": []}
    logging.error(f"[LOAD_MOTIVATION_ERROR] {e}")

# === Переменная окружения ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Переменная BOT_TOKEN не задана. Установи её в окружении.")

bot = TeleBot(BOT_TOKEN)
ADMIN_ID = 693609628
VERSION = "SHARKAN BOT v1.0 — MULTILANG + GENDER"

# === Логирование ===
logging.basicConfig(
    level=logging.INFO,
    filename="bot.log",
    filemode="a",
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# === Профили пользователей ===
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

# === Языки ===
LANGUAGES = {'ua': 'Українська', 'ru': 'Русский', 'en': 'English'}
user_lang = {}

# === Подгрузка языков при запуске ===
for user_id, profile in user_profiles.items():
    if "language" in profile:
        user_lang[user_id] = profile["language"]

# === Команда /start ===
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    for code, name in LANGUAGES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"lang_{code}"))
    bot.send_message(message.chat.id, "👋 Обери мову / Choose your language / Выберите язык:", reply_markup=markup)

# === Выбор языка ===
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
        text = "✅ Твоя мова — українська. Вітаємо в SHARKAN BOT!\n\n👤 Обери свою стать:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Я — чоловік", callback_data="gender_male"),
            types.InlineKeyboardButton("Я — жінка", callback_data="gender_female")
        )
    elif lang == "ru":
        text = "✅ Ваш язык — русский. Добро пожаловать в SHARKAN BOT!\n\n👤 Выбери свой пол:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Я — мужчина", callback_data="gender_male"),
            types.InlineKeyboardButton("Я — женщина", callback_data="gender_female")
        )
    else:
        text = "✅ Your language is English. Welcome to SHARKAN BOT!\n\n👤 Select your gender:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("I am a man", callback_data="gender_male"),
            types.InlineKeyboardButton("I am a woman", callback_data="gender_female")
        )

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=markup)

# === Команда /motivation ===
@bot.message_handler(commands=['motivation'])
def send_motivation(message):
    user_id = str(message.from_user.id)
    lang = user_lang.get(user_id, 'ua')
    phrases = motivation_data.get(lang, [])
    if phrases:
        bot.send_message(message.chat.id, random.choice(phrases))
    else:
        bot.send_message(message.chat.id, "Немає мотивацій для твоєї мови.")

# === Выбор пола ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender(call):
    chat_id = call.message.chat.id
    user_id = str(call.from_user.id)
    gender = call.data.split("_")[1]  # male / female

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

# === Текстовая мотивация из JSON ===
@bot.message_handler(func=lambda message: message.text.lower() in [
    "🧠 мотивація", "💖 натхнення", "🧠 мотивация", "💖 вдохновение",
    "🧠 motivation", "💖 inspiration"
])
def motivation_handler(message):
    user_id = str(message.from_user.id)
    lang = user_lang.get(user_id, "ua")
    phrases = motivation_data.get(lang, [])

    if phrases:
        bot.send_message(message.chat.id, random.choice(phrases))
    else:
        bot.send_message(message.chat.id, "Немає мотивацій для твоєї мови.")

    bot.send_message(message.chat.id, text)

# === Главное меню ===
def menu_from_id(chat_id, user_id):
    lang = user_lang.get(user_id, "ua")
    gender = user_profiles.get(user_id, {}).get("gender", "male")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = []

    if lang == "ua":
        if gender == "female":
            buttons = [
                "🔥 Мій план", "🏋️ Тренування", "💖 Натхнення", "⚔️ Shadow Mode",
                "👑 Мій шлях", "📊 Мій прогрес", "🌟 Виклик", "💎 SHRK COINS",
                "🛍 Магазин", "⏱ Режим БІГ", "📚 Книги SHARKAN", "🎵 Музика",
                "🥷 Бій з Тінню", "📈 Прогрес / Ранги", "🤖 AI SHARKAN", "🎓 Поради від тренерів",
                "🏆 Рейтинг SHARKAN", "💬 Чат SHARKAN", "📢 Канал SHARKAN", "❓ FAQ / Підтримка",
                "📨 Співпраця", "🔒 Темна Зона", "🧘‍♀️ Відновлення", "⚙️ Налаштування"
            ]
        else:
            buttons = [
                "🔥 План на сьогодні", "🏋️ Тренування", "🧠 Мотивація", "⚔️ Shadow Mode",
                "👤 Мій профіль", "📊 Мої результати", "🥇 Виклик", "🪙 SHRK COINS",
                "🛍 Магазин", "⏱ Режим БІГ", "📚 Книги SHARKAN", "🎵 Музика",
                "🥷 Бій з Тінню", "📈 Статистика", "🤖 AI SHARKAN", "🎓 Поради від тренерів",
                "🏆 Рейтинг SHARKAN", "💬 Чат SHARKAN", "📢 Канал SHARKAN", "❓ Допомога / FAQ",
                "📨 Співпраця", "🔒 Темна Зона", "🧘 Відновлення", "⚙️ Налаштування"
            ]
    elif lang == "ru":
        if gender == "female":
            buttons = [
                "🔥 Мой план", "🏋️ Тренировка", "💖 Вдохновение", "⚔️ Shadow Mode",
                "👑 Мой путь", "📊 Мой прогресс", "🌟 Вызов", "💎 SHRK COINS",
                "🛍 Магазин", "⏱ Режим БЕГ", "📚 Книги SHARKAN", "🎵 Музыка",
                "🥷 Бой с Тенью", "📈 Прогресс / Ранги", "🤖 AI SHARKAN", "🎓 Советы от тренеров",
                "🏆 Рейтинг SHARKAN", "💬 Чат SHARKAN", "📢 Канал SHARKAN", "❓ FAQ / Поддержка",
                "📨 Сотрудничество", "🔒 Тёмная Зона", "🧘‍♀️ Восстановление", "⚙️ Настройки"
            ]
        else:
            buttons = [
                "🔥 План на сегодня", "🏋️ Тренировка", "🧠 Мотивация", "⚔️ Shadow Mode",
                "👤 Мой профиль", "📊 Мои результаты", "🥇 Вызов", "🪙 SHRK COINS",
                "🛍 Магазин", "⏱ Режим БЕГ", "📚 Книги SHARKAN", "🎵 Музыка",
                "🥷 Бой с Тенью", "📈 Статистика", "🤖 AI SHARKAN", "🎓 Советы от тренеров",
                "🏆 Рейтинг SHARKAN", "💬 Чат SHARKAN", "📢 Канал SHARKAN", "❓ Помощь / FAQ",
                "📨 Сотрудничество", "🔒 Тёмная Зона", "🧘 Восстановление", "⚙️ Настройки"
            ]
    elif lang == "en":
        if gender == "female":
            buttons = [
                "🔥 My Plan", "🏋️ Workout", "💖 Inspiration", "⚔️ Shadow Mode",
                "👑 My Path", "📊 My Progress", "🌟 Challenge", "💎 SHRK COINS",
                "🛍 Shop", "⏱ Running Mode", "📚 SHARKAN Books", "🎵 Music",
                "🥷 Shadow Fight", "📈 Progress / Ranks", "🤖 AI SHARKAN", "🎓 Pro Trainer Tips",
                "🏆 SHARKAN Ranking", "💬 SHARKAN Chat", "📢 SHARKAN Channel", "❓ Help / FAQ",
                "📨 Contact Us", "🔒 Dark Zone", "🧘‍♀️ Recovery", "⚙️ Settings"
            ]
        else:
            buttons = [
                "🔥 Today's Plan", "🏋️ Workout", "🧠 Motivation", "⚔️ Shadow Mode",
                "👤 My Profile", "📊 My Results", "🥇 Challenge", "🪙 SHRK COINS",
                "🛍 Shop", "⏱ Running Mode", "📚 SHARKAN Books", "🎵 Music",
                "🥷 Shadow Fight", "📈 Statistics", "🤖 AI SHARKAN", "🎓 Pro Trainer Tips",
                "🏆 SHARKAN Ranking", "💬 SHARKAN Chat", "📢 SHARKAN Channel", "❓ Help / FAQ",
                "📨 Contact Us", "🔒 Dark Zone", "🧘 Recovery", "⚙️ Settings"
            ]

    # Двухрядное добавление кнопок
    for i in range(0, len(buttons), 2):
        markup.add(*[types.KeyboardButton(b) for b in buttons[i:i+2]])

    bot.send_message(chat_id, "📋 Меню активовано:", reply_markup=markup)

# === Запуск ===
print(f"{VERSION} запущено.")
bot.infinity_polling()
