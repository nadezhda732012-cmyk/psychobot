import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass

from gigachat import GigaChat
from gigachat.models import Chat, Messages

from config import GIGACHAT_KEY
from router import Route


logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Внутренний план ответа
# -------------------------------------------------------------------

@dataclass(frozen=True)
class ResponsePlan:
    """
    Внутренний план ответа.

    Пользователь его не видит.
    Он используется только для управления генерацией.
    """

    goal: str
    strategy: str
    focus: str
    tone: str

    give_advice: bool
    ask_question: bool
    max_questions: int
    max_sentences: int

    avoid: tuple[str, ...]


ALLOWED_STRATEGIES = {
    "direct_answer",
    "clarify",
    "explore",
    "reflect",
    "decision_criterion",
    "practical_result",
    "continue_context",
}


ALLOWED_TONES = {
    "neutral",
    "warm",
    "calm",
    "direct",
    "supportive",
}


# -------------------------------------------------------------------
# Надёжные планы по умолчанию
# -------------------------------------------------------------------

DEFAULT_PLANS = {
    Route.ACKNOWLEDGEMENT: ResponsePlan(
        goal="Естественно продолжить предыдущую тему.",
        strategy="continue_context",
        focus="Предыдущий вопрос или тема разговора.",
        tone="calm",
        give_advice=False,
        ask_question=True,
        max_questions=1,
        max_sentences=3,
        avoid=(
            "анализ короткого слова",
            "выводы об интонации",
            "новая несвязанная тема",
        ),
    ),

    Route.PRACTICAL_TASK: ResponsePlan(
        goal="Дать готовый результат, который можно использовать.",
        strategy="practical_result",
        focus="Конкретная задача пользователя.",
        tone="direct",
        give_advice=True,
        ask_question=False,
        max_questions=0,
        max_sentences=8,
        avoid=(
            "психологический анализ",
            "выдуманные обстоятельства",
            "канцелярит",
            "предположение пола пользователя",
            "лишний вопрос после результата",
        ),
    ),

    Route.FACTUAL_QUESTION: ResponsePlan(
        goal="Ответить прямо и по существу.",
        strategy="direct_answer",
        focus="Фактический вопрос пользователя.",
        tone="neutral",
        give_advice=True,
        ask_question=False,
        max_questions=0,
        max_sentences=6,
        avoid=(
            "психологическая интерпретация",
            "поиск скрытого запроса",
            "необязательный вопрос",
        ),
    ),

    Route.EMOTIONAL_DISCLOSURE: ResponsePlan(
        goal="Помочь определить конкретный источник переживания.",
        strategy="clarify",
        focus="Событие, человек или ожидание, вызывающее переживание.",
        tone="warm",
        give_advice=False,
        ask_question=True,
        max_questions=1,
        max_sentences=4,
        avoid=(
            "советы",
            "упражнения",
            "шаблонная эмпатия",
            "общие рассуждения об эмоциях",
            "несколько вопросов",
        ),
    ),

    Route.DECISION_SUPPORT: ResponsePlan(
        goal="Помочь определить один главный критерий решения.",
        strategy="decision_criterion",
        focus=(
            "Что удерживает пользователя, что подталкивает к изменению "
            "или что должно измениться."
        ),
        tone="calm",
        give_advice=False,
        ask_question=True,
        max_questions=1,
        max_sentences=4,
        avoid=(
            "решение за пользователя",
            "список плюсов и минусов",
            "универсальное домашнее задание",
            "несколько критериев одновременно",
        ),
    ),

    Route.REFLECTION_REQUEST: ResponsePlan(
        goal="Помочь проверить одну возможную закономерность.",
        strategy="explore",
        focus="Одна конкретная ситуация, мысль или ожидаемое последствие.",
        tone="warm",
        give_advice=False,
        ask_question=True,
        max_questions=1,
        max_sentences=4,
        avoid=(
            "диагноз",
            "готовая психологическая причина",
            "объяснение всего детством",
            "несколько гипотез одновременно",
        ),
    ),

    Route.GENERAL: ResponsePlan(
        goal="Ответить на фактический смысл сообщения.",
        strategy="direct_answer",
        focus="Текущий запрос пользователя.",
        tone="neutral",
        give_advice=True,
        ask_question=False,
        max_questions=1,
        max_sentences=5,
        avoid=(
            "лишняя психологизация",
            "выдуманные скрытые причины",
            "обязательный вопрос в конце",
        ),
    ),
}


