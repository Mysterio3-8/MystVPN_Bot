"""
Заглушка ИИ-ассистента. Сейчас всегда возвращает None (человек обрабатывает).

КАК ПОДКЛЮЧИТЬ CLAUDE (будущее):
1. pip install anthropic  (добавить в requirements.txt)
2. Добавить в .env: ANTHROPIC_API_KEY=sk-ant-...
3. Раскомментировать блок ниже и удалить заглушку
"""

from __future__ import annotations


async def get_ai_response(message: str) -> str | None:
    """
    Возвращает автоответ или None (значит — передать человеку).

    Логика приоритетов при включении ИИ:
    - Если вопрос покрыт FAQ → отвечает ИИ
    - Если тема нестандартная или ИИ не уверен → None → человек
    - Слова "возврат", "деньги", "ошибка оплаты" → сразу None (критично)
    """
    return None  # STUB


# ─── Будущая интеграция с Claude ───────────────────────────────────────────
#
# import os
# import anthropic
# from content.faq import _TEXTS
#
# _client: anthropic.AsyncAnthropic | None = None
#
# def _get_client() -> anthropic.AsyncAnthropic:
#     global _client
#     if _client is None:
#         _client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
#     return _client
#
# _FAQ_CONTEXT = "\n\n".join(f"### {k}\n{v}" for k, v in _TEXTS.items())
#
# _SYSTEM = f"""Ты — вежливый ИИ-ассистент службы поддержки MystVPN.
# Отвечай на вопросы пользователей, опираясь на FAQ ниже.
# Всегда отвечай на том языке, на котором написал пользователь.
# Если вопрос касается денег, возврата или технических ошибок — отвечай:
# "Этот вопрос передам специалисту — он скоро ответит."
# Если не уверен — тоже передавай специалисту.
#
# FAQ:
# {_FAQ_CONTEXT}
# """
#
# _ESCALATE_KEYWORDS = ("возврат", "деньги", "списали", "ошибка оплаты", "refund")
#
# async def get_ai_response(message: str) -> str | None:
#     if any(kw in message.lower() for kw in _ESCALATE_KEYWORDS):
#         return None
#     try:
#         resp = await _get_client().messages.create(
#             model="claude-sonnet-4-6",
#             max_tokens=600,
#             system=_SYSTEM,
#             messages=[{"role": "user", "content": message}],
#         )
#         text = resp.content[0].text.strip()
#         if "специалист" in text.lower() or "передам" in text.lower():
#             return None
#         return text
#     except Exception:
#         return None
