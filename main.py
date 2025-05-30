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

# === Загрузка советов от тренеров ===
try:
    with open("coaches_tips.json", "r", encoding="utf-8") as f:
        coaches_data = json.load(f)
except Exception as e:
    coaches_data = {"ua": [], "ru": [], "en": []}
    logging.error(f"[LOAD_COACHES_ERROR] {e}")
    
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

# === Советы от тренеров ===
@bot.message_handler(func=lambda message: message.text.lower() in [
    "🎓 поради від тренерів", "🎓 советы от тренеров", "🎓 pro trainer tips"
])
def coach_tip_handler(message):
    user_id = str(message.from_user.id)
    lang = user_lang.get(user_id, "ua")
    tips = coaches_data.get(lang, [])

    if not tips:
        bot.send_message(message.chat.id, "❌ Немає порад для обраної мови.")
        return

    coach = random.choice(tips)
    name = coach.get("name", "Без імені")
    bio = coach.get(f"bio_{lang}", coach.get("bio", ""))
    tip = coach.get(f"tip_{lang}", coach.get("tip", ""))

    text = f"👤 *{name}*\n\n🧬 _{bio}_\n\n{tip}"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

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
    "🥷 Бій з Тінню", "📚 Книги SHARKAN", "🎓 Поради від тренерів", "🤖 AI SHARKAN",
    "🌟 Виклик", "💎 SHRK COINS", "📊 Мій прогрес", "📈 Прогрес / Ранги",
    "🏆 Рейтинг SHARKAN", "🎵 Музика", "💬 Чат SHARKAN", "📢 Канал SHARKAN",
    "🧘‍♀️ Відновлення", "🔒 Темна Зона", "⚙️ Налаштування", "❓ FAQ / Підтримка",
    "📨 Співпраця", "👑 Мій шлях", "🛍 Магазин", "⏱ Режим БІГ"
]
        else:
buttons = [
    "🔥 План на сьогодні", "🏋️ Тренування", "🧠 Мотивація", "⚔️ Shadow Mode",
    "🥷 Бій з Тінню", "📚 Книги SHARKAN", "🎓 Поради від тренерів", "🤖 AI SHARKAN",
    "🥇 Виклик", "🪙 SHRK COINS", "📊 Мої результати", "📈 Статистика",
    "🏆 Рейтинг SHARKAN", "🎵 Музика", "💬 Чат SHARKAN", "📢 Канал SHARKAN",
    "🧘 Відновлення", "🔒 Темна Зона", "⚙️ Налаштування", "❓ Допомога / FAQ",
    "📨 Співпраця", "👤 Мій профіль", "🛍 Магазин", "⏱ Режим БІГ"
]
    elif lang == "ru":
        if gender == "female":
buttons = [
    "🔥 Мой план", "🏋️ Тренировка", "💖 Вдохновение", "⚔️ Shadow Mode",
    "🥷 Бой с Тенью", "📚 Книги SHARKAN", "🎓 Советы от тренеров", "🤖 AI SHARKAN",
    "🌟 Вызов", "💎 SHRK COINS", "📊 Мой прогресс", "📈 Прогресс / Ранги",
    "🏆 Рейтинг SHARKAN", "🎵 Музыка", "💬 Чат SHARKAN", "📢 Канал SHARKAN",
    "🧘‍♀️ Восстановление", "🔒 Тёмная Зона", "⚙️ Настройки", "❓ FAQ / Поддержка",
    "📨 Сотрудничество", "👑 Мой путь", "🛍 Магазин", "⏱ Режим БЕГ"
]
        else:
buttons = [
    "🔥 План на сегодня", "🏋️ Тренировка", "🧠 Мотивация", "⚔️ Shadow Mode",
    "🥷 Бой с Тенью", "📚 Книги SHARKAN", "🎓 Советы от тренеров", "🤖 AI SHARKAN",
    "🥇 Вызов", "🪙 SHRK COINS", "📊 Мои результаты", "📈 Статистика",
    "🏆 Рейтинг SHARKAN", "🎵 Музыка", "💬 Чат SHARKAN", "📢 Канал SHARKAN",
    "🧘 Восстановление", "🔒 Тёмная Зона", "⚙️ Настройки", "❓ Помощь / FAQ",
    "📨 Сотрудничество", "👤 Мой профиль", "🛍 Магазин", "⏱ Режим БЕГ"
]
    elif lang == "en":
        if gender == "female":
buttons = [
    "🔥 My Plan", "🏋️ Workout", "💖 Inspiration", "⚔️ Shadow Mode",
    "🥷 Shadow Fight", "📚 SHARKAN Books", "🎓 Pro Trainer Tips", "🤖 AI SHARKAN",
    "🌟 Challenge", "💎 SHRK COINS", "📊 My Progress", "📈 Progress / Ranks",
    "🏆 SHARKAN Ranking", "🎵 Music", "💬 SHARKAN Chat", "📢 SHARKAN Channel",
    "🧘‍♀️ Recovery", "🔒 Dark Zone", "⚙️ Settings", "❓ Help / FAQ",
    "📨 Contact Us", "👑 My Path", "🛍 Shop", "⏱ Running Mode"
]
        else:
buttons = [
    "🔥 Today's Plan", "🏋️ Workout", "🧠 Motivation", "⚔️ Shadow Mode",
    "🥷 Shadow Fight", "📚 SHARKAN Books", "🎓 Pro Trainer Tips", "🤖 AI SHARKAN",
    "🥇 Challenge", "🪙 SHRK COINS", "📊 My Results", "📈 Statistics",
    "🏆 SHARKAN Ranking", "🎵 Music", "💬 SHARKAN Chat", "📢 SHARKAN Channel",
    "🧘 Recovery", "🔒 Dark Zone", "⚙️ Settings", "❓ Help / FAQ",
    "📨 Contact Us", "👤 My Profile", "🛍 Shop", "⏱ Running Mode"
]

    # Двухрядное добавление кнопок
    for i in range(0, len(buttons), 2):
        markup.add(*[types.KeyboardButton(b) for b in buttons[i:i+2]])

    bot.send_message(chat_id, "📋 Меню активовано:", reply_markup=markup)

# === Запуск ===
print(f"{VERSION} запущено.")
bot.infinity_polling()
