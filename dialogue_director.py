import re
from dataclasses import dataclass

from response_policy import ResponsePolicy
from router import Route


@dataclass(frozen=True)
class DirectorResult:
    """
    Решение Dialogue Director.

    approved:
        Можно ли отправить ответ пользователю.

    violations:
        Какие ошибки обнаружены в ходе разговора.

    rewrite_instruction:
        Как именно нужно перестроить ответ.
    """

    approved: bool
    violations: tuple[str, ...]
    rewrite_instruction: str


def normalize_text(text: str) -> str:
    """
    Нормализует текст для проверок.
    """

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
    """
    Проверяет наличие хотя бы одного маркера.
    """

    return any(
        marker in text
        for marker in markers
    )


def evaluate_dialogue_direction(
    user_message: str,
    response_text: str,
    route: Route,
    policy: ResponsePolicy,
) -> DirectorResult:
    """
    Проверяет, соответствует ли ответ правильному
    направлению разговора.

    Response Critic проверяет форму ответа.
    Dialogue Director проверяет выбранное действие:
    ответ, совет, исследование, вопрос или план.
    """

    normalized_user = normalize_text(
        user_message
    )

    normalized_response = normalize_text(
        response_text
    )

    violations: list[str] = []
    rewrite_rules: list[str] = []

    # ---------------------------------------------------------------
    # PRACTICAL TASK
    # ---------------------------------------------------------------

    if route == Route.PRACTICAL_TASK:
        advice_before_result_markers = (
            "для начала подумай",
            "сначала разберись",
            "важно понять свои чувства",
            "попробуй разобраться",
            "прежде чем писать",
        )

        if contains_any(
            normalized_response,
            advice_before_result_markers,
        ):
            violations.append(
                "practical_task_not_completed_directly"
            )

            rewrite_rules.append(
                "Сразу выполни практическую задачу пользователя. "
                "Не добавляй психологический анализ до готового результата."
            )

        awkward_business_markers = (
            "замена моего присутствия",
            "замену моего присутствия",
            "переносы задач",
            "распределить задачи между коллегами",
            "обсудить детали и планы по замене",
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
                "Используй естественный деловой язык. "
                "Для сообщения начальнику достаточно сообщить об отсутствии, "
                "кратко извиниться за предупреждение и при необходимости "
                "указать, что пользователь будет на связи."
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
                "Не используй формы, указывающие на пол пользователя."
            )

        if response_text.strip().endswith("?"):
            violations.append(
                "unnecessary_follow_up_question"
            )

            rewrite_rules.append(
                "Верни готовый результат и не заканчивай ответ вопросом."
            )

    # ---------------------------------------------------------------
    # EMOTIONAL DISCLOSURE
    # ---------------------------------------------------------------

    if route == Route.EMOTIONAL_DISCLOSURE:
        generic_validation_markers = (
            "твое беспокойство понятно",
            "твоё беспокойство понятно",
            "твои переживания понятны",
            "твои чувства важны",
            "это естественно",
            "это совершенно нормально",
            "понимаю, как сложно",
            "понимаю, что тебе сложно",
        )

        if contains_any(
            normalized_response,
            generic_validation_markers,
        ):
            violations.append(
                "generic_emotional_validation"
            )

            rewrite_rules.append(
                "Замени общую шаблонную поддержку на короткое отражение "
                "конкретного смысла сообщения пользователя."
            )

        premature_advice_markers = (
            "важно позволить себе",
            "стоит заранее",
            "попробуй",
            "тебе нужно",
            "следует",
            "лучше",
            "необходимо",
            "подготовиться морально",
            "подготовиться физически",
            "продумать, как ты будешь справляться",
            "продумать как ты будешь справляться",
        )

        if contains_any(
            normalized_response,
            premature_advice_markers,
        ):
            violations.append(
                "premature_emotional_advice"
            )

            rewrite_rules.append(
                "Не давай советов и не предлагай подготовку. "
                "Сначала помоги уточнить, чего именно боится пользователь."
            )

        if "?" not in response_text:
            violations.append(
                "missing_specific_exploration"
            )

            rewrite_rules.append(
                "Задай один конкретный вопрос, который поможет понять, "
                "что именно пугает пользователя."
            )

        vague_question_markers = (
            "что тебя тревожит",
            "что тебя беспокоит",
            "можешь рассказать подробнее",
            "хочешь поговорить об этом",
        )

        if contains_any(
            normalized_response,
            vague_question_markers,
        ):
            violations.append(
                "question_too_vague"
            )

            rewrite_rules.append(
                "Сделай вопрос конкретнее. Например, помоги различить: "
                "пугает определённый человек, ожидаемая ситуация "
                "или само возвращение на работу."
            )

    # ---------------------------------------------------------------
    # DECISION SUPPORT
    # ---------------------------------------------------------------

    if route == Route.DECISION_SUPPORT:
        generic_decision_markers = (
            "плюсы и минусы",
            "за и против",
            "прислушайся к себе",
            "истинные желания",
            "внутреннее состояние",
            "хорошо подумай",
            "взвесь все",
            "взвесь всё",
            "подумай о причинах",
        )

        if contains_any(
            normalized_response,
            generic_decision_markers,
        ):
            violations.append(
                "generic_decision_method"
            )

            rewrite_rules.append(
                "Не предлагай список плюсов и минусов и не давай "
                "универсальное домашнее задание. "
                "Помоги определить один главный критерий выбора."
            )

        if "?" not in response_text:
            violations.append(
                "missing_decision_question"
            )

            rewrite_rules.append(
                "Задай один точный вопрос о главном критерии решения."
            )

        decision_question_markers = (
            "что должно измениться",
            "что удерживает",
            "что заставляет остаться",
            "что заставляет уйти",
            "какая причина",
            "какой фактор",
            "какое условие",
        )

        if (
            "?" in response_text
            and not contains_any(
                normalized_response,
                decision_question_markers,
            )
        ):
            violations.append(
                "decision_question_not_focused"
            )

            rewrite_rules.append(
                "Вопрос должен выявлять главный критерий: "
                "что удерживает пользователя, что подталкивает уйти "
                "или что должно измениться, чтобы остаться."
            )

        decision_commands = (
            "увольняйся",
            "оставайся",
            "тебе нужно уйти",
            "тебе нужно остаться",
            "лучше уволиться",
            "лучше остаться",
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
    # REFLECTION REQUEST
    # ---------------------------------------------------------------

    if route == Route.REFLECTION_REQUEST:
        unsupported_interpretations = (
            "это связано с детством",
            "это из-за детства",
            "у тебя травма",
            "на самом деле ты",
            "ты боишься близости",
            "ты боишься отвержения",
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
                "Не сообщай готовую психологическую причину. "
                "Представь её как одну возможную гипотезу "
                "или задай один проверяющий вопрос."
            )

        if response_text.count("?") > 1:
            violations.append(
                "too_many_reflection_questions"
            )

            rewrite_rules.append(
                "Оставь только один наиболее полезный вопрос."
            )

    # ---------------------------------------------------------------
    # ACKNOWLEDGEMENT
    # ---------------------------------------------------------------

    if route == Route.ACKNOWLEDGEMENT:
        short_word_analysis_markers = (
            "ты подчеркиваешь",
            "ты подчёркиваешь",
            "интонация",
            "это свидетельствует",
            "это говорит о",
            "эмоции особенно интенсивны",
            "дважды подтверждаешь",
        )

        if contains_any(
            normalized_response,
            short_word_analysis_markers,
        ):
            violations.append(
                "short_reply_overinterpreted"
            )

            rewrite_rules.append(
                "Не анализируй короткое слово. "
                "Продолжи предыдущую тему естественно и кратко."
            )

    # ---------------------------------------------------------------
    # Общая проверка соответствия пользовательскому запросу
    # ---------------------------------------------------------------

    if route == Route.PRACTICAL_TASK:
        practical_user_markers = (
            "напиши",
            "составь",
            "перепиши",
            "помоги написать",
        )

        if contains_any(
            normalized_user,
            practical_user_markers,
        ):
            result_markers = (
                "здравствуйте",
                "добрый день",
                "уважаемый",
                "уважаемая",
                ">",
                "«",
            )

            if not contains_any(
                normalized_response,
                result_markers,
            ):
                violations.append(
                    "missing_practical_result"
                )

                rewrite_rules.append(
                    "Верни готовый текст, который пользователь сможет "
                    "сразу скопировать и отправить."
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
