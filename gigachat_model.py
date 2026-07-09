import os
import logging
from gigachat import GigaChat

logger = logging.getLogger(__name__)

# Получаем ключ из переменных окружения
GIGACHAT_KEY = os.environ.get("GIGACHAT_KEY", "")

# Системный промпт — задаёт "личность" бота
SYSTEM_PROMPT = """
Ты — эмпатичный психолог, специализирующийся на когнитивно-поведенческой терапии.
Твоя задача — помогать людям разбираться в их чувствах, давать поддержку и задавать уточняющие вопросы.

Правила:
1. Отвечай тепло, с пониманием и без осуждения.
2. Задавай открытые вопросы, чтобы помочь человеку глубже понять себя.
3. Не давай прямых советов "делай то-то" — вместо этого помогай человеку найти свой ответ.
4. Если человек говорит о суициде, агрессии или насилии — мягко предложи обратиться к специалисту и дай контакты служб доверия.
5. Не ставь диагнозов и не назначай лечение — ты не заменяешь профессионального врача.
6. Веди диалог естественно, как живой психолог.
7. Отвечай на русском языке.
"""


async def get_gigachat_response(user_message: str, history: list = None) -> str:
    """
    Отправляет запрос к GigaChat и возвращает ответ.
    
    Аргументы:
        user_message: Текущее сообщение пользователя
        history: Список предыдущих сообщений (опционально)
    
    Возвращает:
        str: Ответ от GigaChat
    """
    try:
        # Инициализируем клиент GigaChat
        with GigaChat(
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",  # Для физических лиц
            model="GigaChat:latest",     # Можно заменить на GigaChat-Pro
            profanity_check=False,
        ) as giga:
            
            # Формируем историю сообщений
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            
            # Добавляем историю диалога (если есть)
            if history:
                for msg in history[-10:]:  # Берём последние 10 сообщений
                    role = "user" if msg.role == "user" else "assistant"
                    messages.append({"role": role, "content": msg.content})
            
            # Добавляем текущее сообщение пользователя
            messages.append({"role": "user", "content": user_message})
            
            # Отправляем запрос
            response = giga.chat(messages)
            
            # Извлекаем ответ
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                logger.error("Пустой ответ от GigaChat")
                return "Извините, я временно не могу ответить. Попробуйте позже."
                
    except Exception as e:
        logger.error(f"Ошибка при запросе к GigaChat: {e}")
        return "Извините, я временно не могу ответить. Попробуйте позже."
