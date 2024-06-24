from aiogram import types, Router, F, Bot
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, or_f
import locale

from language_dictionary.language import MESSAGES, MESSAGES_RU, MESSAGES_UZ, GENDER_MAPPING

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
import buttons.inline_buttons as kb
from database.orm_queries import orm_set_user, orm_get_product_by_id, orm_create_order_item, \
    orm_get_order_items_by_order_id, orm_clean_order_items_by_order_id, orm_create_order, orm_update_user, \
    orm_get_user_by_tg_id, orm_update_user_language, orm_get_user_language, orm_get_category_name

user_private = Router()

class LanguageState(StatesGroup):
    language = State()

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
async def cmd_start(message: Message, state: FSMContext):
    await orm_set_user(message.from_user.id)  # Assuming orm.set_user() registers the user
    await state.set_state(LanguageState.language)
    await state.update_data(language='ru')  # Default language
    await message.answer(text="Вас приветсвует магазин Mosmade выберите язык интерфейса.\n\n\nMosmade do'koniga hush kelibsiz interfeys tilini tanlang.",
                         reply_markup=kb.language_selection_keyboard())

@user_private.callback_query(F.data.startswith('select_language_'))
async def select_language(callback: CallbackQuery, state: FSMContext):
    language_code = callback.data.split('_')[2]
    await state.update_data(language=language_code)
    await orm_update_user_language(callback.from_user.id, language_code)  # Update user language in DB
    await callback.answer('')
    await callback.message.edit_text(MESSAGES[language_code]['language_selected'], reply_markup= kb.main_menu_keyboard(language_code))


@user_private.callback_query(F.data == 'to_main')
async def to_main(callback: CallbackQuery, state: FSMContext):
    message_type = (await state.get_data()).get('message_type', 'text')

    # Assuming orm_get_user_language is defined to get user language from the database
    language_code = await orm_get_user_language(callback.from_user.id)
    await state.update_data(language_code=language_code)
    # Fetch messages in the user's preferred language
    messages = MESSAGES.get(language_code, MESSAGES['ru'])  # Default to Russian if language code is not found

    if language_code == 'uz':
        messages = MESSAGES_UZ
    else:
        messages = MESSAGES_RU

    if message_type == 'photo':
        # Delete photo message
        await callback.message.delete()
        await callback.message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))
    else:
        await callback.message.edit_text(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))

    await state.update_data(message_type='text')


@user_private.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')

    data = await state.get_data()
    message_type = data.get('message_type', 'text')  # Retrieve the message type from the state

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])  # Default to Russian if language code is not found

    if message_type == 'photo':
        # Delete photo message
        await callback.message.delete()
        await callback.message.answer(
            text=messages['choose_gender'],
            reply_markup=kb.category_gender_selection_keyboard(language_code)
        )
    else:
        await callback.message.edit_text(
            text=messages['choose_gender'],
            reply_markup=kb.category_gender_selection_keyboard(language_code)
        )



@user_private.callback_query(F.data.startswith('gender_'))
async def category_gender_selection(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split('_')[1]
    sex = GENDER_MAPPING.get(gender, gender)  # Convert gender term to Russian

    await state.update_data(sex=sex)

    data = await state.get_data()
    message_type = data.get('message_type', 'text')

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    if message_type == 'photo':
        # Delete photo message
        await callback.message.delete()
        await callback.message.answer(
            text=messages['category_menu'],
            reply_markup=await kb.user_categories(back_callback='catalog', page=1, categories_per_page=4,
                                                  language=language_code, sex=sex)
        )
    else:
        await callback.message.edit_text(
            text=messages['category_menu'],
            reply_markup=await kb.user_categories(back_callback='catalog', page=1, categories_per_page=4,
                                                  language=language_code, sex=sex)
        )

@user_private.callback_query(F.data.startswith('usercategories_'))
async def categories_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split('_')[1])
    data = await state.get_data()
    sex = data.get('sex', None)

    await callback.answer('')

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await callback.message.edit_text(
        messages['category_menu'],
        reply_markup=await kb.user_categories(back_callback='catalog', page=page, categories_per_page=4,
                                              language=language_code, sex=sex)
    )


