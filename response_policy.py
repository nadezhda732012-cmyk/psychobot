from dataclasses import dataclass

from router import Route


@dataclass(frozen=True)
class ResponsePolicy:
    """
    Ограничения, которым должен соответствовать ответ модели.
    """

    mode: str
    goal: str

    min_sentences: int
    max_sentences: int
    max_questions: int

    allow_advice: bool
    allow_exercise: bool
    allow_reflection: bool
    allow_memory_reference: bool

    require_direct_answer: bool
    require_validation: bool
    require_user_consent_before_exercise: bool

    optional_follow_up: bool
    end_with_question: bool

    forbidden_behaviors: tuple[str, ...]


COMMON_FORBIDDEN_BEHAVIORS = (
    "Не ставить диагноз.",
    "Не изображать психолога, врача или психотерапевта.",
    "Не утверждать, что точно знаешь чувства или мотивы пользователя.",
    "Не придумывать скрытый смысл без достаточного контекста.",
    "Не использовать мотивационные клише.",
    "Не изображать человеческую привязанность.",
    "Не писать «я всегда рядом».",
    "Не задавать несколько вопросов одновременно.",
    "Не использовать снисходительный или назидательный тон.",
    "Не выдавать предположение за факт.",
)


POLICIES = {
    Route.GREETING: ResponsePolicy(
        mode="greeting",
        goal="Коротко и естественно поздороваться.",
        min_sentences=1,
        max_sentences=2,
        max_questions=0,
        allow_advice=False,
        allow_exercise=False,
        allow_reflection=False,
        allow_memory_reference=False,
        require_direct_answer=True,
        require_validation=False,
        require_user_consent_before_exercise=True,
        optional_follow_up=False,
        end_with_question=False,
        forbidden_behaviors=COMMON_FORBIDDEN_BEHAVIORS,
    ),

    Route.GRATITUDE: ResponsePolicy(
        mode="gratitude",
        goal="Коротко и естественно принять благодарность.",
        min_sentences=1,
        max_sentences=1,
        max_questions=0,
        allow_advice=False,
        allow_exercise=False,
        allow_reflection=False,
        allow_memory_reference=False,
        require_direct_answer=True,
        require_validation=False,
        require_user_consent_before_exercise=True,
        optional_follow_up=False,
        end_with_question=False,
        forbidden_behaviors=COMMON_FORBIDDEN_BEHAVIORS,
    ),

    Route.GOODBYE: ResponsePolicy(
        mode="goodbye",
        goal="Спокойно завершить разговор без попытки удержать пользователя.",
        min_sentences=1,
        max_sentences=2,
        max_questions=0,
        allow_advice=False,
        allow_exercise=False,
        allow_reflection=False,
        allow_memory_reference=False,
        require_direct_answer=True,
        require_validation=False,
        require_user_consent_before_exercise=True,
        optional_follow_up=False,
        end_with_question=False,
        forbidden_behaviors=COMMON_FORBIDDEN_BEHAVIORS,
    ),

    Route.ACKNOWLEDGEMENT: ResponsePolicy(
        mode="acknowledgement",
        goal=(
            "Продолжить предыдущий контекст "
            "без анализа короткого слова."
        ),
        min_sentences=1,
        max_sentences=3,
        max_questions=1,
        allow_advice=False,
        allow_exercise=False,
        allow_reflection=False,
        allow_memory_reference=False,
        require_direct_answer=False,
        require_validation=False,
        require_user_consent_before_exercise=True,
        optional_follow_up=True,
        end_with_question=False,
        forbidden_behaviors=(
            *COMMON_FORBIDDEN_BEHAVIORS,
            "Не анализировать интонацию короткого ответа.",
            "Не делать выводы о личности по словам «да», «нет», «хорошо».",
            "Не начинать новую тему без связи с предыдущим контекстом.",
        ),
    ),

    Route.PRACTICAL_TASK: ResponsePolicy(
        mode="practical_task",
        goal="Сразу выполнить конкретную задачу пользователя.",
        min_sentences=1,
        max_sentences=10,
        max_questions=1,
        allow_advice=True,
        allow_exercise=False,
        allow_reflection=False,
        allow_memory_reference=False,
        require_direct_answer=True,
        require_validation=False,
        require_user_consent_before_exercise=True,
        optional_follow_up=True,
        end_with_question=False,
        forbidden_behaviors=(
            *COMMON_FORBIDDEN_BEHAVIORS,
            "Не уводить разговор в психологический анализ.",
            "Не задавать вопрос, если задача понятна.",
            "Не добавлять обязательный вопрос после готового результата.",
            "Не смешивать формальное и неформальное обращение.",
            "Не предполагать пол пользователя.",
            "Не использовать неестественные канцелярские формулировки.",
            "Не добавлять детали, которых пользователь не сообщал.",
            "Не писать «буду рад» или «буду рада», если пол неизвестен.",
            "Не усложнять простой текст лишними объяснениями.",
        ),
    ),

    Route.FACTUAL_QUESTION: ResponsePolicy(
        mode="factual_question",
        goal="Дать прямой информационный ответ.",
        min_sentences=1,
        max_sentences=8,
        max_questions=0,
        allow_advice=True,
        allow_exercise=False,
        allow_reflection=False,
        allow_memory_reference=False,
        require_direct_answer=True,
        require_validation=False,
        require_user_consent_before_exercise=True,
        optional_follow_up=False,
        end_with_question=False,
        forbidden_behaviors=(
            *COMMON_FORBIDDEN_BEHAVIORS,
            "Не превращать информационный вопрос в психологическую консультацию.",
            "Не искать скрытый запрос, если пользователь просит конкретный факт.",
            "Не добавлять ненужный эмоциональный комментарий.",
        ),
    ),

    Route.DECISION_SUPPORT: ResponsePolicy(
        mode="decision_support",
        goal=(
            "Помочь определить главный конфликт или критерий решения, "
            "не принимая решение за пользователя."
        ),
        min_sentences=2,
        max_sentences=7,
        max_questions=1,
        allow_advice=True,
        allow_exercise=False,
        allow_reflection=True,
        allow_memory_reference=True,
        require_direct_answer=False,
        require_validation=False,
        require_user_consent_before_exercise=True,
        optional_follow_up=True,
        end_with_question=False,
        forbidden_behaviors=(
            *COMMON_FORBIDDEN_BEHAVIORS,
            "Не принимать решение за пользователя.",
            "Не давать категоричную команду.",
            "Не перечислять слишком много вариантов.",
            "Не предлагать автоматически список плюсов и минусов.",
            "Не использовать выражение «истинные желания».",
            "Не давать общее домашнее задание вместо анализа выбора.",
            "Предпочитать один точный вопрос о главном критерии решения.",
            "Не использовать фразы «просто подумай» и «тебе нужно понять».",
            "Не сводить сложный выбор к универсальному совету.",
        ),
    ),

    Route.REFLECTION_REQUEST: ResponsePolicy(
        mode="reflection_request",
        goal=(
            "Помочь исследовать ситуацию "
            "без навязывания готовой причины."
        ),
        min_sentences=2,
        max_sentences=6,
        max_questions=1,
        allow_advice=False,
        allow_exercise=False,
        allow_reflection=True,
        allow_memory_reference=True,
        require_direct_answer=False,
        require_validation=True,
        require_user_consent_before_exercise=True,
        optional_follow_up=True,
        end_with_question=True,
        forbidden_behaviors=(
            *COMMON_FORBIDDEN_BEHAVIORS,
            "Не объяснять всё детством или травмой без оснований.",
            "Не выдавать гипотезу за факт.",
            "Не использовать формулировки «ты всегда» и «на самом деле ты».",
            "Не навязывать единственную причину поведения.",
            "Не задавать слишком абстрактный или слишком глубокий вопрос без необходимости.",
            "Не использовать психологические термины, если можно сказать проще.",
        ),
    ),

    Route.EMOTIONAL_DISCLOSURE: ResponsePolicy(
        mode="emotional_disclosure",
        goal=(
            "Сначала дать человеку почувствовать, "
            "что его услышали, а затем выбрать один следующий шаг."
        ),
        min_sentences=2,
        max_sentences=5,
        max_questions=1,
        allow_advice=False,
        allow_exercise=False,
        allow_reflection=True,
        allow_memory_reference=True,
        require_direct_answer=False,
        require_validation=True,
        require_user_consent_before_exercise=True,
        optional_follow_up=True,
        end_with_question=False,
        forbidden_behaviors=(
            *COMMON_FORBIDDEN_BEHAVIORS,
            "Не давать советы слишком рано.",
            "Не предлагать упражнение автоматически.",
            "Не превращать ответ в лекцию.",
            "Не начинать ответ словами «Понимаю, как сложно».",
            "Не писать универсальные фразы «твои чувства важны и понятны».",
            "Не использовать фразу «это нормально» без необходимости.",
            "Не делать эмоциональное отражение слишком общим.",
            "Вопрос должен быть конкретным и облегчать ответ пользователя.",
            "Не задавать вопрос, если человеку сейчас полезнее короткая поддержка.",
            "Не добавлять несколько возможных эмоций списком без необходимости.",
        ),
    ),

    Route.CRISIS_SIGNAL: ResponsePolicy(
        mode="crisis_signal",
        goal="Сосредоточиться на непосредственной безопасности.",
        min_sentences=2,
        max_sentences=6,
        max_questions=1,
        allow_advice=True,
        allow_exercise=False,
        allow_reflection=False,
        allow_memory_reference=False,
        require_direct_answer=True,
        require_validation=True,
        require_user_consent_before_exercise=True,
        optional_follow_up=False,
        end_with_question=True,
        forbidden_behaviors=(
            *COMMON_FORBIDDEN_BEHAVIORS,
            "Не уходить в глубокий психологический анализ.",
            "Не давать длинные упражнения.",
            "Не обещать абсолютную конфиденциальность.",
            "Не обещать постоянное присутствие.",
            "Не спорить с пользователем.",
            "Не стыдить и не обвинять.",
            "Не использовать длинные вступления.",
        ),
    ),

    Route.GENERAL: ResponsePolicy(
        mode="general",
        goal=(
            "Ответить на реальный запрос "
            "без лишней психологизации."
        ),
        min_sentences=1,
        max_sentences=6,
        max_questions=1,
        allow_advice=True,
        allow_exercise=False,
        allow_reflection=True,
        allow_memory_reference=True,
        require_direct_answer=False,
        require_validation=False,
        require_user_consent_before_exercise=True,
        optional_follow_up=True,
        end_with_question=False,
        forbidden_behaviors=(
            *COMMON_FORBIDDEN_BEHAVIORS,
            "Не искать скрытую психологическую проблему в обычном сообщении.",
            "Не добавлять советы, если пользователь их не просил.",
            "Не завершать каждый ответ вопросом.",
        ),
    ),
}


