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
        goal="Продолжить предыдущий контекст без анализа короткого слова.",
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
        forbidden_behaviors=COMMON_FORBIDDEN_BEHAVIORS,
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
        ),
    ),

    Route.DECISION_SUPPORT: ResponsePolicy(
        mode="decision_support",
        goal="Помочь пользователю рассмотреть решение, не принимая его за него.",
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
        ),
    ),

    Route.REFLECTION_REQUEST: ResponsePolicy(
        mode="reflection_request",
        goal="Помочь исследовать ситуацию без навязывания готовой причины.",
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
        ),
    ),

    Route.EMOTIONAL_DISCLOSURE: ResponsePolicy(
        mode="emotional_disclosure",
        goal="Сначала дать человеку почувствовать, что его услышали.",
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
            "Не обещать абсолютную конфиденциальность или постоянное присутствие.",
        ),
    ),

    Route.GENERAL: ResponsePolicy(
        mode="general",
        goal="Ответить на реальный запрос без лишней психологизации.",
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
        forbidden_behaviors=COMMON_FORBIDDEN_BEHAVIORS,
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
    Преобразует объект политики в инструкцию для языковой модели.
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
        "Можно использовать релевантный прошлый контекст."
        if policy.allow_memory_reference
        else "Не упоминай прошлую память пользователя."
    )

    direct_rule = (
        "Сначала дай прямой ответ на запрос."
        if policy.require_direct_answer
        else "Прямой готовый ответ не обязателен."
    )

    validation_rule = (
        "Коротко признай значимость или сложность переживания."
        if policy.require_validation
        else "Не добавляй эмоциональное подтверждение без необходимости."
    )

    question_rule = (
        f"Допустимо не более {policy.max_questions} вопроса."
        if policy.max_questions > 0
        else "Не задавай вопросов."
    )

    ending_rule = (
        "Ответ может закончиться одним вопросом."
        if policy.end_with_question
        else "Не заканчивай ответ вопросом автоматически."
    )

    optional_follow_up_rule = (
        "После основного ответа можно кратко предложить альтернативный формат, "
        "но без обязательного вопроса."
        if policy.optional_follow_up
        else "Не добавляй предложение продолжить разговор."
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

ЗАПРЕЩЕНО:

{forbidden}

Проверь ответ перед отправкой.
Если ответ нарушает ограничения, перепиши его.
""".strip()
