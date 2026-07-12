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
# Короткие служебные сообщения
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


# -------------------------------------------------------------------
# Safety: только явные формулировки
# -------------------------------------------------------------------

CRISIS_PATTERNS = (
    r"\bхочу\s+умереть\b",
    r"\bне\s+хочу\s+жить\b",
    r"\bхочу\s+покончить\s+с\s+собой\b",
    r"\bпокончить\s+с\s+собой\b",
    r"\bубить\s+себя\b",
    r"\bубью\s+себя\b",
    r"\bпричинить\s+себе\s+вред\b",
    r"\bнавредить\s+себе\b",
    r"\bрасстаться\s+с\s+жизнью\b",
    r"\bесть\s+план.{0,30}(умереть|покончить\s+с\s+собой)\b",
    r"\bжизнь\s+не\s+имеет\s+смысла\b",
)

# Фразы, которые сами по себе не должны считаться кризисом.
CRISIS_NEGATIONS = (
    "не хочу умирать",
    "боюсь умереть",
    "не собираюсь умирать",
    "не думаю о самоубийстве",
    "не хочу причинять себе вред",
)


# -------------------------------------------------------------------
# Практические задачи
# -------------------------------------------------------------------

PRACTICAL_PATTERNS = (
    r"\bнапиши\b.{0,40}\b(сообщение|письмо|текст|ответ|пост|заявление)\b",
    r"\bсоставь\b.{0,40}\b(сообщение|письмо|текст|ответ|пост|заявление)\b",
    r"\bпомоги\s+(написать|составить|ответить|сформулировать)\b",
    r"\bперепиши\b",
    r"\bисправь\s+(текст|сообщение|письмо)\b",
    r"\bчто\s+ответить\b",
    r"\bкак\s+(ответить|написать|сформулировать)\b",
    r"\bпридумай\s+(текст|сообщение|ответ|подпись|пост)\b",
    r"\bподготовь\s+(сообщение|письмо|текст|ответ)\b",
    r"\bпереведи\b",
    r"\bсократи\s+(текст|сообщение|письмо)\b",
    r"\bсделай\s+(текст|сообщение|письмо)\b.{0,30}\b(вежлив|мягк|официальн|короче)\b",
)


# -------------------------------------------------------------------
# Решения и выбор
# -------------------------------------------------------------------

DECISION_PATTERNS = (
    # «стоит ли…», «нужно ли…», «может ли быть лучше…»
    r"\bстоит\s+ли\b",
    r"\bнужно\s+ли\s+мне\b",
    r"\bимеет\s+ли\s+смысл\b",
    r"\bкак\s+мне\s+решить\b",
    r"\bпомоги\s+(принять|сделать)\s+решение\b",
    r"\bне\s+могу\s+решить\b",
    r"\bне\s+знаю.{0,25}\b(ли|или)\b",
    r"\bсомневаюсь.{0,25}\b(ли|или)\b",
    r"\bвыбрать\b.{0,35}\bили\b",
    r"\bчто\s+выбрать\b",
    r"\bкак\s+выбрать\b",

    # Глаголы выбора
    r"\bувольняться\b.{0,30}\bили\b",
    r"\bуволиться\b.{0,30}\bили\b",
    r"\bоставаться\b.{0,30}\bили\b",
    r"\bостаться\b.{0,30}\bили\b",
    r"\bуходить\b.{0,30}\bили\b",
    r"\bуйти\b.{0,30}\bили\b",
    r"\bрасставаться\b.{0,30}\bили\b",
    r"\bрасстаться\b.{0,30}\bили\b",
    r"\bразводиться\b.{0,30}\bили\b",
    r"\bпереезжать\b.{0,30}\bили\b",
    r"\bпереехать\b.{0,30}\bили\b",
    r"\bсоглашаться\b.{0,30}\bили\b",
    r"\bсогласиться\b.{0,30}\bили\b",
    r"\bпокупать\b.{0,30}\bили\b",
    r"\bбрать\b.{0,30}\bили\b",
    r"\bпродолжать\b.{0,30}\bили\b",
    r"\bначинать\b.{0,30}\bили\b",

    # Короткие решения без «или»
    r"\bувольняться\s+мне\b",
    r"\bуволиться\s+ли\b",
    r"\bрасставаться\s+ли\b",
    r"\bпереезжать\s+ли\b",
    r"\bсоглашаться\s+ли\b",
    r"\bоставаться\s+ли\b",
    r"\bпрощать\s+ли\b",
)


