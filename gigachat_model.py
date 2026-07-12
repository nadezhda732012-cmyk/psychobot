import logging

from gigachat import GigaChat
from gigachat.models import Chat, Messages

from config import GIGACHAT_KEY
from response_policy import ResponsePolicy, policy_to_prompt
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

Не говори:

• «всё будет хорошо»;
• «ты сильнее, чем думаешь»;
• «это первый шаг к внутренней гармонии»;
• «я полностью понимаю твои чувства»;
• «я всегда рядом».

Не изображай человеческую привязанность или эмоции.

Отвечай на реальный запрос пользователя.
Не добавляй психологический анализ, если он не нужен.
"""


ROUTE_INSTRUCTIONS = {
    Route.ACKNOWLEDGEMENT: """
Пользователь отправил короткое подтверждение или отрицание.

Используй предыдущий контекст.
Не анализируй само короткое слово.
Не делай выводов об интонации или личности.
""",

    Route.PRACTICAL_TASK: """
Пользователь просит выполнить конкретную задачу.

Сначала выполни эту задачу.
Не уводи разговор в психологический анализ.
Если запрос понятен, не задавай уточняющих вопросов.
""",

    Route.FACTUAL_QUESTION: """
Пользователь задаёт информационный вопрос.

Ответь прямо и по существу.
Не превращай ответ в психологическую консультацию.
""",

    Route.DECISION_SUPPORT: """
Пользователь хочет рассмотреть решение.

Не решай за него.
Помоги увидеть главные варианты, последствия
или недостающую информацию.
""",

    Route.REFLECTION_REQUEST: """
Пользователь явно хочет лучше понять себя.

Не навязывай готовую причину.
Отделяй факты от предположений.
Используй максимум одну осторожную гипотезу.
""",

    Route.EMOTIONAL_DISCLOSURE: """
Пользователь рассказывает о переживаниях.

Сначала коротко покажи, что понял главное.
Не торопись с советами.
Не перегружай человека.
""",

    Route.GENERAL: """
Ответь на реальное сообщение пользователя.

Если запрос понятен, ответь прямо.
Не придумывай скрытые эмоции и причины.
""",
}


def build_system_prompt(
    route: Route,
    response_policy: ResponsePolicy,
) -> str:
    """
    Объединяет базовый промпт,
    маршрут и политику ответа.
    """

    route_instruction = ROUTE_INSTRUCTIONS.get(
        route,
        ROUTE_INSTRUCTIONS[Route.GENERAL],
    )

    policy_instruction = policy_to_prompt(
        response_policy
    )

    return (
        BASE_SYSTEM_PROMPT.strip()
        + "\n\n"
        + route_instruction.strip()
        + "\n\n"
        + policy_instruction.strip()
    )


async def get_gigachat_response(
    user_message: str,
    history=None,
    route: Route = Route.GENERAL,
    response_policy: ResponsePolicy | None = None,
) -> str:
    """
    Получает ответ GigaChat с учётом Router
    и Response Policy Engine.
    """

    if response_policy is None:
        raise ValueError(
            "response_policy обязателен"
        )

    try:
        with GigaChat(
            credentials=GIGACHAT_KEY,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False,
            profanity_check=False,
        ) as giga:

            chat = Chat(messages=[])

            system_prompt = build_system_prompt(
                route=route,
                response_policy=response_policy,
            )

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

            logger.warning(
                (
                    "GigaChat вернул пустой ответ: "
                    "route=%s policy=%s"
                ),
                route.value,
                response_policy.mode,
            )

            return (
                "Не удалось получить ответ. "
                "Попробуй отправить сообщение ещё раз."
            )

    except Exception:
        logger.exception(
            "Ошибка GigaChat: route=%s policy=%s",
            route.value,
            response_policy.mode,
        )

        return (
            "Извини, сейчас я временно не могу ответить. "
            "Попробуй немного позже."
        )
