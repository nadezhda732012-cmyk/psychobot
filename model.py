import logging

from config import CRISIS_CONTACTS, MAX_HISTORY_LENGTH
from database import get_history, save_message
from gigachat_model import (
    get_gigachat_response,
    rewrite_gigachat_response,
)
from response_critic import evaluate_response
from response_policy import get_response_policy
from router import (
    Route,
    RouterResult,
    classify_message,
)


logger = logging.getLogger(__name__)


def get_direct_response(
    router_result: RouterResult,
    has_history: bool,
) -> str | None:
    """
    Возвращает простой ответ для сообщений,
    которым не нужен запрос к языковой модели.
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

    if (
        route == Route.ACKNOWLEDGEMENT
        and not has_history
    ):
        return "Хорошо."

    return None


def build_crisis_response() -> str:
    """
    Временный кризисный ответ.

    Позже будет заменён полноценным Safety Engine.
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


async def get_response(
    user_id: int,
    user_message: str,
) -> str:
    """
    Обрабатывает сообщение по цепочке:

    Router
    → Response Policy
    → GigaChat Draft
    → Response Critic
    → при необходимости одно переписывание
    → сохранение ответа.
    """

    # Историю получаем до сохранения нового сообщения,
    # чтобы сообщение не передавалось модели дважды.
    history = get_history(
        user_id,
        MAX_HISTORY_LENGTH,
    )

    has_history = bool(history)

    # ---------------------------------------------------------------
    # Router
    # ---------------------------------------------------------------

    router_result = classify_message(
        text=user_message,
        has_history=has_history,
    )

    response_policy = get_response_policy(
        router_result.route
    )

    logger.info(
        (
            "Router: user_id=%s route=%s confidence=%.2f "
            "policy=%s reason=%s"
        ),
        user_id,
        router_result.route.value,
        router_result.confidence,
        response_policy.mode,
        router_result.reason,
    )

    # Сохраняем сообщение пользователя.
    save_message(
        user_id,
        "user",
        user_message,
    )

    # ---------------------------------------------------------------
    # Временный кризисный маршрут
    # ---------------------------------------------------------------

    if router_result.route == Route.CRISIS_SIGNAL:
        crisis_response = build_crisis_response()

        save_message(
            user_id,
            "assistant",
            crisis_response,
        )

        return crisis_response

    # ---------------------------------------------------------------
    # Простые ответы без GigaChat
    # ---------------------------------------------------------------

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

    if not router_result.needs_model:
        fallback_response = "Хорошо."

        save_message(
            user_id,
            "assistant",
            fallback_response,
        )

        return fallback_response

    selected_history = (
        history
        if router_result.needs_history
        else None
    )

    # ---------------------------------------------------------------
    # Создание черновика
    # ---------------------------------------------------------------

    try:
        draft_response = await get_gigachat_response(
            user_message=user_message,
            history=selected_history,
            route=router_result.route,
            response_policy=response_policy,
        )

    except Exception:
        logger.exception(
            (
                "Ошибка создания ответа: "
                "user_id=%s route=%s policy=%s"
            ),
            user_id,
            router_result.route.value,
            response_policy.mode,
        )

        draft_response = (
            "Извини, сейчас я временно не могу ответить. "
            "Попробуй немного позже."
        )

    # ---------------------------------------------------------------
    # Response Critic
    # ---------------------------------------------------------------

    critic_result = evaluate_response(
        response_text=draft_response,
        route=router_result.route,
        policy=response_policy,
    )

    final_response = draft_response

    if not critic_result.passed:
        logger.info(
            (
                "Response Critic: user_id=%s route=%s "
                "violations=%s"
            ),
            user_id,
            router_result.route.value,
            critic_result.violations,
        )

        final_response = await rewrite_gigachat_response(
            user_message=user_message,
            draft_response=draft_response,
            route=router_result.route,
            response_policy=response_policy,
            violations=critic_result.violations,
        )

        # Повторно проверяем переписанный ответ,
        # но второй раз модель уже не вызываем.
        second_critic_result = evaluate_response(
            response_text=final_response,
            route=router_result.route,
            policy=response_policy,
        )

        if not second_critic_result.passed:
            logger.warning(
                (
                    "Response Critic after rewrite: "
                    "user_id=%s route=%s violations=%s"
                ),
                user_id,
                router_result.route.value,
                second_critic_result.violations,
            )

    # ---------------------------------------------------------------
    # Сохранение финального ответа
    # ---------------------------------------------------------------

    save_message(
        user_id,
        "assistant",
        final_response,
    )

    return final_response
