"""
Хелпер для форматирования VPN-ключа/ссылки в сообщениях.

Правило:
  - Показываем ТОЛЬКО subscription URL (https://keybest.cc/...).
  - Сырой vless:// ключ НИКОГДА не показываем — он содержит IP сервера и порт.
  - Если sub_url нет — просим обратиться в поддержку.
"""


def fmt_key(vpn_key: str | None, sub_url: str | None) -> str:
    """
    Возвращает готовый HTML-блок для вставки в сообщение после оплаты.
    Не содержит заголовка — только блок с ключом.
    """
    if sub_url:
        return (
            f"\n\n🔗 <b>Твой VPN-ключ:</b>\n"
            f"<code>{sub_url}</code>\n\n"
            f"<i>Скопируй ссылку и добавь в приложение:\n"
            f"📱 <b>Android</b> → <b>Hiddify</b> (работает без настройки)\n"
            f"🍎 <b>iPhone</b> → Hiddify / v2rayTUN\n"
            f"💻 <b>ПК</b> → Hiddify / v2rayTUN\n\n"
            f"В приложении: «+» → «Добавить подписку» → вставить ссылку</i>"
        )
    if vpn_key:
        return (
            "\n\n⚠️ Subscription-ссылка временно недоступна.\n"
            "Зайди в /cabinet через минуту или напиши в @Myst_support."
        )
    return "\n\n📋 Ключ доступен в /cabinet"