@user_private.callback_query(F.data.startswith('UserCategory_'))
async def category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split('_')[1])
    await state.update_data(category_id=category_id)
    await callback.answer('')

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await callback.message.edit_text(
        messages['product_menu'],
        reply_markup=await kb.items(category_id, page=1, items_per_row=3, language=language_code, back_callback='catalog')
    )


@user_private.callback_query(F.data.startswith('itemscategory_'))
async def category_pagination(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    category_id = int(data[1])
    page = int(data[2])
    await state.update_data(category_id=category_id)
    await callback.answer('')

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await callback.message.edit_text(
        messages['product_menu'],
        reply_markup=await kb.items(category_id, page, language=language_code, back_callback='catalog')
    )






@user_private.callback_query(F.data.startswith('item_'))
async def update_product_view(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split('_')[1]  # No int() conversion needed
    product = await orm_get_product_by_id(product_id)

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    if product:
        # Select the correct language fields for name and description
        if language_code == 'uz':
            product_name = product.name_uz
            product_description = product.description_uz
        else:
            product_name = product.name_ru
            product_description = product.description_ru

        await state.update_data(product_id=product_id, product_name=product_name, quantity=1)
        price_formatted = locale.format_string('%d', product.price, grouping=True)  # Format price without decimals
        text = (
            f"{messages['product_name']}: {product_name}\n"
            f"{messages['product_description']}: {product_description}\n"
            f"{messages['product_price']}: {price_formatted} Сум\n"
            f"{messages['product_quantity']}: {1}\n\n"  # Default quantity is set to 1
        )
        if product.image_url:
            data = await state.get_data()
            quantity = data.get('quantity', 1)
            keyboard = kb.create_product_buttons(quantity, language_code = language_code)
            await state.update_data(message_type='photo')  # Update state with message type
            await callback.message.delete()
            await callback.message.answer_photo(photo=product.image_url, caption=text, reply_markup=keyboard)
        else:
            await state.update_data(message_type='text')  # Update state with message type
            await callback.message.edit_text(text, reply_markup=None)
    else:
        await callback.message.edit_text(
            messages['product_not_found'],
            reply_markup=await kb.user_categories(back_callback='to_main', page=1, categories_per_page=4, language=language_code)
        )


async def update_product_text(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    quantity = data.get('quantity', 1)  # Default quantity is 1 if not set
    await callback.answer(str(quantity))

    product = await orm_get_product_by_id(product_id)

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    if product:
        # Select the correct language fields for name and description
        if language_code == 'uz':
            product_name = product.name_uz
            product_description = product.description_uz
        else:
            product_name = product.name_ru
            product_description = product.description_ru

        total_price = product.price * quantity
        total_price_formatted = locale.format_string('%d', total_price, grouping=True)  # Format total price without decimals

        text = (
            f"{messages['product_name']}: {product_name}\n"
            f"{messages['product_description']}: {product_description}\n"
            f"{messages['product_price']}: {total_price_formatted} Сум\n"
            f"{messages['product_quantity']}: {quantity}\n\n"
        )

        if product.image_url:
            keyboard = kb.create_product_buttons(quantity,language_code)
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, reply_markup=None)
    else:
        await callback.message.edit_text(
            messages['product_not_found'],
            reply_markup=await kb.user_categories(back_callback='to_main', page=1, categories_per_page=4, language=language_code)
        )

# Function to handle plus one
@user_private.callback_query(F.data == 'plus_one')
async def handle_plus_one(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quantity = data.get('quantity', 1)  # Default quantity is 1 if not set
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    if quantity < 20:
        quantity += 1
        await state.update_data(quantity=quantity)
        await update_product_text(callback, state)
    else:
        if language_code == 'uz':
            await callback.answer("Maxsimal miqdori - 20")
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

    total_cost = product.price * quantity

    # Store the order item in the database
    await orm_create_order_item(order_id, product_id, quantity, total_cost)

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Select the correct language fields for product name and response
    if language_code == 'uz':
        product_name = product.name_uz
        added_to_cart_message = (
            f"Korzinaga qo'shildi: {product_name} (Soni: {quantity}, Umumiy narxi: {total_cost} Сум)"
        )
    else:  # Default to Russian if language code is not recognized
        product_name = product.name_ru
        added_to_cart_message = (
            f"Добавлено в корзину: {product_name} (Количество: {quantity}, Общая стоимость: {total_cost} Сум)"
        )

    await callback.answer(added_to_cart_message)


@user_private.callback_query(F.data == 'basket')
async def basket_handler(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    user = await orm_get_user_by_tg_id(tg_id)

    # Get the user's preferred language
    language_code = await orm_get_user_language(tg_id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    if not user.phone_number:
        await state.set_state(OrderState.waiting_for_phone_number)
        await callback.message.answer(
            messages['request_phone_number'],
            reply_markup=kb.get_contact_keyboard(language_code=language_code)  # Pass the keyboard without calling it
        )
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
        # Fetch user language
        language_code = await orm_get_user_language(tg_id)
        messages = MESSAGES.get(language_code, MESSAGES['ru'])

        await message.answer(messages['basket_empty'], reply_markup=ReplyKeyboardRemove())
        return

    # Fetch user language
    language_code = await orm_get_user_language(tg_id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    text = messages['basket_items'] + "\n\n"
    total_cost = 0

    for item in order_items:
        product = await orm_get_product_by_id(item.product_id)
        item_cost = item.total_cost
        total_cost += item_cost

        # Select the correct language fields for name and price
        if language_code == 'uz':
            product_name = product.name_uz
        else:
            product_name = product.name_ru  # Default to Russian if language code is invalid

        # Format total cost and product price with thousands separator
        formatted_price = locale.format_string('%d', product.price, grouping=True)
        formatted_item_cost = locale.format_string('%d', item_cost, grouping=True)

        text += (
            f"{messages['product_name']}: {product_name}\n"
            f"{messages['product_price']}: {formatted_price} Сум x {messages['product_quantity']}: {item.quantity} = "
            f"{messages['total_cost']}: {formatted_item_cost} Сум\n\n"
        )

    # Format total order cost with thousands separator
    formatted_total_cost = locale.format_string('%d', total_cost, grouping=True)

    text += f"{messages['total_order_cost']}: {formatted_total_cost} Сум"

    await message.edit_text(text, reply_markup=kb.create_basket_buttons(language_code))


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
            await callback.answer(MESSAGES['ru']['basket_empty'])  # Adjust based on your message dictionary
            return

        total_cost = sum(item.total_cost for item in order_items)

        # Create the order
        new_order = await orm_create_order(user_id, total_cost)

        # Constructing the order details text for the user
        language_code = await orm_get_user_language(callback.from_user.id)
        messages = MESSAGES.get(language_code, MESSAGES['ru'])

        user_text = f"{messages['order_id']}: {new_order.id}\n"

        for item in order_items:
            product = await orm_get_product_by_id(item.product_id)
            category_name = await orm_get_category_name(product.category_id, language_code)

            # Select the correct language fields for name
            if language_code == 'uz':
                product_name = product.name_uz
            else:
                product_name = product.name_ru

            user_text += (
                f"{messages['category']}: {category_name}\n"
                f"{messages['product_name']}: {product_name}\n"
                f"{messages['quantity']}: {item.quantity}\n"
                f"{messages['total_cost']}: {locale.format_string('%d', item.total_cost, grouping=True)} Сум\n\n"
            )

        user_text += f"{messages['total_order_cost']}: {locale.format_string('%d', total_cost, grouping=True)} Сум\n\n"
        user_text += f"{messages['customer_name']}: {callback.from_user.first_name},\n{messages['id']}: {callback.from_user.id}\n{messages['phone']}: {user.phone_number}"

        # Constructing the order details text for the group chat in Russian
        group_messages = MESSAGES['ru']
        group_text = f"{group_messages['order_id']}: {new_order.id}\n"

        for item in order_items:
            product = await orm_get_product_by_id(item.product_id)
            category_name = await orm_get_category_name(product.category_id, 'ru')

            product_name = product.name_ru

            group_text += (
                f"{group_messages['category']}: {category_name}\n"
                f"{group_messages['product_name']}: {product_name}\n"
                f"{group_messages['quantity']}: {item.quantity}\n"
                f"{group_messages['total_cost']}: {locale.format_string('%d', item.total_cost, grouping=True)} Сум\n\n"
            )

        group_text += f"{group_messages['total_order_cost']}: {locale.format_string('%d', total_cost, grouping=True)} Сум\n\n"
        group_text += f"{group_messages['customer_name']}: {callback.from_user.first_name},\n{group_messages['id']}: {callback.from_user.id}\n{group_messages['phone']}: {user.phone_number}"

        # Send the message to all group chats
        for group_id in GROUP_CHAT_IDS:
            await bot.send_message(chat_id=group_id, text=group_text)

        # Clear the user's basket
        await orm_clean_order_items_by_order_id(order_id)  # Implement this ORM function to clean the basket
        await callback.answer(messages['order_sent'])
        await callback.message.edit_text(messages['order_sent_confirmation'])



@user_private.callback_query(F.data == 'clean_basket')
async def clean_basket(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        order_id = data.get('order_id')  # Replace with the actual method to get the current order_id

        # Clear the user's basket
        await orm_clean_order_items_by_order_id(order_id)  # Implement this ORM function to clean the basket

        # Provide feedback to the user
        language_code = await orm_get_user_language(callback.from_user.id)
        messages = MESSAGES.get(language_code, MESSAGES['ru'])
        await callback.answer(messages['basket_cleaned'])
        await callback.message.edit_text(messages['basket_cleaned_confirmation'])
        await callback.message.edit_text(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))



@user_private.message(Order.get_orders)
async def get_orders(message: types.Message, state: FSMContext):
    await message.answer("Ожидайте дальнейших инструкций.")
    await state.clear()


@user_private.callback_query(F.data == 'textile')
async def buy_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    language_code = await orm_get_user_language(callback.from_user.id)
    await callback.message.answer('https://telegra.ph/Mosmade-06-14')
    messages = MESSAGES.get(language_code, MESSAGES['ru'])
    await callback.message.answer(messages['welcome'], reply_markup= kb.main_menu_keyboard(language_code))


@user_private.callback_query(F.data == 'contacts')
async def buy_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    language_code = await orm_get_user_language(callback.from_user.id)
    await callback.message.answer('https://t.me/ruslan_mukhtasimov')
    messages = MESSAGES.get(language_code, MESSAGES['ru'])
    await callback.message.answer(messages['welcome'], reply_markup= kb.main_menu_keyboard(language_code))

@user_private.callback_query(F.data == 'language')
async def buy_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Выберите Язык\nTilni tanlang", reply_markup=kb.language_selection_keyboard())

@user_private.callback_query(F.data == 'private_add_product')
async def to_category(callback: CallbackQuery,state: FSMContext):
    await callback.answer('')
    data = await state.get_data()
    message_type = data.get('message_type', 'text')

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])
    if message_type == 'photo':
        # Delete photo message
        await callback.message.delete()
        await callback.message.answer(
            text=messages['category_menu'],
            reply_markup=await kb.user_categories(back_callback='to_main', page=1, categories_per_page=4,
                                                  language=language_code)
        )
    else:
        await callback.message.edit_text(
            text=messages['category_menu'],
            reply_markup=await kb.user_categories(back_callback='to_main', page=1, categories_per_page=4,
                                                  language=language_code)
        )
