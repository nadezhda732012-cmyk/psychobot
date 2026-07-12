import re
from dataclasses import dataclass

from response_policy import ResponsePolicy
from router import Route


@dataclass(frozen=True)
class CriticResult:
    """
    Результат проверки черновика ответа.
    """

    passed: bool
    violations: tuple[str, ...]


def count_questions(text: str) -> int:
    """
    Считает количество вопросительных знаков.
    """

    return text.count("?")


def count_sentences(text: str) -> int:
    """
    Приблизительно считает количество предложений.

    Для MVP этого достаточно.
    """

    cleaned_text = text.strip()

    if not cleaned_text:
        return 0

    parts = re.split(
        r"(?<=[.!?])\s+",
        cleaned_text,
    )

    sentences = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    return max(
        1,
        len(sentences),
    )


def contains_forbidden_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Проверяет наличие запрещённой фразы
    без учёта регистра и буквы ё.
    """

    normalized_text = (
        text.lower()
        .replace("ё", "е")
    )

    normalized_phrase = (
        phrase.lower()
        .replace("ё", "е")
    )

    return normalized_phrase in normalized_text


def evaluate_response(
    response_text: str,
    route: Route,
    policy: ResponsePolicy,
) -> CriticResult:
    """
    Проверяет черновик ответа по правилам
    выбранного маршрута и Response Policy.

    Critic не изменяет текст самостоятельно.
    Он возвращает список нарушений.
    """

    violations: list[str] = []

    stripped_text = response_text.strip()
    normalized_text = (
        stripped_text.lower()
        .replace("ё", "е")
    )

    if not stripped_text:
        return CriticResult(
            passed=False,
            violations=("empty_response",),
        )

    # ---------------------------------------------------------------
    # Проверка количества вопросов
    # ---------------------------------------------------------------

    questions_count = count_questions(
        stripped_text
    )

    if questions_count > policy.max_questions:
        violations.append(
            "too_many_questions"
        )

    # ---------------------------------------------------------------
    # Проверка длины
    # ---------------------------------------------------------------

    sentences_count = count_sentences(
        stripped_text
    )

    # Даём модели небольшой запас в одно предложение,
    # потому что подсчёт предложений приблизительный.
    if sentences_count > policy.max_sentences + 1:
        violations.append(
            "response_too_long"
        )

    # Слишком короткий ответ проверяем только
    # для содержательных режимов.
    if (
        sentences_count < policy.min_sentences
        and route
        not in {
            Route.GREETING,
            Route.GRATITUDE,
            Route.GOODBYE,
            Route.ACKNOWLEDGEMENT,
        }
    ):
        violations.append(
            "response_too_short"
        )

    # ---------------------------------------------------------------
    # Запрещённые формулировки из политики
    # ---------------------------------------------------------------

    for forbidden_behavior in policy.forbidden_behaviors:
        # В forbidden_behaviors находятся инструкции,
        # а не всегда буквальные цитаты.
        # Поэтому отдельно проверяем только узнаваемые фразы.
        quoted_phrases = re.findall(
            r"«([^»]+)»",
            forbidden_behavior,
        )

        for phrase in quoted_phrases:
            if contains_forbidden_phrase(
                stripped_text,
                phrase,
            ):
                violations.append(
                    f"forbidden_phrase:{phrase}"
                )

    # ---------------------------------------------------------------
    # Общие шаблонные фразы
    # ---------------------------------------------------------------

    generic_phrases = (
        "понимаю, как сложно",
        "твои чувства важны и понятны",
        "ваши чувства важны и понятны",
        "все будет хорошо",
        "всё будет хорошо",
        "ты сильнее, чем думаешь",
        "это первый шаг к внутренней гармонии",
        "я всегда рядом",
        "твоя благодарность очень ценна",
        "истинные желания",
    )

    for phrase in generic_phrases:
        if contains_forbidden_phrase(
            stripped_text,
            phrase,
        ):
            violations.append(
                f"generic_phrase:{phrase}"
            )

    # ---------------------------------------------------------------
    # Практическая задача
    # ---------------------------------------------------------------

    if route == Route.PRACTICAL_TASK:
        if stripped_text.endswith("?"):
            violations.append(
                "practical_task_ends_with_question"
            )

        gender_phrases = (
            "буду рад",
            "буду рада",
            "буду благодарен",
            "буду благодарна",
            "с уважением, ваш",
            "с уважением, ваша",
        )

        for phrase in gender_phrases:
            if phrase in normalized_text:
                violations.append(
                    "gender_assumption"
                )
                break

        awkward_phrases = (
            "замена моего присутствия",
            "по замене моего присутствия",
            "распределить задачи между коллегами",
        )

        for phrase in awkward_phrases:
            if phrase in normalized_text:
                violations.append(
                    "unnatural_business_phrase"
                )
                break

        # Проверка смешивания формального
        # и неформального обращения.
        formal_markers = (
            "уважаемый",
            "уважаемая",
            "здравствуйте",
        )

        informal_markers = (
            "извини",
            "привет",
            "тебе",
            "твой",
        )

        has_formal = any(
            marker in normalized_text
            for marker in formal_markers
        )

        has_informal = any(
            marker in normalized_text
            for marker in informal_markers
        )

        if has_formal and has_informal:
            violations.append(
                "mixed_formal_and_informal_style"
            )

    # ---------------------------------------------------------------
    # Эмоциональное сообщение
    # ---------------------------------------------------------------

    if route == Route.EMOTIONAL_DISCLOSURE:
        if normalized_text.startswith(
            "понимаю"
        ):
            violations.append(
                "generic_empathy_opening"
            )

        if not policy.allow_advice:
            advice_markers = (
                "тебе нужно",
                "вам нужно",
                "попробуй",
                "попробуйте",
                "следует",
                "лучше сделать",
                "необходимо",
            )

            for marker in advice_markers:
                if marker in normalized_text:
                    violations.append(
                        "premature_advice"
                    )
                    break

    # ---------------------------------------------------------------
    # Помощь с решением
    # ---------------------------------------------------------------

    if route == Route.DECISION_SUPPORT:
        generic_decision_markers = (
            "выпиши плюсы и минусы",
            "выписать плюсы и минусы",
            "составь список плюсов и минусов",
            "подумай о плюсах и минусах",
            "прислушайся к себе",
            "истинные желания",
        )

        for marker in generic_decision_markers:
            if marker in normalized_text:
                violations.append(
                    "generic_decision_advice"
                )
                break

        commanding_phrases = (
            "тебе нужно уволиться",
            "тебе нужно остаться",
            "вам нужно уволиться",
            "вам нужно остаться",
            "однозначно увольняйся",
            "однозначно оставайся",
        )

        for phrase in commanding_phrases:
            if phrase in normalized_text:
                violations.append(
                    "decision_made_for_user"
                )
                break

    # ---------------------------------------------------------------
    # Запрос на рефлексию
    # ---------------------------------------------------------------

    if route == Route.REFLECTION_REQUEST:
        unsupported_certainty = (
            "на самом деле ты",
            "это точно связано",
            "причина в твоем детстве",
            "причина в вашем детстве",
            "ты всегда",
            "вы всегда",
        )

        for phrase in unsupported_certainty:
            if phrase in normalized_text:
                violations.append(
                    "unsupported_psychological_conclusion"
                )
                break

    # Удаляем дубликаты, сохраняя порядок.
    unique_violations = tuple(
        dict.fromkeys(violations)
    )

    return CriticResult(
        passed=not unique_violations,
        violations=unique_violations,
    )
