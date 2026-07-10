import os
import logging

from gigachat import GigaChat
from gigachat.models import Chat, Messages

logger = logging.getLogger(__name__)

GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")


async def get_gigachat_response(user_message: str, history=None):
    try:
        with GigaChat(
            credentials=GIGACHAT_KEY,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False,
            profanity_check=False,
        ) as giga:

            chat = Chat(messages=[])

            chat.messages.append(
                Messages(
                    role="system",
                    content="""
Ты — квалифицированный психолог-консультант с опытом работы в когнитивно-поведенческом подходе.

Отвечай кратко, по существу.
Максимум 3–5 предложений.
Не ставь диагнозы.
Предлагай один практический шаг.
"""
                )
            )

            if history:
                for msg in history[-10:]:
                    chat.messages.append(
                        Messages(
                            role=msg.role,
                            content=msg.content
                        )
                    )

            chat.messages.append(
                Messages(
                    role="user",
                    content=user_message
                )
            )

            response = giga.chat(chat)

            if response.choices:
                return response.choices[0].message.content.strip()

            return "Не удалось получить ответ."

    except Exception:
        logger.exception("Ошибка GigaChat")
        return "Извините, сейчас я не могу ответить."
