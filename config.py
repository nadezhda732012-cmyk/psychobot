import os


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("Переменная BOT_TOKEN не установлена")


CRISIS_CONTACTS = """
☎️ Единый общероссийский телефон доверия: 8-800-200-01-22
☎️ Телефон МЧС: 8-800-775-17-17
"""


MAX_HISTORY_LENGTH = 20
