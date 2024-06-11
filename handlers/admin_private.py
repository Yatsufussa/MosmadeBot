from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, Message

from sqlalchemy.ext.asyncio import AsyncSession

from ChatFilter.chat_type import ChatTypeFilter, IsAdmin
import buttons.inline_buttons as kb
from buttons.reply_buttons import get_keyboard
from database.engine import SessionMaker
from database.engine import *
from database.orm_queries import orm_add_category, orm_update_category_name, orm_delete_category, \
    orm_get_category_by_id, orm_add_product, orm_get_categories, orm_get_product_by_id, orm_update_product_name, \
    orm_update_product_description, orm_update_product_price, orm_update_product_photo, orm_delete_product_by_id, \
    orm_update_category_sex

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


# region ADMINS CATEGORY MANIPULATION STATES
class AddCategory(StatesGroup):
    add_name = State()
    add_sex  = State()


class ChangeCategory(StatesGroup):
    ch_name = State()
    ch_sex  = State()


class DeleteCategory(StatesGroup):
    waiting_for_confirmation = State()


# endregion

# region ADMINS PRODUCT MANIPULATION STATES
class AddProduct(StatesGroup):
    add_category    = State()
    add_name        = State()
    add_description = State()
    add_price       = State()
    add_photo       = State()

class ChangeProduct(StatesGroup):
    ch_name        = State()
    ch_description = State()
    ch_price       = State()
    ch_photo       = State()

class DeleteProduct(StatesGroup):
    delete_product = State()
# endregion


# region ADMIN PANEL MAIN CATALOG PRODUCTS CATEGORIES
@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer('Возможные команды: /stop',
                                reply_markup=kb.admin_main)

@admin_router.message(Command("stop"))
async def admin_stop(message: types.Message):
    await message.delete()
    await message.answer('Вы в Админской части поздравляю',
                                reply_markup=kb.admin_main)


@admin_router.callback_query(F.data == 'category')
async def admin_category(callback: CallbackQuery):
    await callback.answer('Вы нажали на категорию')
    await callback.message.edit_text('Действие для Категории',
                                            reply_markup=kb.admin_category)


@admin_router.callback_query(F.data == 'product')
async def admin_product(callback: CallbackQuery):
    await callback.answer('Вы нажали на Продукт')
    await callback.message.edit_text('Действие для Товара',
                                            reply_markup=kb.admin_product)


@admin_router.callback_query(F.data == 'catalog')
async def admin_catalog(callback: CallbackQuery):
    await callback.message.edit_text('Выберите Категорию',
                                            reply_markup=await kb.catalog_categories_menu())
# endregion


# region ADMIN CATEGORY ADD, CHANGE, DELETE Handlers
# region ADD CATEGORY
@admin_router.callback_query(F.data == 'add_category')
async def admin_add_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddCategory.add_name)
    await callback.answer('')
    await callback.message.answer('Введите имя для новой категории', reply_markup=ReplyKeyboardRemove())


@admin_router.message(AddCategory.add_name)
async def admin_add_category_name(message: Message, state=FSMContext):
    category_name = message.text

    # Validate category name length
    if not (2 <= len(category_name) <= 30):
        await message.answer(
            "Имя категории должно быть длиной от 2 до 30 символов. Пожалуйста, введите допустимое имя...")
        return

    await state.update_data(name=category_name)
    await message.answer('Введите пол для Категории (Мужской или Женский)', reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddCategory.add_sex)


@admin_router.message(AddCategory.add_sex)
async def admin_add_category_sex(message: Message, state=FSMContext):
    sex = message.text.strip().lower()

    # Validate sex input
    if sex not in {'мужской', 'женский'}:
        await message.answer('Пол должен быть "Мужской" или "Женский". Пожалуйста, попробуйте снова.')
        return

    # Normalize sex input
    sex = 'Мужской' if sex == 'мужской' else 'Женский'

    data = await state.get_data()
    category_data = {'name': data['name'], 'sex': sex}

    try:
        await orm_add_category(category_data)
        await message.answer("Категория успешно добавлена", reply_markup=kb.admin_category)
    except Exception as e:
        await message.answer(f"Произошла ошибка при добавлении категории: {e}")

    await state.clear()

