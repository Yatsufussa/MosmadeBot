from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext

from buttons import reply_buttons
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, or_f
from aiogram.utils.formatting import as_list, as_marked_section, Bold

user_private_router = Router()


@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message,state: FSMContext):
    await message.answer("Вас приветствует Магазин Mosmade", replymarkup=reply_buttons.start_kb)


@user_private_router.message(StateFilter(None),F.text.lower() == "Каталог")
@user_private_router.message(Command('catalog'))
async def menu_cmd(message: types.Message):
    await message.answer("Выберите Мужской или Женский Каталог")


@user_private_router.message(F.text.lower() == "Мужской")
@user_private_router.message(Command('m_catalog'))
async def menu_cmd(message: types.Message):
    await message.answer("Выберите Категорию")


@user_private_router.message(F.text.lower() == "Мужской")
@user_private_router.message(Command('m_catalog'))
async def menu_cmd(message: types.Message):
    await message.answer("Выберите Мужской или Женский Каталог")




@user_private_router.message(Command('about'))
async def menu_cmd(message: types.Message):
    await message.answer("О нас мы")


@user_private_router.message(Command('textile'))
async def menu_cmd(message: types.Message):
    await message.answer("У нас такие ткани")


@user_private_router.message(Command('help'))
async def menu_cmd(message: types.Message):
    await message.answer("Жди помощь")
