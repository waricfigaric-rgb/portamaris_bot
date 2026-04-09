import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = "PASTE_YOUR_TOKEN_HERE"
ADMIN_ID = 123456789  # замени на свой ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== КНОПКИ =====
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Создать тикет")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

# ===== СОСТОЯНИЯ =====
class Ticket(StatesGroup):
    category = State()
    description = State()
    priority = State()

ticket_counter = 1

# ===== СТАРТ =====
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=kb)

# ===== СОЗДАНИЕ ТИКЕТА =====
@dp.message(F.text == "🛠 Создать тикет")
async def create_ticket(message: types.Message, state: FSMContext):
    await message.answer("Выбери категорию:\nПК / Интернет / Принтер")
    await state.set_state(Ticket.category)

@dp.message(Ticket.category)
async def set_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Опиши проблему:")
    await state.set_state(Ticket.description)

@dp.message(Ticket.description)
async def set_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Срочность: 🔴 Срочно / 🟡 Средне / 🟢 Не срочно")
    await state.set_state(Ticket.priority)

@dp.message(Ticket.priority)
async def finish_ticket(message: types.Message, state: FSMContext):
    global ticket_counter

    data = await state.get_data()

    text = f"""
📩 ТИКЕТ #{ticket_counter}

👤 {message.from_user.full_name}
🆔 {message.from_user.id}

📂 Категория: {data['category']}
📝 Описание: {data['description']}
⚡ Приоритет: {message.text}
"""

    await bot.send_message(ADMIN_ID, text)
    await message.answer(f"✅ Тикет #{ticket_counter} создан!")

    ticket_counter += 1
    await state.clear()

# ===== ПОМОЩЬ =====
@dp.message(F.text == "ℹ️ Помощь")
async def help_cmd(message: types.Message):
    await message.answer("Напишите заявку через кнопку 'Создать тикет'")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())