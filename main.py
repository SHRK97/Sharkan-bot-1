# -*- coding: utf-8 -*-
import os
import json
import logging
import random
import threading
import time
from datetime import datetime, timedelta
from telebot import TeleBot, types
from dotenv import load_dotenv

# =========================
# Boot & config
# =========================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set. Put it in .env or environment")

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
VERSION = "SHARKAN BOT v1.8 — FULL+ (RUN/BOOKS/PROFILE/PLAN/STATS/COINS/SHADOW/MUSIC/AI)"

logging.basicConfig(
    level=logging.INFO,
    filename="bot.log",
    filemode="a",
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# =========================
# File helpers & storage
# =========================
USER_PROFILE_FILE = "user_profiles.json"
RUN_HISTORY_FILE  = "run_history.json"
BOOKMARKS_FILE    = "bookmarks.json"
MUSIC_FILE        = "music_lib.json"
MOTIVATIONS_FILE  = "motivations.json"
COACHES_FILE      = "coaches_tips.json"
BOOKS_FILE        = "books_ua.json"

def safe_load(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"[LOAD_ERROR] {path}: {e}")
    return default

def safe_save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

user_profiles = safe_load(USER_PROFILE_FILE, {})     # per-user: language, gender, weight, height, goal, coins, flags...
run_history   = safe_load(RUN_HISTORY_FILE, {})      # per-user: list of runs
bookmarks     = safe_load(BOOKMARKS_FILE, {})        # per-user: {title: {chapter,page}}
music_lib     = safe_load(MUSIC_FILE, {})            # per-user: {category: [file_id, ...]}
motivations   = safe_load(MOTIVATIONS_FILE, {"ua":[],"ru":[],"en":[]})
coaches_data  = safe_load(COACHES_FILE, {"ua":[],"ru":[],"en":[]})
books_data    = safe_load(BOOKS_FILE, [])            # [{title, chapters:[{title, pages:[]}, ...]}]

LANGUAGES = {'ua':'Українська','ru':'Русский','en':'English'}
user_lang = {uid: prof.get("language","ua") for uid,prof in user_profiles.items()}

def get_lang(uid: str) -> str:
    return user_lang.get(uid, "ua")

def tr(lang, ua=None, ru=None, en=None):
    return {"ua":ua,"ru":ru,"en":en}.get(lang, ua)

def put_prof(uid, **kwargs):
    prof = user_profiles.setdefault(uid, {})
    prof.update(kwargs)
    safe_save(USER_PROFILE_FILE, user_profiles)
    return prof

# last message per user to "clean-edit"
def send_clean(chat_id, uid, text, reply_markup=None):
    key = "last_mid"
    last_mid = user_profiles.setdefault(uid, {}).get(key)
    if last_mid:
        try: bot.delete_message(chat_id, last_mid)
        except Exception: pass
    m = bot.send_message(chat_id, text, reply_markup=reply_markup)
    put_prof(uid, **{key: m.message_id})
    return m

# =========================
# /start + language/gender
# =========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    kb = types.InlineKeyboardMarkup()
    for code, name in LANGUAGES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"lang_{code}"))
    bot.send_message(message.chat.id, "👋 Обери мову / Choose your language / Выберите язык:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("lang_"))
def on_lang(c):
    uid = str(c.from_user.id)
    lang = c.data.split("_",1)[1]
    user_lang[uid] = lang
    put_prof(uid, language=lang)

    if lang == "ua":
        text = "✅ Твоя мова — українська.\n\n👤 Обери свою стать:"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Я — чоловік", callback_data="gender_male"),
               types.InlineKeyboardButton("Я — жінка",  callback_data="gender_female"))
    elif lang == "ru":
        text = "✅ Ваш язык — русский.\n\n👤 Выбери свой пол:"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Я — мужчина", callback_data="gender_male"),
               types.InlineKeyboardButton("Я — женщина", callback_data="gender_female"))
    else:
        text = "✅ Your language is English.\n\n👤 Select your gender:"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("I am a man", callback_data="gender_male"),
               types.InlineKeyboardButton("I am a woman", callback_data="gender_female"))

    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("gender_"))
def on_gender(c):
    uid = str(c.from_user.id)
    gender = c.data.split("_",1)[1]
    put_prof(uid, gender=gender)
    lang = get_lang(uid)
    bot.edit_message_reply_markup(chat_id=c.message.chat.id, message_id=c.message.message_id)
    bot.send_message(c.message.chat.id, tr(lang, "✅ Стать збережено.","✅ Пол сохранён.","✅ Gender saved."))
    show_main(c.message.chat.id, uid)

