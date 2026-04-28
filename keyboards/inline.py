from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import PLANS
from services.i18n import i18n


def main_menu_keyboard(is_admin: bool = False, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=i18n.t("btn_cabinet", lang), callback_data="menu_cabinet")],
        [InlineKeyboardButton(text=i18n.t("btn_buy", lang), callback_data="menu_buy")],
        [
            InlineKeyboardButton(text=i18n.t("btn_about", lang), callback_data="menu_about"),
            InlineKeyboardButton(text=i18n.t("btn_support_project", lang), callback_data="menu_support"),
        ],
        [
            InlineKeyboardButton(text=i18n.t("btn_channel", lang), url="https://t.me/MysterioVPN"),
            InlineKeyboardButton(text=i18n.t("btn_help", lang), url="https://t.me/Myst_support"),
        ],
        [InlineKeyboardButton(text=i18n.t("btn_language", lang), callback_data="menu_language")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="🔧 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cabinet_keyboard(
    has_subscription: bool = False,
    has_key: bool = True,
    lang: str = "ru",
    rotation_pending: bool = False,
) -> InlineKeyboardMarkup:
    buttons = []
    if has_subscription:
        if rotation_pending:
            buttons.append([InlineKeyboardButton(
                text="🔄 Применить новый ключ сейчас",
                callback_data="cabinet_apply_rotation",
            )])
        buttons.append([
            InlineKeyboardButton(text=i18n.t("btn_renew", lang), callback_data="cabinet_renew"),
            InlineKeyboardButton(text=i18n.t("btn_guide", lang), url="https://keybest.cc/guide/"),
        ])
        if not has_key:
            buttons.append([InlineKeyboardButton(text="🔑 Получить ключ", callback_data="cabinet_get_key")])
        else:
            buttons.append([InlineKeyboardButton(text=i18n.t("btn_reset_key", lang), callback_data="cabinet_reset_key")])
    else:
        buttons.append([InlineKeyboardButton(text=i18n.t("btn_buy", lang), callback_data="menu_buy")])
    buttons.append([InlineKeyboardButton(text="👥 Рефералы", callback_data="cabinet_referral")])
    buttons.append([InlineKeyboardButton(text="⚠️ Не подключается?", callback_data="cabinet_no_connection")])
    buttons.append([InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tariffs_keyboard(lang: str = "ru", show_trial: bool = False) -> InlineKeyboardMarkup:
    prices = [
        ("1_month",  i18n.t("plan_period_1m", lang), "219 ₽",  ""),
        ("3_months", i18n.t("plan_period_3m", lang), "549 ₽",  " (-16%)"),
        ("6_months", i18n.t("plan_period_6m", lang), "999 ₽",  " (-24%)"),
        ("1_year",   i18n.t("plan_period_1y", lang), "1 799 ₽", " (-32%)"),
    ]
    buttons = [
        [InlineKeyboardButton(text=f"{period} • {price}{discount}", callback_data=f"plan_{key}")]
        for key, period, price, discount in prices
    ]
    if show_trial:
        buttons.insert(0, [InlineKeyboardButton(
            text="🎁 3 дня БЕСПЛАТНО (триал)", callback_data="trial_activate"
        )])
    buttons.append([
        InlineKeyboardButton(text=i18n.t("btn_promo", lang), callback_data="enter_promo"),
        InlineKeyboardButton(text=i18n.t("btn_gift_vpn", lang), callback_data="menu_gift"),
    ])
    buttons.append([InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def gift_tariffs_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    prices = [
        ("1_month", i18n.t("plan_period_1m", lang), "219 ₽", ""),
        ("3_months", i18n.t("plan_period_3m", lang), "549 ₽", " (-16%)"),
        ("6_months", i18n.t("plan_period_6m", lang), "999 ₽", " (-24%)"),
        ("1_year", i18n.t("plan_period_1y", lang), "1799 ₽", " (-32%)"),
    ]
    buttons = [
        [InlineKeyboardButton(text=f"🎁 {period} • {price}{discount}", callback_data=f"gift_plan_{key}")]
        for key, period, price, discount in prices
    ]
    buttons.append([InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_buy")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def gift_payment_method_keyboard(plan_key: str, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить картой", callback_data=f"pay_gift_yookassa_{plan_key}")],
        [InlineKeyboardButton(text="📱 Оплатить через СБП", callback_data=f"pay_gift_sbp_{plan_key}")],
        [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_gift")],
    ])


def support_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.t("btn_bread", lang), callback_data="donate_bread")],
        [InlineKeyboardButton(text=i18n.t("btn_pie", lang), callback_data="donate_pie")],
        [InlineKeyboardButton(text=i18n.t("btn_bbq", lang), callback_data="donate_bbq")],
        [InlineKeyboardButton(text=i18n.t("btn_custom_amount", lang), callback_data="donate_custom")],
        [InlineKeyboardButton(text=i18n.t("btn_sponsors", lang), callback_data="sponsors_list")],
        [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="back_to_menu")],
    ])


def donate_method_keyboard(amount: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Картой", callback_data=f"donate_pay_card_{amount}")],
        [InlineKeyboardButton(text="📱 Через СБП", callback_data=f"donate_pay_sbp_{amount}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_support")],
    ])


