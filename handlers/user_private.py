from aiogram import types, Router, F, Bot
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, or_f
import locale

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
import buttons.inline_buttons as kb
from database.orm_queries import orm_set_user, orm_get_product_by_id, add_product_to_basket, orm_create_order_item, \
    orm_get_order_items_by_order_id, orm_clean_order_items_by_order_id, orm_create_order, orm_create_user_by_tg_id, \
    orm_get_user_id_by_tg_id, orm_update_user, orm_get_user_by_tg_id

user_private = Router()


class OrderState(StatesGroup):
    waiting_for_phone_number = State()
    viewing_basket = State()


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
                                      reply_markup=await kb.user_categories(back_callback='to_main'))
    else:

        await callback.message.edit_text(text='Выберите категорию.',
                                         reply_markup=await kb.user_categories(back_callback='to_main'))


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
        await callback.message.edit_text("Продукт не найден", reply_markup=await kb.user_categories(back_callback='catalog'))


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
    await orm_create_order_item(order_id, product_id, quantity, total_cost)

    await callback.answer(
        f"Добавлено в корзину: {product.p_name} (Количество: {quantity}, Общая стоимость: {total_cost} Сум)")


@user_private.callback_query(F.data == 'basket')
async def basket_handler(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    user = await orm_get_user_by_tg_id(tg_id)

    if not user.phone_number:
        await state.set_state(OrderState.waiting_for_phone_number)
        await callback.message.answer("Пожалуйста, отправьте ваш номер телефона:", reply_markup=kb.get_contact_keyboard())
        return

    await show_basket(callback, state)



@user_private.message(OrderState.waiting_for_phone_number, F.contact)
async def process_phone_number_contact(message: Message, state: FSMContext):
    contact = message.contact
    phone_number = contact.phone_number
    tg_id = message.from_user.id

    # Update the user's phone number in the database
    user = await orm_get_user_by_tg_id(tg_id)
    user.phone_number = phone_number
    await orm_update_user(user)

    await show_basket(message, state)



@user_private.message(OrderState.waiting_for_phone_number, F.data)
async def process_phone_number_text(message: Message, state: FSMContext):
    await message.answer("Нажмите на кнопку, чтобы отправить контакт или отправьте в формате.")



async def show_basket(callback_or_message, state: FSMContext):
    # Determine if we're handling a callback or a message
    if isinstance(callback_or_message, CallbackQuery):
        tg_id = callback_or_message.from_user.id
        message = callback_or_message.message
    else:
        tg_id = callback_or_message.from_user.id
        message = callback_or_message

    data = await state.get_data()
    order_id = data.get('order_id')  # Replace with actual method to get the current order_id

    order_items = await orm_get_order_items_by_order_id(order_id)
    if not order_items:
        await message.answer("Корзина пуста.", reply_markup=ReplyKeyboardRemove())
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

    await message.edit_text(text, reply_markup= kb.create_basket_buttons)



GROUP_CHAT_IDS = [-4257083278]


def register_handlers_user_private(bot: Bot):
    @user_private.callback_query(F.data == 'buy_product')
    async def user_buy_product(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        order_id = data.get('order_id')  # Replace with the actual method to get the current order_id
        user = await orm_get_user_by_tg_id(callback.from_user.id)
        user_id = user.id
        # Get all order items for this order
        order_items = await orm_get_order_items_by_order_id(order_id)
        if not order_items:
            await callback.answer("Корзина пуста.")
            return

        total_cost = sum(item.total_cost for item in order_items)

        # Create the order
        new_order = await orm_create_order(user_id, total_cost)

        text = f"Заказ номер: {new_order.id}\n"
        text += "Состав заказа:\n\n"
        for item in order_items:
            product = await orm_get_product_by_id(item.product_id)
            text += (
                f"Категория: {product.category_id}\n"
                f"Название: {product.p_name}\n"
                f"Количество: {item.quantity}\n"
                f"Общая стоимость продукта: {int(item.total_cost):n} Сум\n\n"
            )
        text += f"Общая стоимость заказа: {int(total_cost):n} Сум\n\n"
        text += f"Данные Клиента: {callback.from_user.first_name},\nid: {callback.from_user.id}\nтелефон: {user.phone_number}"

        # Send the message to all group chats
        for group_id in GROUP_CHAT_IDS:
            await bot.send_message(chat_id=group_id, text=text)

        # Clear the user's basket
        await orm_clean_order_items_by_order_id(order_id)  # Implement this ORM function to clean the basket
        await callback.answer("Заказ отправлен, ожидайте обратной связи.")
        await callback.message.edit_text("Ваш заказ был отправлен. Ваша корзина пуста.")


@user_private.message(Order.get_orders)
async def get_orders(message: types.Message, state: FSMContext):
    await message.answer("Ожидайте дальнейших инструкций.")
    await state.clear()


@user_private.callback_query(F.data == 'textile')
async def buy_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('https://telegra.ph/Mosmade-06-14')
    await callback.message.answer("Добро пожаловать в магазин Mosmade!", reply_markup=kb.main_menu_keyboard)


@user_private.callback_query(F.data == 'contacts')
async def buy_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    chat_id = 877993978
    await callback.message.answer('https://t.me/ruslan_mukhtasimov')
    await callback.message.answer("Добро пожаловать в интернет магазин! Mosmade!", reply_markup=kb.main_menu_keyboard)


@user_private.callback_query(F.data == 'private_add_product')
async def to_category(callback: CallbackQuery):
    await callback.message.edit_text(text='Выберите категорию.',
                                     reply_markup=await kb.user_categories(back_callback='to_main'))
