import os
import logging
import ssl
import certifi
from gigachat import GigaChat

logger = logging.getLogger(__name__)

GIGACHAT_KEY = os.environ.get("GIGACHAT_KEY", "")

# Устанавливаем путь к сертификатам для корректной работы SSL
os.environ["SSL_CERT_FILE"] = certifi.where()

async def get_gigachat_response(user_message: str, history: list = None) -> str:
    try:
        with GigaChat(
            credentials=GIGACHAT_KEY,
            scope="GIGACHAT_API_PERS",
            model="GigaChat:latest",
            profanity_check=False,
            verify_ssl_certs=False,  # Отключаем проверку SSL для обхода ошибки
        ) as giga:
            messages = [{"role": "system", "content": "Ты — эмпатичный психолог. Отвечай на русском языке, тепло и с пониманием."}]
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