# endregion ADD CATEGORY

# region CHANGE CATEGORY NAME AND SEX
@admin_router.callback_query(F.data == 'change_category')
async def category_operation_type(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text(text='Выберите категорию.', reply_markup=await kb.categories())


# Handler when a category is selected
@admin_router.callback_query(F.data.startswith('category_'))
async def select_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split('_')[-1])
    category = await orm_get_category_by_id(category_id)
    if category:
        await state.update_data(category_id=category_id)
        await callback.answer('')
        await callback.message.edit_text(
            text=f'Вы выбрали категорию {category.name}({category.sex}) с ID {category_id}.\nЧто изменить?',
            reply_markup=kb.admin_category_change
        )
    else:
        await callback.answer('Категория не найдена.', show_alert=True)


# Handler to start the process of changing the category name
@admin_router.callback_query(F.data == 'change_c_name')
async def start_change_category_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeCategory.ch_name)
    await callback.answer('')
    await callback.message.answer('Введите новое имя категории', reply_markup=ReplyKeyboardRemove())


# Handler to process the new category name
@admin_router.message(ChangeCategory.ch_name)
async def set_new_category_name(message: Message, state: FSMContext):
    new_name = message.text.strip()

    # Validate new category name length
    if not (2 <= len(new_name) <= 30):
        await message.answer("Имя категории должно быть длиной от 2 до 30 символов. Пожалуйста, введите допустимое имя.")
        return

    data = await state.get_data()
    category_id = data.get('category_id')

    async with SessionMaker() as session:
        updated = await orm_update_category_name(session, category_id, new_name)

    if updated:
        await message.answer(f'Имя категории обновлено на {new_name}.', reply_markup=kb.admin_category)
    else:
        await message.answer(f'Категория с ID {category_id} не найдена.', reply_markup=kb.admin_category)
    await state.clear()


@admin_router.callback_query(F.data == 'change_c_sex')
async def category_operation_type(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeCategory.ch_sex)
    await callback.answer('')
    await callback.message.answer('Введите новый пол для категории (Мужской или Женский)', reply_markup=ReplyKeyboardRemove())


@admin_router.message(ChangeCategory.ch_sex)
async def change_category_sex(message: Message, state: FSMContext):
    new_sex = message.text.strip().lower()

    # Validate new sex input
    if new_sex not in {'мужской', 'женский'}:
        await message.answer('Пол должен быть "Мужской" или "Женский". Пожалуйста, попробуйте снова.')
        return

    # Normalize sex input
    new_sex = 'Мужской' if new_sex == 'мужской' else 'Женский'

    data = await state.get_data()
    category_id = data.get('category_id')

    async with SessionMaker() as session:
        updated = await orm_update_category_sex(session, category_id, new_sex)

    if updated:
        await message.answer(f'Пол категории обновлен на {new_sex}.', reply_markup=kb.admin_category)
    else:
        await message.answer(f'Категория с ID {category_id} не найдена.', reply_markup=kb.admin_category)
    await state.clear()


# endregion

