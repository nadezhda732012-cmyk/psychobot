import os
import logging
from gigachat import GigaChat
from gigachat.models import Chat, Message

logger = logging.getLogger(__name__)

GIGACHAT_KEY = os.environ.get("GIGACHAT_KEY", "")

async def get_gigachat_response(user_message: str, history: list = None) -> str:
    try:
        with GigaChat(
            credentials=GIGACHAT_KEY,
            scope="GIGACHAT_API_PERS",
            model="GigaChat:latest",
            profanity_check=False,
            verify_ssl_certs=False,
        ) as giga:
            # Создаем список сообщений
            messages = [
                Message(role="system", content="Ты — эмпатичный психолог. Отвечай на русском языке, тепло и с пониманием. Не давай диагностических заключений.")
            ]
            
            # Добавляем историю диалога
            if history:
                for msg in history[-10:]:
                    role = "user" if msg.role == "user" else "assistant"
                    messages.append(Message(role=role, content=msg.content))
            
            # Добавляем текущее сообщение
            messages.append(Message(role="user", content=user_message))
            
            # Создаем объект Chat и отправляем запрос
            chat = Chat(messages=messages)
            response = giga.chat(chat)
            
            # Извлекаем ответ
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                return "Извините, я не смог сформулировать ответ. Попробуйте переформулировать вопрос."
                
    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        return "Извините, я временно не могу ответить. Попробуйте позже."