# =========================
# Main menu
# =========================
def show_main(chat_id, uid):
    lang = get_lang(uid); gender = user_profiles.get(uid, {}).get("gender","male")
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    if lang == "ua":
        buttons = [
            "🔥 Мій план" if gender=="female" else "🔥 План на сьогодні",
            "🏋️ Тренування",
            "💖 Натхнення" if gender=="female" else "🧠 Мотивація",
            "⏱ Режим БІГ",
            "🥷 Бій з Тінню",
            "📚 Книги SHARKAN",
            "🎵 Музика",
            "🎓 Поради від тренерів",
            "🪙 SHRK COINS",
            "📈 Статистика",
            "👤 Мій профіль",
            "⚙️ Налаштування",
            "🤖 AI SHARKAN"
        ]
    elif lang == "ru":
        buttons = [
            "🔥 Мой план" if gender=="female" else "🔥 План на сегодня",
            "🏋️ Тренировка",
            "💖 Вдохновение" if gender=="female" else "🧠 Мотивация",
            "⏱ Режим БЕГ",
            "🥷 Бой с Тенью",
            "📚 Книги SHARKAN",
            "🎵 Музыка",
            "🎓 Советы от тренеров",
            "🪙 SHRK COINS",
            "📈 Статистика",
            "👤 Мой профиль",
            "⚙️ Настройки",
            "🤖 AI SHARKAN"
        ]
    else:
        buttons = [
            "🔥 My Plan" if gender=="female" else "🔥 Today's Plan",
            "🏋️ Workout",
            "💖 Inspiration" if gender=="female" else "🧠 Motivation",
            "⏱ Running Mode",
            "🥷 Shadow Fight",
            "📚 SHARKAN Books",
            "🎵 Music",
            "🎓 Pro Trainer Tips",
            "🪙 SHRK COINS",
            "📈 Statistics",
            "👤 My Profile",
            "⚙️ Settings",
            "🤖 AI SHARKAN"
        ]
    for i in range(0, len(buttons), 2):
        kb.add(*buttons[i:i+2])

    bot.send_message(chat_id, tr(lang, "🧠 Обери розділ:","🧠 Выберите раздел:","🧠 Choose a section:"), reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["⬅️ головне меню","⬅️ главное меню","⬅️ main menu"])
def back_home(m): show_main(m.chat.id, str(m.from_user.id))

# =========================
# Profile wizard (weight/height/goal)
# =========================
profile_wizard = {}  # uid -> {"step":..., "tmp":{}}

def start_profile(chat_id, uid):
    lang = get_lang(uid)
    profile_wizard[uid] = {"step":"weight","tmp":{}}
    bot.send_message(chat_id, tr(lang,"⚖️ Вкажи вагу (кг), напр.: 75","⚖️ Укажи вес (кг), напр.: 75","⚖️ Enter weight (kg), e.g. 75"))

