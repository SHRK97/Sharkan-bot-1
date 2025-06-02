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

# === Статистика пробіжок та монети ===
run_stats_file = "run_stats.json"
if os.path.exists(run_stats_file):
    with open(run_stats_file, "r") as f:
        run_stats = json.load(f)
else:
    run_stats = {}

active_runs = {}

def save_all():
    save_profiles()
    with open(run_stats_file, "w") as f:
        json.dump(run_stats, f, indent=4, ensure_ascii=False)

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

# === Режим БІГ SHARKAN з таймером, статистикою та мовами ===

from datetime import datetime
import json
import os
from telebot import types

running_sessions = {}
RUN_HISTORY_FILE = "run_history.json"

# === Розрахунок калорій ===
def calculate_calories(weight_kg, duration_min):
    MET_running = 9.8
    calories = (MET_running * 3.5 * weight_kg / 200) * duration_min
    return round(calories)

# === Збереження результату ===
def save_run_result(user_id, duration_min, calories):
    try:
        if os.path.exists(RUN_HISTORY_FILE):
            with open(RUN_HISTORY_FILE, "r") as f:
                run_history = json.load(f)
        else:
            run_history = {}
    except:
        run_history = {}

    if user_id not in run_history:
        run_history[user_id] = []

    run_history[user_id].append({
        "date": datetime.now().strftime("%d.%m.%Y"),
        "duration_min": duration_min,
        "calories": calories
    })

    with open(RUN_HISTORY_FILE, "w") as f:
        json.dump(run_history, f, indent=4, ensure_ascii=False)

    return run_history[user_id][-3:]

# === Витяг мови користувача ===
def get_lang(user_id):
    try:
        with open("user_profiles.json", "r") as f:
            profiles = json.load(f)
        return profiles.get(str(user_id), {}).get("lang", "ua")
    except:
        return "ua"