def payment_method_keyboard(plan_key: str, lang: str = "ru", is_admin: bool = False) -> InlineKeyboardMarkup:
    from config import STARS_PRICES
    stars = STARS_PRICES.get(plan_key)
    buttons = [
        [InlineKeyboardButton(text="💳 Оплатить картой", callback_data=f"pay_yookassa_{plan_key}")],
        [InlineKeyboardButton(text="📱 Оплатить через СБП", callback_data=f"pay_sbp_{plan_key}")],
    ]
    if stars:
        buttons.append([InlineKeyboardButton(text=f"⭐ Оплатить {stars} Stars", callback_data=f"pay_stars_{plan_key}")])
    buttons.append([InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_buy")])
    if is_admin:
        buttons.insert(0, [InlineKeyboardButton(
            text="👑 Активировать бесплатно (Админ)",
            callback_data=f"pay_admin_free_{plan_key}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def about_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.t("btn_payment_safety", lang), callback_data="about_payment_safety")],
        [InlineKeyboardButton(text=i18n.t("btn_oferta", lang), url="https://teletype.in/@mystadm/X2oafHAItL9")],
        [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="back_to_menu")],
    ])


def reset_key_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=i18n.t("btn_confirm_reset", lang), callback_data="cabinet_reset_key_confirm"),
        InlineKeyboardButton(text=i18n.t("btn_cancel_reset", lang), callback_data="menu_cabinet"),
    ]])


def subscription_actions_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=i18n.t("btn_renew", lang), callback_data="cabinet_renew")],
        [InlineKeyboardButton(text=i18n.t("btn_cancel_sub", lang), callback_data="cabinet_cancel_confirm")],
        [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_cabinet")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def language_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    languages = [
        ("🇷🇺 Русский", "lang_ru"),
        ("🇬🇧 English", "lang_en"),
        ("🇫🇷 Français", "lang_fr"),
        ("🇪🇸 Español", "lang_es"),
        ("🇵🇹 Português", "lang_pt"),
        ("🇹🇷 Türkçe", "lang_tr"),
        ("🇸🇦 العربية", "lang_ar"),
        ("🇮🇷 فارسی", "lang_fa"),
        ("🇺🇦 Українська", "lang_uk"),
        ("🇮🇩 Bahasa Indonesia", "lang_id"),
        ("🇨🇳 中文", "lang_zh"),
        ("🇯🇵 日本語", "lang_ja"),
        ("🇰🇷 한국어", "lang_ko"),
        ("🇩🇪 Deutsch", "lang_de"),
        ("🇻🇳 Tiếng Việt", "lang_vi"),
        ("🇲🇾 Bahasa Melayu", "lang_ms"),
        ("🇮🇳 हिंदी", "lang_hi"),
    ]
    buttons = []
    for i in range(0, len(languages), 2):
        row = [InlineKeyboardButton(text=languages[i][0], callback_data=languages[i][1])]
        if i + 1 < len(languages):
            row.append(InlineKeyboardButton(text=languages[i + 1][0], callback_data=languages[i + 1][1]))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_keyboard(callback: str = "back_to_menu", lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data=callback)]]
    )


def admin_inline_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton(text="💰 Платежи", callback_data="admin_payments"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
        ],
        [InlineKeyboardButton(text="🎁 Выдать подписку", callback_data="admin_grant")],
        [InlineKeyboardButton(text="🎟️ Промокоды", callback_data="admin_promos")],
        [InlineKeyboardButton(text="🔌 Тест XRay/3x-ui", callback_data="admin_test_xray")],
        [InlineKeyboardButton(text="🔄 Ротация ключей (grace 24ч)", callback_data="admin_rotate_keys")],
        [InlineKeyboardButton(text="◀️ Закрыть", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_promos_keyboard(promos: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_promo_create")],
    ]
    for p in promos[:20]:
        status = "🟢" if p.is_active else "🔴"
        label = f"{status} {p.code} ({p.used_count}/{p.max_uses or '∞'})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"admin_promo_view_{p.id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_promo_view_keyboard(promo_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data=f"admin_promo_toggle_{promo_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_promo_delete_{promo_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_promos")],
    ])


def admin_promo_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Скидка %", callback_data="admin_promo_type_discount")],
        [InlineKeyboardButton(text="🎁 Бесплатный тариф", callback_data="admin_promo_type_free")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_promos")],
    ])


def admin_promo_plan_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц", callback_data="admin_promo_plan_1_month")],
        [InlineKeyboardButton(text="3 месяца", callback_data="admin_promo_plan_3_months")],
        [InlineKeyboardButton(text="6 месяцев", callback_data="admin_promo_plan_6_months")],
        [InlineKeyboardButton(text="1 год", callback_data="admin_promo_plan_1_year")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_promos")],
    ])


def confirm_cancel_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=i18n.t("btn_yes_cancel", lang), callback_data="cabinet_cancel_confirmed"),
        InlineKeyboardButton(text=i18n.t("btn_no", lang), callback_data="menu_cabinet"),
    ]])
