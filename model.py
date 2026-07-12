import logging

from config import CRISIS_CONTACTS, MAX_HISTORY_LENGTH
from conversation_planner import build_conversation_plan
from database import get_history, save_message
from dialogue_director import evaluate_dialogue_direction
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
    Возвращает простой предсказуемый ответ
    без обращения к GigaChat.
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

    Позже эта часть будет заменена полноценным
    Safety Engine.
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


def normalize_text(text: str) -> str:
    """
    Нормализует текст для простых проверок.
    """

    return (
        text.lower()
        .replace("ё", "е")
        .strip()
    )


def build_safe_fallback(
    route: Route,
    user_message: str,
) -> str:
    """
    Возвращает заранее проверенный ответ,
    если черновик и его переписанная версия
    не прошли проверку.

    Этот слой не использует языковую модель,
    поэтому не может добавить новые факты.
    """

    normalized_message = normalize_text(
        user_message
    )

    if route == Route.EMOTIONAL_DISCLOSURE:
        if (
            "работ" in normalized_message
            and (
                "страшно" in normalized_message
                or "боюсь" in normalized_message
            )
        ):
            return (
                "Похоже, сама мысль о возвращении на работу "
                "уже вызывает напряжение. "
                "Что пугает сильнее всего: конкретный человек, "
                "возможная ситуация или сама необходимость туда идти?"
            )

        return (
            "Похоже, эта ситуация вызывает у тебя сильное напряжение. "
            "Что именно сейчас ощущается самым тяжёлым?"
        )

    if route == Route.DECISION_SUPPORT:
        if (
            "уволь" in normalized_message
            or "работ" in normalized_message
        ):
            return (
                "Похоже, у желания уйти и причин остаться "
                "есть для тебя весомые основания. "
                "Что должно измениться на этой работе, "
                "чтобы ты действительно захотела остаться?"
            )

        return (
            "Похоже, в этом выборе сталкиваются "
            "две важные для тебя причины. "
            "Какое условие сильнее всего повлияет на решение?"
        )

    if route == Route.REFLECTION_REQUEST:
        return (
            "Здесь может быть несколько объяснений, "
            "и я не хочу выбирать одно слишком быстро. "
            "Что обычно происходит прямо перед тем, "
            "как ты начинаешь реагировать таким образом?"
        )

    if route == Route.PRACTICAL_TASK:
        is_message_to_boss = (
            "начальник" in normalized_message
            or "руководител" in normalized_message
        )

        is_absence_message = (
            "не выйду" in normalized_message
            or "не смогу выйти" in normalized_message
            or "не приду" in normalized_message
        )

        if is_message_to_boss and is_absence_message:
            return (
                "Здравствуйте, [Имя Отчество].\n\n"
                "Сегодня я не смогу выйти на работу "
                "по личным обстоятельствам. "
                "Прошу прощения за позднее предупреждение.\n\n"
                "С уважением,\n"
                "[Имя]"
            )

        return (
            "Не удалось надёжно сформировать готовый текст "
            "без риска добавить лишние детали. "
            "Напиши, кому предназначено сообщение "
            "и что именно в нём нужно сообщить."
        )

    if route == Route.FACTUAL_QUESTION:
        return (
            "Сейчас мне не удалось сформировать "
            "достаточно надёжный ответ. "
            "Попробуй немного уточнить вопрос."
        )

    if route == Route.ACKNOWLEDGEMENT:
        return "Хорошо, продолжим с этого места."

    return (
        "Кажется, я не смогла достаточно точно понять запрос. "
        "Сформулируй, пожалуйста, что сейчас важнее: "
        "выговориться, разобраться или получить конкретную помощь?"
    )


