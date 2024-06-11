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
from database.orm_queries import orm_add_category, orm_update_category_name, orm_delete_category, \
    orm_get_category_by_id, orm_add_product, orm_get_categories, orm_get_product_by_id

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


# region ADMINS CATEGORY MANIPULATION STATES
class AddCategory(StatesGroup):
    add_name = State()
    add_sex = State()


class ChangeCategory(StatesGroup):
    ch_name = State()
    ch_sex = State()


class DeleteCategory(StatesGroup):
    waiting_for_confirmation = State()


# endregion


class AddProduct(StatesGroup):
    add_category = State()
    add_name = State()
    add_description = State()
    add_price = State()
    add_photo = State()


@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer('Возможные команды: /add_category\n/add_item\ncatalog', reply_markup=kb.admin_main)


@admin_router.callback_query(F.data == 'category')
async def admin_category(callback: CallbackQuery):
    await callback.answer('Вы нажали на категорию')
    await callback.message.edit_text('Действие для Категории', reply_markup=kb.admin_category)


@admin_router.callback_query(F.data == 'product')
async def admin_product(callback: CallbackQuery):
    await callback.answer('Вы нажали на Продукт')
    await callback.message.edit_text('Действие для Товара', reply_markup=kb.admin_product)


@admin_router.callback_query(F.data == 'catalog')
async def admin_catalog(callback: CallbackQuery):
    await callback.message.edit_text('Выберите Категорию', reply_markup=kb.admin_category)


# region ADMIN CATEGORY ADD, CHANGE, DELETE Handlers
# region ADD CATEGORY
@admin_router.callback_query(F.data == 'add_category')
async def admin_add_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddCategory.add_name)
    await callback.answer('')
    await callback.message.answer('Введите имя для новой категории', reply_markup=ReplyKeyboardRemove())


@admin_router.message(AddCategory.add_name)
async def admin_add_category_name(message: Message, state=FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Введите пол для Категории', reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddCategory.add_sex)


@admin_router.message(AddCategory.add_sex)
async def admin_add_category_sex(message: Message, state=FSMContext):
    await state.update_data(sex=message.text)
    data = await state.get_data()
    await orm_add_category(data)
    await message.answer("Категория успешно добавлена", reply_markup=kb.admin_category)
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
    new_name = message.text
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
    await callback.message.answer('Введите новый пол для категории', reply_markup=ReplyKeyboardRemove())


@admin_router.message(ChangeCategory.ch_sex)
async def change_category_sex(message: Message, state: FSMContext):
    new_sex = message.text
    data = await state.get_data()
    category_id = data.get('category_id')

    async with SessionMaker() as session:
        updated = await orm_update_category_name(session, category_id, new_sex)

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

# region Add PRODUCT
@admin_router.callback_query(F.data == 'add_product')
async def admin_add_product(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.add_category)
    await callback.answer('')
    await callback.message.answer('Выберите Категорию Товара', reply_markup=await kb.pcategories())


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

#   CHANGE PRODUCT
@admin_router.callback_query(F.data == 'change_product')
async def admin_main_back(callback: CallbackQuery):
    await callback.answer('Вы в пункте Продукты')
    await callback.message.edit_text('Выберите из Какой Категории Продукт', reply_markup=await kb.pchcategories())

@admin_router.callback_query(F.data.startswith('pchcategory_'))
async def select_category_for_product(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    category_id = int(data[1])
    page = int(data[-1]) if len(data) == 4 else 1  # Default to page 1 if no page is provided
    await state.update_data(category_id=category_id)
    await callback.answer('')
    await callback.message.edit_text('Выберите продукт', reply_markup=await kb.products_by_category(category_id, page))


@admin_router.callback_query(F.data.startswith('product_'))
async def show_product_details(callback: CallbackQuery):
    product_id = int(callback.data.split('_')[1])
    product = await orm_get_product_by_id(product_id)

    if product:
        text = (
            f"Название: {product.p_name}\n"
            f"Описание: {product.p_description}\n"
            f"Цена: {product.p_price} Сум\n\n\n"
            "ВЫБЕРИТЕ ЧТО ХОТИТЕ ИЗМЕНИТЬ"
        )
        if product.image_url:  # Using the image_url for the photo
            await callback.message.delete()  # Delete the previous message
            await callback.message.answer_photo(photo=product.image_url, caption=text, reply_markup=kb.admin_product_change)
        else:
            await callback.message.edit_text(text, reply_markup=kb.admin_main)
    else:
        await callback.message.edit_text("Продукт не найден", reply_markup=kb.admin_main)


@admin_router.callback_query(F.data == 'to_admin_product')
async def admin_main_back(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer('Вы на в пункте Манипуляции Продуктов')
    await callback.message.answer('Выберите Действие для Продуктов', reply_markup=kb.admin_product)
