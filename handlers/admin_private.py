from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from ChatFilter.chat_type import ChatTypeFilter, IsAdmin
from buttons.reply_buttons import get_keyboard

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Изменить товар",
    "Удалить товар",
    "Я так, просто посмотреть зашел",
    placeholder="Выберите действие",
    sizes=(2, 1, 1),
)


@admin_router.message(Command("admin"))
async def add_product(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Я так, просто посмотреть зашел")
async def starring_at_product(message: types.Message):
    await message.answer("ОК, вот список товаров")


@admin_router.message(F.text == "Изменить товар")
async def change_product(message: types.Message):
    await message.answer("ОК, вот список товаров")


@admin_router.message(F.text == "Удалить товар")
async def delete_product(message: types.Message):
    await message.answer("Выберите товар(ы) для удаления")


#Код ниже для машины состояний (FSM)
# Добавление Товара
class AddProduct(StatesGroup):
    sex = State()
    add_category = State()
    old_category = State()
    p_name = State()
    p_description = State()
    p_price = State()
    p_photo = State()

    texts = {
        'AddProduct:sex': 'Введите название заново:',
        'AddProduct:add_category': 'Выберите тип категории заново:',
        'AddProduct:old_category': 'Выберите тип категории заново:',
        'AddProduct:p_name': 'Введите название продукта заново:',
        'AddProduct:p_description': 'Введите описание заново:',
        'AddProduct:p_price': 'Введите стоимость заново:',
        'AddProduct:p_photo': 'Отправьте фото заново:',
    }



@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите Пол", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.sex)


@admin_router.message(AddProduct.sex, F.text)
async def add_name(message: types.Message, state: FSMContext):
    await message.answer("Новая Категория или Старая")
    if message.text == 'Новая':
        await message.answer("Введите название новой категории")
        await state.set_state(AddProduct.add_category)
    elif message.text == 'Старая':
        await message.answer("Выберите категорию")
        await state.set_state(AddProduct.old_category)
    else:
        pass

# Проверка
@admin_router.message(AddProduct.sex)
async def add_name(message: types.Message, state: FSMContext):
    await message.answer("Напиши Мужское или Женское либо нажми на кнопку")


@admin_router.message(AddProduct.add_category, F.text)
async def add_new_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Введите название товара")
    await state.set_state(AddProduct.p_name)

# Проверка
@admin_router.message(AddProduct.add_category)
async def add_new_category(message: types.Message, state: FSMContext):
    await message.answer("Введи или Новая или Старая")


@admin_router.message(AddProduct.old_category, F.text)
async def add_existing_category(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара")
    await state.set_state(AddProduct.p_name)

# Проверка
@admin_router.message(AddProduct.old_category)
async def add_existing_category(message: types.Message, state: FSMContext):
    await message.answer("Введи или Новая или Старая")


@admin_router.message(AddProduct.p_name, F.text)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(p_name=message.text)
    await message.answer("Введите описание товара")
    await state.set_state(AddProduct.p_description)

# Проверка
@admin_router.message(AddProduct.p_name)
async def add_product_name(message: types.Message, state: FSMContext):
    await message.answer("Напиши имя Товара")


@admin_router.message(AddProduct.p_description, F.text)
async def add_product_description(message: types.Message, state: FSMContext):
    await state.update_data(p_description=message.text)
    await message.answer("Введите цену товара за 1 ед")
    await state.set_state(AddProduct.p_price)

# Проверка
@admin_router.message(AddProduct.p_description)
async def add_product_description(message: types.Message, state: FSMContext):
    await message.answer("Напиши описание")



@admin_router.message(AddProduct.p_price, F.text)
async def add_product_price(message: types.Message, state: FSMContext):
    await state.update_data(p_price=message.text)
    await message.answer("Отправьте фото товара(jpg,png)")
    await state.set_state(AddProduct.p_photo)

# Проверка
@admin_router.message(AddProduct.p_price)
async def add_product_price(message: types.Message, state: FSMContext):
    await message.answer('Напиши цену цифрами')


@admin_router.message(AddProduct.p_photo, F.photo)
async def add_product_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(p_photo=photo_id)
    await message.answer("Фото товара добавлено. Теперь вы можете добавить еще один товар или завершить.",
                         reply_markup=ADMIN_KB)
    data = await state.get_data()
    await message.answer(str(data))
    await state.clear()

# Проверка
@admin_router.message(AddProduct.p_photo)
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

    if current_state == AddProduct.p_name:
        await message.answer('Предидущего шага нет, или введите название товара или напишите "отмена"')
        return

    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу \n {AddProduct.texts[previous.state]}")
            return
        previous = step

# Изменение Товара


