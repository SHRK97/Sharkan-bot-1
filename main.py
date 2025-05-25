import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

user_profiles = {}

# === Загрузка профилей ===
def load_profiles():
    global user_profiles
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as f:
            user_profiles = json.load(f)
    except FileNotFoundError:
        user_profiles = {}

# === Сохранение профилей ===
def save_profiles():
    with open("user_profiles.json", "w", encoding="utf-8") as f:
        json.dump(user_profiles, f, indent=4, ensure_ascii=False)

# === Главное меню ===
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "1. План на сьогодні",
        "2. Мотивація",
        "3. Тренування",
        "4. Челленджі",
        "5. Питання до SHARKAN AI",
        "6. Темна Зона",
        "7. Статистика і Прогрес",
        "8. Магазин",
        "9. Музика",
        "10. Поради від топ-тренерів",
        "11. SHARKAN Coins",
        "12. Допомога / FAQ",
        "13. Контакти / Співпраця"
    ]
    for btn in buttons:
        markup.add(types.KeyboardButton(btn))
    bot.send_message(chat_id, "Головне меню SHARKAN BOT. Обери розділ:", reply_markup=markup)

# === Команда /start ===
@bot.message_handler(commands=["start"])
def start_command(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Ласкаво просимо до SHARKAN BOT!")
    show_main_menu(user_id)

# === Обробка натискань ===
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.chat.id
    text = message.text.strip()

    responses = {
        "1. План на сьогодні": "AI готує для тебе персональний план на день...",
        "2. Мотивація": "Твоя сила починається з думки. Вибери: цитата, аудіо, відео чи картинка.",
        "3. Тренування": "Вибери ціль: схуднути, набрати, тримати форму.",
        "4. Челленджі": "Доступні нові виклики. Почни з 100 віджимань!",
        "5. Питання до SHARKAN AI": "Постав мені питання про харчування, тренування або добавки.",
        "6. Темна Зона": "Доступ буде відкрито після першого виклику.",
        "7. Статистика і Прогрес": "Твій прогрес буде тут. Скоро оновлення.",
        "8. Магазин": "Одяг SHARKAN незабаром у продажу.",
        "9. Музика": "Вибери стиль: Oldschool, Techno, Rap...",
        "10. Поради від топ-тренерів": "Тут будуть поради від найкращих тренерів світу.",
        "11. SHARKAN Coins": "Твій баланс: 0 SHRK. Заробляй через виклики.",
        "12. Допомога / FAQ": "Напиши /help щоб побачити інструкції.",
        "13. Контакти / Співпраця": "Для співпраці — @rulya7777 | sharkanmotivation@gmail.com"
    }

    response = responses.get(text, "Ця функція ще в розробці.")
    bot.send_message(user_id, response)

# === Старт ===
if __name__ == "__main__":
    load_profiles()
    bot.polling(none_stop=True)
