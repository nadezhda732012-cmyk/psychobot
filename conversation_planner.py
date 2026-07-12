from dataclasses import dataclass

from router import Route


@dataclass(frozen=True)
class ConversationPlan:
    """
    План следующего шага разговора.

    action:
        Какое действие должен выполнить ответ.

    goal:
        Какого результата должен достичь текущий ответ.

    question_focus:
        О чём можно задать вопрос.

    must_include:
        Что обязательно должно присутствовать.

    must_avoid:
        Чего в ответе быть не должно.
    """

    action: str
    goal: str
    question_focus: str | None

    must_include: tuple[str, ...]
    must_avoid: tuple[str, ...]

    max_questions: int
    should_answer_directly: bool
    should_use_history: bool


def build_conversation_plan(
    route: Route,
    user_message: str,
    has_history: bool,
) -> ConversationPlan:
    """
    Создаёт план следующего ответа.

    Planner не пишет текст пользователю.
    Он определяет цель и правильный ход разговора.
    """

    if route == Route.GREETING:
        return ConversationPlan(
            action="greet",
            goal="Коротко поздороваться.",
            question_focus=None,
            must_include=(
                "Короткое естественное приветствие.",
            ),
            must_avoid=(
                "Психологический анализ.",
                "Длинное вступление.",
            ),
            max_questions=0,
            should_answer_directly=True,
            should_use_history=False,
        )

    if route == Route.GRATITUDE:
        return ConversationPlan(
            action="accept_gratitude",
            goal="Коротко принять благодарность.",
            question_focus=None,
            must_include=(
                "Короткий естественный ответ.",
            ),
            must_avoid=(
                "Анализ благодарности.",
                "Рассуждения о внутренней гармонии.",
                "Попытку продолжить разговор.",
            ),
            max_questions=0,
            should_answer_directly=True,
            should_use_history=False,
        )

    if route == Route.GOODBYE:
        return ConversationPlan(
            action="close_conversation",
            goal="Спокойно завершить разговор.",
            question_focus=None,
            must_include=(
                "Короткое завершение.",
            ),
            must_avoid=(
                "Попытку удержать пользователя.",
                "Вопрос.",
                "Фразу о том, что ИИ будет ждать.",
            ),
            max_questions=0,
            should_answer_directly=True,
            should_use_history=False,
        )

    if route == Route.ACKNOWLEDGEMENT:
        return ConversationPlan(
            action="continue_context",
            goal=(
                "Продолжить предыдущую тему, "
                "не анализируя короткое слово."
            ),
            question_focus=(
                "Только предыдущая тема разговора."
                if has_history
                else None
            ),
            must_include=(
                "Естественную реакцию на контекст.",
            ),
            must_avoid=(
                "Анализ слова «да», «нет» или «хорошо».",
                "Выводы об интонации.",
                "Новую тему без связи с контекстом.",
            ),
            max_questions=1 if has_history else 0,
            should_answer_directly=not has_history,
            should_use_history=has_history,
        )

    if route == Route.PRACTICAL_TASK:
        return ConversationPlan(
            action="deliver_ready_result",
            goal=(
                "Дать готовый результат, который пользователь "
                "может сразу использовать."
            ),
            question_focus=None,
            must_include=(
                "Готовый текст или конкретное решение.",
                "Только сведения, которые сообщил пользователь.",
                "Естественный язык.",
            ),
            must_avoid=(
                "Психологический анализ.",
                "Выдуманные документы, причины или договорённости.",
                "Указание пола пользователя.",
                "Лишний вопрос после готового результата.",
                "Канцелярские формулировки.",
            ),
            max_questions=0,
            should_answer_directly=True,
            should_use_history=True,
        )

    if route == Route.FACTUAL_QUESTION:
        return ConversationPlan(
            action="answer_factually",
            goal="Дать прямой ответ на информационный вопрос.",
            question_focus=None,
            must_include=(
                "Ответ по существу.",
            ),
            must_avoid=(
                "Психологическую интерпретацию.",
                "Поиск скрытого запроса.",
                "Необязательный вопрос.",
            ),
            max_questions=0,
            should_answer_directly=True,
            should_use_history=False,
        )

    if route == Route.EMOTIONAL_DISCLOSURE:
        return ConversationPlan(
            action="clarify_emotional_source",
            goal=(
                "Помочь понять конкретный источник "
                "или объект переживания."
            ),
            question_focus=(
                "Что именно в ситуации вызывает страх, "
                "боль, тревогу или напряжение."
            ),
            must_include=(
                "Короткое отражение конкретного смысла сообщения.",
                "Один конкретный вопрос.",
            ),
            must_avoid=(
                "Советы.",
                "Упражнения.",
                "Общие слова о важности чувств.",
                "Универсальную валидацию.",
                "Несколько вопросов.",
            ),
            max_questions=1,
            should_answer_directly=False,
            should_use_history=True,
        )

    if route == Route.DECISION_SUPPORT:
        return ConversationPlan(
            action="identify_decision_criterion",
            goal=(
                "Помочь определить один главный критерий "
                "или конфликт решения."
            ),
            question_focus=(
                "Что удерживает пользователя, "
                "что подталкивает уйти или "
                "что должно измениться, чтобы остаться."
            ),
            must_include=(
                "Короткое обозначение конфликта выбора.",
                "Один точный вопрос о главном критерии.",
            ),
            must_avoid=(
                "Решение за пользователя.",
                "Список плюсов и минусов.",
                "Общее домашнее задание.",
                "Фразу «прислушайся к себе».",
                "Несколько вопросов.",
            ),
            max_questions=1,
            should_answer_directly=False,
            should_use_history=True,
        )

    if route == Route.REFLECTION_REQUEST:
        return ConversationPlan(
            action="test_one_hypothesis",
            goal=(
                "Помочь пользователю проверить одну "
                "возможную закономерность."
            ),
            question_focus=(
                "Конкретная ситуация, мысль или ожидаемое последствие."
            ),
            must_include=(
                "Не более одной осторожной гипотезы "
                "или одного проверяющего вопроса.",
            ),
            must_avoid=(
                "Готовую психологическую причину.",
                "Диагноз.",
                "Объяснение всего детством.",
                "Формулировки «ты всегда».",
                "Несколько гипотез одновременно.",
            ),
            max_questions=1,
            should_answer_directly=False,
            should_use_history=True,
        )

    if route == Route.CRISIS_SIGNAL:
        return ConversationPlan(
            action="check_immediate_safety",
            goal="Уточнить непосредственную опасность.",
            question_focus=(
                "Есть ли намерение, план или непосредственная опасность."
            ),
            must_include=(
                "Прямой вопрос о безопасности.",
                "Следующий доступный шаг получения помощи.",
            ),
            must_avoid=(
                "Глубокий анализ.",
                "Длинное упражнение.",
                "Спор.",
                "Осуждение.",
            ),
            max_questions=1,
            should_answer_directly=True,
            should_use_history=True,
        )

    return ConversationPlan(
        action="respond_to_current_request",
        goal=(
            "Ответить на текущий запрос "
            "без лишней психологизации."
        ),
        question_focus=(
            "Только информация, без которой невозможно ответить."
        ),
        must_include=(
            "Релевантный ответ на сообщение пользователя.",
        ),
        must_avoid=(
            "Выдуманные скрытые причины.",
            "Ненужный психологический анализ.",
            "Обязательный вопрос в конце.",
        ),
        max_questions=1,
        should_answer_directly=True,
        should_use_history=has_history,
    )