def get_default_plan(
    route: Route,
) -> ResponsePlan:
    """
    Возвращает гарантированно корректный план,
    если LLM-планировщик ошибся.
    """

    return DEFAULT_PLANS.get(
        route,
        DEFAULT_PLANS[Route.GENERAL],
    )


# -------------------------------------------------------------------
# Инструкции для планировщика
# -------------------------------------------------------------------

PLANNER_SYSTEM_PROMPT = """
Ты — внутренний планировщик диалога.

Ты не отвечаешь пользователю.
Ты создаёшь только короткий план следующего ответа.

Требуется вернуть только JSON-объект:

{
  "goal": "цель одного следующего ответа",
  "strategy": "одна стратегия",
  "focus": "главный фокус",
  "tone": "тон",
  "give_advice": false,
  "ask_question": true,
  "max_questions": 1,
  "max_sentences": 4,
  "avoid": [
    "что нельзя делать"
  ]
}

Допустимые strategy:

- direct_answer
- clarify
- explore
- reflect
- decision_criterion
- practical_result
- continue_context

Допустимые tone:

- neutral
- warm
- calm
- direct
- supportive

Правила:

1. План должен описывать только один следующий шаг.
2. Не ставь диагнозы.
3. Не выдумывай причины поведения.
4. Для эмоционального сообщения обычно сначала уточняй источник переживания.
5. Для решения ищи один критерий, а не давай совет.
6. Для практической задачи сначала дай готовый результат.
7. Не предлагай упражнение без прямого запроса.
8. Максимум один вопрос.
9. Верни только JSON. Без Markdown и пояснений.
""".strip()


# -------------------------------------------------------------------
# Инструкции для финального ответа
# -------------------------------------------------------------------

BASE_RESPONSE_PROMPT = """
Ты — ИИ-собеседник для саморефлексии и эмоциональной поддержки.

Ты не являешься психологом, психотерапевтом или врачом.
Не изображай наличие человеческого профессионального опыта.
Не ставь диагнозы и не назначай лечение.

Требования:

1. Выполни только внутренний план ответа.
2. Не показывай и не пересказывай этот план пользователю.
3. Не анализируй короткие слова и благодарность.
4. Не утверждай, что точно знаешь чувства или причины поведения.
5. Не добавляй факты, которых пользователь не сообщил.
6. Не предполагай пол пользователя.
7. Не смешивай «ты» и «вы».
8. Не используй канцелярит.
9. Не используй шаблоны:
   - «Понимаю, как сложно»;
   - «Ваши чувства важны»;
   - «Всё будет хорошо»;
   - «Прислушайся к себе»;
   - «Истинные желания»;
   - «Составь список плюсов и минусов»;
   - «Я всегда рядом».
10. Обычно используй 2–5 предложений.
11. Задавай максимум один вопрос.
12. Не добавляй второй этап разговора.
""".strip()


ROUTE_INSTRUCTIONS = {
    Route.ACKNOWLEDGEMENT: """
Используй предыдущий контекст.
Не анализируй короткое слово.
Продолжи разговор естественно и кратко.
""",

    Route.PRACTICAL_TASK: """
Верни готовый результат, который можно сразу использовать.
Используй только сведения из сообщения пользователя.
Не придумывай документы, справки, причины или договорённости.
Не заканчивай ответ вопросом.
""",

    Route.FACTUAL_QUESTION: """
Ответь прямо и по существу.
Не превращай ответ в психологическую консультацию.
""",

    Route.EMOTIONAL_DISCLOSURE: """
Коротко отрази конкретный смысл сообщения.
Не давай советов и упражнений.
Помоги уточнить конкретный источник переживания.
""",

    Route.DECISION_SUPPORT: """
Не решай за пользователя.
Не предлагай плюсы и минусы.
Помоги определить один главный критерий выбора.
""",

    Route.REFLECTION_REQUEST: """
Не сообщай готовую психологическую причину.
Используй максимум одну осторожную гипотезу
или один проверяющий вопрос.
""",

    Route.GENERAL: """
Ответь на реальный смысл сообщения.
Не добавляй психологический анализ без запроса.
""",
}


