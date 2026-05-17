import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
 
# ⚠️ ВСТАВЬ СВОЙ ТОКЕН СЮДА:
BOT_TOKEN = os.getenv("BOT_TOKEN")
 
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
 
# ─── Данные салона ───
SERVICES = {
    "💈 Стрижка": {"price": 300, "duration": "45 мин"},
    "🪒 Бритьё": {"price": 200, "duration": "30 мин"},
    "💆 Стрижка + борода": {"price": 450, "duration": "60 мин"},
    "🎨 Окрашивание": {"price": 800, "duration": "90 мин"},
}
 
TIMES = [
    "10:00", "10:45", "11:30",
    "12:15", "13:00", "14:00",
    "15:00", "16:00", "17:00",
    "18:00", "19:00",
]
 
MASTERS = ["✂️ Мастер Александр", "✂️ Мастер Дмитрий", "✂️ Мастер Анна"]
 
class BookingState(StatesGroup):
    choosing_service = State()
    choosing_master = State()
    choosing_time = State()
    confirming = State()
 
# ─── Главное меню ───
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться"), KeyboardButton(text="📋 Мои записи")],
            [KeyboardButton(text="ℹ️ О салоне"), KeyboardButton(text="📞 Контакты")],
        ],
        resize_keyboard=True
    )
 
# ─── /start ───
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в *Барбершоп Premium*!\n\n"
        "Мы рады видеть вас. Выберите действие в меню ниже 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
 
# ─── Записаться ───
@dp.message(F.text == "📅 Записаться")
async def start_booking(message: Message, state: FSMContext):
    buttons = []
    for service, info in SERVICES.items():
        buttons.append([InlineKeyboardButton(
            text=f"{service} — {info['price']}₽ ({info['duration']})",
            callback_data=f"service_{service}"
        )])
 
    await message.answer(
        "🎯 *Выберите услугу:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(BookingState.choosing_service)
 
# ─── Выбрали услугу ───
@dp.callback_query(F.data.startswith("service_"))
async def choose_master(call: CallbackQuery, state: FSMContext):
    service = call.data.replace("service_", "")
    await state.update_data(service=service)
 
    buttons = [[InlineKeyboardButton(text=master, callback_data=f"master_{master}")]
               for master in MASTERS]
 
    await call.message.edit_text(
        f"✅ Услуга: *{service}*\n\n👨‍💼 *Выберите мастера:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(BookingState.choosing_master)
 
# ─── Выбрали мастера ───
@dp.callback_query(F.data.startswith("master_"))
async def choose_time(call: CallbackQuery, state: FSMContext):
    master = call.data.replace("master_", "")
    await state.update_data(master=master)
 
    # Кнопки времени по 3 в ряд
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
        f"✅ Мастер: *{master}*\n\n🕐 *Выберите время:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=time_buttons)
    )
    await state.set_state(BookingState.choosing_time)
 
# ─── Выбрали время ───
@dp.callback_query(F.data.startswith("time_"))
async def confirm_booking(call: CallbackQuery, state: FSMContext):
    time = call.data.replace("time_", "")
    await state.update_data(time=time)
    data = await state.get_data()
 
    service_info = SERVICES.get(data["service"], {})
 
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить запись", callback_data="confirm")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
    ])
 
    await call.message.edit_text(
        f"📋 *Проверьте вашу запись:*\n\n"
        f"💈 Услуга: *{data['service']}*\n"
        f"👨‍💼 Мастер: *{data['master']}*\n"
        f"🕐 Время: *{data['time']}*\n"
        f"⏱ Длительность: *{service_info.get('duration', '')}*\n"
        f"💰 Стоимость: *{service_info.get('price', '')}₽*\n\n"
        f"Всё верно?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await state.set_state(BookingState.confirming)
 
# ─── Подтверждение ───
@dp.callback_query(F.data == "confirm")
async def booking_confirmed(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
 
    # ⚠️ ЭТО ДЕМО-БОТ — реальная запись не сохраняется
    await call.message.edit_text(
        f"🎉 *Отлично!*\n\n"
        f"Вы записаны на *{data['service']}*\n"
        f"👨‍💼 Мастер: {data['master']}\n"
        f"🕐 Время: {data['time']}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Это демо-версия бота.*\n"
        f"В реальном боте здесь будет:\n"
        f"• Сохранение записи в базу данных\n"
        f"• Уведомление мастеру\n"
        f"• Напоминание за час до визита\n"
        f"• Подтверждение по SMS\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"_Бот создан как пример. По вопросам: @aquaee_",
        parse_mode="Markdown"
    )
    await state.clear()
 
# ─── Отмена ───
@dp.callback_query(F.data == "cancel")
async def booking_cancelled(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("❌ Запись отменена. Начните заново — нажмите 📅 Записаться")
    await state.clear()
 
# ─── Мои записи ───
@dp.message(F.text == "📋 Мои записи")
async def my_bookings(message: Message):
    await message.answer(
        "📋 *Ваши записи:*\n\n"
        "⚠️ *Это демо-версия бота.*\n"
        "В реальном боте здесь отображались бы все ваши активные записи с возможностью отмены.\n\n"
        "_Бот создан как пример. По вопросам: @aquaee_",
        parse_mode="Markdown"
    )
 
# ─── О салоне ───
@dp.message(F.text == "ℹ️ О салоне")
async def about(message: Message):
    await message.answer(
        "💈 *Барбершоп Premium*\n\n"
        "Мы профессиональный барбершоп с опытом более 5 лет.\n\n"
        "⭐️ Рейтинг: 4.9/5\n"
        "👨‍💼 Мастеров: 3\n"
        "✂️ Услуг: 4\n"
        "📍 Адрес: ул. Примерная, 1\n\n"
        "⚠️ _Это демо-версия бота — данные вымышленные_",
        parse_mode="Markdown"
    )
 
# ─── Контакты ───
@dp.message(F.text == "📞 Контакты")
async def contacts(message: Message):
    await message.answer(
        "📞 *Контакты:*\n\n"
        "📱 Телефон: +7 (999) 123-45-67\n"
        "📍 Адрес: ул. Примерная, 1\n"
        "🕐 Режим работы: 10:00 — 20:00\n"
        "📸 Instagram: @barbershop\n\n"
        "⚠️ _Это демо-версия бота — данные вымышленные_\n"
        "_По вопросам создания бота: @aquaee_",
        parse_mode="Markdown"
    )
 
async def main():
    await dp.start_polling(bot)
 
if __name__ == "__main__":
    asyncio.run(main())
