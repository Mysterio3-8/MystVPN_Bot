"""
Хелпер для форматирования VPN-ключа/ссылки в сообщениях.

Правило:
  - Если есть sub_url → показываем ТОЛЬКО его (красиво, с инструкцией)
  - Если sub_url нет, но есть vpn_key → показываем сырой ключ
  - Ни того ни другого → просим зайти в кабинет
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
            f"\n\n🔑 <b>Твой VPN-ключ:</b>\n"
            f"<code>{vpn_key}</code>\n\n"
            f"<i>📱 Android → Hiddify (без настройки)\n"
            f"🍎 iPhone / 💻 ПК → Hiddify / v2rayTUN</i>"
        )
    return "\n\n📋 Ключ доступен в /cabinet"