# -------------------------------------------------------------------
# Работа с GigaChat
# -------------------------------------------------------------------

def call_gigachat(
    system_prompt: str,
    user_message: str,
    history=None,
) -> str:
    """
    Выполняет один синхронный запрос к GigaChat.
    """

    with GigaChat(
        credentials=GIGACHAT_KEY,
        scope="GIGACHAT_API_PERS",
        verify_ssl_certs=False,
        profanity_check=False,
    ) as giga:

        chat = Chat(
            messages=[
                Messages(
                    role="system",
                    content=system_prompt,
                )
            ]
        )

        if history:
            for message in history[-10:]:
                chat.messages.append(
                    Messages(
                        role=message.role,
                        content=message.content,
                    )
                )

        chat.messages.append(
            Messages(
                role="user",
                content=user_message,
            )
        )

        response = giga.chat(chat)

        if not response.choices:
            raise RuntimeError(
                "GigaChat вернул ответ без choices"
            )

        answer = response.choices[0].message.content

        if not answer:
            raise RuntimeError(
                "GigaChat вернул пустой ответ"
            )

        return answer.strip()


# -------------------------------------------------------------------
# Парсинг и проверка внутреннего плана
# -------------------------------------------------------------------

def extract_json_object(
    text: str,
) -> dict:
    """
    Извлекает JSON даже в случае,
    если модель добавила Markdown-обёртку.
    """

    cleaned = text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "JSON-объект не найден"
        )

    return json.loads(
        cleaned[start:end + 1]
    )


def parse_response_plan(
    raw_plan: str,
    route: Route,
) -> ResponsePlan:
    """
    Проверяет план модели.

    При любой проблеме вызывающий код использует
    надёжный план по умолчанию.
    """

    data = extract_json_object(
        raw_plan
    )

    strategy = str(
        data.get("strategy", "")
    ).strip()

    tone = str(
        data.get("tone", "")
    ).strip()

    if strategy not in ALLOWED_STRATEGIES:
        raise ValueError(
            f"Недопустимая strategy: {strategy}"
        )

    if tone not in ALLOWED_TONES:
        raise ValueError(
            f"Недопустимый tone: {tone}"
        )

    max_questions = int(
        data.get("max_questions", 1)
    )

    max_sentences = int(
        data.get("max_sentences", 4)
    )

    if max_questions < 0 or max_questions > 1:
        raise ValueError(
            "max_questions должен быть 0 или 1"
        )

    if max_sentences < 1 or max_sentences > 8:
        raise ValueError(
            "max_sentences должен быть от 1 до 8"
        )

    avoid_value = data.get(
        "avoid",
        [],
    )

    if not isinstance(avoid_value, list):
        raise ValueError(
            "avoid должен быть массивом"
        )

    avoid = tuple(
        str(item).strip()
        for item in avoid_value[:8]
        if str(item).strip()
    )

    plan = ResponsePlan(
        goal=str(
            data.get("goal", "")
        ).strip(),
        strategy=strategy,
        focus=str(
            data.get("focus", "")
        ).strip(),
        tone=tone,
        give_advice=bool(
            data.get("give_advice", False)
        ),
        ask_question=bool(
            data.get("ask_question", False)
        ),
        max_questions=max_questions,
        max_sentences=max_sentences,
        avoid=avoid,
    )

    if not plan.goal or not plan.focus:
        raise ValueError(
            "В плане отсутствует goal или focus"
        )

    # Жёсткие ограничения маршрутов.
    if route == Route.PRACTICAL_TASK:
        plan = ResponsePlan(
            **{
                **asdict(plan),
                "strategy": "practical_result",
                "ask_question": False,
                "max_questions": 0,
            }
        )

    elif route == Route.EMOTIONAL_DISCLOSURE:
        plan = ResponsePlan(
            **{
                **asdict(plan),
                "give_advice": False,
                "ask_question": True,
                "max_questions": 1,
            }
        )

    elif route == Route.DECISION_SUPPORT:
        plan = ResponsePlan(
            **{
                **asdict(plan),
                "strategy": "decision_criterion",
                "give_advice": False,
                "ask_question": True,
                "max_questions": 1,
            }
        )

    elif route == Route.REFLECTION_REQUEST:
        plan = ResponsePlan(
            **{
                **asdict(plan),
                "give_advice": False,
                "max_questions": min(
                    plan.max_questions,
                    1,
                ),
            }
        )

    return plan


