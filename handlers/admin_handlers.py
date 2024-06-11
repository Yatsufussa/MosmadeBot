from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from ChatFilter.chat_type import ChatTypeFilter, IsAdmin
from buttons.inline_buttons import create_categories_keyboard
from buttons.reply_buttons import get_keyboard, del_kbd
from database.engine import SessionMaker


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

ADMIN_KB = get_keyboard(
    "Товар",
    "Категория",
    "Каталог",
    placeholder="Выберите действие",
    sizes=(2,),
)

PRODUCT_KB = get_keyboard(
    "Добавить товар",
    "Изменить товар",
    "Удалить товар",
    placeholder="Выберите действие",
    sizes=(2,),
)
CHANGE_PRODUCT_KB = get_keyboard(
    "Имя Товара",
    "Описание Товара",
    "Цену Товара",
    "Фото",
    placeholder="Выберите действие",
    sizes=(2,),
)
CATEGORY_KB = get_keyboard(
    "Добавить категорию",
    "Изменить категорию",
    "Удалить категорию",
    placeholder="Выберите действие",
    sizes=(2,),
)
CHANGE_CATEGORY_KB = get_keyboard(
    "Изменить Имя",
    "Изменить Пол",
    placeholder="Выберите действие",
    sizes=(2,),
)

SEX_KB = get_keyboard(
    'Мужской',
    'Женский'
)


class CategoryState(StatesGroup):
    Type = State()
    Add = State()
    new_sex = State()
    new_c_name = State()
    Delete = State()
    Change = State()
    ch_sex = State()
    ch_c_name = State()

