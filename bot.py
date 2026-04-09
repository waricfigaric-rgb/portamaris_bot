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
users = {}  # user_id: name
ticket_counter = 1

# ===== КНОПКИ =====
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Новый тикет")],
        [KeyboardButton(text="📋 Мои тикеты")]
    ],
    resize_keyboard=True
)

category_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💻 Софт"), KeyboardButton(text="🖥 Железо")],
        [KeyboardButton(text="❓ Другое")]
    ],
    resize_keyboard=True
)

priority_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔴 Высокий")],
        [KeyboardButton(text="🟡 Средний")],
        [KeyboardButton(text="🟢 Низкий")]
    ],
    resize_keyboard=True
)

# ===== СОСТОЯНИЯ =====
class Ticket(StatesGroup):
    name = State()
    category = State()
    description = State()
    priority = State()

# ===== СТАРТ =====
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    if message.from_user.id not in users:
        await message.answer("👋 Как вас зовут?")
        await state.set_state(Ticket.name)
    else:
        await message.answer("Бот готов к работе", reply_markup=main_kb)

@dp.message(Ticket.name)
async def get_name(message: types.Message, state: FSMContext):
    users[message.from_user.id] = message.text
    await message.answer("✅ Сохранено!", reply_markup=main_kb)
    await state.clear()

# ===== СОЗДАНИЕ ТИКЕТА =====
@dp.message(F.text == "🛠 Новый тикет")
async def new_ticket(message: types.Message, state: FSMContext):
    await message.answer("Выберите категорию:", reply_markup=category_kb)
    await state.set_state(Ticket.category)

@dp.message(Ticket.category, F.text.in_(["💻 Софт", "🖥 Железо", "❓ Другое"]))
async def category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Опишите проблему (можно с фото):")
    await state.set_state(Ticket.description)

# ===== ОПИСАНИЕ (ТЕКСТ + ФОТО) =====
@dp.message(Ticket.description)
async def description(message: types.Message, state: FSMContext):
    text = message.text if message.text else ""

    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id

    await state.update_data(description=text, photo=photo_id)

    await message.answer("Выберите приоритет:", reply_markup=priority_kb)
    await state.set_state(Ticket.priority)

# ===== ФИНИШ =====
@dp.message(Ticket.priority)
async def finish(message: types.Message, state: FSMContext):
    global ticket_counter

    data = await state.get_data()

    ticket = {
        "id": ticket_counter,
        "user_id": message.from_user.id,
        "name": users.get(message.from_user.id, "Неизвестно"),
        "category": data["category"],
        "description": data["description"],
        "photo": data.get("photo"),
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

    # отправка админу
    if ticket["photo"]:
        await bot.send_photo(ADMIN_ID, ticket["photo"], caption=text)
    else:
        await bot.send_message(ADMIN_ID, text)

    await message.answer(f"✅ Тикет #{ticket_counter} создан", reply_markup=main_kb)

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
