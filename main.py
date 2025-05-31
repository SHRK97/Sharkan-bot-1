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

# === Режим БІГ SHARKAN ===
from threading import Timer

running_sessions = {}

@bot.message_handler(func=lambda msg: msg.text in ["⏱ Режим БІГ", "⏱ Режим БЕГ", "⏱ Running Mode"])
def run_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🏁 Почати біг", "⛔️ Завершити біг")
    markup.add("📊 Мої результати", "⬅️ Головне меню")
    bot.send_message(message.chat.id, "🏃‍♂️ Обери дію для SHARKAN RUN:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text.startswith("🏁"))
def start_run(message):
    user_id = str(message.from_user.id)
    running_sessions[user_id] = {
        "start": datetime.now(),
        "message_id": None
    }
    msg = bot.send_message(message.chat.id, "🏃 Біг розпочато!\n⏱ Таймер: 00:00")
    msg = bot.send_message(message.chat.id, "⏱ Таймер: 00:00", reply_markup=get_run_markup())
    running_sessions[user_id]["message_id"] = msg.message_id
    update_timer(message.chat.id, user_id)

def get_run_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⛔️ Завершити біг")
    return markup

def update_timer(chat_id, user_id):
    if user_id not in running_sessions:
        return

    start = running_sessions[user_id]["start"]
    now = datetime.now()
    elapsed = int((now - start).total_seconds())
    minutes = elapsed // 60
    seconds = elapsed % 60
    text = (
    f"⏱ Біг розпочато!\n"
    f"⏱ Таймер: {minutes:02d}:{seconds:02d}\n"
    f"🔥 Калорії: 0"
    )

    try:
        bot.edit_message_text(chat_id=chat_id, message_id=running_sessions[user_id]["message_id"], text=text, reply_markup=get_run_markup())
    except:
        pass

    Timer(1, update_timer, args=(chat_id, user_id)).start()

@bot.message_handler(func=lambda msg: "завершити" in msg.text.lower())
def stop_run(message):
    user_id = str(message.from_user.id)
    if user_id not in running_sessions:
        bot.send_message(message.chat.id, "❌ Біг не активний.")
        return

    start_time = running_sessions[user_id]["start"]
    end_time = datetime.now()
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    formatted_time = f"{minutes:02d}:{seconds:02d}"

    weight = float(user_profiles.get(user_id, {}).get("weight", 70))
    calories = int((total_seconds / 60) * (weight * 0.087))

    run_entry = {
        "date": start_time.strftime("%Y-%m-%d"),
        "duration_minutes": minutes,
        "calories": calories
    }

    run_stats.setdefault(user_id, []).append(run_entry)
    del running_sessions[user_id]

    profile = user_profiles.setdefault(user_id, {"coins": 0})
    reward = 0
    if len(run_stats[user_id]) == 1:
        reward += 10
        profile["last_reward"] = "+10 за першу пробіжку"
    if minutes >= 30:
        reward += 20
        profile["last_reward"] = "+20 за пробіжку понад 30 хв"

    dates = sorted([datetime.strptime(r["date"], "%Y-%m-%d") for r in run_stats[user_id]], reverse=True)
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    if streak >= 3:
        reward += 30
        profile["last_reward"] = "+30 за стрик 3+ днів"
    if len(run_stats[user_id]) >= 11:
        reward += 50
        profile["last_reward"] = "+50 за рівень Звір"

    profile["coins"] += reward
    save_all()
    
start_time = running_sessions[user_id]["start"]
end_time = datetime.now()
duration = end_time - start_time
total_seconds = int(duration.total_seconds())
minutes = total_seconds // 60
seconds = total_seconds % 60

text = (
    f"✅ Біг завершено!\n"
    f"⏱ Час: {minutes:02d}:{seconds:02d}\n"
    f"🔥 Калорії: {calories}\n"
    f"🎁 Нагорода: +{reward} SHRK COINS"
)

bot.send_message(
    message.chat.id,
    text,
    reply_markup=main_menu_markup(user_id)
)
@bot.message_handler(func=lambda msg: msg.text in ["📊 Мої результати", "📊 My Results"])
def show_results(message):
    user_id = str(message.from_user.id)
    stats = run_stats.get(user_id, [])
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    half_year_ago = today - timedelta(days=183)
    year_ago = today - timedelta(days=365)

    runs_today = [r for r in stats if r["date"] == today_str]
    runs_week = [r for r in stats if datetime.strptime(r["date"], "%Y-%m-%d") >= week_ago]
    runs_month = [r for r in stats if datetime.strptime(r["date"], "%Y-%m-%d") >= month_ago]
    runs_half_year = [r for r in stats if datetime.strptime(r["date"], "%Y-%m-%d") >= half_year_ago]
    runs_year = [r for r in stats if datetime.strptime(r["date"], "%Y-%m-%d") >= year_ago]

    streak = 1
    dates = sorted([datetime.strptime(r["date"], "%Y-%m-%d") for r in stats], reverse=True)
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break

    total_runs = len(stats)
    total_calories = sum(r["calories"] for r in stats)
    if total_runs >= 11:
        rank = "🥇 Звір"
    elif total_runs >= 4:
        rank = "🥈 SHARKAN учень"
    else:
        rank = "🥉 Новачок"

    text = f"""
📊 Мої результати

🏃‍♂️ SHARKAN RUN:
📅 Сьогодні: {len(runs_today)} пробіжка(и)
🗓 За тиждень: {len(runs_week)} пробіжок
📆 За місяць: {len(runs_month)} пробіжок
🕓 За пів року: {len(runs_half_year)} пробіжок
📈 За рік: {len(runs_year)} пробіжок

🔥 Калорій спалено всього: {total_calories}
🎯 Стрик: {streak} днів підряд
🏅 Ранг: {rank}
"""
    bot.send_message(message.chat.id, text.strip(), reply_markup=get_run_markup())

@bot.message_handler(func=lambda msg: "головне меню" in msg.text.lower())
def back_to_main_menu(message):
    user_id = str(message.from_user.id)
    menu_from_id(message.chat.id, user_id)



# === Режим БІГ з підтримкою 3 мов ===

@bot.message_handler(func=lambda msg: msg.text in ["⏱ Режим БІГ", "⏱ Режим БЕГ", "⏱ Running Mode"])
def run_menu(message):
    lang = user_profiles.get(str(message.from_user.id), {}).get("lang", "ua")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        markup.add("🏁 Начать бег", "🛑 Завершить бег")
        markup.add("📊 Мои результаты", "💰 SHRK COINS")
        text = "Выбери действие:"
    elif lang == "en":
        markup.add("🏁 Start Run", "🛑 Stop Run")
        markup.add("📊 My Results", "💰 SHRK COINS")
        text = "Choose an action:"
    else:
        markup.add("🏁 Почати біг", "🛑 Завершити біг")
        markup.add("📊 Мої результати", "💰 SHRK COINS")
        text = "Обери дію:"
    bot.send_message(message.chat.id, text, reply_markup=markup)


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
# === Запуск ===
print(f"{VERSION} запущено.")
bot.infinity_polling()