def create_categories_keyboard(categories, page, total_pages):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for category in categories:
        button = InlineKeyboardButton(text=category.name, callback_data=f"category:{category.id}")
        keyboard.add(button)

    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page:{page + 1}"))

    keyboard.row(*navigation_buttons)
    keyboard.add(InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
    keyboard.add(InlineKeyboardButton(text="Создать новую категорию", callback_data="create_category"))

    return keyboard
async def get_categories(page=1, limit=5):
    # Функция для получения категорий с пагинацией из базы данных
    # Пример возвращаемых данных
    total_categories = 12  # Общее количество категорий
    categories = [{"id": i, "name": f"Category {i}"} for i in
                  range((page - 1) * limit, min(page * limit, total_categories))]
    return categories, total_categories


@admin_router.message(Category.Type, Text(equals="Добавить") | Text(equals="Удалить") | Text(equals="Изменить"))
async def category_operation_type(message: types.Message, state: FSMContext):
    if message.text == "Добавить":
        await message.answer("Выберите Пол для Категории", reply_markup=SEX_KB)
        await state.set_state(CategoryState.new_sex)
    elif message.text == "Удалить":
        async with SessionMaker() as session:
            categories, total = await get_categories(session)
            keyboard = create_categories_keyboard(categories, page=1, total_pages=(total // 5) + 1)
            await message.answer("Выберите Категорию для удаления", reply_markup=keyboard)
        await state.set_state(CategoryState.Delete)
    elif message.text == "Изменить":
        categories, total = await get_categories()
        keyboard = create_categories_keyboard(categories, page=1, total_pages=(total // 5) + 1)
        await message.answer("Выберите Категорию", reply_markup=keyboard)
        await state.set_state(CategoryState.Change)


@admin_router.callback_query(Text(startswith="page:"))
async def pagination_callback(call: types.CallbackQuery, state: FSMContext):
    page = int(call.data.split(":")[1])
    categories, total = await get_categories(page=page)
    keyboard = create_categories_keyboard(categories, page=page, total_pages=(total // 5) + 1)
    await call.message.edit_reply_markup(reply_markup=keyboard)


@admin_router.callback_query(Text(equals="create_category"))
async def create_category_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введите имя новой категории:")
    await state.set_state(CategoryState.new_c_name)


@admin_router.message(CategoryState.new_c_name)
async def set_category_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['category_name'] = message.text
    await message.answer("Теперь отправьте фото для категории:")
    await state.set_state(CategoryState.Add)


@admin_router.message(CategoryState.Add, content_types=types.ContentType.PHOTO)
async def set_category_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['category_photo'] = message.photo[-1].file_id
    await message.answer("Категория успешно создана!")
    # Сохранение категории в базе данных
    # save_category_to_db(data['category_name'], data['category_photo'])
    await state.finish()


# Добавление Новой Категории
@admin_router.message(Category.new_sex, F.text == 'Мужское' or F.text == 'Женское')
async def add_category_sex(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите название новой Категории", reply_markup=del_kbd
    )
    await state.set_state(Category.new_c_name)


@admin_router.message(Category.new_c_name, F.text)
async def add_category_name(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы успешно добавили новую категорию", reply_markup=ADMIN_KB
    )
    await state.clear()


# Изменить Категорию

@admin_router.message(Category.Change, F.text == "Изменить категорию")
async def change_category(message: types.Message, state: FSMContext):
    await message.answer(
        "Что хотите Изменить", reply_markup=CHANGE_CATEGORY_KB)
    if message.text == "Имя":
        await message.answer("Укажите новое имя категории")
        await state.set_state(Category.ch_c_name)

    elif message.text == "Пол":
        await message.answer("Укажите новый пол для категории")
        await state.set_state(Category.ch_sex)

    else:
        pass


@admin_router.message(Category.ch_c_name, F.text == "Изменить Имя")
async def change_category_name(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы успешно изменили имя категории", reply_markup=ADMIN_KB
    )
    await state.clear()


@admin_router.message(Category.ch_sex, F.text == "Изменить Пол")
async def change_category_sex(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы успешно изменили пол категории", reply_markup=ADMIN_KB
    )
    await state.clear()


# Удалить Категоритю
@admin_router.message(Category.Delete, F.text == "Удалить")
async def delete_category(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы успешно удалили категорию", reply_markup=ADMIN_KB
    )
    await state.clear()


# Ветка Товара
class Product(StatesGroup):
    Category = State()

    Type = State()

    delete_product = State

    Change_product = State()
    p_category = State()
    ch_p_name = State()
    ch_p_description = State()
    ch_p_price = State()
    ch_p_photo = State()

    category = State()
    p_name = State()
    p_description = State()
    p_price = State()
    p_photo = State()


@admin_router.message(Product.category, F.text)
async def product_operation_type(message: types.Message, state: FSMContext):
    await message.answer("Категория выбрана.Выберите операцию.", reply_markup=PRODUCT_KB)
    await state.set_state(Product.Type)


@admin_router.message(Product.Type, F.text == "Добавить" or F.text == "Удалить" or F.text == "Изменить")
async def category_operation_type(message: types.Message, state: FSMContext):
    if message.text == "Добавить":
        await message.answer("Выберите имя продукта", reply_markup=SEX_KB)
        await state.set_state(Product.p_name)

    elif message.text == "Удалить":
        await message.answer("Выберите Продукт для удаления")
        await state.set_state(Product.delete_product)

    elif message.text == "Изменить":
        await message.answer("Выберите Продукт для Изменения")
        await state.set_state(Product.Change_product)
    else:
        await message.answer("Выбери Вариант действия")


# Add Product
@admin_router.message(Product.p_name, F.text)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(p_name=message.text)
    await message.answer("Введите описание товара")
    await state.set_state(Product.p_description)


# Проверка
@admin_router.message(Product.p_name)
async def add_product_name(message: types.Message, state: FSMContext):
    await message.answer("Напиши имя Товара")


@admin_router.message(Product.p_description, F.text)
async def add_product_description(message: types.Message, state: FSMContext):
    await state.update_data(p_description=message.text)
    await message.answer("Введите цену товара за 1 ед")
    await state.set_state(Product.p_price)


# Проверка
@admin_router.message(Product.p_description)
async def add_product_description(message: types.Message, state: FSMContext):
    await message.answer("Напиши описание")


@admin_router.message(Product.p_price, F.text)
async def add_product_price(message: types.Message, state: FSMContext):
    await state.update_data(p_price=message.text)
    await message.answer("Отправьте фото товара(jpg,png)")
    await state.set_state(Product.p_photo)


# Проверка
@admin_router.message(Product.p_price)
async def add_product_price(message: types.Message, state: FSMContext):
    await message.answer('Напиши цену цифрами')


@admin_router.message(Product.p_photo, F.photo)
async def add_product_photo(message: types.Message, state: FSMContext, session: AsyncSession):
    photo_id = message.photo[-1].file_id
    await state.update_data(p_photo=photo_id)
    await message.answer("Фото товара добавлено. Теперь вы можете добавить еще один товар или завершить.",
                         reply_markup=ADMIN_KB)
    data = await state.get_data()
    await message.answer(str(data))
    await orm_add_product(AsyncSession, data)
    await state.clear()


# Проверка
@admin_router.message(Product.p_photo)
async def add_product_photo(message: types.Message, state: FSMContext):
    await message.answer("Отправь Фото Товара")


@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == Product.p_name:
        await message.answer('Предидущего шага нет, или введите название товара или напишите "отмена"')
        return

    previous = None
    for step in Product.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу \n {Product.texts[previous.state]}")
            return
        previous = step


# Изменение Товара

@admin_router.message(Product.Change_product, F.text == "Изменить Товар")
async def change_category(message: types.Message, state: FSMContext):
    await message.answer(
        "Что хотите Изменить", reply_markup=CHANGE_PRODUCT_KB)

    if message.text == "Имя Товара":
        await message.answer("Напишите новое имя товара")
        await state.set_state(Product.ch_p_name)

    elif message.text == "Описание Товара":
        await message.answer("Напишите новое описание")
        await state.set_state(Product.ch_p_description)

    elif message.text == "Цену Товара":
        await message.answer("Укажите новую цену товара")
        await state.set_state(Product.ch_p_price)

    elif message.text == "Фото":
        await message.answer("Пришлите Новую Фотаграфию")
        await state.set_state(Product.ch_p_photo)

    else:
        pass


@admin_router.message(Product.ch_p_name)
async def ch_product_name(message: types.Message, state: FSMContext):
    await message.answer('Изменено Успешно', reply_markup=ADMIN_KB)
    await state.clear()


@admin_router.message(Product.ch_p_description)
async def ch_product_description(message: types.Message, state: FSMContext):
    await message.answer('Изменено Успешно', reply_markup=ADMIN_KB)
    await state.clear()


@admin_router.message(Product.ch_p_price)
async def ch_product_price(message: types.Message, state: FSMContext):
    await message.answer('Изменено Успешно', reply_markup=ADMIN_KB)
    await state.clear()


@admin_router.message(Product.ch_p_photo)
async def ch_product_photo(message: types.Message, state: FSMContext):
    await message.answer('Изменено Успешно', reply_markup=ADMIN_KB)
    await state.clear()


#Удаление Товара
@admin_router.message(Product.delete_product)
async def del_product(message: types.Message, state: FSMContext):
    await message.answer('Товар Удален', reply_markup=ADMIN_KB)
    await state.clear()
