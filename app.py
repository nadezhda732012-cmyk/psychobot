import os
import logging
import asyncio

from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, CRISIS_CONTACTS
from database import init_db, clear_history
from model import get_response


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# Flask-приложение
app = Flask(__name__)


# URL, на который Telegram будет отправлять сообщения
WEBHOOK_URL = (
    "https://psychobot-xl1y.onrender.com/webhook"
)


# -------------------------------------------------------------------
# Обработчики команд Telegram
# -------------------------------------------------------------------

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Обрабатывает команду /start.
    """

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
    """
    Обрабатывает команду /help.
    """

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
    """
    Удаляет историю сообщений текущего пользователя.
    """

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
    """
    Показывает контакты экстренной помощи.
    """

    await update.message.reply_text(
        "☎️ Если существует непосредственная опасность "
        "для тебя или другого человека, обратись "
        "в местную экстренную службу или позови человека, "
        "который может физически находиться рядом.\n\n"
        f"{CRISIS_CONTACTS}\n\n"
        "Ты также можешь продолжить писать здесь, "
        "но бот не заменяет экстренную помощь."
    )


# -------------------------------------------------------------------
# Обработка обычных текстовых сообщений
# -------------------------------------------------------------------

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Передает обычное текстовое сообщение в модель
    и отправляет пользователю ответ.
    """

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

        await update.message.reply_text(
            "Произошла ошибка при обработке сообщения. "
            "Попробуй отправить его ещё раз немного позже."
        )


# -------------------------------------------------------------------
# Создание Telegram-приложения
# -------------------------------------------------------------------

telegram_app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)


# Регистрация команд
telegram_app.add_handler(
    CommandHandler(
        "start",
        start,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "help",
        help_command,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "clear",
        clear,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "crisis",
        crisis,
    )
)


# Регистрация обычных текстовых сообщений
telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message,
    )
)


# -------------------------------------------------------------------
# Инициализация Telegram Application
# -------------------------------------------------------------------

initialization_loop = asyncio.new_event_loop()
asyncio.set_event_loop(initialization_loop)

initialization_loop.run_until_complete(
    telegram_app.initialize()
)

logger.info(
    "✅ Telegram-приложение инициализировано"
)


# -------------------------------------------------------------------
# Flask-маршруты
# -------------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    """
    Проверка работы сервиса.
    """

    return "🤖 Бот работает!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Получает обновления от Telegram.
    """

    try:
        json_data = request.get_json(
            force=True
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

        webhook_loop = asyncio.new_event_loop()

        try:
            asyncio.set_event_loop(webhook_loop)

            webhook_loop.run_until_complete(
                telegram_app.process_update(update)
            )

        finally:
            webhook_loop.close()

        return "ok", 200

    except Exception:
        logger.exception(
            "Ошибка при обработке Telegram webhook"
        )

        return "error", 500


@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    """
    Устанавливает Telegram webhook.
    Вызывается вручную после деплоя.
    """

    webhook_loop = asyncio.new_event_loop()

    try:
        asyncio.set_event_loop(webhook_loop)

        result = webhook_loop.run_until_complete(
            telegram_app.bot.set_webhook(
                url=WEBHOOK_URL,
            )
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

    finally:
        webhook_loop.close()


# -------------------------------------------------------------------
# Запуск приложения
# -------------------------------------------------------------------

if __name__ == "__main__":
    init_db()

    logger.info(
        "✅ База данных инициализирована"
    )

    port = int(
        os.environ.get(
            "PORT",
            10000,
        )
    )

    logger.info(
        "🚀 Запуск Flask на порту %s",
        port,
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )
