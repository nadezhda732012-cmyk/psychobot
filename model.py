import logging

from config import CRISIS_CONTACTS, MAX_HISTORY_LENGTH
from database import get_history, save_message
from gigachat_model import get_gigachat_response


logger = logging.getLogger(__name__)


def check_crisis(text: str) -> bool:
    """
    Временная проверка кризисных формулировок.

    Это еще не полноценный Safety Engine.
    Позже заменим ее структурированным анализом риска.
    """
    crisis_phrases = [
        "убить себя",
        "покончить с собой",
        "хочу умереть",
        "не хочу жить",
        "расстаться с жизнью",
        "причинить себе вред",
    ]

    normalized_text = text.lower().strip()

    return any(
        phrase in normalized_text
        for phrase in crisis_phrases
    )


async def get_response(user_id: int, user_message: str) -> str:
    """
    Получает историю, сохраняет сообщение пользователя,
    запрашивает ответ модели и сохраняет ответ.
    """

    if check_crisis(user_message):
        save_message(user_id, "user", user_message)

        crisis_response = (
            "Мне важно уточнить это прямо: "
            "ты сейчас находишься в непосредственной опасности "
            "или думаешь о том, чтобы причинить себе вред?\n\n"
            "Если опасность непосредственная, пожалуйста, "
            "свяжись с местной экстренной службой или человеком, "
            "который может физически находиться рядом с тобой.\n\n"
            f"{CRISIS_CONTACTS}"
        )

        save_message(
            user_id,
            "assistant",
            crisis_response,
        )

        return crisis_response

    # Получаем предыдущую историю ДО сохранения нового сообщения.
    # Благодаря этому новое сообщение не попадет в запрос дважды.
    history = get_history(
        user_id,
        MAX_HISTORY_LENGTH,
    )

    save_message(
        user_id,
        "user",
        user_message,
    )

    try:
        bot_response = await get_gigachat_response(
            user_message=user_message,
            history=history,
        )

    except Exception:
        logger.exception(
            "Ошибка при получении ответа для пользователя %s",
            user_id,
        )

        bot_response = (
            "Извини, сейчас я временно не могу ответить. "
            "Попробуй немного позже."
        )

    save_message(
        user_id,
        "assistant",
        bot_response,
    )

    return bot_response
