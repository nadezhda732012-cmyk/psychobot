import os
import logging
from gigachat import GigaChat

logger = logging.getLogger(__name__)

GIGACHAT_KEY = os.environ.get("GIGACHAT_KEY", "")

async def get_gigachat_response(user_message: str, history: list = None) -> str:
    """Отправляет запрос к GigaChat и возвращает ответ."""
    try:
        with GigaChat(
            credentials=GIGACHAT_KEY,
            scope="GIGACHAT_API_PERS",
            model="GigaChat:latest",
            profanity_check=False,
        ) as giga:
            messages = [{"role": "system", "content": "Ты — эмпатичный психолог."}]
            if history:
                for msg in history[-10:]:
                    role = "user" if msg.role == "user" else "assistant"
                    messages.append({"role": role, "content": msg.content})
            messages.append({"role": "user", "content": user_message})
            
            response = giga.chat(messages)
            return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        return "Извините, я временно не могу ответить. Попробуйте позже."
