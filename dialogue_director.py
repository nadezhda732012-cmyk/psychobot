import re
from dataclasses import dataclass

from conversation_planner import ConversationPlan
from response_policy import ResponsePolicy
from router import Route


@dataclass(frozen=True)
class DirectorResult:
    """
    Результат проверки направления разговора.
    """

    approved: bool
    violations: tuple[str, ...]
    rewrite_instruction: str


def normalize_text(text: str) -> str:
    normalized = text.lower().replace("ё", "е")

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


def contains_any(
    text: str,
    markers: tuple[str, ...],
) -> bool:
    return any(
        marker in text
        for marker in markers
    )


def evaluate_dialogue_direction(
    user_message: str,
    response_text: str,
    route: Route,
    policy: ResponsePolicy,
    conversation_plan: ConversationPlan,
) -> DirectorResult:
    """
    Проверяет соответствие ответа плану разговора.

    Response Critic проверяет форму.
    Dialogue Director проверяет ход и цель.
    """

    normalized_user = normalize_text(
        user_message
    )

    normalized_response = normalize_text(
        response_text
    )

    violations: list[str] = []
    rewrite_rules: list[str] = []

    questions_count = response_text.count("?")

    if questions_count > conversation_plan.max_questions:
        violations.append(
            "plan_question_limit_exceeded"
        )

        rewrite_rules.append(
            f"Оставь не более "
            f"{conversation_plan.max_questions} вопроса."
        )

    # ---------------------------------------------------------------
    # Практическая задача
    # ---------------------------------------------------------------

    if route == Route.PRACTICAL_TASK:
        unsupported_details = (
            "прилагаю объяснительную",
            "объяснительная прилагается",
            "прилагаю справку",
            "медицинская справка",
            "по согласованию с",
            "замену сотрудника",
            "замену моего присутствия",
            "переносы задач",
            "распределить задачи между коллегами",
            "обсудить возможную замену",
        )

        if contains_any(
            normalized_response,
            unsupported_details,
        ):
            violations.append(
                "invented_practical_details"
            )

            rewrite_rules.append(
                "Удали все обстоятельства, документы и договорённости, "
                "которых пользователь не сообщал."
            )

        awkward_business_markers = (
            "замена моего присутствия",
            "переносы задач",
            "компенсировать мое отсутствие",
            "компенсировать моё отсутствие",
        )

        if contains_any(
            normalized_response,
            awkward_business_markers,
        ):
            violations.append(
                "unnatural_practical_wording"
            )

            rewrite_rules.append(
                "Используй простой и естественный деловой язык."
            )

        gender_markers = (
            "я готов ",
            "я готова ",
            "буду рад",
            "буду рада",
            "благодарен",
            "благодарна",
        )

        if contains_any(
            normalized_response,
            gender_markers,
        ):
            violations.append(
                "gender_assumption"
            )

            rewrite_rules.append(
                "Используй гендерно-нейтральную формулировку."
            )

        if response_text.strip().endswith("?"):
            violations.append(
                "unnecessary_practical_question"
            )

            rewrite_rules.append(
                "Не заканчивай готовый практический результат вопросом."
            )

        practical_result_markers = (
            "здравствуйте",
            "добрый день",
            "уважаемый",
            "уважаемая",
            "сегодня не смогу",
            "сегодня я не смогу",
        )

        if not contains_any(
            normalized_response,
            practical_result_markers,
        ):
            violations.append(
                "missing_ready_practical_result"
            )

            rewrite_rules.append(
                "Верни готовый текст, который можно сразу отправить."
            )

    # ---------------------------------------------------------------
    # Эмоциональное сообщение
    # ---------------------------------------------------------------

    if route == Route.EMOTIONAL_DISCLOSURE:
        generic_validation = (
            "понятно, ситуация непростая",
            "твое беспокойство понятно",
            "твоё беспокойство понятно",
            "твои переживания понятны",
            "твои чувства важны",
            "это естественно",
            "это нормально",
            "понимаю, как сложно",
        )

        if contains_any(
            normalized_response,
            generic_validation,
        ):
            violations.append(
                "generic_emotional_opening"
            )

            rewrite_rules.append(
                "Замени общее вступление на отражение конкретного "
                "смысла сообщения пользователя."
            )

        advice_markers = (
            "тебе нужно",
            "вам нужно",
            "попробуй",
            "попробуйте",
            "стоит заранее",
            "важно позволить себе",
            "следует",
            "необходимо",
            "лучше",
            "подготовиться морально",
            "подготовиться физически",
        )

        if contains_any(
            normalized_response,
            advice_markers,
        ):
            violations.append(
                "advice_before_emotional_clarification"
            )

            rewrite_rules.append(
                "Удали советы. Сейчас задача — уточнить источник переживания."
            )

        if "?" not in response_text:
            violations.append(
                "missing_emotional_question"
            )

            rewrite_rules.append(
                "Добавь один конкретный вопрос об источнике переживания."
            )

        vague_questions = (
            "что тебя тревожит",
            "что тебя беспокоит",
            "можешь рассказать подробнее",
            "хочешь поговорить об этом",
        )

        if contains_any(
            normalized_response,
            vague_questions,
        ):
            violations.append(
                "emotional_question_too_vague"
            )

            rewrite_rules.append(
                "Уточни вопрос: речь о конкретном человеке, "
                "ожидаемой ситуации или самом возвращении."
            )

    # ---------------------------------------------------------------
    # Принятие решения
    # ---------------------------------------------------------------

    if route == Route.DECISION_SUPPORT:
        generic_decision_methods = (
            "плюсы и минусы",
            "за и против",
            "прислушайся к себе",
            "истинные желания",
            "выпиши",
            "составь список",
            "хорошо подумай",
            "взвесь все",
            "взвесь всё",
        )

        if contains_any(
            normalized_response,
            generic_decision_methods,
        ):
            violations.append(
                "generic_decision_method"
            )

            rewrite_rules.append(
                "Удали универсальное упражнение. "
                "Сосредоточься на одном критерии выбора."
            )

        if "?" not in response_text:
            violations.append(
                "missing_decision_question"
            )

            rewrite_rules.append(
                "Задай один вопрос о главном критерии решения."
            )

        focused_question_markers = (
            "что должно измениться",
            "что удерживает",
            "что подталкивает",
            "что заставляет остаться",
            "что заставляет уйти",
            "какое условие",
            "какой фактор",
            "что будет тяжелее",
            "что для тебя тяжелее",
        )

        if (
            "?" in response_text
            and not contains_any(
                normalized_response,
                focused_question_markers,
            )
        ):
            violations.append(
                "decision_question_not_focused"
            )

            rewrite_rules.append(
                "Сформулируй вопрос вокруг одного критерия: "
                "что удерживает, что подталкивает уйти "
                "или что должно измениться."
            )

        decision_commands = (
            "увольняйся",
            "оставайся",
            "лучше уволиться",
            "лучше остаться",
            "тебе нужно уйти",
            "тебе нужно остаться",
        )

        if contains_any(
            normalized_response,
            decision_commands,
        ):
            violations.append(
                "decision_made_for_user"
            )

            rewrite_rules.append(
                "Не принимай решение за пользователя."
            )

    # ---------------------------------------------------------------
    # Запрос на саморефлексию
    # ---------------------------------------------------------------

    if route == Route.REFLECTION_REQUEST:
        unsupported_interpretations = (
            "это связано с детством",
            "это из-за детства",
            "у тебя травма",
            "на самом деле ты",
            "ты всегда",
            "причина заключается в",
        )

        if contains_any(
            normalized_response,
            unsupported_interpretations,
        ):
            violations.append(
                "premature_psychological_interpretation"
            )

            rewrite_rules.append(
                "Замени готовый вывод на одну осторожную гипотезу "
                "или один проверяющий вопрос."
            )

    # ---------------------------------------------------------------
    # Короткое подтверждение
    # ---------------------------------------------------------------

    if route == Route.ACKNOWLEDGEMENT:
        overinterpretation_markers = (
            "ты подчеркиваешь",
            "ты подчёркиваешь",
            "интонация",
            "это свидетельствует",
            "дважды подтверждаешь",
            "эмоции особенно интенсивны",
        )

        if contains_any(
            normalized_response,
            overinterpretation_markers,
        ):
            violations.append(
                "acknowledgement_overinterpreted"
            )

            rewrite_rules.append(
                "Не анализируй короткое слово. "
                "Продолжи предыдущую тему."
            )

    # ---------------------------------------------------------------
    # Общая проверка плана
    # ---------------------------------------------------------------

    if (
        conversation_plan.should_answer_directly
        and route == Route.PRACTICAL_TASK
        and len(normalized_response) < 15
    ):
        violations.append(
            "direct_result_missing"
        )

        rewrite_rules.append(
            "Дай полноценный готовый результат."
        )

    unique_violations = tuple(
        dict.fromkeys(violations)
    )

    unique_rules = list(
        dict.fromkeys(rewrite_rules)
    )

    rewrite_instruction = "\n".join(
        f"- {rule}"
        for rule in unique_rules
    )

    return DirectorResult(
        approved=not unique_violations,
        violations=unique_violations,
        rewrite_instruction=rewrite_instruction,
    )
