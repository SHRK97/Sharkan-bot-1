import os
import json
import logging
from datetime import datetime
from telebot import TeleBot, types

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)
ADMIN_ID = 693609628
VERSION = "SHARKAN BOT v1.0 — FULL LAUNCH"

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
    bot.send_message(message.chat.id, "👋 Обери мову / Choose your language:", reply_markup=markup)

# === Обработка языка ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    chat_id = call.message.chat.id
    lang = call.data.split("_")[1]
    user_profiles[str(chat_id)] = user_profiles.get(str(chat_id), {})
    user_profiles[str(chat_id)]["language"] = lang
    save_profiles()

    if lang == "ua":
        welcome_text = "Твоя мова — українська. Вітаємо в SHARKAN BOT."
    elif lang == "ru":
        welcome_text = "Ваш язык — русский. Добро пожаловать в SHARKAN BOT."
    elif lang == "en":
        welcome_text = "Your language is English. Welcome to SHARKAN BOT."
    else:
        welcome_text = "Language set."

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=welcome_text)
    
    # Показать главное меню сразу
    show_main_menu(chat_id)

# === Главное меню ===
@bot.message_handler(commands=["menu"])
def menu(message):
    user_id = str(message.from_user.id)
    lang = user_lang.get(user_id, "ua")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if lang == "ua":
        buttons = ["План на сьогодні", "Тренування", "Мотивація", "Shadow Mode", "Мій профіль", "Мої результати", "Виклик", "SHRK COINS", "Налаштування"]
    elif lang == "ru":
        buttons = ["План на сегодня", "Тренировка", "Мотивация", "Shadow Mode", "Мой профиль", "Мои результаты", "Вызов", "SHRK COINS", "Настройки"]
    else:
        buttons = ["Today’s Plan", "Workout", "Motivation", "Shadow Mode", "My Profile", "My Results", "Challenge", "SHRK COINS", "Settings"]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Меню активовано:", reply_markup=markup)

# === /профіль — Создание профиля ===
@bot.message_handler(commands=["профіль"])
def profile_setup(message):
    user_id = str(message.from_user.id)
    msg = bot.send_message(message.chat.id, "Введи свій ріст (у см):")
    bot.register_next_step_handler(msg, lambda m: get_height(m, user_id))

def get_height(message, user_id):
    try:
        height = int(message.text.strip())
        user_profiles[user_id] = {"height": height}
        msg = bot.send_message(message.chat.id, "Введи свою вагу (у кг):")
        bot.register_next_step_handler(msg, lambda m: get_weight(m, user_id))
    except:
        bot.send_message(message.chat.id, "Будь ласка, введи число.")
        profile_setup(message)

def get_weight(message, user_id):
    try:
        weight = int(message.text.strip())
        user_profiles[user_id]["weight"] = weight
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Схуднути", "Набрати масу", "Підтримувати форму")
        msg = bot.send_message(message.chat.id, "Оберіть ціль:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: get_goal(m, user_id))
    except:
        bot.send_message(message.chat.id, "Будь ласка, введи число.")
        profile_setup(message)

def get_goal(message, user_id):
    goal = message.text.strip()
    user_profiles[user_id]["goal"] = goal
    save_profiles()
    bot.send_message(message.chat.id, f"✅ Профіль збережено!\nРіст: {user_profiles[user_id]['height']} см\nВага: {user_profiles[user_id]['weight']} кг\nЦіль: {goal}")

# === /мійпрофіль — Показ профілю ===
@bot.message_handler(commands=["мійпрофіль"])
def show_profile(message):
    user_id = str(message.from_user.id)
    profile = user_profiles.get(user_id)
    if profile:
        bot.send_message(
            message.chat.id,
            f"Твій профіль:\nРіст: {profile.get('height')} см\nВага: {profile.get('weight')} кг\nЦіль: {profile.get('goal')}"
        )
    else:
        bot.send_message(message.chat.id, "Профіль не знайдено. Введи /профіль щоб створити.")

# === Обработка текста из главного меню ===
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = str(message.from_user.id)
    lang = user_lang.get(user_id, "ua")
    text = message.text.strip().lower()

    if text in ["мотивація", "motivation"]:
        try:
            with open("audio/motivation.mp3", "rb") as audio:
                bot.send_audio(message.chat.id, audio, caption="Слухай. Пам’ятай. Дій.")
        except:
            bot.send_message(message.chat.id, "Файл мотивації не знайдено.")
    elif text in ["shadow mode"]:
        bot.send_message(message.chat.id, "Shadow Mode активовано.\nЦе режим самоти. Тут немає лайків. Немає оплесків. Є лише ти проти себе.")
    elif text in ["мій профіль", "my profile"]:
        show_profile(message)
    elif text in ["план на сьогодні", "today’s plan"]:
        bot.send_message(message.chat.id, "План на сьогодні:\n- Тренування: все тіло\n- Вода: 2 л\n- Їжа: білки + овочі\n- Shadow Mode: 1 сесія")
    else:
        bot.send_message(message.chat.id, "Вибери опцію з меню або введи /menu")

# === Очистка логов (тільки адмін) ===
@bot.message_handler(commands=["clearlog"])
def clear_log(message):
    if message.from_user.id == ADMIN_ID:
        open("bot.log", "w").close()
        bot.send_message(message.chat.id, "Логи очищено.")
    else:
        bot.send_message(message.chat.id, "У тебе немає доступу.")

# === Запуск ===
print(f"{VERSION} запущено.")
bot.infinity_polling()
