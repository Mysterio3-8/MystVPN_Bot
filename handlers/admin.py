import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import AsyncSessionLocal
from services import UserService, SubscriptionService, PaymentService, PromoService, XrayService
from keyboards import (
    admin_inline_keyboard,
    admin_promos_keyboard,
    admin_promo_view_keyboard,
    admin_promo_type_keyboard,
    admin_promo_plan_keyboard,
    back_keyboard,
)
from config import config

router = Router()


class BroadcastState(StatesGroup):
    waiting_message = State()


class GrantState(StatesGroup):
    waiting_user_id = State()
    waiting_plan = State()


class PromoCreateState(StatesGroup):
    waiting_code = State()
    waiting_type = State()
    waiting_discount = State()
    waiting_plan = State()
    waiting_max_uses = State()
    waiting_days_valid = State()


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


async def _admin_panel_text() -> str:
    async with AsyncSessionLocal() as session:
        total_users = await UserService.count(session)
        active_subs = await SubscriptionService.count_active(session)
        revenue = await PaymentService.total_revenue(session)

    return (
        "🔧 <b>Админ панель MystVPN</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"✅ Активных подписок: <b>{active_subs}</b>\n"
        f"💰 Выручка RUB: <b>{revenue:.2f} ₽</b>\n\n"
        "Выберите действие:"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ панели.")
        return
    await message.answer(await _admin_panel_text(), reply_markup=admin_inline_keyboard(), parse_mode="HTML")


@router.message(Command("test_xray"))
async def cmd_test_xray(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    result = await XrayService.test_connection()
    await message.answer(result)


@router.callback_query(F.data == "admin_partners")
async def admin_partners_view(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    from services.partner_service import PartnerService
    from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
    async with AsyncSessionLocal() as session:
        partners = await PartnerService.get_all_partners(session)
        if not partners:
            await callback.message.edit_text(
                "🤝 <b>Партнёры</b>\n\nПартнёров пока нет.\n\nДобавить: /new_partner user_id @channel",
                reply_markup=IKM(inline_keyboard=[[IKB(text="◀️ Назад", callback_data="admin_panel")]]),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        lines = ["🤝 <b>Партнёры MystVPN:</b>\n"]
        total_earnings = 0.0
        for p in partners:
            stats = await PartnerService.get_stats(session, p.user_id)
            total_earnings += stats["partner_earnings"]
            status = "🟢" if p.is_partner else "🔴"
            lines.append(
                f"{status} <b>{p.partner_channel or '—'}</b> (id: <code>{p.user_id}</code>)\n"
                f"   👥 {stats['total_referrals']} рефералов • "
                f"💳 {stats['paying_users']} платящих • "
                f"💰 {stats['partner_earnings']:.0f} ₽ к выплате"
            )

        lines.append(f"\n<b>Итого к выплате: {total_earnings:.0f} ₽</b>")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=IKM(inline_keyboard=[[IKB(text="◀️ Назад", callback_data="admin_panel")]]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_test_xray")
async def admin_test_xray(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.answer("⏳ Проверяю...", show_alert=False)
    result = await XrayService.test_connection()
    await callback.message.answer(result)


@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        await _admin_panel_text(),
        reply_markup=admin_inline_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        total_users = await UserService.count(session)
        active_subs = await SubscriptionService.count_active(session)
        revenue = await PaymentService.total_revenue(session)

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей всего: <b>{total_users}</b>\n"
        f"✅ Активных подписок: <b>{active_subs}</b>\n"
        f"💰 Выручка (RUB): <b>{revenue:.2f} ₽</b>"
    )
    await callback.message.edit_text(text, reply_markup=back_keyboard("admin_panel"), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "📢 Отправьте текст рассылки (поддерживается HTML):",
        reply_markup=back_keyboard("admin_panel"),
    )
    await state.set_state(BroadcastState.waiting_message)
    await callback.answer()


@router.message(BroadcastState.waiting_message, ~Command())
async def admin_broadcast_send(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    async with AsyncSessionLocal() as session:
        users = await UserService.get_all(session)

    sent, failed = 0, 0
    for user in users:
        try:
            await message.bot.send_message(user.user_id, message.text or message.caption or "", parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"📢 Рассылка завершена.\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}")


@router.message(Command("new_partner"))
async def cmd_new_partner(message: Message) -> None:
    """
    /new_partner user_id @channel_name
    Регистрирует партнёра. Пример: /new_partner 123456789 @MyCryptoChannel
    """
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /new_partner <user_id> <@channel>\nПример: /new_partner 123456789 @MyCryptoChannel")
        return

    try:
        partner_user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ user_id должен быть числом")
        return

    channel = parts[2]

    from sqlalchemy import select as _sel
    from models import User as _User
    async with AsyncSessionLocal() as session:
        result = await session.execute(_sel(_User).where(_User.user_id == partner_user_id))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(f"❌ Пользователь {partner_user_id} не найден в БД.\nОн должен сначала написать /start боту.")
            return
        user.is_partner = True
        user.partner_channel = channel
        await session.commit()

    from services import ReferralService
    ref_link = ReferralService.get_ref_link(partner_user_id)
    await message.answer(
        f"✅ <b>Партнёр создан!</b>\n\n"
        f"ID: <code>{partner_user_id}</code>\n"
        f"Канал: <b>{channel}</b>\n"
        f"Реф-ссылка: <code>{ref_link}</code>\n\n"
        f"Партнёр может проверить статистику командой /partner в боте.",
        parse_mode="HTML",
    )

    # Уведомляем партнёра
    try:
        await message.bot.send_message(
            partner_user_id,
            f"🎉 <b>Добро пожаловать в партнёрскую программу MystVPN!</b>\n\n"
            f"Ваша реф-ссылка для размещения в канале {channel}:\n"
            f"<code>{ref_link}</code>\n\n"
            f"Вы получаете <b>30% от всех платежей</b> приведённых пользователей — пожизненно.\n\n"
            f"Статистика: /partner\n"
            f"Вопросы: @Myst_support",
            parse_mode="HTML",
        )
    except Exception:
        await message.answer("⚠️ Не удалось уведомить партнёра (возможно, заблокировал бота).")


@router.message(Command("partners"))
async def cmd_partners_list(message: Message) -> None:
    """Список всех партнёров с краткой статистикой."""
    if not is_admin(message.from_user.id):
        return

    from services.partner_service import PartnerService
    async with AsyncSessionLocal() as session:
        partners = await PartnerService.get_all_partners(session)
        if not partners:
            await message.answer("Партнёров пока нет. Добавь: /new_partner user_id @channel")
            return

        lines = ["👥 <b>Партнёры MystVPN:</b>\n"]
        for p in partners:
            stats = await PartnerService.get_stats(session, p.user_id)
            lines.append(
                f"• {p.partner_channel or '—'} (id: <code>{p.user_id}</code>)\n"
                f"  Рефералов: {stats['total_referrals']} | "
                f"Платящих: {stats['paying_users']} | "
                f"Заработок: {stats['partner_earnings']:.0f} ₽"
            )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("ref_push"))
async def cmd_ref_push(message: Message) -> None:
    """
    Персонализированная реф-рассылка — каждому юзеру его уникальная ссылка.
    Отправляет только пользователям у кого был хоть один старт (есть в БД).
    """
    if not is_admin(message.from_user.id):
        return

    await message.answer("⏳ Запускаю реф-рассылку...")

    from services import ReferralService
    from config import REFERRAL_BONUS_DAYS

    async with AsyncSessionLocal() as session:
        users = await UserService.get_all(session)

    sent, failed, skipped = 0, 0, 0
    for user in users:
        # Не спамим себе
        if user.user_id in config.admin_ids:
            skipped += 1
            continue

        ref_link = ReferralService.get_ref_link(user.user_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Моя реф-ссылка", url=ref_link)],
            [InlineKeyboardButton(text="💳 Купить подписку", callback_data="menu_buy")],
        ])

        text = (
            f"👥 <b>Зови друзей — получай дни бесплатно!</b>\n\n"
            f"За каждого друга которого ты пригласишь в MystVPN — "
            f"тебе начисляется <b>+{REFERRAL_BONUS_DAYS} дней</b> бесплатного VPN.\n\n"
            f"🔗 <b>Твоя личная ссылка:</b>\n"
            f"<code>{ref_link}</code>\n\n"
            f"Поделись с другом — он получит VPN, ты получишь дни. "
            f"Дни копятся и применяются к любой подписке 👇"
        )

        try:
            await message.bot.send_message(user.user_id, text, reply_markup=keyboard, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)  # не флудим Telegram API
        except Exception:
            failed += 1

    await message.answer(
        f"✅ <b>Реф-рассылка завершена</b>\n\n"
        f"Отправлено: <b>{sent}</b>\n"
        f"Ошибок: <b>{failed}</b>\n"
        f"Пропущено (админы): <b>{skipped}</b>",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_grant")
async def admin_grant_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "🎁 Введите Telegram user_id пользователя:",
        reply_markup=back_keyboard("admin_panel"),
    )
    await state.set_state(GrantState.waiting_user_id)
    await callback.answer()


@router.message(GrantState.waiting_user_id, ~Command())
async def admin_grant_user(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введите числовой user_id")
        return
    await state.update_data(target_user_id=int(message.text))
    await message.answer(
        "Выберите тариф:\n1️⃣ 1_month\n2️⃣ 3_months\n3️⃣ 6_months\n4️⃣ 1_year\n\nВведите ключ тарифа:"
    )
    await state.set_state(GrantState.waiting_plan)


@router.message(GrantState.waiting_plan, ~Command())
async def admin_grant_plan(message: Message, state: FSMContext) -> None:
    from config import PLANS
    plan_key = message.text.strip() if message.text else ""
    if plan_key not in PLANS:
        await message.answer(f"❌ Неверный тариф. Доступны: {', '.join(PLANS.keys())}")
        return

    data = await state.get_data()
    target_uid = data["target_user_id"]
    await state.clear()

    async with AsyncSessionLocal() as session:
        sub = await SubscriptionService.create_pending(session, target_uid, plan_key)
        await SubscriptionService.activate(session, sub.id)

    await message.answer(f"✅ Подписка <b>{plan_key}</b> выдана пользователю <code>{target_uid}</code>.", parse_mode="HTML")


@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    async with AsyncSessionLocal() as session:
        users = await UserService.get_all(session)
    lines = [f"👥 <b>Пользователи ({len(users)})</b>\n"]
    for u in users[:20]:
        status = "🔒" if u.is_banned else "✅"
        lines.append(f"{status} <code>{u.user_id}</code> @{u.username or '—'}")
    if len(users) > 20:
        lines.append(f"... и ещё {len(users) - 20}")
    await callback.message.edit_text("\n".join(lines), reply_markup=back_keyboard("admin_panel"), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_payments")
async def admin_payments(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    async with AsyncSessionLocal() as session:
        revenue = await PaymentService.total_revenue(session)
    await callback.message.edit_text(
        f"💰 <b>Статистика платежей</b>\n\nОбщая выручка (RUB): <b>{revenue:.2f} ₽</b>",
        reply_markup=back_keyboard("admin_panel"),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------- Promo codes ----------

async def _show_promos(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        promos = await PromoService.list_all(session)
    text = "🎟️ <b>Управление промокодами</b>\n\n"
    if not promos:
        text += "Промокодов пока нет."
    else:
        text += f"Всего: <b>{len(promos)}</b>\nВыберите промокод для управления:"
    await callback.message.edit_text(text, reply_markup=admin_promos_keyboard(promos), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_promos")
async def admin_promos(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await _show_promos(callback)


async def _show_promo_view(callback: CallbackQuery, promo_id: int) -> None:
    async with AsyncSessionLocal() as session:
        promo = await PromoService.get(session, promo_id)
    if not promo:
        await callback.answer("Промокод не найден", show_alert=True)
        return
    status = "🟢 Активен" if promo.is_active else "🔴 Неактивен"
    kind = f"Бесплатный тариф: {promo.free_plan}" if promo.free_plan else f"Скидка: {promo.discount_percent}%"
    valid = promo.valid_until.strftime("%d.%m.%Y") if promo.valid_until else "без ограничений"
    max_uses = str(promo.max_uses) if promo.max_uses else "∞"
    text = (
        f"🎟️ <b>Промокод</b> <code>{promo.code}</code>\n\n"
        f"Статус: {status}\n"
        f"{kind}\n"
        f"Использовано: <b>{promo.used_count}/{max_uses}</b>\n"
        f"Действует до: <b>{valid}</b>\n"
        f"Создан: {promo.created_at.strftime('%d.%m.%Y')}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_promo_view_keyboard(promo.id, promo.is_active),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_promo_view_"))
async def admin_promo_view(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    promo_id = int(callback.data.replace("admin_promo_view_", ""))
    await _show_promo_view(callback, promo_id)


@router.callback_query(F.data.startswith("admin_promo_toggle_"))
async def admin_promo_toggle(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    promo_id = int(callback.data.replace("admin_promo_toggle_", ""))
    async with AsyncSessionLocal() as session:
        await PromoService.toggle_active(session, promo_id)
    await _show_promo_view(callback, promo_id)


@router.callback_query(F.data.startswith("admin_promo_delete_"))
async def admin_promo_delete(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    promo_id = int(callback.data.replace("admin_promo_delete_", ""))
    async with AsyncSessionLocal() as session:
        await PromoService.delete(session, promo_id)
    await callback.answer("✅ Удалён", show_alert=False)
    await _show_promos(callback)


@router.callback_query(F.data == "admin_rotate_keys")
async def admin_rotate_keys_confirm(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    async with AsyncSessionLocal() as session:
        active_count = await SubscriptionService.count_active(session)
    await callback.message.edit_text(
        f"🔄 <b>Ротация ключей</b>\n\n"
        f"Активных подписок: <b>{active_count}</b>\n\n"
        f"Для каждого пользователя будет создан новый ключ.\n"
        f"Старый ключ останется работать <b>24 часа</b>, затем отключится.\n\n"
        f"Пользователи получат уведомление и смогут переключиться досрочно.\n\n"
        f"⚠️ Запустить ротацию?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, запустить", callback_data="admin_rotate_keys_go"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel"),
            ]
        ]),
        parse_mode="HTML",
    )
    await callback.answer()


_rotation_lock = asyncio.Lock()


@router.callback_query(F.data == "admin_rotate_keys_go")
async def admin_rotate_keys_go(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    if _rotation_lock.locked():
        await callback.answer("⏳ Ротация уже выполняется — подождите", show_alert=True)
        return

    async with _rotation_lock:
        await callback.answer("⏳ Запускаю ротацию...", show_alert=False)
        await callback.message.edit_text(
            "⏳ <b>Ротация запущена...</b>\n\nЭто может занять несколько минут.",
            parse_mode="HTML",
        )

        from services.key_helper import fmt_key

        success, failed, skipped = 0, 0, 0
        now = datetime.utcnow()
        async with AsyncSessionLocal() as session:
            subs = await SubscriptionService.get_all_active(session)

        for sub in subs:
            # Идемпотентность: если у юзера уже есть ожидающий новый ключ
            # (не истёкший grace) — пропускаем. Это защищает от повторных
            # нажатий админом и от параллельных задач.
            if sub.new_vpn_key and sub.key_rotation_deadline and sub.key_rotation_deadline > now:
                skipped += 1
                continue
            try:
                days_left = max(1, (sub.end_date - now).days)
                new_key, new_sub_url = await XrayService.create_client(sub.user_id, days_left)
                if new_key:
                    async with AsyncSessionLocal() as session:
                        await SubscriptionService.save_rotation_key(session, sub.id, new_key, new_sub_url)
                    try:
                        await callback.bot.send_message(
                            sub.user_id,
                            f"🔄 <b>Важно: обновление VPN-ключей</b>\n\n"
                            f"Мы обновили инфраструктуру.\n"
                            f"Твой <b>новый ключ</b> уже доступен в кабинете.\n\n"
                            f"Старый ключ будет работать ещё <b>24 часа</b>.\n"
                            f"После — переключись на новый."
                            f"{fmt_key(new_key, new_sub_url)}\n\n"
                            f"👉 /cabinet → «Применить новый ключ сейчас»",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass
                    success += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        await callback.message.edit_text(
            f"✅ <b>Ротация завершена</b>\n\n"
            f"Новые ключи выданы: <b>{success}</b>\n"
            f"Пропущено (уже в ротации): <b>{skipped}</b>\n"
            f"Ошибок: <b>{failed}</b>\n\n"
            f"Старые ключи отключатся через 24 часа автоматически.",
            reply_markup=back_keyboard("admin_panel"),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "admin_promo_create")
async def admin_promo_create_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.set_state(PromoCreateState.waiting_code)
    await callback.message.edit_text(
        "🎟️ <b>Создание промокода</b>\n\nВведите код (например <code>SUMMER2026</code>):",
        reply_markup=back_keyboard("admin_promos"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(PromoCreateState.waiting_code, ~Command())
async def admin_promo_create_code(message: Message, state: FSMContext) -> None:
    code = (message.text or "").strip().upper()
    if not code or len(code) < 3:
        await message.answer("❌ Код должен быть не короче 3 символов. Попробуйте ещё раз:")
        return
    async with AsyncSessionLocal() as session:
        existing = await PromoService.get_by_code(session, code)
    if existing:
        await message.answer("❌ Такой промокод уже существует. Введите другой:")
        return
    await state.update_data(code=code)
    await state.set_state(PromoCreateState.waiting_type)
    await message.answer("Выберите тип промокода:", reply_markup=admin_promo_type_keyboard())


@router.callback_query(PromoCreateState.waiting_type, F.data == "admin_promo_type_discount")
async def admin_promo_type_discount(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PromoCreateState.waiting_discount)
    await callback.message.edit_text(
        "Введите размер скидки в процентах (1-100):",
        reply_markup=back_keyboard("admin_promos"),
    )
    await callback.answer()


@router.message(PromoCreateState.waiting_discount, ~Command())
async def admin_promo_discount_value(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or not (1 <= int(text) <= 100):
        await message.answer("❌ Введите число от 1 до 100:")
        return
    await state.update_data(discount_percent=int(text), free_plan=None)
    await state.set_state(PromoCreateState.waiting_max_uses)
    await message.answer("Введите максимальное число использований (0 = без ограничений):")


@router.callback_query(PromoCreateState.waiting_type, F.data == "admin_promo_type_free")
async def admin_promo_type_free(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PromoCreateState.waiting_plan)
    await callback.message.edit_text(
        "Выберите бесплатный тариф:",
        reply_markup=admin_promo_plan_keyboard(),
    )
    await callback.answer()


@router.callback_query(PromoCreateState.waiting_plan, F.data.startswith("admin_promo_plan_"))
async def admin_promo_plan_pick(callback: CallbackQuery, state: FSMContext) -> None:
    from config import PLANS
    plan_key = callback.data.replace("admin_promo_plan_", "")
    if plan_key not in PLANS:
        await callback.answer("❌ Неверный тариф", show_alert=True)
        return
    await state.update_data(free_plan=plan_key, discount_percent=0)
    await state.set_state(PromoCreateState.waiting_max_uses)
    await callback.message.edit_text(
        "Введите максимальное число использований (0 = без ограничений):",
        reply_markup=back_keyboard("admin_promos"),
    )
    await callback.answer()


@router.message(PromoCreateState.waiting_max_uses, ~Command())
async def admin_promo_max_uses(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("❌ Введите число (0 для безлимита):")
        return
    await state.update_data(max_uses=int(text))
    await state.set_state(PromoCreateState.waiting_days_valid)
    await message.answer("Введите срок действия в днях (0 = бессрочно):")


@router.message(PromoCreateState.waiting_days_valid, ~Command())
async def admin_promo_days(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("❌ Введите число (0 для бессрочного):")
        return
    days = int(text)
    valid_until = datetime.utcnow() + timedelta(days=days) if days > 0 else None
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        promo = await PromoService.create(
            session,
            code=data["code"],
            discount_percent=data.get("discount_percent", 0),
            free_plan=data.get("free_plan"),
            max_uses=data.get("max_uses", 0),
            valid_until=valid_until,
        )

    kind = f"Бесплатный тариф: {promo.free_plan}" if promo.free_plan else f"Скидка {promo.discount_percent}%"
    max_uses_text = str(promo.max_uses) if promo.max_uses else "∞"
    valid_text = promo.valid_until.strftime("%d.%m.%Y") if promo.valid_until else "бессрочно"
    await message.answer(
        f"✅ Промокод <code>{promo.code}</code> создан!\n\n"
        f"{kind}\nИспользований: 0/{max_uses_text}\nДействует до: {valid_text}",
        reply_markup=back_keyboard("admin_promos"),
        parse_mode="HTML",
    )
