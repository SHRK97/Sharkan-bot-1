import telebot
from telebot import types
from datetime import datetime, timedelta
import json
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

user_profiles = {}
if os.path.exists("user_profiles.json"):
    with open("user_profiles.json", "r") as f:
        user_profiles = json.load(f)

def save_profiles():
    with open("user_profiles.json", "w") as f:
        json.dump(user_profiles, f, indent=4, ensure_ascii=False)

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.chat.id)
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "start_time": datetime.now().isoformat(),
            "step": "gender"
        }
        save_profiles()
        bot.send_message(message.chat.id,
            "Це SHARKAN BOT — платформа для дисципліни, сили і викликів.\n\n"
            "Перші 3 дні безкоштовно. Потім — підписка.\n"
            "Ти отримаєш:\n"
            "• Персональні плани\n"
            "• Shadow Mode\n"
            "• Темну Зону\n"
            "• AI-наставника\n"
            "• Мотивацію, музику, книги\n\n"
            "Натисни 'Продовжити', щоб розпочати.")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Продовжити"))
        bot.send_message(message.chat.id, "Готовий почати?", reply_markup=markup)
    else:
        check_access_and_continue(message)

@bot.message_handler(func=lambda msg: True)
def message_handler(message):
    user_id = str(message.chat.id)
    text = message.text

    if user_id not in user_profiles:
        start_command(message)
        return

    profile = user_profiles[user_id]

    if text == "Продовжити" and profile.get("step") == "gender":
        bot.send_message(message.chat.id, "Оберіть вашу стать:", reply_markup=gender_buttons())
        return

    if profile.get("step") == "gender":
        if text in ["Чоловік", "Жінка", "Інше"]:
            profile["gender"] = text
            profile["step"] = "goal"
            save_profiles()
            bot.send_message(message.chat.id, "Яка твоя мета?", reply_markup=goal_buttons())
        return

    if profile.get("step") == "goal":
        profile["goal"] = text
        profile["step"] = "level"
        save_profiles()
        bot.send_message(message.chat.id, "Який твій рівень?", reply_markup=level_buttons())
        return

    if profile.get("step") == "level":
        profile["level"] = text
        profile["step"] = "complete"
        save_profiles()
        bot.send_message(message.chat.id, "Профіль збережено. Вітаємо в SHARKAN BOT!")
        show_main_menu(message)
        return

    check_access_and_continue(message)

def check_access_and_continue(message):
    user_id = str(message.chat.id)
    profile = user_profiles.get(user_id, {})
    start_time = datetime.fromisoformat(profile.get("start_time", datetime.now().isoformat()))
    now = datetime.now()
    trial_duration = timedelta(days=3)

    if now - start_time > trial_duration:
        bot.send_message(message.chat.id,
                         "Пробний період завершено. Щоб продовжити користування:\nПідпишіться — €3.99/місяць.",
                         reply_markup=subscription_buttons())
    else:
        show_main_menu(message)

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["План на сьогодні", "Мотивація", "Тренування", "Челленджі",
               "SHARKAN AI", "Темна Зона", "Книги", "Музика", "Прогрес", "Харчування / Вода"]
    for btn in buttons:
        markup.add(types.KeyboardButton(btn))
    bot.send_message(message.chat.id, "Вибери розділ:", reply_markup=markup)

def gender_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Чоловік", "Жінка", "Інше")
    return markup

def goal_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Схуднути", "Набрати масу", "Пройти виклики", "Покращити дисципліну", "Все разом")
    return markup

def level_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Новачок", "Середній рівень", "Я SHARKAN")
    return markup

def subscription_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Оплатити", "FAQ", "Повернутися")
    return markup

# === Реакции на основное меню ===
@bot.message_handler(func=lambda m: m.text in [
    "План на сьогодні", "Мотивація", "Тренування", "Челленджі",
    "SHARKAN AI", "Темна Зона", "Книги", "Музика", "Прогрес", "Харчування / Вода"])
def handle_sections(message):
    responses = {
        "План на сьогодні": "Ось твій план:
- Ранок: кардіо 15 хв
- Обід: курка + рис
- Вечір: розтяжка та 2л води",
        "Мотивація": "Ти не став кращим — ти став дисциплінованішим.",
        "Тренування": "Оберіть тип:
- Силове
- На масу
- Shadow Mode (режим тиші)",
        "Челленджі": "Доступні виклики:
- 100 віджимань
- Холодний душ 5 днів
- Дисципліна сну",
        "SHARKAN AI": "Пиши питання про тренування, харчування або дисципліну — SHARKAN відповість.",
        "Темна Зона": "Цей розділ відкриється після завершення першого челенджу.",
        "Книги": "Список книг:
- 'Думай і багатій' — Наполеон Хілл
- '12 правил життя' — Джордан Пітерсон",
        "Музика": "Доступні стилі:
- Oldschool Rap
- Техно
- Французький / Мексиканський / Німецький реп",
        "Прогрес": "Прогрес буде доступний після перших виконаних завдань.",
        "Харчування / Вода": "Пий 2–3л води в день.
Харчування: білок, овочі, чисте меню без цукру."
    }
    bot.send_message(message.chat.id, responses[message.text])

bot.infinity_polling()