@bot.message_handler(func=lambda m: m.text in ["👤 Мій профіль","👤 Мой профиль","👤 My Profile","👑 Мій шлях","👑 Мой путь","👑 My Path"])
def on_profile_btn(m):
    uid = str(m.from_user.id); prof = user_profiles.get(uid, {}); lang = get_lang(uid)
    if not all(k in prof for k in ["weight","height","goal"]):
        start_profile(m.chat.id, uid); return
    txt = tr(
        lang,
        f"👤 Профіль:\nВага: {prof.get('weight')} кг\nЗріст: {prof.get('height')} см\nЦіль: {prof.get('goal')}\nМонети: {prof.get('coins',0)}",
        f"👤 Профиль:\nВес: {prof.get('weight')} кг\nРост: {prof.get('height')} см\nЦель: {prof.get('goal')}\nМонеты: {prof.get('coins',0)}",
        f"👤 Profile:\nWeight: {prof.get('weight')} kg\nHeight: {prof.get('height')} cm\nGoal: {prof.get('goal')}\nCoins: {prof.get('coins',0)}"
    )
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: str(m.from_user.id) in profile_wizard)
def profile_flow(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    data = profile_wizard[uid]; step = data["step"]; value = (m.text or "").strip()

    if step == "weight":
        if not value.isdigit() or not (30 <= int(value) <= 300):
            bot.send_message(m.chat.id, tr(lang,"Введи число 30–300.","Введи число 30–300.","Enter 30–300.")); return
        data["tmp"]["weight"] = int(value); data["step"]="height"
        bot.send_message(m.chat.id, tr(lang,"📏 Тепер зріст (см), напр.: 180","📏 Теперь рост (см), напр.: 180","📏 Now height (cm), e.g. 180")); return

    if step == "height":
        if not value.isdigit() or not (120 <= int(value) <= 250):
            bot.send_message(m.chat.id, tr(lang,"Введи число 120–250.","Введи число 120–250.","Enter 120–250.")); return
        data["tmp"]["height"] = int(value); data["step"]="goal"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if lang=="ru": kb.add("Похудеть","Набрать массу"); kb.add("Поддерживать форму")
        elif lang=="en": kb.add("Lose weight","Gain muscle"); kb.add("Maintain")
        else: kb.add("Схуднути","Набрати масу"); kb.add("Підтримувати форму")
        bot.send_message(m.chat.id, tr(lang,"🎯 Обери ціль:","🎯 Выбери цель:","🎯 Choose your goal:"), reply_markup=kb); return

    if step == "goal":
        maps = {
            "ua":{"схуднути":"lose","набрати масу":"gain","підтримувати форму":"maintain"},
            "ru":{"похудеть":"lose","набрать массу":"gain","поддерживать форму":"maintain"},
            "en":{"lose weight":"lose","gain muscle":"gain","maintain":"maintain"},
        }
        goal = maps.get(lang, maps["ua"]).get(value.lower())
        if not goal:
            bot.send_message(m.chat.id, tr(lang,"Обери з кнопок.","Выбери из кнопок.","Choose from buttons.")); return
        prof = put_prof(uid, **data["tmp"], goal=goal, coins=user_profiles.get(uid,{}).get("coins",0))
        profile_wizard.pop(uid, None)
        bot.send_message(m.chat.id, tr(lang,"✅ Профіль збережено.","✅ Профиль сохранён.","✅ Profile saved."), reply_markup=types.ReplyKeyboardRemove())
        show_main(m.chat.id, uid)

# =========================
# Plan for today
# =========================
@bot.message_handler(func=lambda m: m.text in ["🔥 План на сьогодні","🔥 План на сегодня","🔥 Today's Plan","🔥 Мій план","🔥 Мой план","🔥 My Plan"])
def plan_today(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    prof = user_profiles.get(uid, {})
    weight = int(prof.get("weight", 70))
    goal = prof.get("goal","maintain")

    if goal == "lose":
        workout = ["1) Берпі — 3×12 (60с)","2) Присідання — 4×15 (45с)","3) Планка — 3×45с (30с)","4) Випади — 3×12/нога","5) Кардіо — 10 хв"]
        kcal = max(500, 6*weight)
        meals = ["Сніданок: йогурт + ягоди","Обід: курка + овочі","Вечеря: риба + салат","Перекус: яблуко"]
    elif goal == "gain":
        workout = ["1) Віджимання — 5×12 (90с)","2) Присідання — 5×12 (90с)","3) Тяга — 4×12 (90с)","4) Жим — 4×10 (90с)","5) Прес — 3×15"]
        kcal = max(2600, 30*weight)
        meals = ["Сніданок: вівсянка + банан + паста","Обід: рис + м'ясо + овочі","Перекус: творог + горіхи","Вечеря: паста/картопля + білок"]
    else:
        workout = ["1) Легка пробіжка — 20 хв","2) Віджимання — 3×12","3) Присідання — 3×15","4) Планка — 3×40с","5) Розтяжка — 10 хв"]
        kcal = max(2000, 22*weight)
        meals = ["Сніданок: омлет + овочі","Обід: гречка + індичка","Перекус: фрукти/горіхи","Вечеря: риба/овочі/салат"]

    water = f"Вода: {round(weight*0.03,1)} л/день"
    text = tr(
        lang,
        "🗓 <b>План на сьогодні</b>\n\n<b>Тренування</b>:\n"+'\n'.join(workout)+
        "\n\n<b>Харчування</b>:\n- " + '\n- '.join(meals) + f"\n\n<b>Калорії</b>: ~{kcal} ккал\n{water}\nДобавки: вітамін D, омега-3, електроліти.",
        "🗓 <b>План на сегодня</b>\n\n<b>Тренировка</b>:\n"+'\n'.join(workout)+
        "\n\n<b>Питание</b>:\n- " + '\n- '.join(meals) + f"\n\n<b>Калории</b>: ~{kcal} ккал\n"+water+"\nДобавки: витамин D, омега-3, электролиты.",
        "🗓 <b>Plan for today</b>\n\n<b>Workout</b>:\n"+'\n'.join(workout)+
        "\n\n<b>Nutrition</b>:\n- " + '\n- '.join(meals) + f"\n\n<b>Calories</b>: ~{kcal} kcal\n"+water+"\nSupplements: vitamin D, omega-3, electrolytes."
    )
    bot.send_message(m.chat.id, text)

# =========================
# Motivation & Coaches
# =========================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["🧠 мотивація","💖 натхнення","🧠 мотивация","💖 вдохновение","🧠 motivation","💖 inspiration"])
def on_motivation(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    phrases = motivations.get(lang, [])
    bot.send_message(m.chat.id, random.choice(phrases) if phrases else tr(lang,"…","…","…"))

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["🎓 поради від тренерів","🎓 советы от тренеров","🎓 pro trainer tips"])
def on_coach(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    tips = coaches_data.get(lang, [])
    if not tips:
        bot.send_message(m.chat.id, tr(lang,"❌ Немає порад.","❌ Нет советов.","❌ No tips.")); return
    coach = random.choice(tips)
    name = coach.get("name","—"); bio = coach.get(f"bio_{lang}", coach.get("bio","")); tip = coach.get(f"tip_{lang}", coach.get("tip",""))
    bot.send_message(m.chat.id, f"👤 <b>{name}</b>\n\n🧬 <i>{bio}</i>\n\n{tip}")

# =========================
# Books with chapters + bookmarks
# =========================
def find_book(title):
    for b in books_data:
        if b["title"] == title:
            return b
    return None

@bot.message_handler(func=lambda m: m.text in ["📚 Книги SHARKAN","📚 SHARKAN Books"])
def books_menu(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for b in books_data:
        kb.add(f"📖 {b['title']}")
    kb.add("⬅️ Головне меню","⬅️ Главное меню","⬅️ Main menu")
    bot.send_message(m.chat.id, tr(get_lang(str(m.from_user.id)),"📚 Обери книгу:","📚 Выбери книгу:","📚 Choose a book:"), reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text.startswith("📖 "))
def choose_book(m):
    uid = str(m.from_user.id)
    title = m.text.replace("📖 ","",1).strip()
    book = find_book(title)
    if not book:
        bot.send_message(m.chat.id, tr(get_lang(uid),"❌ Книгу не знайдено.","❌ Книга не найдена.","❌ Book not found.")); return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for ch in book.get("chapters", []):
        kb.add(f"📘 {title} | {ch['title']}")
    kb.add("🔖 Продовжити з закладки","⬅️ Головне меню")
    put_prof(uid, last_book=title)
    bot.send_message(m.chat.id, f"📚 <b>{title}</b>\n{tr(get_lang(uid),'Обери главу або продовж з закладки.','Выбери главу или продолжи с закладки.','Choose a chapter or continue from bookmark.')} ", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text.startswith("📘 "))
def open_chapter(m):
    uid = str(m.from_user.id)
    payload = m.text.replace("📘 ","",1)
    if " | " not in payload: return
    title, ch_title = payload.split(" | ",1)
    book = find_book(title)
    if not book: 
        bot.send_message(m.chat.id, tr(get_lang(uid),"❌ Книгу не знайдено.","❌ Книга не найдена.","❌ Book not found.")); return
    ch_idx = next((i for i,c in enumerate(book["chapters"]) if c["title"]==ch_title), None)
    if ch_idx is None:
        bot.send_message(m.chat.id, tr(get_lang(uid),"❌ Главу не знайдено.","❌ Главу не найдено.","❌ Chapter not found.")); return
    bookmarks.setdefault(uid, {})[title] = {"chapter": ch_idx, "page": 0}
    safe_save(BOOKMARKS_FILE, bookmarks)
    show_current_page(m.chat.id, uid, title)

@bot.message_handler(func=lambda m: m.text in ["⬅️ Назад","➡️ Вперед","🔖 Продовжити з закладки"])
def nav_book(m):
    uid = str(m.from_user.id)
    last = user_profiles.get(uid, {}).get("last_book")
    if not last:
        if m.text == "🔖 Продовжити з закладки":
            bot.send_message(m.chat.id, tr(get_lang(uid),"❌ Немає закладок.","❌ Нет закладок.","❌ No bookmarks.")); 
        return
    if m.text == "🔖 Продовжити з закладки":
        show_current_page(m.chat.id, uid, last); return
    bm = bookmarks.get(uid, {}).get(last)
    if not bm: return
    book = find_book(last); chapter = book["chapters"][bm["chapter"]]; pages = chapter["pages"]
    if m.text == "➡️ Вперед": bm["page"] = min(len(pages)-1, bm["page"]+1)
    elif m.text == "⬅️ Назад": bm["page"] = max(0, bm["page"]-1)
    safe_save(BOOKMARKS_FILE, bookmarks)
    show_current_page(m.chat.id, uid, last)

def show_current_page(chat_id, uid, title):
    book = find_book(title); bm = bookmarks.get(uid, {}).get(title)
    if not book or not bm:
        bot.send_message(chat_id, tr(get_lang(uid),"❌ Немає даних для книги.","❌ Нет данных по книге.","❌ No data for this book.")); return
    ch = book["chapters"][bm["chapter"]]; pages = ch["pages"]; page = max(0, min(bm["page"], len(pages)-1))
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("⬅️ Назад","➡️ Вперед"); kb.add("⬅️ Головне меню")
    put_prof(uid, last_book=title)
    bot.send_message(chat_id, f"📖 <b>{title}</b>\n<i>{ch['title']}</i>\n\n📄 {page+1}/{len(pages)}\n\n{pages[page]}", reply_markup=kb)

# =========================
# RUN: timer + history + coins
# =========================
running_timers = {}  # uid -> RunTimer

def calc_calories(weight_kg, duration_min):
    MET = 9.8
    return round((MET * 3.5 * weight_kg / 200) * duration_min)

class RunTimer:
    def __init__(self, chat_id, uid, weight, lang):
        self.chat_id = chat_id; self.uid=uid; self.weight=weight; self.lang=lang
        self.start = datetime.now(); self.active=True; self.mid=None
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.active=False
        duration = max(1, round((datetime.now()-self.start).seconds/60))
        calories = calc_calories(self.weight, duration)
        run_history.setdefault(self.uid, []).append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "duration_min": duration,
            "calories": calories
        })
        safe_save(RUN_HISTORY_FILE, run_history)
        prof = user_profiles.setdefault(self.uid, {})
        coins = int(prof.get("coins",0)) + max(5, (duration//10)*5)
        prof["coins"] = coins; safe_save(USER_PROFILE_FILE, user_profiles)
        return duration, calories, coins

    def loop(self):
        while self.active:
            minutes = (datetime.now()-self.start).seconds//60
            txts = {
                "ua":f"🕒 Пройшло: {minutes} хв",
                "ru":f"🕒 Прошло: {minutes} мин",
                "en":f"🕒 Elapsed: {minutes} min"
            }
            try:
                if self.mid: bot.delete_message(self.chat_id, self.mid)
                msg = bot.send_message(self.chat_id, txts.get(self.lang, txts["ua"]))
                self.mid = msg.message_id
            except Exception: pass
            time.sleep(60)

def detect(text, variants): 
    t=(text or "").lower(); return any(v.lower() in t for v in variants)

@bot.message_handler(func=lambda m: m.text and detect(m.text, ["⏱ режим біг","⏱ режим бег","⏱ running mode"]))
def run_menu(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang=="ru":
        kb.add("🏁 Начать бег","⛔️ Завершить бег"); kb.add("📊 Мои результаты","⬅️ Главное меню")
        txt = "🏃‍♂️ Выбери действие для SHARKAN RUN:"
    elif lang=="en":
        kb.add("🏁 Start run","⛔️ Stop run"); kb.add("📊 My results","⬅️ Main menu")
        txt = "🏃‍♂️ Choose an action for SHARKAN RUN:"
    else:
        kb.add("🏁 Почати біг","⛔️ Завершити біг"); kb.add("📊 Мої результати","⬅️ Головне меню")
        txt = "🏃‍♂️ Обери дію для SHARKAN RUN:"
    send_clean(m.chat.id, uid, txt, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and (detect(m.text, ["🏁 Почати біг","🏁 Начать бег","🏁 Start run"]) or detect(m.text, ["почати біг","начать бег","start run"])))
def start_run(m):
    uid = str(m.from_user.id); chat_id = m.chat.id; lang = get_lang(uid)
    weight = int(user_profiles.get(uid, {}).get("weight", 70))
    if uid in running_timers:
        try: running_timers[uid].stop()
        except Exception: pass
    running_timers[uid] = RunTimer(chat_id, uid, weight, lang)
    send_clean(chat_id, uid, tr(lang,"🏃‍♂️ Біжи! Я фіксую час...\n⛔️ Натисни «Завершити біг».",
                                      "🏃‍♂️ Беги! Я фиксирую время...\n⛔️ Нажми «Завершить бег».",
                                      "🏃‍♂️ Run! I’m tracking your time...\n⛔️ Tap “Stop run”.")
               )

@bot.message_handler(func=lambda m: m.text and (detect(m.text, ["⛔️ Завершити біг","⛔️ Завершить бег","⛔️ Stop run"]) or detect(m.text, ["завершити біг","завершить бег","stop run"])))
def stop_run(m):
    uid = str(m.from_user.id); chat_id = m.chat.id; lang = get_lang(uid)
    if uid not in running_timers:
        bot.send_message(chat_id, tr(lang,"❌ Біг не активний.","❌ Бег не запущен.","❌ Run not active.")); return
    duration, calories, coins = running_timers[uid].stop(); del running_timers[uid]
    unit = {"ua":"хв","ru":"мин","en":"min"}[lang if lang in ["ua","ru","en"] else "ua"]
    bot.send_message(chat_id, tr(lang,
        f"✅ Завершено!\n⏱ {duration} {unit}\n🔥 {calories} ккал\n🪙 Монети: +{max(5,(duration//10)*5)} (всього {coins})",
        f"✅ Готово!\n⏱ {duration} {unit}\n🔥 {calories} ккал\n🪙 Монеты: +{max(5,(duration//10)*5)} (всего {coins})",
        f"✅ Done!\n⏱ {duration} {unit}\n🔥 {calories} kcal\n🪙 Coins: +{max(5,(duration//10)*5)} (total {coins})"
    ))

@bot.message_handler(func=lambda m: m.text and detect(m.text, ["результат","results"]))
def show_run_results(m):
    uid = str(m.from_user.id); lang=get_lang(uid)
    recs = run_history.get(uid, [])
    if not recs:
        bot.send_message(m.chat.id, tr(lang,"❌ Немає збережених пробіжок.","❌ Нет сохранённых пробежек.","❌ No saved runs.")); return
    unit = {"ua":"хв","ru":"мин","en":"min"}[lang if lang in ["ua","ru","en"] else "ua"]
    header = tr(lang,"📊 Останні пробіжки:","📊 Последние пробежки:","📊 Recent runs:")
    lines = [header] + [f"📅 {r['date']} — {r['duration_min']} {unit} — {r['calories']} ккал" for r in recs[-3:]]
    bot.send_message(m.chat.id, "\n".join(lines))

# =========================
# Stats
# =========================
def compute_streak(records):
    if not records: return 0
    dates = {datetime.strptime(r["date"], "%Y-%m-%d").date() for r in records}
    cur = datetime.now().date(); streak=0
    while cur in dates: streak+=1; cur = cur - timedelta(days=1)
    return streak

@bot.message_handler(func=lambda m: m.text in ["📈 Статистика","📈 Прогрес / Ранги","📈 Statistics","📈 Progress / Ranks"])
def stats(m):
    uid = str(m.from_user.id); lang=get_lang(uid); recs = run_history.get(uid, [])
    total_runs = len(recs); total_min=sum(r["duration_min"] for r in recs); total_kcal=sum(r["calories"] for r in recs); streak=compute_streak(recs)
    bot.send_message(m.chat.id, tr(lang,
        f"📈 <b>Статистика</b>\nПробіжок: {total_runs}\nХвилин: {total_min}\nКалорій: {total_kcal}\nСтрік: {streak} дн.",
        f"📈 <b>Статистика</b>\nПробежек: {total_runs}\nМинут: {total_min}\nКалорий: {total_kcal}\nСтик: {streak} дн.",
        f"📈 <b>Statistics</b>\nRuns: {total_runs}\nMinutes: {total_min}\nCalories: {total_kcal}\nStreak: {streak} days"
    ), parse_mode="HTML")

# =========================
# Coins
# =========================
@bot.message_handler(func=lambda m: m.text in ["🪙 SHRK COINS","💎 SHRK COINS"])
def coins(m):
    uid = str(m.from_user.id); lang=get_lang(uid); coins = int(user_profiles.get(uid,{}).get("coins",0))
    bot.send_message(m.chat.id, tr(lang, f"🪙 Баланс: <b>{coins}</b>", f"🪙 Баланс: <b>{coins}</b>", f"🪙 Balance: <b>{coins}</b>"), parse_mode="HTML")

# =========================
# Settings
# =========================
@bot.message_handler(func=lambda m: m.text in ["⚙️ Налаштування","⚙️ Настройки","⚙️ Settings"])
def settings_menu(m):
    uid = str(m.from_user.id); lang=get_lang(uid)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang=="ru":
        kb.add("🌐 Сменить язык","🧹 Сбросить профиль"); kb.add("⬅️ Главное меню")
        title="⚙️ Настройки"
    elif lang=="en":
        kb.add("🌐 Change language","🧹 Reset profile"); kb.add("⬅️ Main menu")
        title="⚙️ Settings"
    else:
        kb.add("🌐 Змінити мову","🧹 Скинути профіль"); kb.add("⬅️ Головне меню")
        title="⚙️ Налаштування"
    bot.send_message(m.chat.id, title, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["🌐 Сменить язык","🌐 Change language","🌐 Змінити мову"])
def change_lang(m):
    kb = types.InlineKeyboardMarkup()
    for code, name in LANGUAGES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"lang_{code}"))
    bot.send_message(m.chat.id, "🌐 Обери мову / Choose language / Выберите язык:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["🧹 Сбросить профиль","🧹 Reset profile","🧹 Скинути профіль"])
def reset_profile(m):
    uid = str(m.from_user.id); lang=get_lang(uid)
    user_profiles[uid] = {"language": lang, "coins": 0}
    safe_save(USER_PROFILE_FILE, user_profiles)
    bot.send_message(m.chat.id, tr(lang,"✅ Профіль скинуто.","✅ Профиль сброшен.","✅ Profile reset."))
    show_main(m.chat.id, uid)

# =========================
# Shadow Fight — rounds with rest & optional "audio" alerts
# =========================
round_sessions = {}  # uid -> state

@bot.message_handler(func=lambda m: m.text in ["🥷 Бій з Тінню","🥷 Бой с Тенью","🥷 Shadow Fight"])
def shadow_menu(m):
    uid = str(m.from_user.id); lang=get_lang(uid)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang=="ru":
        kb.add("3×1 мин","4×2 мин","5×3 мин"); kb.add("Своя сессия","Перерыв: 60с","🔔 Звуковые сигналы: вкл/выкл"); kb.add("⬅️ Главное меню")
        title="🥷 Выбери формат:"
    elif lang=="en":
        kb.add("3×1 min","4×2 min","5×3 min"); kb.add("Custom","Rest: 60s","🔔 Audio cues: on/off"); kb.add("⬅️ Main menu")
        title="🥷 Choose format:"
    else:
        kb.add("3×1 хв","4×2 хв","5×3 хв"); kb.add("Своя сесія","Перерва: 60с","🔔 Звукові сигнали: вкл/викл"); kb.add("⬅️ Головне меню")
        title="🥷 Обери формат:"
    put_prof(uid, shadow_rest=60, shadow_audio=True)
    bot.send_message(m.chat.id, title, reply_markup=kb)

def parse_rounds(text):
    import re
    m = re.search(r"(\d+)\s*[×x]\s*(\d+)", text)
    if not m: return None
    return int(m.group(1)), int(m.group(2))

@bot.message_handler(func=lambda m: m.text and ("×" in m.text or "x" in m.text or m.text in ["Своя сесія","Custom","Перерыв: 60с","Rest: 60s","Перерва: 60с","🔔 Звуковые сигналы: вкл/выкл","🔔 Audio cues: on/off","🔔 Звукові сигнали: вкл/викл"]))
def shadow_handle(m):
    uid = str(m.from_user.id); lang = get_lang(uid); chat_id = m.chat.id
    text = m.text

    # Toggle audio cues
    if "🔔" in text and ("вкл" in text or "on" in text or "викл" in text or "off" in text):
        audio = not bool(user_profiles.get(uid, {}).get("shadow_audio", True))
        put_prof(uid, shadow_audio=audio)
        bot.send_message(chat_id, tr(lang, f"🔔 Звукові сигнали: {'увімкнено' if audio else 'вимкнено'}",
                                      f"🔔 Звуковые сигналы: {'включены' if audio else 'выключены'}",
                                      f"🔔 Audio cues: {'enabled' if audio else 'disabled'}"))
        return

    # Set rest to 60s quickly
    if "60с" in text or "60s" in text:
        put_prof(uid, shadow_rest=60)
        bot.send_message(chat_id, tr(lang,"🧊 Перерва 60с встановлена.","🧊 Перерыв 60с установлен.","🧊 Rest 60s set.")); 
        return

    # Custom format request
    if text in ["Своя сесія","Custom"]:
        round_sessions[uid] = {"await":"format"}
        bot.send_message(chat_id, tr(lang,"Введи формат як 6x2 (6 раундів по 2 хв).","Введи формат как 6x2 (6 раундов по 2 мин).","Enter like 6x2 (6 rounds × 2 min)."))
        return

    # Try parse NxM
    fmt = parse_rounds(text)
    if not fmt:
        if round_sessions.get(uid,{}).get("await")=="format":
            fmt = parse_rounds(text)
            if not fmt:
                bot.send_message(chat_id, tr(lang,"Не розпізнав формат.","Не распознал формат.","Couldn’t parse format.")); 
                return
        else:
            return

    rounds, minutes = fmt
    round_sessions.pop(uid, None)
    rest = int(user_profiles.get(uid, {}).get("shadow_rest", 60))
    audio = bool(user_profiles.get(uid, {}).get("shadow_audio", True))
    threading.Thread(target=shadow_timer, args=(chat_id, uid, rounds, minutes, rest, audio, lang), daemon=True).start()

def shadow_timer(chat_id, uid, rounds, minutes, rest, audio, lang):
    bot.send_message(chat_id, tr(lang, f"🥷 Старт: {rounds}×{minutes} хв (перерва {rest}с)",
                                      f"🥷 Старт: {rounds}×{minutes} мин (перерыв {rest}с)",
                                      f"🥷 Start: {rounds}×{minutes} min (rest {rest}s)"))
    for r in range(1, rounds+1):
        bot.send_message(chat_id, tr(lang, f"🔔 Раунд {r} — {minutes} хв!","🔔 Раунд {r} — {minutes} мин!","🔔 Round {r} — {minutes} min!"))
        # per-minute tick (не спамим каждую секунду)
        for m in range(minutes, 0, -1):
            time.sleep(60)
            if m>1:
                bot.send_message(chat_id, tr(lang, f"⏳ Залишилось {m-1} хв", f"⏳ Осталось {m-1} мин", f"⏳ {m-1} min left"))
        bot.send_message(chat_id, tr(lang, "⛔️ Стоп раунд!","⛔️ Стоп раунд!","⛔️ Round over!"))
        if r < rounds:
            if audio: bot.send_message(chat_id, "🔊 🔔 🔔 🔔")
            bot.send_message(chat_id, tr(lang, f"🧊 Перерва {rest}с.","🧊 Перерыв {rest}с.","🧊 Rest "+str(rest)+"s"))
            time.sleep(rest)
    bot.send_message(chat_id, tr(lang,"✅ Сесію завершено.","✅ Сессия завершена.","✅ Session complete."))

# =========================
# Music — personal playlists
# =========================
MUSIC_CATEGORIES = {
    "ua": ["Американський олдскул","Французький реп","Німецький реп","Техно"],
    "ru": ["Американский олдскул","Французский рэп","Немецкий рэп","Техно"],
    "en": ["US Old-school","French Rap","German Rap","Techno"]
}

@bot.message_handler(func=lambda m: m.text in ["🎵 Музика","🎵 Музыка","🎵 Music"])
def music_menu(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for c in MUSIC_CATEGORIES[lang]:
        kb.add(f"➕ Додати трек — {c}" if lang=="ua" else f"➕ Добавить трек — {c}" if lang=="ru" else f"➕ Add track — {c}")
        kb.add(f"▶️ Відтворити — {c}" if lang=="ua" else f"▶️ Воспроизвести — {c}" if lang=="ru" else f"▶️ Play — {c}")
    kb.add("⬅️ Головне меню" if lang=="ua" else "⬅️ Главное меню" if lang=="ru" else "⬅️ Main menu")
    bot.send_message(m.chat.id, tr(lang, "🎵 Кинь MP3 в чат — я запомню по категории.", "🎵 Кинь MP3 в чат — я запомню по категории.", "🎵 Send an MP3 — I’ll remember it per category."), reply_markup=kb)

def parse_music_cmd(text):
    # returns (action, category) or None
    for lang, cats in MUSIC_CATEGORIES.items():
        for c in cats:
            if text.endswith(f"— {c}") or text.endswith(f"- {c}"):  # em dash/ hyphen
                if text.startswith("➕") or text.lower().startswith(("➕","add","добавить","додати")):
                    return ("add", c)
                if text.startswith("▶️") or text.lower().startswith(("▶️","play","воспроизвести","відтворити")):
                    return ("play", c)
    return None

@bot.message_handler(content_types=["audio"])
def on_audio(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    # If user recently pressed "add" for some category, remember last choice:
    last_cat = user_profiles.get(uid, {}).get("music_last_cat")
    if not last_cat:
        bot.reply_to(m, tr(lang,"Спочатку вибери категорію через кнопку «➕ Додати трек — …».",
                                "Сначала выбери категорию кнопкой «➕ Добавить трек — …».",
                                "First choose a category via “➕ Add track — …”."))
        return
    file_id = m.audio.file_id
    music_lib.setdefault(uid, {}).setdefault(last_cat, [])
    if file_id not in music_lib[uid][last_cat]:
        music_lib[uid][last_cat].append(file_id)
        safe_save(MUSIC_FILE, music_lib)
    bot.reply_to(m, tr(lang, f"🎵 Збережено у категорії: {last_cat}", f"🎵 Сохранено в категории: {last_cat}", f"🎵 Saved to: {last_cat}"))

@bot.message_handler(func=lambda m: m.text and ("➕" in m.text or "▶️" in m.text))
def music_actions(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    parsed = parse_music_cmd(m.text)
    if not parsed: return
    action, category = parsed
    if action == "add":
        put_prof(uid, music_last_cat=category)
        bot.send_message(m.chat.id, tr(lang, f"Кинь MP3 — додам у «{category}».", f"Кинь MP3 — добавлю в «{category}».", f"Send an MP3 — I’ll add it to “{category}”.")); 
    else:
        tracks = music_lib.get(uid, {}).get(category, [])
        if not tracks:
            bot.send_message(m.chat.id, tr(lang,"❌ Немає треків у цій категорії.","❌ Нет треков в этой категории.","❌ No tracks in this category.")); 
            return
        file_id = random.choice(tracks)
        bot.send_audio(m.chat.id, file_id, caption=tr(lang, f"▶️ «{category}»", f"▶️ «{category}»", f"▶️ “{category}”"))

# =========================
# AI SHARKAN — simple mode
# =========================
ai_active = set()

@bot.message_handler(func=lambda m: m.text == "🤖 AI SHARKAN")
def ai_enter(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    ai_active.add(uid)
    bot.send_message(m.chat.id, tr(lang,
        "Я в режимі AI. Пиши питання (харчування/вода/тренування). Вийти — /ai_exit",
        "Я в режиме AI. Пиши вопросы (питание/вода/тренировки). Выйти — /ai_exit",
        "AI mode on. Ask about nutrition/water/training. Exit — /ai_exit"
    ))

@bot.message_handler(commands=["ai_exit"])
def ai_exit(m):
    uid = str(m.from_user.id); lang = get_lang(uid)
    ai_active.discard(uid)
    bot.send_message(m.chat.id, tr(lang,"Вийшов з AI-режиму.","Вышел из AI-режима.","Left AI mode."))

@bot.message_handler(func=lambda m: str(m.from_user.id) in ai_active)
def ai_answer(m):
    uid = str(m.from_user.id); lang = get_lang(uid); text = (m.text or "").lower()

    if any(w in text for w in ["вода","water"]):
        bot.send_message(m.chat.id, tr(lang,"Пий ~30 мл/кг ваги протягом дня.","Пей ~30 мл/кг веса в течение дня.","Drink ~30 ml/kg of body weight per day.")); return
    if any(w in text for w in ["білок","протеїн","protein","белок"]):
        bot.send_message(m.chat.id, tr(lang,"Білок: 1.6–2.2 г/кг ваги.","Белок: 1.6–2.2 г/кг массы.","Protein: 1.6–2.2 g/kg body weight.")); return
    if any(w in text for w in ["кардіо","кардио","cardio","біг","бег","run"]):
        bot.send_message(m.chat.id, tr(lang,"Кардіо 2–4×/тиждень по 20–40 хв помірно.","Кардио 2–4×/нед по 20–40 мин умеренно.","Cardio 2–4×/week for 20–40 min, moderate.")); return
    if any(w in text for w in ["вес","вага","weight","калор","calor"]):
        prof = user_profiles.get(uid, {})
        bot.send_message(m.chat.id, tr(lang,
            f"Твоя вага/ціль: {prof.get('weight','?')} кг / {prof.get('goal','?')}. План можна згенерувати через «🔥 План на сьогодні».",
            f"Твой вес/цель: {prof.get('weight','?')} кг / {prof.get('goal','?')}. План можно сгенерировать через «🔥 План на сегодня».",
            f"Your weight/goal: {prof.get('weight','?')} kg / {prof.get('goal','?')}. Generate a plan via “🔥 Today’s Plan”."
        )); return
    # default tip
    bot.send_message(m.chat.id, tr(lang,
        "Здай питання конкретніше: вода/харчування/кардіо/силове.",
        "Сформулируй конкретнее: вода/питание/кардио/силовая.",
        "Ask more specifically: water/nutrition/cardio/strength."
    ))

# =========================
# Entry points for training/motivation placeholders
# =========================
@bot.message_handler(func=lambda m: m.text in ["🏋️ Тренування","🏋️ Тренировка","🏋️ Workout"])
def workout_placeholder(m):
    lang = get_lang(str(m.from_user.id))
    bot.send_message(m.chat.id, tr(lang,"Розділ у підготовці — скажи, які тренування додати першими.",
                                       "Раздел в подготовке — скажи, какие тренировки добавить первыми.",
                                       "Coming soon — tell me which workouts to add first."))

# =========================
# Start bot
# =========================
print(f"{VERSION} started.")
bot.infinity_polling(skip_pending=True)