def plan_to_prompt(
    plan: ConversationPlan,
) -> str:
    """
    Преобразует план в инструкцию для модели.
    """

    must_include = "\n".join(
        f"- {item}"
        for item in plan.must_include
    )

    must_avoid = "\n".join(
        f"- {item}"
        for item in plan.must_avoid
    )

    question_focus = (
        plan.question_focus
        if plan.question_focus
        else "Вопрос не требуется."
    )

    return f"""
ПЛАН СЛЕДУЮЩЕГО ШАГА

ДЕЙСТВИЕ:
{plan.action}

ЦЕЛЬ:
{plan.goal}

ФОКУС ВОПРОСА:
{question_focus}

ОБЯЗАТЕЛЬНО ВКЛЮЧИТЬ:
{must_include}

НЕ ДОПУСКАТЬ:
{must_avoid}

ДОПОЛНИТЕЛЬНЫЕ ОГРАНИЧЕНИЯ:

- Максимум вопросов: {plan.max_questions}.
- Прямой ответ требуется: {
    "да" if plan.should_answer_directly else "нет"
}.
- Использовать историю разговора: {
    "да" if plan.should_use_history else "нет"
}.

Не меняй цель ответа.
Не добавляй второй шаг разговора.
Выполни только этот план.
""".strip()