@bot.message_handler(func=lambda msg: msg.text.lower() in ["⏱ режим бег", "⏱ режим біг", "⏱ running mode"])
def run_menu(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        markup.add("🏁 Начать бег", "⛔️ Завершить бег")
        markup.add("📊 Мои результаты", "⬅️ Главное меню")
        bot.send_message(message.chat.id, "🏃‍♂️ Выбери действие для SHARKAN RUN:", reply_markup=markup)
    elif lang == "en":
        markup.add("🏁 Start run", "⛔️ Stop run")
        markup.add("📊 My results", "⬅️ Main menu")
        bot.send_message(message.chat.id, "🏃‍♂️ Choose an action for SHARKAN RUN:", reply_markup=markup)
    else:
        markup.add("🏁 Почати біг", "⛔️ Завершити біг")
        markup.add("📊 Мої результати", "⬅️ Головне меню")
        bot.send_message(message.chat.id, "🏃‍♂️ Обери дію для SHARKAN RUN:", reply_markup=markup)

# === Початок бігу ===
@bot.message_handler(func=lambda msg: "почати" in msg.text.lower() or "start" in msg.text.lower())
def start_run(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    running_sessions[user_id] = {"start": datetime.now()}

    text = {
        "ua": "🏃‍♂️ Біжи! Я фіксую твій результат.\n⛔️ Натисни «Завершити біг», коли закінчиш.",
        "ru": "🏃‍♂️ Беги! Я фиксирую твой результат.\n⛔️ Нажми «Завершить бег», когда закончишь.",
        "en": "🏃‍♂️ Run! I'm tracking your session.\n⛔️ Tap 'Stop run' when you’re done."
    }
    bot.send_message(message.chat.id, text.get(lang, text["ua"]))

# === Завершення бігу ===
@bot.message_handler(func=lambda msg: "завершити" in msg.text.lower() or "stop" in msg.text.lower())
def end_run(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)

    if user_id not in running_sessions:
        text = {
            "ua": "❌ Пробіжка не активна. Натисни «Почати біг».",
            "ru": "❌ Бег не активен. Нажми «Начать бег».",
            "en": "❌ Run not active. Tap 'Start run'."
        }
        bot.send_message(message.chat.id, text.get(lang, text["ua"]))
        return

    start_time = running_sessions[user_id]["start"]
    end_time = datetime.now()
    duration_min = round((end_time - start_time).seconds / 60)

    # Вага з профілю
    try:
        with open("user_profiles.json", "r") as f:
            profiles = json.load(f)
        weight = int(profiles.get(user_id, {}).get("weight", 70))
    except:
        weight = 70

    calories = calculate_calories(weight, duration_min)
    save_run_result(user_id, duration_min, calories)
    del running_sessions[user_id]

    text = {
        "ua": f"✅ Пробіжка завершена!\n⏱ Тривалість: {duration_min} хв\n🔥 Спалено: {calories} ккал\n📦 Результат збережено.",
        "ru": f"✅ Бег завершён!\n⏱ Длительность: {duration_min} мин\n🔥 Сожжено: {calories} ккал\n📦 Результат сохранён.",
        "en": f"✅ Run finished!\n⏱ Duration: {duration_min} min\n🔥 Burned: {calories} kcal\n📦 Result saved."
    }
    bot.send_message(message.chat.id, text.get(lang, text["ua"]))

# === Перегляд останніх результатів ===
@bot.message_handler(func=lambda msg: "результат" in msg.text.lower())
def show_results(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)

    try:
        with open(RUN_HISTORY_FILE, "r") as f:
            run_history = json.load(f)
        records = run_history.get(user_id, [])
    except:
        records = []

    if not records:
        text = {
            "ua": "❌ Немає збережених пробіжок.",
            "ru": "❌ Нет сохранённых пробежек.",
            "en": "❌ No saved runs."
        }
        bot.send_message(message.chat.id, text.get(lang, text["ua"]))
        return

    response = {
        "ua": "📊 Останні пробіжки:\n",
        "ru": "📊 Последние пробежки:\n",
        "en": "📊 Recent runs:\n"
    }[lang]

    for run in reversed(records[-3:]):
        response += f"📅 {run['date']} — {run['duration_min']} хв — {run['calories']} ккал\n"

    bot.send_message(message.chat.id, response)
    
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
                "🔥 Мій план", "🏋️ Тренування", "💖 Натхнення", "⏱ Режим БІГ",
                "🥷 Бій з Тінню", "📚 Книги SHARKAN", "🎓 Поради від тренерів", "🤖 AI SHARKAN",
                "🌟 Виклик", "💎 SHRK COINS", "📊 Мій прогрес", "📈 Прогрес / Ранги",
                "🏆 Рейтинг SHARKAN", "🎵 Музика", "👑 Мій шлях", "🛍 Магазин",
                "💬 Чат SHARKAN", "📢 Канал SHARKAN", "🧘‍♀️ Відновлення", "🔒 Темна Зона",
                "⚙️ Налаштування", "❓ FAQ / Підтримка", "📨 Співпраця"
            ]
        else:
            buttons = [
                "🔥 План на сьогодні", "🏋️ Тренування", "🧠 Мотивація", "⏱ Режим БІГ",
                "🥷 Бій з Тінню", "📚 Книги SHARKAN", "🎓 Поради від тренерів", "🤖 AI SHARKAN",
                "🥇 Виклик", "🪙 SHRK COINS", "📊 Мої результати", "📈 Статистика",
                "🏆 Рейтинг SHARKAN", "🎵 Музика", "👤 Мій профіль", "🛍 Магазин",
                "💬 Чат SHARKAN", "📢 Канал SHARKAN", "🧘 Відновлення", "🔒 Темна Зона",
                "⚙️ Налаштування", "❓ Допомога / FAQ", "📨 Співпраця"
            ]

    elif lang == "ru":
        if gender == "female":
            buttons = [
                "🔥 Мой план", "🏋️ Тренировка", "💖 Вдохновение", "⏱ Режим БЕГ",
                "🥷 Бой с Тенью", "📚 Книги SHARKAN", "🎓 Советы от тренеров", "🤖 AI SHARKAN",
                "🌟 Вызов", "💎 SHRK COINS", "📊 Мой прогресс", "📈 Прогресс / Ранги",
                "🏆 Рейтинг SHARKAN", "🎵 Музыка", "👑 Мой путь", "🛍 Магазин",
                "💬 Чат SHARKAN", "📢 Канал SHARKAN", "🧘‍♀️ Восстановление", "🔒 Тёмная Зона",
                "⚙️ Настройки", "❓ FAQ / Поддержка", "📨 Сотрудничество"
            ]
        else:
            buttons = [
                "🔥 План на сегодня", "🏋️ Тренировка", "🧠 Мотивация", "⏱ Режим БЕГ",
                "🥷 Бой с Тенью", "📚 Книги SHARKAN", "🎓 Советы от тренеров", "🤖 AI SHARKAN",
                "🥇 Вызов", "🪙 SHRK COINS", "📊 Мои результаты", "📈 Статистика",
                "🏆 Рейтинг SHARKAN", "🎵 Музыка", "👤 Мой профиль", "🛍 Магазин",
                "💬 Чат SHARKAN", "📢 Канал SHARKAN", "🧘 Восстановление", "🔒 Тёмная Зона",
                "⚙️ Настройки", "❓ Помощь / FAQ", "📨 Сотрудничество"
            ]

    elif lang == "en":
        if gender == "female":
            buttons = [
                "🔥 My Plan", "🏋️ Workout", "💖 Inspiration", "⏱ Running Mode",
                "🥷 Shadow Fight", "📚 SHARKAN Books", "🎓 Pro Trainer Tips", "🤖 AI SHARKAN",
                "🌟 Challenge", "💎 SHRK COINS", "📊 My Progress", "📈 Progress / Ranks",
                "🏆 SHARKAN Ranking", "🎵 Music", "👑 My Path", "🛍 Shop",
                "💬 SHARKAN Chat", "📢 SHARKAN Channel", "🧘‍♀️ Recovery", "🔒 Dark Zone",
                "⚙️ Settings", "❓ Help / FAQ", "📨 Contact Us"
            ]
        else:
            buttons = [
                "🔥 Today's Plan", "🏋️ Workout", "🧠 Motivation", "⏱ Running Mode",
                "🥷 Shadow Fight", "📚 SHARKAN Books", "🎓 Pro Trainer Tips", "🤖 AI SHARKAN",
                "🥇 Challenge", "🪙 SHRK COINS", "📊 My Results", "📈 Statistics",
                "🏆 SHARKAN Ranking", "🎵 Music", "👤 My Profile", "🛍 Shop",
                "💬 SHARKAN Chat", "📢 SHARKAN Channel", "🧘 Recovery", "🔒 Dark Zone",
                "⚙️ Settings", "❓ Help / FAQ", "📨 Contact Us"
            ]

    # Отображение в два ряда
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i + 2])

    bot.send_message(chat_id, "🧠 Обери розділ:" if lang == "ua" else
                                 "🧠 Выберите раздел:" if lang == "ru" else
                                 "🧠 Choose a section:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text.lower() in ["⬅️ головне меню", "⬅️ главное меню", "⬅️ main menu"])
def back_to_main_menu(message):
    user_id = str(message.from_user.id)
    menu_from_id(message.chat.id, user_id)
    
# === Запуск ===
print(f"{VERSION} запущено.")
bot.infinity_polling()
