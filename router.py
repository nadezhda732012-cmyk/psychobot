import re
from dataclasses import dataclass
from enum import Enum


class Route(str, Enum):
    """
    Возможные маршруты пользовательского сообщения.
    """

    GREETING = "greeting"
    GRATITUDE = "gratitude"
    GOODBYE = "goodbye"
    ACKNOWLEDGEMENT = "acknowledgement"

    PRACTICAL_TASK = "practical_task"
    FACTUAL_QUESTION = "factual_question"
    DECISION_SUPPORT = "decision_support"
    REFLECTION_REQUEST = "reflection_request"
    EMOTIONAL_DISCLOSURE = "emotional_disclosure"

    CRISIS_SIGNAL = "crisis_signal"
    GENERAL = "general"


@dataclass(frozen=True)
class RouterResult:
    """
    Результат работы Router.
    """

    route: Route
    confidence: float
    needs_model: bool
    needs_history: bool
    needs_safety: bool
    reason: str


# -------------------------------------------------------------------
# Словари и фразы
# -------------------------------------------------------------------

GREETING_PHRASES = {
    "привет",
    "здравствуй",
    "здравствуйте",
    "доброе утро",
    "добрый день",
    "добрый вечер",
    "хай",
    "hello",
    "приветик",
    "ку",
}


GRATITUDE_PHRASES = {
    "спасибо",
    "благодарю",
    "спасибо большое",
    "большое спасибо",
    "огромное спасибо",
    "спасибочки",
}


GOODBYE_PHRASES = {
    "пока",
    "до свидания",
    "до встречи",
    "спокойной ночи",
    "всего доброго",
    "всё пока",
    "все пока",
}


ACKNOWLEDGEMENT_PHRASES = {
    "да",
    "нет",
    "понятно",
    "ясно",
    "хорошо",
    "ок",
    "окей",
    "ага",
    "угу",
    "ладно",
    "возможно",
    "наверное",
    "согласна",
    "согласен",
}


CRISIS_PHRASES = {
    "хочу умереть",
    "не хочу жить",
    "убить себя",
    "покончить с собой",
    "причинить себе вред",
    "навредить себе",
    "расстаться с жизнью",
    "у меня есть план как умереть",
    "у меня есть план покончить с собой",
}


PRACTICAL_MARKERS = (
    "напиши сообщение",
    "составь сообщение",
    "помоги написать",
    "помоги составить",
    "перепиши",
    "исправь текст",
    "что ответить",
    "как ответить",
    "как написать",
    "составь письмо",
    "напиши письмо",
    "придумай текст",
    "подготовь сообщение",
)


DECISION_MARKERS = (
    "не знаю, стоит ли",
    "не знаю стоит ли",
    "что выбрать",
    "как выбрать",
    "увольняться или",
    "расставаться или",
    "разводиться или",
    "переезжать или",
    "соглашаться или",
    "остаться или",
    "уйти или",
    "что мне решить",
    "помоги принять решение",
)


REFLECTION_MARKERS = (
    "почему я",
    "что со мной",
    "не понимаю себя",
    "помоги разобраться в себе",
    "помоги понять себя",
    "почему со мной",
    "почему я всегда",
    "почему я постоянно",
    "почему мне сложно",
    "почему мне трудно",
    "что я чувствую",
    "не могу понять свои чувства",
)


EMOTIONAL_MARKERS = (
    "мне плохо",
    "мне тяжело",
    "мне страшно",
    "мне грустно",
    "мне больно",
    "я устала",
    "я устал",
    "я тревожусь",
    "я переживаю",
    "я злюсь",
    "я плачу",
    "я расстроена",
    "я расстроен",
    "я раздражена",
    "я раздражен",
    "я в отчаянии",
    "я растеряна",
    "я растерян",
    "ничего не хочется",
    "нет сил",
    "всё достало",
    "все достало",
)


FACTUAL_MARKERS = (
    "что такое",
    "кто такой",
    "кто такая",
    "когда произошло",
    "где находится",
    "как работает",
    "что означает",
    "чем отличается",
    "сколько",
    "какой год",
    "какая дата",
)


# -------------------------------------------------------------------
# Вспомогательные функции
# -------------------------------------------------------------------

def normalize_message(text: str) -> str:
    """
    Приводит сообщение к форме, удобной для классификации.
    """

    normalized = text.lower().strip()

    normalized = normalized.replace("ё", "е")

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"[!?.,:;…]+$",
        "",
        normalized,
    )

    return normalized.strip()


def matches_exact_phrase(
    normalized_text: str,
    phrases: set[str],
) -> bool:
    """
    Проверяет точное совпадение с одной из коротких фраз.
    """

    return normalized_text in phrases


