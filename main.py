import os
import json
import logging
import random
from datetime import datetime
from telebot import TeleBot, types
from book_reader_module import *

import json
from telebot import types

# === Завантаження книг при запуску ===
try:
    with open("думай_і_багатій_ua.json", "r", encoding="utf-8") as f:
        book_think_rich = json.load(f)
    with open("сила_звички_ua.json", "r", encoding="utf-8") as f:
        book_habit = json.load(f)
except Exception as e:
    print(f"Помилка при завантаженні книг: {e}")
    book_think_rich, book_habit = [], []

# === Вибір книги ===
@bot.message_handler(func=lambda msg: msg.text == "📚 Книги SHARKAN")
def book_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📘 Думай і багатій", "📙 Сила звички")
    markup.add("⬅️ Головне меню")
    bot.send_message(message.chat.id, "📚 Обери книгу для читання:", reply_markup=markup)

# === Обробка вибору книги ===
@bot.message_handler(func=lambda msg: msg.text in ["📘 Думай і багатій", "📙 Сила звички"])
def read_book(message):
    user_id = str(message.from_user.id)
    book = book_think_rich if message.text == "📘 Думай і багатій" else book_habit
    if not book:
        bot.send_message(message.chat.id, "⚠️ Книга недоступна.")
        return
    user_states[user_id] = {"book": message.text, "page": 0}
    show_page(message.chat.id, user_id)

# === Кнопки ⬅️➡️ для навігації ===
@bot.message_handler(func=lambda msg: msg.text in ["⬅️ Назад", "➡️ Вперед"])
def flip_page(message):
    user_id = str(message.from_user.id)
    state = user_states.get(user_id, {})
    if "book" not in state: return

    if message.text == "➡️ Вперед":
        state["page"] += 1
    elif message.text == "⬅️ Назад" and state["page"] > 0:
        state["page"] -= 1

    show_page(message.chat.id, user_id)

