import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.storage.base import StorageKey
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv('API_TOKEN')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

storage = RedisStorage.from_url(REDIS_URL)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=storage)

with open('quest.json', 'r', encoding='utf-8') as f:
    QUEST_DATA = json.load(f)


class Quest(StatesGroup):
    waiting_for_answer = State()
    waiting_for_photo = State()


# Данные с добавленными подсказками
QUEST_DATA = [
    {
        "riddle": """Мы встретились под яйцами коня.
Центральней место надо поискать.
А всадника фамилия..""",
        "correct_answer": "жуков",
        "hint": "Стены цвет сзади красный. Фамилии начало Ж",
        "next_instruction": "Жду селфи с яйцами коня🚶‍♂️",
        "compliment": "Блестяще⭐️"
    },
    {
        "riddle": """Сквозь ярмарку к великому поэту
Пройди скорей народною тропой.
Взгляни в печальное лиц его
Кого восславил он...""",
        "correct_answer": "свободу",
        "hint": "Пересекает он дорогу в тверь. На тумбе стих.",
        "next_instruction": "Уже ты знаешь что хочу я от тебя.\nМне нужно селфи👙",
        "compliment": "Какая красота, сейчас ослепну😍"
    },
    {
        "riddle": """Иди туда, откуда он пришел к любителю высот и гор бульваром
С какого года он стоит и мёрзнет без альпенистки своей и скалалалалазки своей""",
        "correct_answer": "1995",
        "hint": "Не путай с Окуджавой, наш друг на небо смотрит",
        "next_instruction": "Надень же шапку, чтоб не мерз Владимир\nИ селфи новогодний мне пришли😼",
        "compliment": "Милахи🫣"
    },
    {
        "riddle": """Есть рядом сад уединенный.
В саду подарок городу Москве от мэрии Парижа.
Мне нужно имя...""",
        "correct_answer": "гюго",
        "hint": "Их все Отвергли, он про это пишет. А сад тот Эрмитаж.",
        "next_instruction": "Давай давай же фоточку с Гюго",
        "compliment": "Вы просто молодцы😘\nОсталось получить награду🎄"
    }
]

START_MESSAGE = """Начинаем же квест!

В москве есть 5 локаций.
Тебе их непременно стоит отыскать.
Возьми с собою шапку,
Что не жалеешь ты отдать.
"""

FINISH_MESSAGE = """Скажи хозяевам коня 'МЫ ВИДЕЛИ КОНЯ ЯИЧКИ'
`55.771102, 37.612979`"""


active_users = set()

# Функция для создания клавиатуры с кнопкой подсказки
def get_quest_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Нужна подсказка! 💡")
    return builder.as_markup(resize_keyboard=True)


@dp.message(Command("start"))
async def start_quest(message: types.Message, state: FSMContext):
    active_users.add(message.from_user.id)  # Добавляем пользователя в активные
    data = await state.get_data()
    if not data:
        await state.update_data(current_step=0)
    await message.answer(START_MESSAGE, reply_markup=get_quest_keyboard())
    current_step = (await state.get_data()).get('current_step', 0)
    await message.answer(QUEST_DATA[current_step]["riddle"])
    await state.set_state(Quest.waiting_for_answer)

# Обработчик кнопки подсказки
@dp.message(F.text == "Нужна подсказка! 💡")
async def give_hint(message: types.Message, state: FSMContext):
    active_users.add(message.from_user.id)  # Добавляем пользователя в активные
    data = await state.get_data()
    step = data.get('current_step', 0)
    hint_text = QUEST_DATA[step]["hint"]
    await message.answer(f"Лови подсказку: {hint_text}")

@dp.message(Quest.waiting_for_answer)
async def check_answer(message: types.Message, state: FSMContext):
    # Если пользователь нажал на кнопку подсказки, этот хендлер не сработает,
    # так как выше есть специальный фильтр F.text == "Нужна подсказка! 💡"
    active_users.add(message.from_user.id)
    data = await state.get_data()
    step = data['current_step']

    user_answer = message.text.lower().strip()
    correct_answer = QUEST_DATA[step]["correct_answer"].lower()

    if user_answer == correct_answer:
        await message.answer(QUEST_DATA[step]["next_instruction"],
                             reply_markup=types.ReplyKeyboardRemove())  # Убираем кнопку, пока ждем фото
        await state.set_state(Quest.waiting_for_photo)
    else:
        await message.answer("Неверно. Попробуй еще раз или воспользуйся подсказкой!")


@dp.message(Quest.waiting_for_photo, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    step = data['current_step'] + 1
    await message.answer(QUEST_DATA[step-1]["compliment"], reply_markup=get_quest_keyboard())


    if step < len(QUEST_DATA):
        await state.update_data(current_step=step)
        await message.answer(QUEST_DATA[step]["riddle"])
        await state.set_state(Quest.waiting_for_answer)
    else:
        await message.answer(FINISH_MESSAGE, reply_markup=types.ReplyKeyboardRemove())
        await state.clear()

@dp.message()
async def handle_unknown_state(message: types.Message, state: FSMContext):
    # Проверяем, есть ли активное состояние у пользователя
    current_state = await state.get_state()
    if current_state is None:
        # Если состояния нет, предлагаем начать заново
        await message.answer(
            "Кажется, ваш прогресс был сброшен. "
            "Хотите начать квест заново? /start"
        )
    else:
        # Если состояние есть, но бот не знает, что с ним делать — уточняем
        await message.answer(
            "Я не понял ваше сообщение. "
            "Попробуйте ответить на вопрос или воспользуйтесь подсказкой."
        )



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