def contains_marker(
    normalized_text: str,
    markers: tuple[str, ...],
) -> bool:
    """
    Проверяет наличие одного из смысловых маркеров.
    """

    return any(
        marker in normalized_text
        for marker in markers
    )


def contains_crisis_signal(
    normalized_text: str,
) -> bool:
    """
    Выполняет предварительную проверку явных кризисных фраз.

    Это не полноценный Safety Engine.
    """

    return any(
        phrase in normalized_text
        for phrase in CRISIS_PHRASES
    )


# -------------------------------------------------------------------
# Главная функция Router
# -------------------------------------------------------------------

def classify_message(
    text: str,
    has_history: bool = False,
) -> RouterResult:
    """
    Определяет основной маршрут пользовательского сообщения.

    Router не ставит диагнозы и не анализирует личность.
    Он только выбирает тип дальнейшей обработки.
    """

    normalized = normalize_message(text)

    if not normalized:
        return RouterResult(
            route=Route.GENERAL,
            confidence=1.0,
            needs_model=False,
            needs_history=False,
            needs_safety=False,
            reason="Пустое сообщение",
        )

    # 1. Безопасность всегда имеет наивысший приоритет.
    if contains_crisis_signal(normalized):
        return RouterResult(
            route=Route.CRISIS_SIGNAL,
            confidence=0.98,
            needs_model=False,
            needs_history=True,
            needs_safety=True,
            reason="Обнаружена явная кризисная формулировка",
        )

    # 2. Короткие служебные сообщения.
    if matches_exact_phrase(
        normalized,
        GREETING_PHRASES,
    ):
        return RouterResult(
            route=Route.GREETING,
            confidence=0.99,
            needs_model=False,
            needs_history=False,
            needs_safety=False,
            reason="Короткое приветствие",
        )

    if matches_exact_phrase(
        normalized,
        GRATITUDE_PHRASES,
    ):
        return RouterResult(
            route=Route.GRATITUDE,
            confidence=0.99,
            needs_model=False,
            needs_history=False,
            needs_safety=False,
            reason="Короткая благодарность",
        )

    if matches_exact_phrase(
        normalized,
        GOODBYE_PHRASES,
    ):
        return RouterResult(
            route=Route.GOODBYE,
            confidence=0.99,
            needs_model=False,
            needs_history=False,
            needs_safety=False,
            reason="Завершение разговора",
        )

    if matches_exact_phrase(
        normalized,
        ACKNOWLEDGEMENT_PHRASES,
    ):
        return RouterResult(
            route=Route.ACKNOWLEDGEMENT,
            confidence=0.96,
            needs_model=has_history,
            needs_history=has_history,
            needs_safety=False,
            reason=(
                "Короткий ответ, который необходимо "
                "интерпретировать только в контексте"
            ),
        )

    # 3. Практическая задача имеет приоритет над психологическим
    # анализом, если пользователь просит создать конкретный текст.
    if contains_marker(
        normalized,
        PRACTICAL_MARKERS,
    ):
        return RouterResult(
            route=Route.PRACTICAL_TASK,
            confidence=0.94,
            needs_model=True,
            needs_history=True,
            needs_safety=False,
            reason="Пользователь просит выполнить практическую задачу",
        )

    # 4. Помощь с выбором.
    if contains_marker(
        normalized,
        DECISION_MARKERS,
    ):
        return RouterResult(
            route=Route.DECISION_SUPPORT,
            confidence=0.91,
            needs_model=True,
            needs_history=True,
            needs_safety=False,
            reason="Пользователь просит помочь с решением",
        )

    # 5. Явная просьба разобраться в себе.
    if contains_marker(
        normalized,
        REFLECTION_MARKERS,
    ):
        return RouterResult(
            route=Route.REFLECTION_REQUEST,
            confidence=0.91,
            needs_model=True,
            needs_history=True,
            needs_safety=False,
            reason="Пользователь просит о саморефлексии",
        )

    # 6. Описание эмоционального состояния.
    if contains_marker(
        normalized,
        EMOTIONAL_MARKERS,
    ):
        return RouterResult(
            route=Route.EMOTIONAL_DISCLOSURE,
            confidence=0.88,
            needs_model=True,
            needs_history=True,
            needs_safety=True,
            reason="Пользователь сообщает об эмоциональном состоянии",
        )

    # 7. Фактический вопрос.
    if contains_marker(
        normalized,
        FACTUAL_MARKERS,
    ):
        return RouterResult(
            route=Route.FACTUAL_QUESTION,
            confidence=0.86,
            needs_model=True,
            needs_history=False,
            needs_safety=False,
            reason="Пользователь задаёт информационный вопрос",
        )

    # 8. Общий маршрут.
    return RouterResult(
        route=Route.GENERAL,
        confidence=0.55,
        needs_model=True,
        needs_history=has_history,
        needs_safety=True,
        reason="Не найдено достаточно признаков специального маршрута",
    )