# === Показати сторінку ===
def show_page(chat_id, user_id):
    state = user_states.get(user_id, {})
    book = book_think_rich if state.get("book") == "📘 Думай і багатій" else book_habit
    page = state.get("page", 0)

    if page >= len(book):
        bot.send_message(chat_id, "📖 Це остання сторінка.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⬅️ Назад", "➡️ Вперед")
    markup.add("⬅️ Головне меню")
    bot.send_message(chat_id, f"📖 Сторінка {page+1}:

{book[page]}", reply_markup=markup)
    
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

# === SHARKAN RUN v3 — Режим БІГ з таймером, автоочисткою, історією ===

import threading
import time
from datetime import datetime
import json
from telebot import types

# === Глобальні змінні ===
running_timers = {}
last_bot_messages = {}

# === Отримання мови ===
def get_lang(user_id):
    return user_lang.get(user_id, "ua")

# === Калькуляція калорій ===
def calculate_calories(weight_kg, duration_min):
    MET = 9.8
    return round((MET * 3.5 * weight_kg / 200) * duration_min)

# === Збереження результату ===
def save_run_result(user_id, duration_min, calories):
    try:
        with open("run_history.json", "r") as f:
            data = json.load(f)
    except:
        data = {}
    if user_id not in data:
        data[user_id] = []
    data[user_id].append({
        "date": datetime.now().strftime("%d.%m.%Y"),
        "duration_min": duration_min,
        "calories": calories
    })
    with open("run_history.json", "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return data[user_id][-3:]

# === Відправка нового повідомлення з очищенням ===
def send_clean_message(chat_id, user_id, text, reply_markup=None):
    if user_id in last_bot_messages:
        try:
            bot.delete_message(chat_id, last_bot_messages[user_id])
        except:
            pass
    msg = bot.send_message(chat_id, text, reply_markup=reply_markup)
    last_bot_messages[user_id] = msg.message_id
    return msg.message_id

# === Клас таймера з оновленням ===
class RunTimer:
    def __init__(self, bot, chat_id, user_id, weight_kg, lang):
        self.bot = bot
        self.chat_id = chat_id
        self.user_id = user_id
        self.weight_kg = weight_kg
        self.lang = lang
        self.start_time = datetime.now()
        self.active = True
        self.message_id = None
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def stop(self):
        self.active = False
        duration = round((datetime.now() - self.start_time).seconds / 60)
        calories = calculate_calories(self.weight_kg, duration)
        save_run_result(self.user_id, duration, calories)
        return duration, calories

    def loop(self):
        while self.active:
            minutes = (datetime.now() - self.start_time).seconds // 60
            msg_text = {
                "ua": f"🕒 Пройшло: {minutes} хв",
                "ru": f"🕒 Прошло: {minutes} мин",
                "en": f"🕒 Elapsed: {minutes} min"
            }.get(self.lang, f"🕒 Пройшло: {minutes} хв")
            try:
                if self.message_id:
                    self.bot.delete_message(self.chat_id, self.message_id)
                msg = self.bot.send_message(self.chat_id, msg_text)
                self.message_id = msg.message_id
            except:
                pass
            time.sleep(60)

# === Кнопка "Почати біг" ===
@bot.message_handler(func=lambda msg: msg.text.lower() in ["почати біг", "начать бег", "start run"])
def start_run(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    lang = get_lang(user_id)
    weight = 70
    try:
        with open("user_profiles.json", "r") as f:
            profile = json.load(f)
        weight = int(profile.get(user_id, {}).get("weight", 70))
    except:
        pass

    if user_id in running_timers:
        running_timers[user_id].stop()
    running_timers[user_id] = RunTimer(bot, chat_id, user_id, weight, lang)

    texts = {
    "ua": "🏃‍♂️ Біжи! Я фіксую твій час...\n⛔️ Натисни «Завершити біг», коли завершиш.",
    "ru": "🏃‍♂️ Беги! Я фиксирую твоё время...\n⛔️ Нажми «Завершить бег», когда закончишь.",
    "en": "🏃‍♂️ Run! I’m tracking your time...\n⛔️ Tap 'Stop run' when you’re done."
}
    send_clean_message(chat_id, user_id, texts.get(lang, texts["ua"]))

# === Кнопка "Завершити біг" ===
@bot.message_handler(func=lambda msg: msg.text.lower() in ["завершити біг", "завершить бег", "stop run"])
def stop_run(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    lang = get_lang(user_id)

    if user_id not in running_timers:
        texts = {
            "ua": "❌ Біг не активний.",
            "ru": "❌ Бег не запущен.",
            "en": "❌ Run not active."
        }
        send_clean_message(chat_id, user_id, texts.get(lang, texts["ua"]))
        return

    duration, calories = running_timers[user_id].stop()
    del running_timers[user_id]

    texts = {
    "ua": "🏃‍♂️ Біжи! Я фіксую твій час...\n⛔️ Натисни «Завершити біг», коли завершиш.",
    "ru": "🏃‍♂️ Беги! Я фиксирую твоё время...\n⛔️ Нажми «Завершить бег», когда закончишь.",
    "en": "🏃‍♂️ Run! I’m tracking your time...\n⛔️ Tap 'Stop run' when you’re done."
}
    send_clean_message(chat_id, user_id, result_text.get(lang, result_text["ua"]))

# === Меню SHARKAN RUN ===
@bot.message_handler(func=lambda msg: msg.text.lower() in ["⏱ режим біг", "⏱ режим бег", "⏱ running mode"])
def run_menu(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        markup.add("🏁 Начать бег", "⛔️ Завершить бег")
        markup.add("📊 Мои результаты", "⬅️ Главное меню")
        text = "🏃‍♂️ Выбери действие для SHARKAN RUN:"
    elif lang == "en":
        markup.add("🏁 Start run", "⛔️ Stop run")
        markup.add("📊 My results", "⬅️ Main menu")
        text = "🏃‍♂️ Choose an action for SHARKAN RUN:"
    else:
        markup.add("🏁 Почати біг", "⛔️ Завершити біг")
        markup.add("📊 Мої результати", "⬅️ Головне меню")
        text = "🏃‍♂️ Обери дію для SHARKAN RUN:"

    send_clean_message(message.chat.id, user_id, text, reply_markup=markup)

# === Останні пробіжки ===
@bot.message_handler(func=lambda msg: "результат" in msg.text.lower())
def show_run_results(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    lang = get_lang(user_id)

    try:
        with open("run_history.json", "r") as f:
            run_history = json.load(f)
        records = run_history.get(user_id, [])
    except:
        records = []

    if not records:
        no_data = {
            "ua": "❌ Немає збережених пробіжок.",
            "ru": "❌ Нет сохранённых пробежек.",
            "en": "❌ No saved runs."
        }
        send_clean_message(chat_id, user_id, no_data.get(lang, no_data["ua"]))
        return

    titles = {
        "ua": "📊 Останні пробіжки:",
        "ru": "📊 Последние пробежки:",
        "en": "📊 Recent runs:"
    }

    result = titles.get(lang, titles["ua"]) + "\n"
    for run in reversed(records[-3:]):
        result += f"📅 {run['date']} — {run['duration_min']} хв — {run['calories']} ккал\n"

    send_clean_message(chat_id, user_id, result)

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