# region DELETE CATEGORY
@admin_router.callback_query(F.data == 'delete_category')
async def category_operation_type(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Выберите категорию.', reply_markup=await kb.select_categories())


@admin_router.callback_query(F.data.startswith('select_category_'))
async def select_category_to_delete(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split('_')[-1])
    await state.update_data(category_id=category_id)
    await callback.answer('')
    await callback.message.edit_text(
        text=f'Вы выбрали категорию {category_id}.\nВы уверены, что хотите удалить эту категорию? (Y/N)'
    )
    await state.set_state(DeleteCategory.waiting_for_confirmation)


@admin_router.message(DeleteCategory.waiting_for_confirmation)
async def confirm_category_deletion(message: Message, state: FSMContext):
    confirmation = message.text.lower()
    data = await state.get_data()
    category_id = data.get('category_id')

    if confirmation == 'y':
        # Use async session to delete the category
        async with SessionMaker() as session:
            deleted = await orm_delete_category(session, category_id)

        if deleted:
            await message.answer(f'Категория с ID {category_id} была удалена.\nВы в разделе категории',
                                 reply_markup=kb.admin_category)
        else:
            await message.answer(f'Категория с ID {category_id} не найдена.', reply_markup=kb.admin_category)
    elif confirmation == 'n':
        await message.answer('Удаление категории отменено.', reply_markup=kb.admin_category)
    else:
        await message.answer('Неверный ввод. Пожалуйста, введите Y для подтверждения или N для отмены.',
                             reply_markup=ReplyKeyboardRemove())
        return

    await state.clear()


# endregion delete
@admin_router.callback_query(F.data == 'to_admin_category')
async def admin_main_back(callback: CallbackQuery):
    await callback.answer('Вы на в пункте категории')
    await callback.message.edit_text('Выберите Действие для Категории', reply_markup=kb.admin_category)


@admin_router.callback_query(F.data == 'to_admin_main')
async def admin_main_back(callback: CallbackQuery):
    await callback.answer('Вы на Главной')
    await callback.message.edit_text('Выберите что будете менять', reply_markup=kb.admin_main)


# endregion

# region ADMIN PRODUCT ADD, CHANGE, DELETE Handlers
# region Add PRODUCT
@admin_router.callback_query(F.data == 'add_product')
async def admin_add_product(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.add_category)
    await callback.answer('')
    await callback.message.edit_text('Выберите Категорию Товара', reply_markup=await kb.pcategory_keyboard())


@admin_router.callback_query(F.data.startswith('pcategory_'))
async def select_category_for_product(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split('_')[-1])
    await state.update_data(category_id=category_id)
    await callback.answer('')
    await callback.message.answer('Введите имя нового товара', reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddProduct.add_name)


@admin_router.message(AddProduct.add_name)
async def admin_add_product_name(message: Message, state=FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Введите Описание Товара одним сообщением', reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddProduct.add_description)


@admin_router.message(AddProduct.add_description)
async def admin_add_product_description(message: Message, state=FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Введите цену товара только числами(Сум)', reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddProduct.add_price)


@admin_router.message(AddProduct.add_price)
async def admin_add_product_price(message: Message, state=FSMContext):
    await state.update_data(price=message.text)
    await message.answer('Отправьте фотографию Товара', reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddProduct.add_photo)


@admin_router.message(AddProduct.add_photo, F.photo)
async def admin_add_product_photo(message: Message, state=FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()
    category_id = data['category_id']
    name = data['name']
    description = data['description']
    price = float(data['price'])  # Ensure price is a float
    photo = data['photo']

    # Save the new product to the database
    await orm_add_product(name, description, price, category_id, photo)

    await message.answer(f'Товар {name} успешно добавлен в категорию №{category_id}', reply_markup=kb.admin_product)
    await state.clear()


# endregion

#  region CHANGE PRODUCT
@admin_router.callback_query(F.data == 'change_product')
async def admin_main_back(callback: CallbackQuery):
    await callback.answer('Вы в пункте Продукты')
    await callback.message.edit_text('Выберите из Какой Категории Продукт',
                                     reply_markup=await kb.pchcategory_keyboard())


@admin_router.callback_query(F.data.startswith('pchcategory_'))
async def select_category_for_product(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    category_id = int(data[1])
    page = int(data[2]) if len(data) == 3 else 1  # Default to page 1 if no page is provided
    await state.update_data(category_id=category_id)
    await callback.answer('')

    # Ensure the message content changes to avoid the "message is not modified" error
    products_markup = await kb.products_by_category(category_id, page)
    await callback.message.edit_text(f'Выберите продукт (Страница {page})', reply_markup=products_markup)


@admin_router.callback_query(F.data.startswith('product_'))
async def show_product_details(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[1])
    product = await orm_get_product_by_id(product_id)

    if product:
        await state.update_data(product_id=product_id)  # Store product_id in state
        text = (
            f"Название: {product.p_name}\n"
            f"Описание: {product.p_description}\n"
            f"Цена: {product.p_price} Сум\n\n\n"
            "ВЫБЕРИТЕ ЧТО ХОТИТЕ ИЗМЕНИТЬ"
        )
        if product.image_url:  # Using the image_url for the photo
            await callback.message.delete()  # Delete the previous message
            await callback.message.answer_photo(photo=product.image_url, caption=text,
                                                reply_markup=kb.admin_product_change)
        else:
            await callback.message.edit_text(text, reply_markup=kb.admin_main)
    else:
        await callback.message.edit_text("Продукт не найден", reply_markup=kb.admin_main)


@admin_router.callback_query(F.data == 'change_p_name')
async def start_change_product_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeProduct.ch_name)
    await callback.answer('')
    await callback.message.answer('Введите новое имя продукта', reply_markup=ReplyKeyboardRemove())


@admin_router.message(ChangeProduct.ch_name)
async def set_new_product_name(message: Message, state: FSMContext):
    new_name = message.text
    data = await state.get_data()
    product_id = data.get('product_id')

    async with SessionMaker() as session:
        updated = await orm_update_product_name(session, product_id, new_name)

    if updated:
        await message.answer(f'Имя продукта обновлено на {new_name}.', reply_markup=kb.admin_product)
    else:
        await message.answer(f'Продукт с ID {product_id} не найден.', reply_markup=kb.admin_product)
    await state.clear()


@admin_router.callback_query(F.data == 'change_p_description')
async def start_change_product_description(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeProduct.ch_description)
    await callback.answer('')
    await callback.message.answer('Введите новое описание продукта', reply_markup=ReplyKeyboardRemove())


@admin_router.message(ChangeProduct.ch_description)
async def set_new_product_description(message: Message, state: FSMContext):
    new_description = message.text
    data = await state.get_data()
    product_id = data.get('product_id')

    async with SessionMaker() as session:
        updated = await orm_update_product_description(session, product_id, new_description)

    if updated:
        await message.answer(f'Описание продукта обновлено на {new_description}.', reply_markup=kb.admin_product)
    else:
        await message.answer(f'Продукт с ID {product_id} не найден.', reply_markup=kb.admin_product)
    await state.clear()


@admin_router.callback_query(F.data == 'change_p_price')
async def start_change_product_price(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeProduct.ch_price)
    await callback.answer('')
    await callback.message.answer('Введите новое имя продукта', reply_markup=ReplyKeyboardRemove())


@admin_router.message(ChangeProduct.ch_price)
async def set_new_product_price(message: Message, state: FSMContext):
    new_price = int(message.text)
    data = await state.get_data()
    product_id = data.get('product_id')

    async with SessionMaker() as session:
        updated = await orm_update_product_price(session, product_id, new_price)

    if updated:
        await message.answer(f'Имя категории обновлено на {new_price}.', reply_markup=kb.admin_product)
    else:
        await message.answer(f'Продукт с ID {product_id} не найден.', reply_markup=kb.admin_product)
    await state.clear()


@admin_router.callback_query(F.data == 'change_p_photo')
async def start_change_product_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeProduct.ch_photo)
    await callback.answer('')
    await callback.message.answer('Отправьте новое фото продукта', reply_markup=ReplyKeyboardRemove())


@admin_router.message(ChangeProduct.ch_photo, F.photo)
async def set_new_product_photo(message: Message, state: FSMContext):
    new_photo = message.photo[-1].file_id
    data = await state.get_data()
    product_id = data.get('product_id')

    async with SessionMaker() as session:
        updated = await orm_update_product_photo(session, product_id, new_photo)

    if updated:
        await message.answer(f'Имя категории обновлено на {new_photo}.', reply_markup=kb.admin_product)
    else:
        await message.answer(f'Продукт с ID {product_id} не найден.', reply_markup=kb.admin_product)
    await state.clear()


# endregion

# region Delete Product

@admin_router.callback_query(F.data == 'delete_product')
async def admin_main_back(callback: CallbackQuery):
    await callback.answer('Удаление')
    await callback.message.edit_text('Выберите из Какой Категории Продукт для удаления',
                                     reply_markup=await kb.pdcategory_keyboard())

@admin_router.callback_query(F.data.startswith('pdcategory_'))
async def select_category_for_product(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    category_id = int(data[1])
    page = int(data[2]) if len(data) == 3 else 1  # Default to page 1 if no page is provided
    await state.update_data(category_id=category_id)
    await callback.answer('')

    # Ensure the message content changes to avoid the "message is not modified" error
    products_markup = await kb.products_to_delete(category_id, page)
    await callback.message.edit_text(f'Выберите продукт для удаления (Страница {page})', reply_markup=products_markup)

@admin_router.callback_query(F.data.startswith('dproduct_'))
async def show_product_details(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[1])
    product = await orm_get_product_by_id(product_id)

    if product:
        await state.update_data(product_id=product_id, product_name=product.p_name)  # Store product_id and name in state
        text = (
            f"Название: {product.p_name}\n"
            f"Описание: {product.p_description}\n"
            f"Цена: {product.p_price} Сум\n\n\n"
            "Вы уверены что хотите удалить этот продукт? (Y/N)"
        )
        if product.image_url:  # Using the image_url for the photo
            await callback.message.delete()  # Delete the previous message
            await callback.message.answer_photo(photo=product.image_url, caption=text, reply_markup=None)
        else:
            await callback.message.edit_text(text, reply_markup=None)

        await state.set_state(DeleteProduct.delete_product)
    else:
        await callback.message.edit_text("Продукт не найден", reply_markup=kb.admin_main)

@admin_router.message(DeleteProduct.delete_product)
async def confirm_product_deletion(message: Message, state: FSMContext):
    confirmation = message.text.strip().lower()
    data = await state.get_data()
    product_id = data.get('product_id')
    product_name = data.get('product_name')

    if confirmation == 'y':
        async with SessionMaker() as session:
             deleted = await orm_delete_product_by_id(session, product_id)

        if deleted:
            await message.answer(f'Продукт "{product_name}" успешно удален.', reply_markup=kb.admin_product)
        else:
            await message.answer(f'Ошибка при удалении продукта "{product_name}".')
    elif confirmation == 'n':
        await message.answer('Удаление отменено.')
    else:
        await message.answer('Пожалуйста, введите "Y" для подтверждения удаления или "N" для отмены.')

    # Clear the state after handling the confirmation
    await state.clear()
# endregion

@admin_router.callback_query(F.data == 'to_admin_product')
async def admin_main_back(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer('Выберите Действие для Товара', reply_markup=kb.admin_product)
# endregion

# region ADMIN PANEL CATALOG
@admin_router.callback_query(F.data == 'catalog_categories_')
async def admin_main_back(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    category_id = int(data[1])
    page = int(data[2]) if len(data) == 3 else 1  # Default to page 1 if no page is provided
    await state.update_data(category_id=category_id)
    await callback.answer('')

    # Ensure the message content changes to avoid the "message is not modified" error
    products_markup = await kb.products_for_catalog(category_id, page)
    await callback.message.edit_text(f'Выберите продукт (Страница {page})', reply_markup=products_markup)


@admin_router.callback_query(F.data.startswith('catalog_products_'))
async def show_product_details(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[1])
    product = await orm_get_product_by_id(product_id)

    if product:
        await state.update_data(product_id=product_id)  # Store product_id in state
        text = (
            f"Название: {product.p_name}\n"
            f"Описание: {product.p_description}\n"
            f"Цена: {product.p_price} Сум\n\n\n"
        )
        if product.image_url:  # Using the image_url for the photo
            await callback.message.delete()  # Delete the previous message
            await callback.message.answer_photo(photo=product.image_url, caption=text,
                                                reply_markup=kb.admin_main)
        else:
            await callback.message.edit_text(text, reply_markup=kb.admin_main)
    else:
        await callback.message.edit_text("Продукт не найден", reply_markup=kb.admin_main)