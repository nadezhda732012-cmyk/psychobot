import logging

from gigachat import GigaChat
from gigachat.models import Chat, Messages

from config import GIGACHAT_KEY
from conversation_planner import (
    ConversationPlan,
    plan_to_prompt,
)
from response_policy import (
    ResponsePolicy,
    policy_to_prompt,
)
from router import Route


logger = logging.getLogger(__name__)


BASE_SYSTEM_PROMPT = """
Ты — ИИ-собеседник для саморефлексии и эмоциональной поддержки.

Ты не являешься психологом, психотерапевтом или врачом.
Ты не изображаешь наличие человеческого профессионального опыта.
Ты не ставишь диагнозы и не ведёшь психотерапию.

Твоя задача — помогать человеку:

• яснее понимать ситуацию;
• структурировать мысли и переживания;
• замечать возможные варианты;
• сохранять самостоятельность в принятии решений.

Не ищи глубокий психологический смысл в каждом сообщении.

Не утверждай, что точно знаешь:

• чувства человека;
• мотивы человека;
• скрытые причины поведения;
• намерения других людей;
• психологический диагноз.

Если делаешь предположение, используй осторожный язык:

• «похоже»;
• «возможно»;
• «если я правильно понял»;
• «одна из возможных версий».

Не используй мотивационные клише.
Не изображай человеческую привязанность или эмоции.

Выполняй только один шаг разговора,
который указан в Conversation Plan.
"""


ROUTE_INSTRUCTIONS = {
    Route.ACKNOWLEDGEMENT: """
Используй предыдущий контекст.
Не анализируй короткое слово.
""",

    Route.PRACTICAL_TASK: """
Верни готовый результат.

Не добавляй факты, документы, причины,
договорённости или действия,
которых пользователь не сообщал.

Не предполагай пол пользователя.
Не заканчивай ответ вопросом.
""",

    Route.FACTUAL_QUESTION: """
Ответь прямо и по существу.
Не превращай ответ в психологическую консультацию.
""",

    Route.DECISION_SUPPORT: """
Не решай за пользователя.
Не предлагай плюсы и минусы.
Определи один главный критерий выбора.
""",

    Route.REFLECTION_REQUEST: """
Не навязывай готовую психологическую причину.
Используй одну осторожную гипотезу
или один проверяющий вопрос.
""",

    Route.EMOTIONAL_DISCLOSURE: """
Не давай советов.
Не предлагай упражнений.
Коротко отрази конкретный смысл
и задай один конкретный вопрос.
""",

    Route.GENERAL: """
Ответь на реальный запрос
без лишней психологизации.
""",
}


def build_system_prompt(
    route: Route,
    response_policy: ResponsePolicy,
    conversation_plan: ConversationPlan,
) -> str:
    """
    Создаёт полный системный промпт.
    """

    route_instruction = ROUTE_INSTRUCTIONS.get(
        route,
        ROUTE_INSTRUCTIONS[Route.GENERAL],
    )

    policy_instruction = policy_to_prompt(
        response_policy
    )

    plan_instruction = plan_to_prompt(
        conversation_plan
    )

    return (
        BASE_SYSTEM_PROMPT.strip()
        + "\n\n"
        + route_instruction.strip()
        + "\n\n"
        + plan_instruction.strip()
        + "\n\n"
        + policy_instruction.strip()
    )


def call_gigachat(
    system_prompt: str,
    user_message: str,
    history=None,
) -> str:
    """
    Выполняет один запрос к GigaChat.
    """

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
                content=system_prompt,
            )
        )

        if history:
            for msg in history[-10:]:
                chat.messages.append(
                    Messages(
                        role=msg.role,
                        content=msg.content,
                    )
                )

        chat.messages.append(
            Messages(
                role="user",
                content=user_message,
            )
        )

        response = giga.chat(chat)

        if response.choices:
            answer = response.choices[0].message.content

            if answer:
                return answer.strip()

        raise RuntimeError(
            "GigaChat вернул пустой ответ"
        )


async def get_gigachat_response(
    user_message: str,
    history=None,
    route: Route = Route.GENERAL,
    response_policy: ResponsePolicy | None = None,
    conversation_plan: ConversationPlan | None = None,
) -> str:
    """
    Создаёт черновик на основании
    маршрута, политики и плана.
    """

    if response_policy is None:
        raise ValueError(
            "response_policy обязателен"
        )

    if conversation_plan is None:
        raise ValueError(
            "conversation_plan обязателен"
        )

    try:
        system_prompt = build_system_prompt(
            route=route,
            response_policy=response_policy,
            conversation_plan=conversation_plan,
        )

        return call_gigachat(
            system_prompt=system_prompt,
            user_message=user_message,
            history=history,
        )

    except Exception:
        logger.exception(
            "Ошибка GigaChat: route=%s plan=%s",
            route.value,
            conversation_plan.action,
        )

        return (
            "Извини, сейчас я временно не могу ответить. "
            "Попробуй немного позже."
        )


async def rewrite_gigachat_response(
    user_message: str,
    draft_response: str,
    route: Route,
    response_policy: ResponsePolicy,
    conversation_plan: ConversationPlan,
    critic_violations: tuple[str, ...],
    director_violations: tuple[str, ...],
    director_instruction: str,
) -> str:
    """
    Один раз переписывает ответ.
    """

    critic_text = "\n".join(
        f"- {violation}"
        for violation in critic_violations
    )

    director_text = "\n".join(
        f"- {violation}"
        for violation in director_violations
    )

    rewrite_system_prompt = f"""
Ты — финальный редактор ответа.

Верни только готовый ответ пользователю.
Не объясняй изменения.

МАРШРУТ:
{route.value}

CONVERSATION PLAN:
{plan_to_prompt(conversation_plan)}

RESPONSE POLICY:
{policy_to_prompt(response_policy)}

НАРУШЕНИЯ RESPONSE CRITIC:
{critic_text or "- нет"}

НАРУШЕНИЯ DIALOGUE DIRECTOR:
{director_text or "- нет"}

ОБЯЗАТЕЛЬНЫЕ ИСПРАВЛЕНИЯ:
{director_instruction or "- сохранить текущий ход"}

Не добавляй новых фактов.
Не меняй цель Conversation Plan.
Выполни только один указанный шаг.
""".strip()

    rewrite_user_message = f"""
СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ:

{user_message}

ЧЕРНОВИК:

{draft_response}

Верни только исправленный ответ.
""".strip()

    try:
        return call_gigachat(
            system_prompt=rewrite_system_prompt,
            user_message=rewrite_user_message,
            history=None,
        )

    except Exception:
        logger.exception(
            "Ошибка переписывания: route=%s",
            route.value,
        )

        return draft_response
