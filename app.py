import asyncio
import logging
import os
import threading
from concurrent.futures import Future

from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, CRISIS_CONTACTS
from database import clear_history, init_db
from model import get_response


# -------------------------------------------------------------------
# Логирование
# -------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Основные настройки
# -------------------------------------------------------------------

app = Flask(__name__)

WEBHOOK_URL = (
    "https://psychobot-xl1y.onrender.com/webhook"
)


# -------------------------------------------------------------------
# Обработчики Telegram
# -------------------------------------------------------------------

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обрабатывает команду /start."""

    if not update.message:
        return

    user = update.effective_user

    first_name = (
        user.first_name
        if user and user.first_name
        else ""
    )

    greeting = (
        f"👋 Привет, {first_name}!"
        if first_name
        else "👋 Привет!"
    )

    await update.message.reply_text(
        f"{greeting}\n\n"
        "Я — ИИ-собеседник для саморефлексии "
        "и эмоциональной поддержки.\n\n"
        "Я могу помочь тебе:\n"
        "• выговориться;\n"
        "• структурировать мысли;\n"
        "• внимательнее посмотреть на ситуацию;\n"
        "• обдумать возможные следующие шаги.\n\n"
        "💬 Просто напиши, что сейчас происходит.\n"
        "🔄 /clear — очистить историю разговора\n"
        "☎️ /crisis — контакты экстренной помощи\n"
        "❓ /help — список команд\n\n"
        "Важно: я не являюсь психологом, "
        "психотерапевтом или врачом и не заменяю "
        "профессиональную или экстренную помощь."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обрабатывает команду /help."""

    if not update.message:
        return

    await update.message.reply_text(
        "📋 Доступные команды:\n\n"
        "/start — начать разговор\n"
        "/help — показать список команд\n"
        "/clear — очистить историю разговора\n"
        "/crisis — показать контакты помощи\n\n"
        "Чтобы начать разговор, просто отправь сообщение."
    )


