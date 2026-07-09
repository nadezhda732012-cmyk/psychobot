# tests.py
from database import save_message

# Тест на тревожность (HADS) — 7 вопросов
ANXIETY_TEST = {
    "questions": [
        "1/7: Я чувствую себя напряжённым(ой) или мне не по себе. (0 — нет, 3 — очень часто)",
        "2/7: Я испытываю страх, и мне кажется, что что-то ужасное может случиться.",
        "3/7: Беспокойные мысли крутятся у меня в голове.",
        "4/7: Я могу легко присесть и расслабиться. (0 — да, 3 — нет)",
        "5/7: Я испытываю внутреннее напряжение или дрожь.",
        "6/7: Мне не сидится на месте, мне постоянно нужно двигаться.",
        "7/7: У меня бывает внезапное чувство паники."
    ],
    "scores": []
}

# Состояние теста для каждого пользователя
test_sessions = {}

def start_test(user_id: int):
    """Начинает новый тест"""
    test_sessions[user_id] = {
        "step": 0,
        "answers": []
    }

def get_next_question(user_id: int) -> str:
    """Возвращает следующий вопрос или результат"""
    session = test_sessions.get(user_id)
    if not session:
        return None
    
    step = session["step"]
    if step < 7:
        return ANXIETY_TEST["questions"][step]
    else:
        # Тест закончен — считаем результат
        return calculate_result(user_id)

def save_answer(user_id: int, answer_text: str):
    """Сохраняет ответ пользователя"""
    session = test_sessions.get(user_id)
    if not session:
        return
    
    # Парсим ответ (пользователь должен ввести число от 0 до 3)
    try:
        score = int(answer_text.strip())
        if 0 <= score <= 3:
            session["answers"].append(score)
            session["step"] += 1
        else:
            # Если введено не число или вне диапазона — игнорируем
            pass
    except ValueError:
        pass

def calculate_result(user_id: int) -> str:
    """Вычисляет результат теста"""
    session = test_sessions.get(user_id)
    if not session or len(session["answers"]) < 7:
        return "Тест не завершён. Попробуй ещё раз."
    
    total = sum(session["answers"])
    
    # Интерпретация результатов
    if total <= 7:
        result = "✅ Норма. Уровень тревожности в пределах нормы."
    elif total <= 10:
        result = "⚠️ Умеренная тревожность. Рекомендуется обратить внимание на своё состояние."
    else:
        result = "🔴 Высокая тревожность. Рекомендуется обратиться к психологу или психотерапевту."
    
    # Удаляем сессию теста
    test_sessions[user_id] = None
    
    return f"📊 Результат теста на тревожность:\nСумма баллов: {total} из 21\n{result}"