# -------------------------------------------------------------------
# Саморефлексия
# -------------------------------------------------------------------

REFLECTION_PATTERNS = (
    r"\bпочему\s+я\b",
    r"\bпочему\s+мне\b",
    r"\bпочему\s+со\s+мной\b",
    r"\bчто\s+со\s+мной\b",
    r"\bне\s+понимаю\s+себя\b",
    r"\bпомоги\s+разобраться\s+в\s+себе\b",
    r"\bпомоги\s+понять\s+себя\b",
    r"\bне\s+могу\s+понять\s+свои\s+чувства\b",
    r"\bчто\s+я\s+чувствую\b",
    r"\bоткуда\s+у\s+меня\b",
    r"\bзачем\s+я\b",
    r"\bпочему\s+это\s+со\s+мной\s+происходит\b",
    r"\bпочему\s+я\s+(всегда|постоянно|снова|опять)\b",
)


# -------------------------------------------------------------------
# Эмоциональные сообщения
# -------------------------------------------------------------------

EMOTIONAL_PATTERNS = (
    # Прямое состояние
    r"\bмне\s+(плохо|тяжело|страшно|грустно|больно|тревожно|одиноко|стыдно|пусто)\b",
    r"\bя\s+(устала|устал|тревожусь|переживаю|злюсь|плачу|боюсь)\b",
    r"\bя\s+(расстроена|расстроен|раздражена|раздражен|растеряна|растерян)\b",
    r"\bя\s+в\s+(отчаянии|панике|шоке)\b",
    r"\bчувствую\s+(одиночество|пустоту|тревогу|страх|стыд|вину|злость|бессилие)\b",
    r"\bощущаю\s+(одиночество|пустоту|тревогу|страх|стыд|вину|злость|бессилие)\b",

    # Истощение и отсутствие сил
    r"\bничего\s+не\s+хочется\b",
    r"\bничего\s+не\s+хочу\b",
    r"\bнет\s+сил\b",
    r"\bне\s+могу\s+перестать\s+плакать\b",
    r"\bвсе\s+достало\b",
    r"\bя\s+больше\s+не\s+могу\b",
    r"\bочень\s+устал[аи]?\b",

    # Одиночество и отвержение
    r"\bникому\s+не\s+нужн[а-я]*\b",
    r"\bне\s+с\s+кем\s+поговорить\b",
    r"\bменя\s+никто\s+не\s+понимает\b",
    r"\bя\s+совсем\s+одн[а-я]*\b",

    # Переживание после события
    r"\bпосле\b.{0,60}\bмне\s+(плохо|тяжело|больно|страшно|грустно)\b",
)


# -------------------------------------------------------------------
# Фактические вопросы
# -------------------------------------------------------------------

FACTUAL_PATTERNS = (
    r"^\s*что\s+такое\b",
    r"^\s*кто\s+(такой|такая|такие)\b",
    r"^\s*когда\s+(произошло|было|будет)\b",
    r"^\s*где\s+находится\b",
    r"^\s*как\s+работает\b",
    r"^\s*что\s+означает\b",
    r"^\s*чем\s+отличается\b",
    r"^\s*сколько\b",
    r"^\s*какой\s+год\b",
    r"^\s*какая\s+дата\b",
    r"^\s*как\s+называется\b",
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
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[!?.,:;…]+$", "", normalized)

    return normalized.strip()


def matches_exact_phrase(
    normalized_text: str,
    phrases: set[str],
) -> bool:
    return normalized_text in phrases


def matches_any_pattern(
    normalized_text: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            pattern,
            normalized_text,
            flags=re.IGNORECASE,
        )
        is not None
        for pattern in patterns
    )


