import os
import json
import logging
from datetime import datetime
from telebot import TeleBot, types

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
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

# === Загрузка и сохранение профилей ===
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

# === /start ===
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    for code, name in LANGUAGES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"lang_{code}"))
    bot.send_message(message.chat.id, "👋 Обери мову / Choose your language / Выберите язык:", reply_markup=markup)

# === Обработка языка + Меню ===
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
        text = "✅ Твоя мова — українська. Вітаємо в SHARKAN BOT!\n👤 Обери свою стать:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Я — чоловік", callback_data="gender_male"),
            types.InlineKeyboardButton("Я — жінка", callback_data="gender_female")
        )
    elif lang == "ru":
        text = "✅ Ваш язык — русский. Добро пожаловать в SHARKAN BOT!\n👤 Выбери свой пол:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Я — мужчина", callback_data="gender_male"),
            types.InlineKeyboardButton("Я — женщина", callback_data="gender_female")
        )
    else:
        text = "✅ Your language is English. Welcome to SHARKAN BOT!\n👤 Select your gender:"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("I am a man", callback_data="gender_male"),
            types.InlineKeyboardButton("I am a woman", callback_data="gender_female")
        )

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=markup)

    # Показать меню сразу
    menu_from_id(chat_id, user_id)

# === Команда /стать /gender ===
@bot.message_handler(commands=["стать", "gender"])
def select_gender(message):
    user_id = str(message.from_user.id)
    lang = user_lang.get(user_id, "ua")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    if lang == "ua":
        markup.add("Я — чоловік", "Я — жінка")
        msg = bot.send_message(message.chat.id, "👤 Обери свою стать:", reply_markup=markup)
    elif lang == "ru":
        markup.add("Я — мужчина", "Я — женщина")
        msg = bot.send_message(message.chat.id, "👤 Выбери свой пол:", reply_markup=markup)
    else:
        markup.add("I am a man", "I am a woman")
        msg = bot.send_message(message.chat.id, "👤 Select your gender:", reply_markup=markup)

    bot.register_next_step_handler(msg, lambda m: save_gender(m, user_id))

def save_gender(message, user_id):
    text = message.text.strip().lower()
    lang = user_lang.get(user_id, "ua")
    gender = "male"

    if text in ["я — жінка", "я — женщина", "i am a woman"]:
        gender = "female"

    user_profiles[user_id] = user_profiles.get(user_id, {})
    user_profiles[user_id]["gender"] = gender
    save_profiles()

    confirm = {
        "ua": "✅ Стать збережено.",
        "ru": "✅ Пол сохранён.",
        "en": "✅ Gender saved."
    }

    bot.send_message(message.chat.id, confirm.get(lang, "✅ Done."))
    menu_from_id(message.chat.id, user_id)

# === Главное меню по user_id ===
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
    # === /профіль — Створення профілю ===
@bot.message_handler(commands=["профіль", "профиль", "profile"])
def profile_setup(message):
    user_id = str(message.from_user.id)
    msg = bot.send_message(message.chat.id, "📏 Введи свій ріст (у см):")
    bot.register_next_step_handler(msg, lambda m: get_height(m, user_id))

def get_height(message, user_id):
    try:
        height = int(message.text.strip())
        user_profiles[user_id] = user_profiles.get(user_id, {})
        user_profiles[user_id]["height"] = height
        msg = bot.send_message(message.chat.id, "⚖️ Введи свою вагу (у кг):")
        bot.register_next_step_handler(msg, lambda m: get_weight(m, user_id))
    except:
        bot.send_message(message.chat.id, "❌ Будь ласка, введи число.")
        profile_setup(message)

def get_weight(message, user_id):
    try:
        weight = int(message.text.strip())
        user_profiles[user_id]["weight"] = weight
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Схуднути", "Набрати масу", "Підтримувати форму")
        msg = bot.send_message(message.chat.id, "🎯 Обери свою ціль:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: get_goal(m, user_id))
    except:
        bot.send_message(message.chat.id, "❌ Будь ласка, введи число.")
        profile_setup(message)

def get_goal(message, user_id):
    goal = message.text.strip()
    user_profiles[user_id]["goal"] = goal
    save_profiles()
    bot.send_message(
        message.chat.id,
        f"✅ Профіль збережено!\n\n📏 Ріст: {user_profiles[user_id]['height']} см\n⚖️ Вага: {user_profiles[user_id]['weight']} кг\n🎯 Ціль: {goal}"
    )

# === /мійпрофіль — Показ профілю ===
@bot.message_handler(commands=["мійпрофіль", "мойпрофиль", "myprofile"])
def show_profile(message):
    user_id = str(message.from_user.id)
    profile = user_profiles.get(user_id)
    if profile:
        bot.send_message(
            message.chat.id,
            f"👤 Твій профіль:\n📏 Ріст: {profile.get('height')} см\n⚖️ Вага: {profile.get('weight')} кг\n🎯 Ціль: {profile.get('goal')}"
        )
    else:
        bot.send_message(message.chat.id, "❗ Профіль не знайдено. Введи /профіль щоб створити.")

# === Обработка текста из меню ===
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = str(message.from_user.id)
    lang = user_lang.get(user_id, "ua")
    text = message.text.strip().lower()

    # Мотивация
    if text in ["мотивація", "motivation", "натхнення", "вдохновение", "inspiration"]:
        try:
            with open("audio/motivation.mp3", "rb") as audio:
                bot.send_audio(message.chat.id, audio, caption="🎧 Слухай. Пам’ятай. Дій.")
        except:
            bot.send_message(message.chat.id, "❌ Файл мотивації не знайдено.")
    # Shadow Mode
    elif text in ["shadow mode"]:
        bot.send_message(message.chat.id, "⚔️ Shadow Mode активовано.\nЦе режим самоти. Тут немає лайків. Немає оплесків. Є лише ти проти себе.")
    # Мій профіль
    elif text in ["мій профіль", "my profile", "мой профиль", "мій шлях", "мой путь", "my path"]:
        show_profile(message)
    # План на день
    elif text in ["план на сьогодні", "today’s plan", "мой план", "мій план", "my plan"]:
        bot.send_message(
            message.chat.id,
            "📅 План на сьогодні:\n- 🏋️ Тренування: все тіло\n- 💧 Вода: 2 л\n- 🍽️ Їжа: білки + овочі\n- ⚔️ Shadow Mode: 1 сесія"
        )
    else:
        bot.send_message(message.chat.id, "📍 Вибери опцію з меню або напиши /menu")

# === Очистка логов (тільки адмін) ===
@bot.message_handler(commands=["clearlog"])
def clear_log(message):
    if message.from_user.id == ADMIN_ID:
        open("bot.log", "w").close()
        bot.send_message(message.chat.id, "🧹 Логи очищено.")
    else:
        bot.send_message(message.chat.id, "🚫 У тебе немає доступу.")

# === Запуск ===
print(f"{VERSION} запущено.")
bot.infinity_polling()
