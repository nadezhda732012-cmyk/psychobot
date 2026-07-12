import logging

from gigachat import GigaChat
from gigachat.models import Chat, Messages

from config import GIGACHAT_KEY
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

Сначала выполни задачу.
Не уводи разговор в психологический анализ.
Если запрос понятен, не задавай уточняющих вопросов.

Если создаёшь сообщение или письмо:

• верни готовый текст;
• не предполагай пол пользователя;
• не смешивай «вы» и «ты»;
• используй естественный язык;
• не придумывай лишние обстоятельства;
• не заканчивай ответ вопросом.
""",

    Route.FACTUAL_QUESTION: """
Пользователь задаёт информационный вопрос.

Ответь прямо и по существу.
Не превращай ответ в психологическую консультацию.
""",

    Route.DECISION_SUPPORT: """
Пользователь хочет рассмотреть решение.

Не решай за него.
Не предлагай автоматически плюсы и минусы.
Не давай универсальное домашнее задание.

Помоги определить один главный критерий:

• что удерживает пользователя;
• что подталкивает уйти;
• что должно измениться, чтобы остаться.

Задай максимум один точный вопрос.
""",

    Route.REFLECTION_REQUEST: """
Пользователь явно хочет лучше понять себя.

Не навязывай готовую причину.
Отделяй факты от предположений.
Используй максимум одну осторожную гипотезу.
Не объясняй всё детством или травмой без оснований.
""",

    Route.EMOTIONAL_DISCLOSURE: """
Пользователь рассказывает о переживаниях.

Коротко отрази конкретный смысл его сообщения.
Не используй шаблонную валидацию.
Не давай советов.
Не предлагай упражнения.

Задай один конкретный вопрос, который поможет понять,
чего именно человек боится или что оказалось самым тяжёлым.
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
    инструкцию маршрута и Response Policy.
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


def call_gigachat(
    system_prompt: str,
    user_message: str,
    history=None,
) -> str:
    """
    Выполняет запрос к GigaChat.
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
) -> str:
    """
    Создаёт первоначальный черновик ответа.
    """

    if response_policy is None:
        raise ValueError(
            "response_policy обязателен"
        )

    try:
        system_prompt = build_system_prompt(
            route=route,
            response_policy=response_policy,
        )

        return call_gigachat(
            system_prompt=system_prompt,
            user_message=user_message,
            history=history,
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


async def rewrite_gigachat_response(
    user_message: str,
    draft_response: str,
    route: Route,
    response_policy: ResponsePolicy,
    critic_violations: tuple[str, ...],
    director_violations: tuple[str, ...],
    director_instruction: str,
) -> str:
    """
    Переписывает ответ один раз с учётом
    Response Critic и Dialogue Director.
    """

    critic_text = "\n".join(
        f"- {violation}"
        for violation in critic_violations
    )

    director_text = "\n".join(
        f"- {violation}"
        for violation in director_violations
    )

    policy_prompt = policy_to_prompt(
        response_policy
    )

    rewrite_system_prompt = f"""
Ты — финальный редактор ответа ИИ.

Перепиши черновик так, чтобы он строго соответствовал:

1. маршруту разговора;
2. политике ответа;
3. замечаниям Response Critic;
4. решению Dialogue Director.

Не объясняй изменения.
Не пиши комментарии редактора.
Верни только финальный ответ пользователю.

МАРШРУТ:
{route.value}

НАРУШЕНИЯ RESPONSE CRITIC:
{critic_text or "- нет"}

НАРУШЕНИЯ DIALOGUE DIRECTOR:
{director_text or "- нет"}

КАК НУЖНО ИЗМЕНИТЬ ХОД ОТВЕТА:
{director_instruction or "- сохранить текущий ход"}

ПОЛИТИКА ОТВЕТА:
{policy_prompt}

ОБЯЗАТЕЛЬНО:

• отвечай на реальный запрос;
• не добавляй новых фактов;
• не предполагай пол пользователя;
• не используй шаблонную эмпатию;
• не давай совет раньше времени;
• не добавляй ненужный вопрос;
• не принимай решение за пользователя;
• не делай ответ длиннее без необходимости.
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