def contains_crisis_signal(
    normalized_text: str,
) -> bool:
    """
    Ищет явный кризисный сигнал и учитывает простые отрицания.
    """

    if any(
        negation in normalized_text
        for negation in CRISIS_NEGATIONS
    ):
        return False

    return matches_any_pattern(
        normalized_text,
        CRISIS_PATTERNS,
    )


def result(
    route: Route,
    confidence: float,
    needs_model: bool,
    needs_history: bool,
    needs_safety: bool,
    reason: str,
) -> RouterResult:
    return RouterResult(
        route=route,
        confidence=confidence,
        needs_model=needs_model,
        needs_history=needs_history,
        needs_safety=needs_safety,
        reason=reason,
    )


# -------------------------------------------------------------------
# Главная функция Router
# -------------------------------------------------------------------

def classify_message(
    text: str,
    has_history: bool = False,
) -> RouterResult:
    """
    Определяет основной маршрут сообщения.

    Приоритеты:
    1. Безопасность.
    2. Короткие служебные сообщения.
    3. Практическая задача.
    4. Решение/выбор.
    5. Саморефлексия.
    6. Эмоциональное состояние.
    7. Фактический вопрос.
    8. Общий маршрут.
    """

    normalized = normalize_message(text)

    if not normalized:
        return result(
            route=Route.GENERAL,
            confidence=1.0,
            needs_model=False,
            needs_history=False,
            needs_safety=False,
            reason="Пустое сообщение",
        )

    # 1. Safety имеет абсолютный приоритет.
    if contains_crisis_signal(normalized):
        return result(
            route=Route.CRISIS_SIGNAL,
            confidence=0.99,
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
        return result(
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
        return result(
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
        return result(
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
        return result(
            route=Route.ACKNOWLEDGEMENT,
            confidence=0.97,
            needs_model=has_history,
            needs_history=has_history,
            needs_safety=False,
            reason=(
                "Короткий ответ, который интерпретируется "
                "только в контексте"
            ),
        )

    # 3. Конкретная практическая задача.
    if matches_any_pattern(
        normalized,
        PRACTICAL_PATTERNS,
    ):
        return result(
            route=Route.PRACTICAL_TASK,
            confidence=0.95,
            needs_model=True,
            needs_history=True,
            needs_safety=False,
            reason="Пользователь просит выполнить практическую задачу",
        )

    # 4. Решение или выбор.
    if matches_any_pattern(
        normalized,
        DECISION_PATTERNS,
    ):
        return result(
            route=Route.DECISION_SUPPORT,
            confidence=0.94,
            needs_model=True,
            needs_history=True,
            needs_safety=False,
            reason="Пользователь рассматривает решение или выбор",
        )

    # 5. Запрос на понимание себя.
    if matches_any_pattern(
        normalized,
        REFLECTION_PATTERNS,
    ):
        return result(
            route=Route.REFLECTION_REQUEST,
            confidence=0.93,
            needs_model=True,
            needs_history=True,
            needs_safety=False,
            reason="Пользователь просит помочь с саморефлексией",
        )

    # 6. Сообщение об эмоциональном состоянии.
    if matches_any_pattern(
        normalized,
        EMOTIONAL_PATTERNS,
    ):
        return result(
            route=Route.EMOTIONAL_DISCLOSURE,
            confidence=0.92,
            needs_model=True,
            needs_history=True,
            needs_safety=True,
            reason="Пользователь сообщает об эмоциональном состоянии",
        )

    # 7. Информационный вопрос.
    if matches_any_pattern(
        normalized,
        FACTUAL_PATTERNS,
    ):
        return result(
            route=Route.FACTUAL_QUESTION,
            confidence=0.90,
            needs_model=True,
            needs_history=False,
            needs_safety=False,
            reason="Пользователь задаёт информационный вопрос",
        )

    # 8. Общий маршрут.
    return result(
        route=Route.GENERAL,
        confidence=0.55,
        needs_model=True,
        needs_history=has_history,
        needs_safety=True,
        reason="Не найдено достаточно признаков специального маршрута",
    )