def get_response_policy(route: Route) -> ResponsePolicy:
    """
    Возвращает политику ответа для выбранного маршрута.
    """

    return POLICIES.get(
        route,
        POLICIES[Route.GENERAL],
    )


def policy_to_prompt(policy: ResponsePolicy) -> str:
    """
    Преобразует объект политики в инструкцию
    для языковой модели.
    """

    advice_rule = (
        "Советы допустимы."
        if policy.allow_advice
        else "Не давай советов в этом ответе."
    )

    exercise_rule = (
        "Упражнение допустимо."
        if policy.allow_exercise
        else "Не предлагай упражнение."
    )

    reflection_rule = (
        "Осторожное отражение допустимо."
        if policy.allow_reflection
        else "Не добавляй психологическое отражение."
    )

    memory_rule = (
        "Можно использовать только релевантный прошлый контекст."
        if policy.allow_memory_reference
        else "Не упоминай прошлую память пользователя."
    )

    direct_rule = (
        "Сначала дай прямой ответ на запрос."
        if policy.require_direct_answer
        else "Прямой готовый ответ не обязателен."
    )

    validation_rule = (
        "Коротко признай сложность или значимость переживания, "
        "но без шаблонных фраз."
        if policy.require_validation
        else "Не добавляй эмоциональное подтверждение без необходимости."
    )

    if policy.max_questions == 0:
        question_rule = "Не задавай вопросов."
    elif policy.max_questions == 1:
        question_rule = "Допустим максимум один вопрос."
    else:
        question_rule = (
            f"Допустимо не более {policy.max_questions} вопросов."
        )

    ending_rule = (
        "Ответ должен закончиться одним уместным вопросом."
        if policy.end_with_question
        else "Не заканчивай ответ вопросом автоматически."
    )

    optional_follow_up_rule = (
        "После основного ответа можно кратко предложить "
        "другой формат или уточнение, но без давления."
        if policy.optional_follow_up
        else "Не добавляй предложение продолжить разговор."
    )

    consent_rule = (
        "Перед упражнением обязательно получи согласие пользователя."
        if policy.require_user_consent_before_exercise
        else "Упражнение можно предложить без отдельного согласия."
    )

    forbidden = "\n".join(
        f"- {item}"
        for item in policy.forbidden_behaviors
    )

    return f"""
РЕЖИМ ОТВЕТА: {policy.mode}

ЦЕЛЬ:
{policy.goal}

ЖЁСТКИЕ ОГРАНИЧЕНИЯ:

- Ответ должен содержать от {policy.min_sentences}
  до {policy.max_sentences} предложений.
- {question_rule}
- {advice_rule}
- {exercise_rule}
- {reflection_rule}
- {memory_rule}
- {direct_rule}
- {validation_rule}
- {ending_rule}
- {optional_follow_up_rule}
- {consent_rule}

ЗАПРЕЩЕНО:

{forbidden}

ПЕРЕД ОТПРАВКОЙ ПРОВЕРЬ:

1. Ответ соответствует реальному запросу?
2. Нет ли лишнего психологического анализа?
3. Не добавлен ли ненужный вопрос?
4. Нет ли шаблонной фразы?
5. Не сделан ли вывод без достаточного контекста?
6. Не предполагается ли пол пользователя?
7. Не смешаны ли формальный и неформальный стили?
8. Соблюдён ли лимит вопросов?
9. Соблюдена ли допустимая длина?
10. Нет ли совета там, где он запрещён?

Если хотя бы одно ограничение нарушено,
перепиши ответ до отправки.
""".strip()
