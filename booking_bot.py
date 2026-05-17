import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

SERVICES = {
    "💈 Стрижка": {"price": "300", "duration": "45 хв"},
    "🪒 Гоління": {"price": "200", "duration": "30 хв"},
    "💆 Стрижка + борода": {"price": "450", "duration": "60 хв"},
    "🎨 Фарбування": {"price": "800", "duration": "90 хв"},
}

TIMES = [
    "10:00", "10:45", "11:30",
    "12:15", "13:00", "14:00",
    "15:00", "16:00", "17:00",
    "18:00", "19:00",
]

MASTERS = ["✂️ Майстер Олександр", "✂️ Майстер Дмитро", "✂️ Майстер Анна"]

class BookingState(StatesGroup):
    choosing_service = State()
    choosing_master = State()
    choosing_time = State()
    confirming = State()

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записатись"), KeyboardButton(text="📋 Мої записи")],
            [KeyboardButton(text="ℹ️ Про салон"), KeyboardButton(text="📞 Контакти")],
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Ласкаво просимо до *Барбершоп Premium*!\n\n"
        "Раді вас бачити. Оберіть дію в меню нижче 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "📅 Записатись")
async def start_booking(message: Message, state: FSMContext):
    buttons = []
    for service, info in SERVICES.items():
        buttons.append([InlineKeyboardButton(
            text=f"{service} — {info['price']} грн ({info['duration']})",
            callback_data=f"service_{service}"
        )])
    await message.answer(
        "🎯 *Оберіть послугу:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(BookingState.choosing_service)

@dp.callback_query(F.data.startswith("service_"))
async def choose_master(call: CallbackQuery, state: FSMContext):
    service = call.data.replace("service_", "")
    await state.update_data(service=service)
    buttons = [[InlineKeyboardButton(text=master, callback_data=f"master_{master}")]
               for master in MASTERS]
    await call.message.edit_text(
        f"✅ Послуга: *{service}*\n\n👨‍💼 *Оберіть майстра:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(BookingState.choosing_master)

@dp.callback_query(F.data.startswith("master_"))
async def choose_time(call: CallbackQuery, state: FSMContext):
    master = call.data.replace("master_", "")
    await state.update_data(master=master)
    time_buttons = []
    row = []
    for i, time in enumerate(TIMES):
        row.append(InlineKeyboardButton(text=time, callback_data=f"time_{time}"))
        if len(row) == 3:
            time_buttons.append(row)
            row = []
    if row:
        time_buttons.append(row)
    await call.message.edit_text(
        f"✅ Майстер: *{master}*\n\n🕐 *Оберіть час:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=time_buttons)
    )
    await state.set_state(BookingState.choosing_time)

@dp.callback_query(F.data.startswith("time_"))
async def confirm_booking(call: CallbackQuery, state: FSMContext):
    time = call.data.replace("time_", "")
    await state.update_data(time=time)
    data = await state.get_data()
    service_info = SERVICES.get(data["service"], {})
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити запис", callback_data="confirm")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel")],
    ])
    await call.message.edit_text(
        f"📋 *Перевірте ваш запис:*\n\n"
        f"💈 Послуга: *{data['service']}*\n"
        f"👨‍💼 Майстер: *{data['master']}*\n"
        f"🕐 Час: *{data['time']}*\n"
        f"⏱ Тривалість: *{service_info.get('duration', '')}*\n"
        f"💰 Вартість: *{service_info.get('price', '')} грн*\n\n"
        f"Все вірно?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await state.set_state(BookingState.confirming)

@dp.callback_query(F.data == "confirm")
async def booking_confirmed(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.message.edit_text(
        f"🎉 *Чудово!*\n\n"
        f"Ви записані на *{data['service']}*\n"
        f"👨‍💼 Майстер: {data['master']}\n"
        f"🕐 Час: {data['time']}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Це демо-версія бота.*\n"
        f"У реальному боті тут буде:\n"
        f"• Збереження запису в базу даних\n"
        f"• Сповіщення майстру\n"
        f"• Нагадування за годину до візиту\n"
        f"• Підтвердження по SMS\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"_Бот створено як приклад. З питань: @aquaee_",
        parse_mode="Markdown"
    )
    await state.clear()

@dp.callback_query(F.data == "cancel")
async def booking_cancelled(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("❌ Запис скасовано. Почніть знову — натисніть 📅 Записатись")
    await state.clear()

@dp.message(F.text == "📋 Мої записи")
async def my_bookings(message: Message):
    await message.answer(
        "📋 *Ваші записи:*\n\n"
        "⚠️ *Це демо-версія бота.*\n"
        "У реальному боті тут відображались би всі ваші активні записи з можливістю скасування.\n\n"
        "_Бот створено як приклад. З питань: @aquaee_",
        parse_mode="Markdown"
    )

@dp.message(F.text == "ℹ️ Про салон")
async def about(message: Message):
    await message.answer(
        "💈 *Барбершоп Premium*\n\n"
        "Ми професійний барбершоп з досвідом понад 5 років.\n\n"
        "⭐️ Рейтинг: 4.9/5\n"
        "👨‍💼 Майстрів: 3\n"
        "✂️ Послуг: 4\n"
        "📍 Адреса: вул. Прикладна, 1\n\n"
        "⚠️ _Це демо-версія бота — дані вигадані_",
        parse_mode="Markdown"
    )

@dp.message(F.text == "📞 Контакти")
async def contacts(message: Message):
    await message.answer(
        "📞 *Контакти:*\n\n"
        "📱 Телефон: +380 99 123 45 67\n"
        "📍 Адреса: вул. Прикладна, 1\n"
        "🕐 Режим роботи: 10:00 — 20:00\n"
        "📸 Instagram: @barbershop\n\n"
        "⚠️ _Це демо-версія бота — дані вигадані_\n"
        "_З питань створення бота: @aquaee_",
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
