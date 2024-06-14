from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.filters import CommandStart, Command, or_f

import buttons.inline_buttons as kb
from database.orm_queries import orm_set_user, orm_get_product_by_id, add_product_to_basket, orm_create_order_item, \
    orm_get_order_items_by_order_id

user_private = Router()

class Order(StatesGroup):
    get_orders = State()
class PMenu(StatesGroup):
    add = State()
    subst = State()

class Form(StatesGroup):
    category = State()
    item = State()


@user_private.message(CommandStart())
async def cmd_start(message: Message):
    await orm_set_user(message.from_user.id)  # Assuming orm.set_user() registers the user
    await message.answer("Добро пожаловать в интернет магазин!", reply_markup=kb.main_menu_keyboard)


@user_private.callback_query(F.data == 'to_main')
async def to_main(callback: CallbackQuery, state: FSMContext):
    message_type = (await state.get_data()).get('message_type', 'text')

    if message_type == 'photo':
        # Delete photo message
        await callback.message.delete()
        await callback.message.answer("Добро пожаловать в интернет магазин!", reply_markup=kb.main_menu_keyboard)
    else:
        await callback.message.edit_text("Добро пожаловать в интернет магазин!", reply_markup=kb.main_menu_keyboard)

    await state.update_data(message_type='text')

@user_private.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    data = await state.get_data()
    message_type = data.get('message_type', 'text')

    if message_type == 'photo':
        # Delete photo message
        await callback.message.delete()
        await callback.message.answer(text='Выберите категорию.',
                                         reply_markup=await kb.user_categories())
    else:

        await callback.message.edit_text(text='Выберите категорию.',
                                         reply_markup=await kb.user_categories())


@user_private.callback_query(F.data.startswith('usercategories_'))
async def categories_pagination(callback: CallbackQuery):
    page = int(callback.data.split('_')[1])
    await callback.answer('')
    await callback.message.edit_text('Выберите категорию.', reply_markup=await kb.user_categories(page))


@user_private.callback_query(F.data.startswith('UserCategory_'))
async def category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split('_')[1])
    await state.update_data(category_id=category_id)
    await callback.answer('')
    await callback.message.edit_text('Выберите товар', reply_markup=await kb.items(category_id, page=1))


@user_private.callback_query(F.data.startswith('itemscategory_'))
async def category_pagination(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    category_id = int(data[1])
    page = int(data[2])
    await state.update_data(category_id=category_id)
    await callback.answer('')
    await callback.message.edit_text('Выберите товар', reply_markup=await kb.items(category_id, page))

@user_private.callback_query(F.data.startswith('item_'))
async def update_product_view(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split('_')[1]  # No int() conversion needed
    product = await orm_get_product_by_id(product_id)

    if product:
        await state.update_data(product_id=product_id, product_name=product.p_name, quantity=1)
        text = (
            f"Название: {product.p_name}\n"
            f"Описание: {product.p_description}\n"
            f"Цена: {product.p_price} Сум\n"
            f"Количество: {1}\n\n"  # Default quantity is set to 1
        )
        if product.image_url:
            data = await state.get_data()
            quantity = data.get('quantity', 1)
            keyboard = kb.create_product_buttons(product.category_id, quantity)
            await state.update_data(message_type='photo')  # Update state with message type
            await callback.message.delete()
            await callback.message.answer_photo(photo=product.image_url, caption=text, reply_markup=keyboard)
        else:
            await state.update_data(message_type='text')  # Update state with message type
            await callback.message.edit_text(text, reply_markup=None)
    else:
        await callback.message.edit_text("Продукт не найден", reply_markup=await kb.user_categories())

async def update_product_text(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    quantity = data.get('quantity', 1)  # Default quantity is 1 if not set
    await callback.answer(str(quantity))

    product = await orm_get_product_by_id(product_id)

    if product:
        total_price = product.p_price * quantity
        text = (
            f"Название: {product.p_name}\n"
            f"Описание: {product.p_description}\n"
            f"Цена: {total_price} Сум\n"
            f"Количество: {quantity}\n\n"
        )
        if product.image_url:
            keyboard = kb.create_product_buttons(product.category_id, quantity)
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, reply_markup=None)

# Function to handle plus one
@user_private.callback_query(F.data == 'plus_one')
async def handle_plus_one(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quantity = data.get('quantity', 1)  # Default quantity is 1 if not set
    if quantity < 20:  # Set maximum quantity to 20
        quantity += 1
        await state.update_data(quantity=quantity)

        # Directly update the product view text after updating the quantity
        await update_product_text(callback, state)
    else:
        await callback.answer("Максимальное количество товара - 20")

# Function to handle minus one
@user_private.callback_query(F.data == 'minus')
async def handle_minus_one(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quantity = data.get('quantity', 1)  # Default quantity is 1 if not set
    if quantity > 1:
        quantity -= 1
        await state.update_data(quantity=quantity)

        # Directly update the product view text after updating the quantity
        await update_product_text(callback, state)


@user_private.callback_query(F.data == 'dobavit_v_korzinu')
async def handle_product_basker(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)  # Default quantity is 1 if not set

    # Assuming you have the order_id available in the state or retrieved somehow
    order_id = data.get('order_id')  # Replace with actual method to get the current order_id

    product = await orm_get_product_by_id(product_id)
    if not product:
        await callback.answer("Продукт не найден")
        return

    total_cost = product.p_price * quantity

    # Store the order item in the database
    new_order_item = await orm_create_order_item(order_id, product_id, quantity, total_cost)

    await callback.answer(f"Добавлено в корзину: {product.p_name} (Количество: {quantity}, Общая стоимость: {total_cost} Сум)")

@user_private.callback_query(F.data=='basket')
async def buy_product(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')  # Replace with actual method to get the current order_id

    order_items = await orm_get_order_items_by_order_id(order_id)
    if not order_items:
        await callback.answer("Корзина пуста.")
        return

    text = "Ваши товары в корзине:\n\n"
    total_cost = 0

    for item in order_items:
        product = await orm_get_product_by_id(item.product_id)
        item_cost = item.total_cost
        total_cost += item_cost
        text += (
            f"Название: {product.p_name}\n"
            f"Цена продукта: {product.p_price} Сум x Количество: {item.quantity} = Общая стоимость продукта: {item_cost} Сум\n\n"
        )

    text += f"Общая стоимость всех продуктов: {total_cost} Сум"

    await callback.message.edit_text(text, reply_markup= kb.create_basket_buttons)

GROUP_CHAT_IDS = [-4257083278]
def register_handlers_user_private(bot):
    # Callback query handler for 'buy_product'
    @user_private.callback_query(F.data == 'buy_product')
    async def user_buy_product(callback: types.CallbackQuery, state: FSMContext):

        await callback.message.edit_text("Заказ отправлен ожидайте обратной связи")
        await state.set_state(Order.get_orders.state)

        # Send the message to all groups
        for group_id in GROUP_CHAT_IDS:
            await bot.send_message(chat_id=group_id, text="Пользователь подтвердил заказ")

    # Message handler for Order.get_orders state
@user_private.message(Order.get_orders)
async def get_orders(message: types.Message, state: FSMContext):
    await message.answer("Ожидайте дальнейших инструкций.")
    await state.clear()













@user_private.callback_query(F.data=='textile')
async def buy_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('https://telegra.ph/Mosmade-06-14')

@user_private.callback_query(F.data=='contacts')
async def buy_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    chat_id = 877993978
    await callback.message.answer('https://t.me/ruslan_mukhtasimov')