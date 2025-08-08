import os
import json
import logging
import random
import threading
import time
from datetime import datetime, timedelta
from telebot import TeleBot, types

# === Переменная окружения и инициализация бота ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Переменная BOT_TOKEN не задана. Установи её в окружении.")

bot = TeleBot(BOT_TOKEN)
VERSION = "SHARKAN BOT v1.2 — RUN + BOOKS + PROFILE + PLAN + STATS + COINS"

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
    with open(USER_PROFILE_FILE, "r", encoding="utf-8") as f:
        user_profiles = json.load(f)
else:
    user_profiles = {}

def save_profiles():
    try:
        with open(USER_PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(user_profiles, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"[SAVE_PROFILE_ERROR] {e}")

# === Языки ===
LANGUAGES = {'ua': 'Українська', 'ru': 'Русский', 'en': 'English'}
user_lang = {}
for uid, profile in user_profiles.items():
    if "language" in profile:
        user_lang[uid] = profile["language"]

def get_lang(user_id: str) -> str:
    return user_lang.get(user_id, "ua")

# === Книги ===
user_states = {}
try:
    with open("books_ua.json", "r", encoding="utf-8") as f:
        all_books = json.load(f)
except Exception as e:
    print(f"Помилка при завантаженні книг: {e}")
    all_books = []

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def show_book_page(chat_id, user_id):
    state = user_states.get(user_id, {})
    title = state.get("book_title")
    page = state.get("page", 0)

    for book in all_books:
        if book["title"] == title:
            pages = book.get("pages", [])
            if not pages:
                bot.send_message(chat_id, "❌ Книга порожня.")
                return
            page = clamp(page, 0, len(pages) - 1)
            user_states[user_id]["page"] = page

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("⬅️ Назад", "➡️ Вперед")
            markup.add("⬅️ Головне меню")
            bot.send_message(
                chat_id,
                f"📘 *{title}*\n\n📄 Сторінка {page + 1} з {len(pages)}:\n\n{pages[page]}",
                parse_mode="Markdown",
                reply_markup=markup
            )
            return
    bot.send_message(chat_id, "❌ Книгу не знайдено.")

@bot.message_handler(func=lambda msg: msg.text == "📚 Книги SHARKAN")
def show_book_list(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for book in all_books:
        markup.add(f"📖 {book['title']}")
    markup.add("⬅️ Головне меню")
    bot.send_message(message.chat.id, "📚 Обери книгу:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("📖 "))
def handle_book_selection(message):
    user_id = str(message.from_user.id)
    title = message.text.replace("📖 ", "", 1).strip()
    for book in all_books:
        if book["title"] == title:
            user_states[user_id] = {"book_title": title, "page": 0}
            show_book_page(message.chat.id, user_id)
            return
    bot.send_message(message.chat.id, "❌ Книгу не знайдено.")

@bot.message_handler(func=lambda msg: msg.text in ["⬅️ Назад", "➡️ Вперед"])
def handle_book_page_nav(message):
    user_id = str(message.from_user.id)
    if user_id not in user_states or "book_title" not in user_states[user_id]:
        return
    if message.text == "➡️ Вперед":
        user_states[user_id]["page"] += 1
    elif message.text == "⬅️ Назад":
        user_states[user_id]["page"] -= 1
    show_book_page(message.chat.id, user_id)

# === Мотивации и советы тренеров ===
try:
    with open("motivations.json", "r", encoding="utf-8") as f:
        motivation_data = json.load(f)
except Exception as e:
    motivation_data = {"ua": [], "ru": [], "en": []}
    logging.error(f"[LOAD_MOTIVATION_ERROR] {e}")

try:
    with open("coaches_tips.json", "r", encoding="utf-8") as f:
        coaches_data = json.load(f)
except Exception as e:
    coaches_data = {"ua": [], "ru": [], "en": []}
    logging.error(f"[LOAD_COACHES_ERROR] {e}")

@bot.message_handler(commands=['motivation'])
def cmd_motivation(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    phrases = motivation_data.get(lang, [])
    bot.send_message(message.chat.id, random.choice(phrases) if phrases else "Немає мотивацій для твоєї мови.")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in [
    "🧠 мотивація", "💖 натхнення", "🧠 мотивация", "💖 вдохновение",
    "🧠 motivation", "💖 inspiration"
])
def motivation_handler(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    phrases = motivation_data.get(lang, [])
    bot.send_message(message.chat.id, random.choice(phrases) if phrases else "Немає мотивацій для твоєї мови.")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in [
    "🎓 поради від тренерів", "🎓 советы от тренеров", "🎓 pro trainer tips"
])
def coach_tip_handler(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
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

# === SHARKAN RUN — таймер, стоп, история ===
running_timers = {}
last_bot_messages = {}

def calculate_calories(weight_kg, duration_min):
    MET = 9.8
    return round((MET * 3.5 * weight_kg / 200) * duration_min)

def save_run_result(user_id, duration_min, calories):
    try:
        with open("run_history.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data.setdefault(user_id, []).append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "duration_min": duration_min,
        "calories": calories
    })
    with open("run_history.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return data[user_id][-3:]

def send_clean_message(chat_id, user_id, text, reply_markup=None):
    mid = last_bot_messages.get(user_id)
    if mid:
        try:
            bot.delete_message(chat_id, mid)
        except Exception:
            pass
    msg = bot.send_message(chat_id, text, reply_markup=reply_markup)
    last_bot_messages[user_id] = msg.message_id
    return msg.message_id

class RunTimer:
    def __init__(self, bot_obj, chat_id, user_id, weight_kg, lang):
        self.bot = bot_obj
        self.chat_id = chat_id
        self.user_id = user_id
        self.weight_kg = weight_kg
        self.lang = lang
        self.start_time = datetime.now()
        self.active = True
        self.message_id = None
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.active = False
        duration = max(1, round((datetime.now() - self.start_time).seconds / 60))
        calories = calculate_calories(self.weight_kg, duration)
        save_run_result(self.user_id, duration, calories)
        # === Начислим SHRK COINS ===
        profile = user_profiles.setdefault(self.user_id, {})
        coins = int(profile.get("coins", 0))
        coins += max(1, duration // 10) * 5  # 5 монет за каждые 10 минут (минимум 5)
        profile["coins"] = coins
        save_profiles()
        return duration, calories, coins

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
            except Exception:
                pass
            time.sleep(60)

def text_contains_any(text: str, options: list[str]) -> bool:
    return any(opt in text for opt in options)

@bot.message_handler(func=lambda m: m.text and text_contains_any(m.text, ["🏁 Почати біг", "🏁 Начать бег", "🏁 Start run"]) or
                                  (m.text and m.text.lower() in ["почати біг", "начать бег", "start run"]))
def start_run(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    lang = get_lang(user_id)

    weight = 70
    try:
        weight = int(user_profiles.get(user_id, {}).get("weight", 70))
    except Exception:
        pass

    if user_id in running_timers:
        try:
            running_timers[user_id].stop()
        except Exception:
            pass

    running_timers[user_id] = RunTimer(bot, chat_id, user_id, weight, lang)

    texts = {
        "ua": "🏃‍♂️ Біжи! Я фіксую твій час...\n⛔️ Натисни «Завершити біг», коли завершиш.",
        "ru": "🏃‍♂️ Беги! Я фиксирую твоё время...\n⛔️ Нажми «Завершить бег», когда закончишь.",
        "en": "🏃‍♂️ Run! I’m tracking your time...\n⛔️ Tap 'Stop run' when you’re done."
    }
    send_clean_message(chat_id, user_id, texts.get(lang, texts["ua"]))

@bot.message_handler(func=lambda m: m.text and text_contains_any(m.text, ["⛔️ Завершити біг", "⛔️ Завершить бег", "⛔️ Stop run"]) or
                                  (m.text and m.text.lower() in ["завершити біг", "завершить бег", "stop run"]))
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

    duration, calories, coins = running_timers[user_id].stop()
    del running_timers[user_id]

    unit = {"ua": "хв", "ru": "мин", "en": "min"}[lang if lang in ["ua","ru","en"] else "ua"]
    result_text = {
        "ua": f"✅ Завершено!\n⏱ Тривалість: {duration} {unit}\n🔥 Калорії: {calories} ккал\n🪙 Монети: +{max(5, (duration//10)*5)} (всього: {coins})",
        "ru": f"✅ Готово!\n⏱ Длительность: {duration} {unit}\n🔥 Калории: {calories} ккал\n🪙 Монеты: +{max(5, (duration//10)*5)} (всего: {coins})",
        "en": f"✅ Done!\n⏱ Duration: {duration} {unit}\n🔥 Calories: {calories} kcal\n🪙 Coins: +{max(5, (duration//10)*5)} (total: {coins})"
    }
    send_clean_message(chat_id, user_id, result_text.get(lang, result_text["ua"]))

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["⏱ режим біг", "⏱ режим бег", "⏱ running mode"])
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

@bot.message_handler(func=lambda m: m.text and any(s in m.text.lower() for s in ["результат", "results"]))
def show_run_results(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    lang = get_lang(user_id)
    try:
        with open("run_history.json", "r", encoding="utf-8") as f:
            run_history = json.load(f)
        records = run_history.get(user_id, [])
    except Exception:
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
    unit = {"ua": "хв", "ru": "мин", "en": "min"}[lang if lang in ["ua","ru","en"] else "ua"]

    result = [titles.get(lang, titles["ua"])]
    for run in reversed(records[-3:]):
        result.append(f"📅 {run['date']} — {run['duration_min']} {unit} — {run['calories']} ккал")
    send_clean_message(chat_id, user_id, "\n".join(result))

# === Язык/гендер ===
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    for code, name in LANGUAGES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"lang_{code}"))
    bot.send_message(message.chat.id, "👋 Обери мову / Choose your language / Выберите язык:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    chat_id = call.message.chat.id
    user_id = str(call.from_user.id)
    lang = call.data.split("_", 1)[1]

    profile = user_profiles.setdefault(user_id, {})
    profile["language"] = lang
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender(call):
    chat_id = call.message.chat.id
    user_id = str(call.from_user.id)
    gender = call.data.split("_", 1)[1]  # male / female

    profile = user_profiles.setdefault(user_id, {})
    profile["gender"] = gender
    save_profiles()

    lang = get_lang(user_id)
    confirm = {
        "ua": "✅ Стать збережено.",
        "ru": "✅ Пол сохранён.",
        "en": "✅ Gender saved."
    }
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id)
    bot.send_message(chat_id, confirm.get(lang, "✅ Done."))
    menu_from_id(chat_id, user_id)

# === Главное меню и обработчики кнопок ===
def menu_from_id(chat_id, user_id):
    lang = get_lang(user_id)
    gender = user_profiles.get(user_id, {}).get("gender", "male")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    if lang == "ua":
        buttons = [
            "🔥 Мій план" if gender == "female" else "🔥 План на сьогодні",
            "🏋️ Тренування",
            "💖 Натхнення" if gender == "female" else "🧠 Мотивація",
            "⏱ Режим БІГ",
            "🥷 Бій з Тінню",
            "📚 Книги SHARKAN",
            "🎓 Поради від тренерів",
            "🤖 AI SHARKAN",
            "🌟 Виклик" if gender == "female" else "🥇 Виклик",
            "💎 SHRK COINS" if gender == "female" else "🪙 SHRK COINS",
            "📊 Мій прогрес" if gender == "female" else "📊 Мої результати",
            "📈 Прогрес / Ранги" if gender == "female" else "📈 Статистика",
            "🏆 Рейтинг SHARKAN",
            "🎵 Музика",
            "👑 Мій шлях" if gender == "female" else "👤 Мій профіль",
            "🛍 Магазин",
            "💬 Чат SHARKAN",
            "📢 Канал SHARKAN",
            "🧘‍♀️ Відновлення" if gender == "female" else "🧘 Відновлення",
            "🔒 Темна Зона",
            "⚙️ Налаштування",
            "❓ FAQ / Підтримка" if gender == "female" else "❓ Допомога / FAQ",
            "📨 Співпраця"
        ]
    elif lang == "ru":
        buttons = [
            "🔥 Мой план" if gender == "female" else "🔥 План на сегодня",
            "🏋️ Тренировка",
            "💖 Вдохновение" if gender == "female" else "🧠 Мотивация",
            "⏱ Режим БЕГ",
            "🥷 Бой с Тенью",
            "📚 Книги SHARKAN",
            "🎓 Советы от тренеров",
            "🤖 AI SHARKAN",
            "🌟 Вызов" if gender == "female" else "🥇 Вызов",
            "💎 SHRK COINS" if gender == "female" else "🪙 SHRK COINS",
            "📊 Мой прогресс" if gender == "female" else "📊 Мои результаты",
            "📈 Прогресс / Ранги" if gender == "female" else "📈 Статистика",
            "🏆 Рейтинг SHARKAN",
            "🎵 Музыка",
            "👑 Мой путь" if gender == "female" else "👤 Мой профиль",
            "🛍 Магазин",
            "💬 Чат SHARKAN",
            "📢 Канал SHARKAN",
            "🧘‍♀️ Восстановление" if gender == "female" else "🧘 Восстановление",
            "🔒 Тёмная Зона",
            "⚙️ Настройки",
            "❓ FAQ / Поддержка" if gender == "female" else "❓ Помощь / FAQ",
            "📨 Сотрудничество"
        ]
    else:
        buttons = [
            "🔥 My Plan" if gender == "female" else "🔥 Today's Plan",
            "🏋️ Workout",
            "💖 Inspiration" if gender == "female" else "🧠 Motivation",
            "⏱ Running Mode",
            "🥷 Shadow Fight",
            "📚 SHARKAN Books",
            "🎓 Pro Trainer Tips",
            "🤖 AI SHARKAN",
            "🌟 Challenge" if gender == "female" else "🥇 Challenge",
            "💎 SHRK COINS" if gender == "female" else "🪙 SHRK COINS",
            "📊 My Progress" if gender == "female" else "📊 My Results",
            "📈 Progress / Ranks" if gender == "female" else "📈 Statistics",
            "🏆 SHARKAN Ranking",
            "🎵 Music",
            "👑 My Path" if gender == "female" else "👤 My Profile",
            "🛍 Shop",
            "💬 SHARKAN Chat",
            "📢 SHARKAN Channel",
            "🧘‍♀️ Recovery" if gender == "female" else "🧘 Recovery",
            "🔒 Dark Zone",
            "⚙️ Settings",
            "❓ Help / FAQ",
            "📨 Contact Us"
        ]

    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i+2])

    bot.send_message(
        chat_id,
        "🧠 Обери розділ:" if lang == "ua" else "🧠 Выберите раздел:" if lang == "ru" else "🧠 Choose a section:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower() in ["⬅️ головне меню", "⬅️ главное меню", "⬅️ main menu"])
def back_to_main_menu(message):
    user_id = str(message.from_user.id)
    menu_from_id(message.chat.id, user_id)

# === Профиль: вес/рост/цель ===
profile_wizard = {}  # user_id -> {"step": ..., "tmp": {...}}

def start_profile(chat_id, user_id):
    lang = get_lang(user_id)
    profile_wizard[user_id] = {"step": "weight", "tmp": {}}
    prompt = {
        "ua": "⚖️ Вкажи свою вагу (кг), напр.: 75",
        "ru": "⚖️ Укажи свой вес (кг), напр.: 75",
        "en": "⚖️ Enter your weight (kg), e.g. 75"
    }
    bot.send_message(chat_id, prompt.get(lang, prompt["ua"]))

@bot.message_handler(func=lambda m: m.text and m.text in [
    "👤 Мій профіль","👤 Мой профиль","👤 My Profile","👑 Мій шлях","👑 Мой путь","👑 My Path"
])
def on_profile_button(message):
    user_id = str(message.from_user.id)
    profile = user_profiles.get(user_id, {})
    lang = get_lang(user_id)
    if not profile.get("weight") or not profile.get("height") or not profile.get("goal"):
        start_profile(message.chat.id, user_id)
        return

    txt = {
        "ua": f"👤 Профіль:\nВага: {profile.get('weight','?')} кг\nЗріст: {profile.get('height','?')} см\nЦіль: {profile.get('goal','?')}\nМонети: {profile.get('coins',0)}",
        "ru": f"👤 Профиль:\nВес: {profile.get('weight','?')} кг\nРост: {profile.get('height','?')} см\nЦель: {profile.get('goal','?')}\nМонеты: {profile.get('coins',0)}",
        "en": f"👤 Profile:\nWeight: {profile.get('weight','?')} kg\nHeight: {profile.get('height','?')} cm\nGoal: {profile.get('goal','?')}\nCoins: {profile.get('coins',0)}",
    }
    bot.send_message(message.chat.id, txt.get(lang, txt["ua"]))

@bot.message_handler(func=lambda m: str(m.from_user.id) in profile_wizard)
def profile_flow(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    data = profile_wizard[user_id]
    step = data["step"]
    value = (message.text or "").strip()

    def ask_height():
        data["step"] = "height"
        q = {
            "ua":"📏 Тепер зріст (см), напр.: 180",
            "ru":"📏 Теперь рост (см), напр.: 180",
            "en":"📏 Now height (cm), e.g. 180"
        }
        bot.send_message(message.chat.id, q.get(lang,q["ua"]))

    def ask_goal():
        data["step"] = "goal"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if lang == "ru":
            kb.add("Похудеть","Набрать массу")
            kb.add("Поддерживать форму")
        elif lang == "en":
            kb.add("Lose weight","Gain muscle")
            kb.add("Maintain")
        else:
            kb.add("Схуднути","Набрати масу")
            kb.add("Підтримувати форму")
        bot.send_message(message.chat.id, {
            "ua":"🎯 Обери ціль:",
            "ru":"🎯 Выбери цель:",
            "en":"🎯 Choose your goal:"
        }.get(lang,"🎯 Обери ціль:"), reply_markup=kb)

    if step == "weight":
        if not value.isdigit() or not (30 <= int(value) <= 300):
            bot.send_message(message.chat.id, {"ua":"Введи число 30–300.","ru":"Введи число 30–300.","en":"Enter 30–300."}[lang])
            return
        data["tmp"]["weight"] = int(value)
        ask_height()
        return

    if step == "height":
        if not value.isdigit() or not (120 <= int(value) <= 250):
            bot.send_message(message.chat.id, {"ua":"Введи число 120–250.","ru":"Введи число 120–250.","en":"Enter 120–250."}[lang])
            return
        data["tmp"]["height"] = int(value)
        ask_goal()
        return

    if step == "goal":
        goals_map = {
            "ua": {"схуднути":"lose", "набрати масу":"gain", "підтримувати форму":"maintain"},
            "ru": {"похудеть":"lose", "набрать массу":"gain", "поддерживать форму":"maintain"},
            "en": {"lose weight":"lose", "gain muscle":"gain", "maintain":"maintain"},
        }
        key = value.lower()
        goal_code = None
        for gk, gm in goals_map.items():
            if gk == lang and key in gm:
                goal_code = gm[key]
        if not goal_code:
            bot.send_message(message.chat.id, {"ua":"Обери варіант з кнопок.","ru":"Выбери вариант с кнопок.","en":"Choose from buttons."}[lang])
            return

        # Сохраняем профиль
        prof = user_profiles.setdefault(user_id, {})
        prof.update(data["tmp"])
        prof["goal"] = goal_code
        prof.setdefault("coins", 0)
        save_profiles()
        profile_wizard.pop(user_id, None)

        done = {"ua":"✅ Профіль збережено.","ru":"✅ Профиль сохранён.","en":"✅ Profile saved."}[lang]
        bot.send_message(message.chat.id, done, reply_markup=types.ReplyKeyboardRemove())
        menu_from_id(message.chat.id, user_id)
        return

# === План на сьогодні ===
@bot.message_handler(func=lambda m: m.text and m.text in [
    "🔥 План на сьогодні","🔥 План на сегодня","🔥 Today's Plan","🔥 Мій план","🔥 Мой план","🔥 My Plan"
])
def plan_today(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    prof = user_profiles.get(user_id, {})
    weight = int(prof.get("weight", 70))
    goal = prof.get("goal", "maintain")

    # Простая логика генерации плана
    if goal == "lose":
        workout = [
            "1) Берпі — 3×12 (відпочинок 60с)",
            "2) Присідання з вагою тіла — 4×15 (45с)",
            "3) Планка — 3×45с (30с)",
            "4) Випади — 3×12/нога (60с)",
            "5) Скакалка/кардіо — 10 хв помірно"
        ]
        kcal_target = max(500, 6 * weight)
        meals = [
            "Сніданок: йогурт + ягоди + жменя горіхів",
            "Обід: куряче філе на парі + овочі",
            "Вечеря: риба/тунець + салат",
            "Перекус: яблуко/морква"
        ]
    elif goal == "gain":
        workout = [
            "1) Віджимання — 5×10-15 (90с)",
            "2) Присідання — 5×12 (90с)",
            "3) Тяга в нахилі (еластик/гантелі) — 4×12 (90с)",
            "4) Жим над головою (гантелі/еластик) — 4×10 (90с)",
            "5) Прес: скручування — 3×15 (60с)"
        ]
        kcal_target = max(2600, 30 * weight)
        meals = [
            "Сніданок: вівсянка + банан + арахісова паста",
            "Обід: рис + курка/яловичина + овочі",
            "Перекус: творог/йогурт + горіхи",
            "Вечеря: паста/картопля + риба/м'ясо + салат"
        ]
    else:
        workout = [
            "1) Легка пробіжка — 20 хв",
            "2) Віджимання — 3×12 (60с)",
            "3) Присідання — 3×15 (60с)",
            "4) Планка — 3×40с (30с)",
            "5) Розтяжка — 10 хв"
        ]
        kcal_target = max(2000, 22 * weight)
        meals = [
            "Сніданок: омлет + овочі",
            "Обід: гречка + індичка/курка + салат",
            "Перекус: фрукти/горіхи",
            "Вечеря: риба/овочі/салат"
        ]

    water = f"Вода: {round(weight*0.03,1)} л/день"
    supps = "Добавки: вітамін D, омега-3, електроліти (за потреби)."

    text_map = {
        "ua": f"🗓 <b>План на сьогодні</b>\n\n<b>Тренування</b>:\n" + "\n".join(workout) +
              f"\n\n<b>Харчування</b>:\n- " + "\n- ".join(meals) +
              f"\n\n<b>Калорії (орієнтир)</b>: ~{kcal_target} ккал\n{water}\n{supps}",
        "ru": f"🗓 <b>План на сегодня</b>\n\n<b>Тренировка</b>:\n" + "\n".join(workout) +
              f"\n\n<b>Питание</b>:\n- " + "\n- ".join(meals) +
              f"\n\n<b>Калории (ориентир)</b>: ~{kcal_target} ккал\n{water}\n{supps}",
        "en": f"🗓 <b>Plan for today</b>\n\n<b>Workout</b>:\n" + "\n".join(workout) +
              f"\n\n<b>Nutrition</b>:\n- " + "\n- ".join(meals) +
              f"\n\n<b>Calories (target)</b>: ~{kcal_target} kcal\n{water}\nSupplements: vitamin D, omega-3, electrolytes."
    }
    bot.send_message(message.chat.id, text_map.get(lang, text_map["ua"]), parse_mode="HTML")

# === Статистика / Progress ===
def compute_streak(records):
    if not records:
        return 0
    dates = sorted({r["date"] for r in records}, reverse=True)
    # формат YYYY-MM-DD
    today = datetime.now().date()
    streak = 0
    cur = today
    dates_set = set(datetime.strptime(d, "%Y-%m-%d").date() for d in dates)
    while cur in dates_set:
        streak += 1
        cur = cur - timedelta(days=1)
    return streak

@bot.message_handler(func=lambda m: m.text and m.text in ["📈 Статистика","📈 Прогрес / Ранги","📈 Statistics","📈 Progress / Ranks"])
def show_stats(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    try:
        with open("run_history.json","r",encoding="utf-8") as f:
            data = json.load(f)
        recs = data.get(user_id, [])
    except Exception:
        recs = []

    total_runs = len(recs)
    total_min = sum(r.get("duration_min",0) for r in recs)
    total_kcal = sum(r.get("calories",0) for r in recs)
    streak = compute_streak(recs)

    txt = {
        "ua": f"📈 <b>Статистика</b>\nПробіжок: {total_runs}\nХвилин: {total_min}\nКалорій: {total_kcal}\nСтрік: {streak} дн.",
        "ru": f"📈 <b>Статистика</b>\nПробежек: {total_runs}\nМинут: {total_min}\nКалорий: {total_kcal}\nСтик: {streak} дн.",
        "en": f"📈 <b>Statistics</b>\nRuns: {total_runs}\nMinutes: {total_min}\nCalories: {total_kcal}\nStreak: {streak} days"
    }
    bot.send_message(message.chat.id, txt.get(lang, txt["ua"]), parse_mode="HTML")

# === SHRK COINS ===
@bot.message_handler(func=lambda m: m.text and m.text in ["🪙 SHRK COINS","💎 SHRK COINS"])
def coins_handler(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    coins = int(user_profiles.get(user_id, {}).get("coins", 0))
    txt = {
        "ua": f"🪙 Твій баланс SHRK COINS: <b>{coins}</b>",
        "ru": f"🪙 Твой баланс SHRK COINS: <b>{coins}</b>",
        "en": f"🪙 Your SHRK COINS balance: <b>{coins}</b>"
    }
    bot.send_message(message.chat.id, txt.get(lang, txt["ua"]), parse_mode="HTML")

# === Настройки ===
@bot.message_handler(func=lambda m: m.text and m.text in ["⚙️ Налаштування","⚙️ Настройки","⚙️ Settings"])
def settings_menu(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add("🌐 Сменить язык","🧹 Сбросить профиль")
        kb.add("⬅️ Главное меню")
        txt = "⚙️ Настройки"
    elif lang == "en":
        kb.add("🌐 Change language","🧹 Reset profile")
        kb.add("⬅️ Main menu")
        txt = "⚙️ Settings"
    else:
        kb.add("🌐 Змінити мову","🧹 Скинути профіль")
        kb.add("⬅️ Головне меню")
        txt = "⚙️ Налаштування"
    bot.send_message(message.chat.id, txt, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text in ["🌐 Сменить язык","🌐 Change language","🌐 Змінити мову"])
def settings_change_lang(message):
    markup = types.InlineKeyboardMarkup()
    for code, name in LANGUAGES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"lang_{code}"))
    bot.send_message(message.chat.id, "🌐 Обери мову / Choose language / Выберите язык:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and m.text in ["🧹 Сбросить профиль","🧹 Reset profile","🧹 Скинути профіль"])
def reset_profile(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    user_profiles[user_id] = {"language": lang, "coins": 0}
    save_profiles()
    bot.send_message(message.chat.id, {"ua":"✅ Профіль скинуто.","ru":"✅ Профиль сброшен.","en":"✅ Profile reset."}[lang])
    menu_from_id(message.chat.id, user_id)

# === Заглушки для ещё не реализованных разделов ===
@bot.message_handler(func=lambda m: m.text and m.text in ["🥷 Бій з Тінню","🥷 Бой с Тенью","🥷 Shadow Fight"])
def shadow_fight(message):
    lang = get_lang(str(message.from_user.id))
    txt = {
        "ua":"🥷 Розділ готується. Хочеш таймер раундів 3×1 хв з озвучкою — скажи, додам.",
        "ru":"🥷 Раздел в подготовке. Хочешь таймер раундов 3×1 мин с озвучкой — скажи, добавлю.",
        "en":"🥷 Coming soon. Want a 3×1 min round timer with voice cues? Say the word."
    }
    bot.send_message(message.chat.id, txt.get(lang, txt["ua"]))

@bot.message_handler(func=lambda m: m.text and m.text in ["🎵 Музика","🎵 Музыка","🎵 Music"])
def music_section(message):
    lang = get_lang(str(message.from_user.id))
    txt = {
        "ua":"🎵 Додам плейлисти (олдскул/техно/реп) та оновлення. Потрібні MP3 — скину формати.",
        "ru":"🎵 Добавлю плейлисты (олдскул/техно/рэп) и обновления. Нужны MP3 — подскажу форматы.",
        "en":"🎵 I’ll add playlists (old-school/techno/rap) and updates. Provide MP3s and I’ll wire them in."
    }
    bot.send_message(message.chat.id, txt.get(lang, txt["ua"]))

# === Старт ===
print(f"{VERSION} запущено.")
bot.infinity_polling(skip_pending=True)
