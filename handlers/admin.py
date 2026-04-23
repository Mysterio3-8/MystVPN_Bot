from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
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


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ панели.")
        return
    await message.answer("🔧 <b>Админ панель MystVPN</b>\n\nВыберите действие:", reply_markup=admin_inline_keyboard(), parse_mode="HTML")


@router.message(Command("test_xray"))
async def cmd_test_xray(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    result = await XrayService.test_connection()
    await message.answer(result)


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
        "🔧 <b>Админ панель MystVPN</b>\n\nВыберите действие:",
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


@router.message(BroadcastState.waiting_message)
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


@router.message(GrantState.waiting_user_id)
async def admin_grant_user(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введите числовой user_id")
        return
    await state.update_data(target_user_id=int(message.text))
    await message.answer(
        "Выберите тариф:\n1️⃣ 1_month\n2️⃣ 3_months\n3️⃣ 6_months\n4️⃣ 1_year\n\nВведите ключ тарифа:"
    )
    await state.set_state(GrantState.waiting_plan)


@router.message(GrantState.waiting_plan)
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


@router.message(PromoCreateState.waiting_code)
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


@router.message(PromoCreateState.waiting_discount)
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


@router.message(PromoCreateState.waiting_max_uses)
async def admin_promo_max_uses(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("❌ Введите число (0 для безлимита):")
        return
    await state.update_data(max_uses=int(text))
    await state.set_state(PromoCreateState.waiting_days_valid)
    await message.answer("Введите срок действия в днях (0 = бессрочно):")


@router.message(PromoCreateState.waiting_days_valid)
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
