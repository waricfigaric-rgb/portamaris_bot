import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== "БАЗА" В ПАМЯТИ =====
tickets = []
ticket_counter = 1

# ===== КНОПКИ =====
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Новый тикет")],
        [KeyboardButton(text="📋 Мои тикеты")]
    ],
    resize_keyboard=True
)

# ===== СОСТОЯНИЯ =====
class Ticket(StatesGroup):
    category = State()
    description = State()
    priority = State()

# ===== СТАРТ =====
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Helpdesk бот запущен", reply_markup=kb)

# ===== СОЗДАНИЕ ТИКЕТА =====
@dp.message(F.text == "🛠 Новый тикет")
async def new_ticket(message: types.Message, state: FSMContext):
    await message.answer("Категория: ПК / Интернет / Принтер")
    await state.set_state(Ticket.category)

@dp.message(Ticket.category)
async def category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Опишите проблему:")
    await state.set_state(Ticket.description)

@dp.message(Ticket.description)
async def description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Приоритет: 🔴 / 🟡 / 🟢")
    await state.set_state(Ticket.priority)

@dp.message(Ticket.priority)
async def finish(message: types.Message, state: FSMContext):
    global ticket_counter

    data = await state.get_data()

    ticket = {
        "id": ticket_counter,
        "user_id": message.from_user.id,
        "name": message.from_user.full_name,
        "category": data["category"],
        "description": data["description"],
        "priority": message.text,
        "status": "open"
    }

    tickets.append(ticket)

    text = f"""
📩 ТИКЕТ #{ticket_counter}

👤 {ticket['name']}
📂 {ticket['category']}
📝 {ticket['description']}
⚡ {ticket['priority']}
"""

    await bot.send_message(ADMIN_ID, text)
    await message.answer(f"✅ Тикет #{ticket_counter} создан")

    ticket_counter += 1
    await state.clear()

# ===== МОИ ТИКЕТЫ =====
@dp.message(F.text == "📋 Мои тикеты")
async def my_tickets(message: types.Message):
    user_tickets = [t for t in tickets if t["user_id"] == message.from_user.id and t["status"] == "open"]

    if not user_tickets:
        await message.answer("У вас нет открытых тикетов")
        return

    text = "📋 Ваши тикеты:\n"
    for t in user_tickets:
        text += f"\n#{t['id']} | {t['category']} | {t['priority']}"

    await message.answer(text)

# ===== АДМИН: ВСЕ ТИКЕТЫ =====
@dp.message(Command("all"))
async def all_tickets(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    open_tickets = [t for t in tickets if t["status"] == "open"]

    if not open_tickets:
        await message.answer("Нет открытых тикетов")
        return

    text = "📋 Все тикеты:\n"
    for t in open_tickets:
        text += f"\n#{t['id']} | {t['name']} | {t['category']} | {t['priority']}"

    await message.answer(text)

# ===== АДМИН: ЗАКРЫТЬ =====
@dp.message(Command("close"))
async def close(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        ticket_id = int(message.text.split()[1])

        for t in tickets:
            if t["id"] == ticket_id:
                t["status"] = "closed"
                await message.answer(f"✅ Тикет #{ticket_id} закрыт")
                return

        await message.answer("Тикет не найден")

    except:
        await message.answer("Используй: /close 1")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
