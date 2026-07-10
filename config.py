import os


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "Переменная окружения BOT_TOKEN не установлена"
    )


GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")

if not GIGACHAT_KEY:
    raise RuntimeError(
        "Переменная окружения GIGACHAT_KEY не установлена"
    )


CRISIS_CONTACTS = """
☎️ При непосредственной опасности позвони в местную экстренную службу.
"""


MAX_HISTORY_LENGTH = 20
