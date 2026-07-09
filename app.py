import os
import logging
import asyncio
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import BOT_TOKEN, CRISIS_CONTACTS
from database import init_db, clear_history
from model import get_response
from tests import start_test, get_next_question, save_answer, test_sessions

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём Flask-приложение
app = Flask(__name__)

# Глобальная переменная для Telegram-приложения
telegram_app = None

# --- Все обработчики команд (они такие же, как в bot.py) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — твой виртуальный помощник. Я здесь, чтобы выслушать и поддержать.\n\n"
        "💬 Просто напиши мне, что у тебя на душе.\n"
        "📝 /test — пройти тест на тревожность\n"
        "🔄 /clear — очистить историю\n"
        "❓ /help — список команд\n\n"
        "Помни: я не заменяю профессионального психолога."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Команды:\n"
        "/start — начать\n"
        "/help — помощь\n"
        "/test — тест на тревожность\n"
        "/clear — очистить историю\n"
        "/crisis — службы доверия\n\n"
        "Просто пиши свои мысли."
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    clear_history(user_id)
    await update.message.reply_text("🧹 История очищена.")

async def crisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"☎️ Если тебе нужна помощь:\n\n{CRISIS_CONTACTS}\n\n"
        "Обращение за помощью — это сила. ❤️"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    start_test(user_id)
    question = get_next_question(user_id)
    await update.message.reply_text(
        f"📝 Начинаем тест на тревожность.\n\n"
        f"Отвечай на каждый вопрос числом от 0 до 3:\n"
        f"0 — нет, 1 — иногда, 2 — часто, 3 — очень часто.\n\n"
        f"{question}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Проверяем, не проходит ли пользователь тест
    if user_id in test_sessions and test_sessions[user_id] is not None:
        session = test_sessions[user_id]
        if session["step"] < 7:
            save_answer(user_id, user_message)
            next_question = get_next_question(user_id)
            if next_question:
                await update.message.reply_text(next_question)
            return
        else:
            test_sessions[user_id] = None

    try:
        await update.message.chat.send_action(action="typing")
        response = await get_response(user_id, user_message)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуй ещё раз.")

def setup_telegram_app():
    """Настраивает Telegram-приложение"""
    global telegram_app
    
    logger.info("🔄 Инициализация Telegram-приложения...")
    init_db()
    logger.info("✅ База данных инициализирована")
    
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("clear", clear))
    telegram_app.add_handler(CommandHandler("crisis", crisis))
    telegram_app.add_handler(CommandHandler("test", test_command))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Обработчики зарегистрированы")
    return telegram_app

def run_bot_polling():
    """Запускает бота в режиме long polling в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app_bot = setup_telegram_app()
    logger.info("🚀 Запуск polling...")
    app_bot.run_polling(allowed_updates=Update.ALL_TYPES)

# --- Flask-маршруты (для поддержания жизни сервера) ---

@app.route('/')
def home():
    return "🤖 Бот-психолог работает!"

@app.route('/health')
def health():
    return "OK", 200

# --- Точка входа ---

if __name__ == "__main__":
    import sys
    
    # Запускаем бота в отдельном потоке (чтобы Flask тоже работал)
    bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask-сервер
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Запуск Flask на порту {port}...")
    app.run(host="0.0.0.0", port=port)