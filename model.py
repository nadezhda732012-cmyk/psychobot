import random
from database import save_message, get_history
from config import CRISIS_CONTACTS, MAX_HISTORY_LENGTH
from gigachat_model import get_gigachat_response


def check_crisis(text: str) -> bool:
    """Проверка на кризисные ключевые слова"""
    crisis_words = ['суицид', 'убить себя', 'не хочу жить', 'покончить с собой', 
                    'смерть', 'расстаться с жизнью', 'навсегда уснуть', 
                    'хочу умереть', 'жизнь не имеет смысла']
    return any(word in text.lower() for word in crisis_words)


async def get_response(user_id: int, user_message: str) -> str:
    """Главная функция получения ответа"""
    
    # 1. Проверка на кризис
    if check_crisis(user_message):
        save_message(user_id, 'user', user_message)
        crisis_response = f"""
Я слышу, что тебе очень тяжело. Пожалуйста, помни, что ты не один(а).
Твои чувства важны, и есть люди, которые готовы помочь прямо сейчас.

{CRISIS_CONTACTS}

Поговори с ними, это может быть первым шагом к облегчению.
Хочешь, мы можем продолжить разговор, но помни: я не заменяю профессиональную помощь.
"""
        save_message(user_id, 'assistant', crisis_response)
        return crisis_response
    
    # 2. Сохраняем сообщение пользователя
    save_message(user_id, 'user', user_message)
    
    # 3. Получаем историю диалога
    history = get_history(user_id, MAX_HISTORY_LENGTH)
    
    # 4. Получаем ответ от GigaChat
    try:
        bot_response = await get_gigachat_response(user_message, history)
    except Exception as e:
        logger.error(f"Ошибка при получении ответа от GigaChat: {e}")
        bot_response = "Извините, я временно не могу ответить. Попробуйте позже."
    
    # 5. Сохраняем ответ бота
    save_message(user_id, 'assistant', bot_response)
    
    return bot_response
