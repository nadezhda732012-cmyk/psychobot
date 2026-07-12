import logging

from config import CRISIS_CONTACTS, MAX_HISTORY_LENGTH
from database import get_history, save_message
from gigachat_model import get_gigachat_response
from router import Route, RouterResult, classify_message


logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Простые ответы без обращения к GigaChat
# -------------------------------------------------------------------

def get_direct_response(
    router_result: RouterResult,
    has_history: bool,
) -> str | None:
    """
    Возвращает простой ответ для сообщений,
    которым не нужен запрос к языковой модели.

    Если требуется GigaChat, возвращает None.
    """

    route = router_result.route

    if route == Route.GREETING:
        return (
            "Привет. Рассказывай, что сейчас происходит, "
            "или просто задай вопрос."
        )

    if route == Route.GRATITUDE:
        return "Пожалуйста."

    if route == Route.GOODBYE:
        return "До встречи. Береги себя."

    if route == Route.ACKNOWLEDGEMENT and not has_history:
        return "Хорошо."

    return None


# -------------------------------------------------------------------
# Временный кризисный ответ
# -------------------------------------------------------------------

def build_crisis_response() -> str:
    """
    Формирует временный кризисный ответ.

    Позже эта логика будет заменена полноценным Safety Engine.
    """

    return (
        "Мне важно уточнить это прямо: "
        "ты сейчас находишься в непосредственной опасности "
        "или думаешь о том, чтобы причинить себе вред?\n\n"
        "Если опасность непосредственная, пожалуйста, "
        "свяжись с местной экстренной службой или позови человека, "
        "который может физически находиться рядом.\n\n"
        f"{CRISIS_CONTACTS}"
    )


# -------------------------------------------------------------------
# Главная функция
# -------------------------------------------------------------------

async def get_response(
    user_id: int,
    user_message: str,
) -> str:
    """
    Классифицирует сообщение через Router,
    получает ответ и сохраняет историю.
    """

    # Получаем историю ДО сохранения нового сообщения.
    # Это предотвращает двойную передачу текущего сообщения модели.
    history = get_history(
        user_id,
        MAX_HISTORY_LENGTH,
    )

    has_history = bool(history)

    router_result = classify_message(
        text=user_message,
        has_history=has_history,
    )

    logger.info(
        "Router: user_id=%s route=%s confidence=%.2f reason=%s",
        user_id,
        router_result.route.value,
        router_result.confidence,
        router_result.reason,
    )

    # Сохраняем исходное сообщение пользователя.
    save_message(
        user_id,
        "user",
        user_message,
    )

    # Кризисный маршрут имеет приоритет.
    if router_result.route == Route.CRISIS_SIGNAL:
        crisis_response = build_crisis_response()

        save_message(
            user_id,
            "assistant",
            crisis_response,
        )

        return crisis_response

    # Для простых сообщений модель не вызываем.
    direct_response = get_direct_response(
        router_result=router_result,
        has_history=has_history,
    )

    if direct_response is not None:
        save_message(
            user_id,
            "assistant",
            direct_response,
        )

        return direct_response

    # Если Router считает, что модель не требуется,
    # но готового ответа нет, используем нейтральную реакцию.
    if not router_result.needs_model:
        fallback_response = "Хорошо."

        save_message(
            user_id,
            "assistant",
            fallback_response,
        )

        return fallback_response

    # Передаём модели только ту историю,
    # которая нужна выбранному маршруту.
    selected_history = (
        history
        if router_result.needs_history
        else None
    )

    try:
        bot_response = await get_gigachat_response(
            user_message=user_message,
            history=selected_history,
            route=router_result.route,
        )

    except Exception:
        logger.exception(
            "Ошибка при получении ответа: user_id=%s route=%s",
            user_id,
            router_result.route.value,
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