async def clear(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Удаляет историю текущего пользователя."""

    if not update.message:
        return

    user = update.effective_user

    if not user:
        await update.message.reply_text(
            "Не удалось определить пользователя."
        )
        return

    try:
        clear_history(user.id)

        await update.message.reply_text(
            "🧹 История разговора очищена."
        )

    except Exception:
        logger.exception(
            "Ошибка при очистке истории пользователя %s",
            user.id,
        )

        await update.message.reply_text(
            "Не удалось очистить историю. "
            "Попробуй немного позже."
        )


async def crisis(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показывает контакты экстренной помощи."""

    if not update.message:
        return

    await update.message.reply_text(
        "☎️ Если существует непосредственная опасность "
        "для тебя или другого человека, обратись "
        "в местную экстренную службу или позови человека, "
        "который может физически находиться рядом.\n\n"
        f"{CRISIS_CONTACTS}\n\n"
        "Ты также можешь продолжить писать здесь, "
        "но бот не заменяет экстренную помощь."
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обрабатывает обычное текстовое сообщение."""

    if not update.message:
        return

    user = update.effective_user
    user_message = update.message.text

    if not user:
        await update.message.reply_text(
            "Не удалось определить пользователя."
        )
        return

    if not user_message:
        return

    user_message = user_message.strip()

    if not user_message:
        await update.message.reply_text(
            "Сообщение оказалось пустым. "
            "Попробуй написать ещё раз."
        )
        return

    try:
        await update.message.chat.send_action(
            action="typing"
        )

        response = await get_response(
            user_id=user.id,
            user_message=user_message,
        )

        await update.message.reply_text(response)

    except Exception:
        logger.exception(
            "Ошибка при обработке сообщения пользователя %s",
            user.id,
        )

        try:
            await update.message.reply_text(
                "Произошла ошибка при обработке сообщения. "
                "Попробуй отправить его ещё раз немного позже."
            )
        except Exception:
            logger.exception(
                "Не удалось отправить сообщение об ошибке"
            )


async def telegram_error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Записывает необработанные ошибки Telegram."""

    logger.error(
        "Необработанная ошибка Telegram",
        exc_info=context.error,
    )


# -------------------------------------------------------------------
# Создание Telegram Application
# -------------------------------------------------------------------

telegram_app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

telegram_app.add_handler(
    CommandHandler("start", start)
)

telegram_app.add_handler(
    CommandHandler("help", help_command)
)

telegram_app.add_handler(
    CommandHandler("clear", clear)
)

telegram_app.add_handler(
    CommandHandler("crisis", crisis)
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message,
    )
)

telegram_app.add_error_handler(
    telegram_error_handler
)


# -------------------------------------------------------------------
# Один постоянный event loop для Telegram
# -------------------------------------------------------------------

telegram_loop = asyncio.new_event_loop()

telegram_ready = threading.Event()


async def initialize_telegram() -> None:
    """
    Инициализирует Telegram-приложение
    внутри постоянного event loop.
    """

    await telegram_app.initialize()

    logger.info(
        "✅ Telegram-приложение инициализировано"
    )

    telegram_ready.set()


def run_telegram_loop() -> None:
    """
    Запускает постоянный event loop
    в отдельном потоке.
    """

    asyncio.set_event_loop(telegram_loop)

    telegram_loop.run_until_complete(
        initialize_telegram()
    )

    telegram_loop.run_forever()


telegram_thread = threading.Thread(
    target=run_telegram_loop,
    name="telegram-event-loop",
    daemon=True,
)

telegram_thread.start()


# Ждём инициализации не более 30 секунд.
if not telegram_ready.wait(timeout=30):
    raise RuntimeError(
        "Telegram-приложение не успело инициализироваться"
    )


def log_future_error(future: Future) -> None:
    """
    Записывает ошибку фоновой обработки webhook,
    если она возникла.
    """

    try:
        future.result()

    except Exception:
        logger.exception(
            "Ошибка фоновой обработки Telegram update"
        )


# -------------------------------------------------------------------
# Flask-маршруты
# -------------------------------------------------------------------

@app.route("/", methods=["GET", "HEAD"])
def home():
    """Проверка состояния сервиса."""

    return "🤖 Бот работает!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Получает update от Telegram и передаёт его
    в постоянный event loop.
    """

    try:
        json_data = request.get_json(
            force=True,
            silent=False,
        )

        if not json_data:
            logger.warning(
                "Webhook получил пустой запрос"
            )

            return "empty request", 400

        update = Update.de_json(
            json_data,
            telegram_app.bot,
        )

        future = asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            telegram_loop,
        )

        future.add_done_callback(
            log_future_error
        )

        # Telegram быстро получает подтверждение.
        # Обработка сообщения продолжается в фоне.
        return "ok", 200

    except Exception:
        logger.exception(
            "Ошибка при приёме Telegram webhook"
        )

        return "error", 500


@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    """Устанавливает webhook Telegram."""

    try:
        future = asyncio.run_coroutine_threadsafe(
            telegram_app.bot.set_webhook(
                url=WEBHOOK_URL,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            ),
            telegram_loop,
        )

        result = future.result(
            timeout=30
        )

        if result:
            logger.info(
                "✅ Webhook установлен: %s",
                WEBHOOK_URL,
            )

            return (
                f"✅ Вебхук установлен: {WEBHOOK_URL}",
                200,
            )

        logger.error(
            "Telegram не подтвердил установку webhook"
        )

        return (
            "❌ Telegram не подтвердил установку вебхука",
            500,
        )

    except Exception as error:
        logger.exception(
            "Ошибка при установке webhook"
        )

        return (
            f"❌ Ошибка при установке вебхука: {error}",
            500,
        )


# -------------------------------------------------------------------
# Запуск Flask
# -------------------------------------------------------------------

if __name__ == "__main__":
    init_db()

    logger.info(
        "✅ База данных инициализирована"
    )

    port = int(
        os.environ.get(
            "PORT",
            "10000",
        )
    )

    logger.info(
        "🚀 Запуск Flask на порту %s",
        port,
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
        use_reloader=False,
    )