async def build_response_plan(
    user_message: str,
    route: Route,
    history=None,
) -> ResponsePlan:
    """
    Создаёт внутренний план отдельным запросом.

    При ошибке использует заранее проверенный
    маршрутный план.
    """

    default_plan = get_default_plan(
        route
    )

    route_instruction = ROUTE_INSTRUCTIONS.get(
        route,
        ROUTE_INSTRUCTIONS[Route.GENERAL],
    )

    planning_prompt = (
        PLANNER_SYSTEM_PROMPT
        + "\n\nТЕКУЩИЙ МАРШРУТ:\n"
        + route.value
        + "\n\nОСОБЫЕ ПРАВИЛА МАРШРУТА:\n"
        + route_instruction.strip()
    )

    try:
        raw_plan = await asyncio.to_thread(
            call_gigachat,
            planning_prompt,
            user_message,
            history,
        )

        plan = parse_response_plan(
            raw_plan=raw_plan,
            route=route,
        )

        logger.info(
            (
                "Thinking plan: route=%s "
                "strategy=%s goal=%s"
            ),
            route.value,
            plan.strategy,
            plan.goal,
        )

        return plan

    except Exception:
        logger.exception(
            (
                "Thinking plan failed. "
                "Using default plan: route=%s"
            ),
            route.value,
        )

        return default_plan


def plan_to_prompt(
    plan: ResponsePlan,
) -> str:
    """
    Преобразует план в короткую инструкцию.
    """

    avoid_text = "\n".join(
        f"- {item}"
        for item in plan.avoid
    )

    return f"""
ВНУТРЕННИЙ ПЛАН ОТВЕТА

Цель:
{plan.goal}

Стратегия:
{plan.strategy}

Фокус:
{plan.focus}

Тон:
{plan.tone}

Давать советы:
{"да" if plan.give_advice else "нет"}

Задать вопрос:
{"да" if plan.ask_question else "нет"}

Максимум вопросов:
{plan.max_questions}

Максимум предложений:
{plan.max_sentences}

Избегать:
{avoid_text}

Выполни только этот план.
Не показывай план пользователю.
""".strip()


# -------------------------------------------------------------------
# Финальный ответ
# -------------------------------------------------------------------

async def get_gigachat_response(
    user_message: str,
    history=None,
    route: Route = Route.GENERAL,
) -> str:
    """
    Двухэтапная обработка:

    1. Внутренний план.
    2. Финальный ответ по плану.
    """

    try:
        response_plan = await build_response_plan(
            user_message=user_message,
            route=route,
            history=history,
        )

        route_instruction = ROUTE_INSTRUCTIONS.get(
            route,
            ROUTE_INSTRUCTIONS[Route.GENERAL],
        )

        final_system_prompt = (
            BASE_RESPONSE_PROMPT
            + "\n\n"
            + route_instruction.strip()
            + "\n\n"
            + plan_to_prompt(response_plan)
        )

        return await asyncio.to_thread(
            call_gigachat,
            final_system_prompt,
            user_message,
            history,
        )

    except Exception:
        logger.exception(
            "Ошибка GigaChat: route=%s",
            route.value,
        )

        return (
            "Извини, сейчас я временно не могу ответить. "
            "Попробуй немного позже."
        )