async def get_response(
    user_id: int,
    user_message: str,
) -> str:
    """
    Полный цикл обработки сообщения:

    1. Router.
    2. Conversation Planner.
    3. Response Policy.
    4. Создание одного черновика.
    5. Проверка Critic и Director.
    6. Не более одного переписывания.
    7. Повторная проверка.
    8. Безопасный резервный ответ при повторной ошибке.
    """

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

    # ---------------------------------------------------------------
    # Conversation Planner
    # ---------------------------------------------------------------

    conversation_plan = build_conversation_plan(
        route=router_result.route,
        user_message=user_message,
        has_history=has_history,
    )

    # ---------------------------------------------------------------
    # Response Policy
    # ---------------------------------------------------------------

    response_policy = get_response_policy(
        router_result.route
    )

    logger.info(
        (
            "Pipeline: user_id=%s route=%s "
            "plan=%s confidence=%.2f policy=%s"
        ),
        user_id,
        router_result.route.value,
        conversation_plan.action,
        router_result.confidence,
        response_policy.mode,
    )

    # Сохраняем сообщение пользователя после получения истории,
    # чтобы оно не попадало в запрос к модели дважды.
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
        if conversation_plan.should_use_history
        else None
    )

    # ---------------------------------------------------------------
    # Первый и основной запрос к GigaChat
    # ---------------------------------------------------------------

    draft_response = await get_gigachat_response(
        user_message=user_message,
        history=selected_history,
        route=router_result.route,
        response_policy=response_policy,
        conversation_plan=conversation_plan,
    )

    # ---------------------------------------------------------------
    # Первая проверка
    # ---------------------------------------------------------------

    first_critic = evaluate_response(
        response_text=draft_response,
        route=router_result.route,
        policy=response_policy,
    )

    first_director = evaluate_dialogue_direction(
        user_message=user_message,
        response_text=draft_response,
        route=router_result.route,
        policy=response_policy,
        conversation_plan=conversation_plan,
    )

    draft_is_valid = (
        first_critic.passed
        and first_director.approved
    )

    if draft_is_valid:
        save_message(
            user_id,
            "assistant",
            draft_response,
        )

        return draft_response

    logger.info(
        (
            "Response needs rewrite: user_id=%s route=%s "
            "critic=%s director=%s"
        ),
        user_id,
        router_result.route.value,
        first_critic.violations,
        first_director.violations,
    )

    # ---------------------------------------------------------------
    # Только одна попытка переписывания
    # ---------------------------------------------------------------

    rewritten_response = await rewrite_gigachat_response(
        user_message=user_message,
        draft_response=draft_response,
        route=router_result.route,
        response_policy=response_policy,
        conversation_plan=conversation_plan,
        critic_violations=first_critic.violations,
        director_violations=first_director.violations,
        director_instruction=(
            first_director.rewrite_instruction
        ),
    )

    # ---------------------------------------------------------------
    # Обязательная повторная проверка
    # ---------------------------------------------------------------

    second_critic = evaluate_response(
        response_text=rewritten_response,
        route=router_result.route,
        policy=response_policy,
    )

    second_director = evaluate_dialogue_direction(
        user_message=user_message,
        response_text=rewritten_response,
        route=router_result.route,
        policy=response_policy,
        conversation_plan=conversation_plan,
    )

    rewritten_is_valid = (
        second_critic.passed
        and second_director.approved
    )

    if rewritten_is_valid:
        final_response = rewritten_response

        logger.info(
            (
                "Rewritten response approved: "
                "user_id=%s route=%s"
            ),
            user_id,
            router_result.route.value,
        )

    else:
        # Ключевое изменение:
        # ответ, который система сама признала плохим,
        # больше не отправляется пользователю.
        logger.warning(
            (
                "Using safe fallback: user_id=%s route=%s "
                "critic=%s director=%s"
            ),
            user_id,
            router_result.route.value,
            second_critic.violations,
            second_director.violations,
        )

        final_response = build_safe_fallback(
            route=router_result.route,
            user_message=user_message,
        )

    # ---------------------------------------------------------------
    # Сохранение только финального ответа
    # ---------------------------------------------------------------

    save_message(
        user_id,
        "assistant",
        final_response,
    )

    return final_response
