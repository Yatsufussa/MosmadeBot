import locale
from datetime import datetime
from typing import Union
from decimal import Decimal
from aiogram.client import bot
from aiogram.exceptions import TelegramMigrateToChat
from integrations.yandex import get_address_from_coordinates
import buttons.inline_buttons as kb
from aiogram.filters import CommandStart, or_f, Command
from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.exc import SQLAlchemyError
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from language_dictionary.language import MESSAGES, GENDER_MAPPING

from database.orm_queries import orm_set_user, orm_get_product_by_id, orm_create_order_item, \
    orm_get_order_items_by_order_id, orm_clean_order_items_by_order_id, orm_create_order, orm_update_user, \
    orm_get_user_by_tg_id, orm_update_user_language, orm_get_user_language, orm_get_category_name, orm_save_excel_order, \
    orm_create_user_by_tg_id, orm_get_user_by_referral_code, orm_save_user, save_user_location, \
    orm_get_referred_users_count, orm_get_referred_users_with_orders_count, orm_get_user_location, \
    orm_update_user_location, orm_update_user_phone, orm_get_promo_code_by_text, orm_activate_promo_code_for_user, \
    orm_get_promo_code_by_id, orm_get_orders_by_user_id, \
    orm_get_excel_orders_by_user_phone

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
user_private = Router()
GROUP_CHAT_IDS = [-1002408666314]

GROUP_CHAT_IDS_WITH_THREADS = [
    {"chat_id": -1002408666314, "message_thread_id": 3},  # Example thread ID # Example thread ID
]


class LanguageState(StatesGroup):
    language = State()


class OrderState(StatesGroup):
    waiting_for_phone_number = State()
    waiting_for_location = State()
    viewing_basket = State()


class Order(StatesGroup):
    get_orders = State()


class PMenu(StatesGroup):
    add = State()
    subst = State()


class Form(StatesGroup):
    category = State()
    item = State()


class PersonalInfoState(StatesGroup):
    waiting_for_phone_number = State()
    waiting_for_location = State()


@user_private.message(CommandStart())
async def cmd_start(message: CallbackQuery, state: FSMContext):
    user = await orm_get_user_by_tg_id(message.from_user.id)

    if user:
        language_code = user.language
        await state.update_data(language=language_code)
        await to_main(message, state, first_time=True)
        return

    referral_code = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referral_code = args[1][4:]

    new_user = await orm_create_user_by_tg_id(message.from_user.id)

    if referral_code:
        referrer = await orm_get_user_by_referral_code(referral_code)
        if referrer:
            new_user.referred_by = referrer.id
            await orm_save_user(new_user)

            try:
                await message.bot.send_message(
                    referrer.tg_id,
                    f"Ваш реферальный код использован {message.from_user.username or 'новым пользователем'}!"
                )
            except Exception as e:
                print(f"Ошибка при отправке уведомления рефереру: {e}")

            await message.answer("Добро пожаловать! Вы зарегистрировались по реферальной ссылке")
        else:
            await message.answer("Ошибка: недействительный реферальный код!")
    else:
        await orm_save_user(new_user)
        await message.answer("Добро пожаловать в TAYYOR BOX!")

    await state.set_state(LanguageState.language)
    await state.update_data(language='ru')
    await message.answer(
        text=("TAYYOR BOX приветствует вас!\nВыберите язык интерфейса.\n\n"
              "TAYYOR BOX do'koniga xo'sh kelibsiz\nInterfeys tilini tanlang."),
        reply_markup=kb.language_selection_keyboard()
    )


@user_private.message(Command("start"))
async def menu_cmd(message: CallbackQuery, state: FSMContext):
    user = await orm_get_user_by_tg_id(message.from_user.id)

    if user:
        language_code = user.language
        await state.update_data(language=language_code)
        await to_main(message, state, first_time=True)
    else:
        await orm_create_user_by_tg_id(message.from_user.id)
        await state.set_state(LanguageState.language)
        await state.update_data(language='ru')
        await message.answer(
            text=("TAYYOR BOX приветствует вас!\nВыберите язык интерфейса.\n\n"
                  "TAYYOR BOX do'koniga xo'sh kelibsiz\nInterfeys tilini tanlang."),
            reply_markup=kb.language_selection_keyboard()
        )


@user_private.callback_query(F.data.startswith('select_language_'))
async def select_language(callback: CallbackQuery, state: FSMContext):
    language_code = callback.data.split('_')[2]
    await state.update_data(language=language_code)
    await orm_update_user_language(callback.from_user.id, language_code)  # Update user language in DB
    await callback.answer('')
    await callback.message.edit_text(MESSAGES[language_code]['language_selected'],
                                     reply_markup=kb.main_menu_keyboard(language_code))


@user_private.callback_query(F.data == 'to_main')
async def to_main(event: Union[CallbackQuery, Message], state: FSMContext, first_time=False):
    if isinstance(event, Message):  # Если передан message вместо callback
        message = event
    else:
        message = event.message  # Это callback, достаём message

    tg_id = message.from_user.id

    # Сначала пытаемся взять язык из FSMContext
    user_data = await state.get_data()
    language_code = user_data.get("language_code")

    if not language_code:
        # Если в FSMContext нет языка, берем его из БД
        language_code = await orm_get_user_language(tg_id)
        await state.update_data(language_code=language_code)  # Сохраняем в FSMContext

    messages = MESSAGES.get(language_code, MESSAGES['ru'])  # По умолчанию русский

    if first_time:
        await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))
    else:
        try:
            if message.photo or message.video:
                await message.delete()
                await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))
            else:
                await message.edit_text(
                    text=messages['welcome'],
                    reply_markup=kb.main_menu_keyboard(language_code)
                )
        except Exception as e:
            print(f"Ошибка при редактировании или удалении сообщения: {e}")
            await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))



@user_private.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])  # Default to Russian if language code is not found

    # Define the single category ID (replace with your actual category ID)
    single_category_id = 1  # Replace with your actual category ID

    # Update the state with the category ID
    await state.update_data(category_id=single_category_id)

    # Show products directly from the single category
    await callback.message.edit_text(
        text=messages['product_menu'],
        reply_markup=await kb.items(single_category_id, page=1, items_per_row=3, language=language_code,
                                    back_callback='to_main')
    )


# @user_private.callback_query(F.data.startswith('usercategories_'))
# async def categories_pagination(callback: CallbackQuery, state: FSMContext):
#     page = int(callback.data.split('_')[1])
#     data = await state.get_data()
#     sex = data.get('sex', None)
#
#     await callback.answer('')
#
#     # Get the user's preferred language
#     language_code = await orm_get_user_language(callback.from_user.id)
#     messages = MESSAGES.get(language_code, MESSAGES['ru'])
#
#     await callback.message.edit_text(
#         messages['category_menu'],
#         reply_markup=await kb.user_categories(back_callback='catalog', page=page, categories_per_page=4,
#                                               language=language_code, sex=sex)
#     )
#
#
# @user_private.callback_query(F.data.startswith('UserCategory_'))
# async def category(callback: CallbackQuery, state: FSMContext):
#     category_id = int(callback.data.split('_')[1])
#     await state.update_data(category_id=category_id)
#     await callback.answer('')
#
#     # Get the user's preferred language
#     language_code = await orm_get_user_language(callback.from_user.id)
#     messages = MESSAGES.get(language_code, MESSAGES['ru'])
#
#     await callback.message.edit_text(
#         messages['product_menu'],
#         reply_markup=await kb.items(category_id, page=1, items_per_row=3, language=language_code,
#                                     back_callback='catalog')
#     )


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
    product_id = callback.data.split('_')[1]
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

        await state.update_data(product_id=product_id,
                                product_name=product_name,
                                quantity=1)

        # Get the user's active promo code
        user = await orm_get_user_by_tg_id(callback.from_user.id)
        discount = Decimal(0)  # Initialize discount as Decimal
        if user and user.active_promo_code_id:
            promo_code = await orm_get_promo_code_by_id(user.active_promo_code_id)
            if promo_code and (not promo_code.expiry_date or promo_code.expiry_date > datetime.now()):
                discount = Decimal(str(promo_code.discount))  # Convert discount to Decimal

        # Calculate the discounted price
        price = product.price  # Default price
        discounted_price_text = ""  # Initialize empty text for discounted price

        if discount > 0:  # Only apply discount if it exists
            discounted_price = product.price * (Decimal(1) - discount / Decimal(100))
            discounted_price_formatted = locale.format_string('%d', discounted_price, grouping=True)
            discounted_price_text = f"{messages['discounted_price']}: {discounted_price_formatted} {messages['currency']}\n"

        price_formatted = locale.format_string('%d', product.price, grouping=True)

        text = (
            f"{messages['product_name']}: {product_name}\n"
            f"{messages['product_description']}: {product_description}\n"
            f"{messages['product_price']}: {price_formatted} {messages['currency']}\n"
            f"{discounted_price_text}"  # Only added if discount exists
            f"{messages['product_quantity']}: {1}\n\n"
        )

        data = await state.get_data()
        quantity = data.get('quantity', 1)
        keyboard = kb.create_product_buttons(quantity, language_code=language_code)

        if product.video_url:
            await state.update_data(message_type='video')  # Update state with message type
            await callback.message.delete()  # Delete the previous message
            await callback.message.answer_video(
                video=product.video_url,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(
            messages['product_not_found'],
            reply_markup=await kb.user_categories(back_callback='to_main',
                                                  page=1,
                                                  categories_per_page=4,
                                                  language=language_code)
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

        # Get the user's active promo code
        user = await orm_get_user_by_tg_id(callback.from_user.id)
        discount = 0
        if user and user.active_promo_code_id:
            promo_code = await orm_get_promo_code_by_id(user.active_promo_code_id)
            if promo_code and (not promo_code.expiry_date or promo_code.expiry_date > datetime.now()):
                discount = promo_code.discount

        # Calculate the discounted price
        total_price = product.price * quantity * (Decimal(1) - Decimal(discount) / Decimal(100))
        total_price_formatted = locale.format_string('%d', total_price, grouping=True)  # Discounted price
        original_price_formatted = locale.format_string('%d', product.price * quantity, grouping=True)  # Original price

        text = (
            f"{messages['product_name']}: {product_name}\n"
            f"{messages['product_description']}: {product_description}\n"
            f"{messages['original_price']}: {original_price_formatted} {messages['currency']}\n"
        )

        if discount > 0:
            text += f"{messages['discounted_price']}: {total_price_formatted} {messages['currency']}\n"

        text += f"{messages['product_quantity']}: {quantity}\n\n"

        # Check if the product has a video
        if product.video_url:
            keyboard = kb.create_product_buttons(quantity, language_code)
            try:
                # Edit the video message caption
                await callback.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error editing video caption: {e}")
                # If editing fails, send a new video message
                await callback.message.delete()
                await callback.message.answer_video(
                    video=product.video_url,
                    caption=text,
                    reply_markup=keyboard
                )
        else:
            # If there's no video, edit the text message
            keyboard = kb.create_product_buttons(quantity, language_code)
            try:
                await callback.message.edit_text(
                    text=text,
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error editing text message: {e}")
                # If editing fails, send a new text message
                await callback.message.answer(
                    text=text,
                    reply_markup=keyboard
                )
    else:
        await callback.message.edit_text(
            messages['product_not_found'],
            reply_markup=await kb.user_categories(back_callback='to_main',
                                                  page=1,
                                                  categories_per_page=4,
                                                  language=language_code)
        )


# Function to handle plus one
# Function to handle plus one
@user_private.callback_query(F.data == 'plus_one')
async def handle_plus_one(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quantity = data.get('quantity', 1)  # Default quantity is 1 if not set
    language_code = await orm_get_user_language(callback.from_user.id)

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
        await update_product_text(callback, state)


@user_private.callback_query(F.data == 'dobavit_v_korzinu')
async def handle_product_basker(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)  # Default quantity is 1 if not set
    order_id = data.get('order_id')
    try:
        product = await orm_get_product_by_id(product_id)
        if not product:
            await callback.answer("Продукт не найден")
            return

        total_cost = product.price * quantity

        # Store the order item in the database
        await orm_create_order_item(order_id, product_id, quantity, total_cost)

        language_code = await orm_get_user_language(callback.from_user.id)

        if language_code == 'uz':
            product_name = product.name_uz
            added_to_cart_message = (
                f"Korzinaga qo'shildi: {product_name} (Soni: {quantity}, Umumiy narxi: {total_cost} So'm)"
            )
        else:  # Default to Russian if language code is not recognized
            product_name = product.name_ru
            added_to_cart_message = (
                f"Добавлено в корзину: {product_name} (Количество: {quantity}, Общая стоимость: {total_cost} Сум)"
            )

        await callback.answer(added_to_cart_message)

    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        await callback.answer("Произошла ошибка при добавлении товара в корзину. Пожалуйста, попробуйте снова.")


@user_private.callback_query(F.data == 'basket')
async def basket_handler(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id

    # Retrieve user by Telegram ID
    user = await orm_get_user_by_tg_id(tg_id)

    # Check if the user exists, and create them if not
    if not user:
        user = await orm_create_user_by_tg_id(tg_id)  # Create a new user if they don't exist

    # Get the user's preferred language
    language_code = await orm_get_user_language(tg_id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Check if user phone number is missing
    if not user.phone_number:
        await state.set_state(OrderState.waiting_for_phone_number)
        await callback.message.answer(
            messages['request_phone_number'],
            reply_markup=kb.get_contact_keyboard(language_code=language_code)  # Pass the keyboard without calling it
        )
        return

    # Check if user location is missing
    if not user.latitude or not user.longitude:
        await state.set_state(OrderState.waiting_for_location)
        await callback.message.answer(
            messages['request_location'],  # Provide a message prompting for location
            reply_markup=kb.get_location_keyboard(language_code=language_code)  # Send the location request keyboard
        )
        return

    # If both phone number and location are available, show the basket
    await show_basket(callback, state)


@user_private.message(OrderState.waiting_for_phone_number, F.contact)
async def process_phone_number_contact(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number
    tg_id = message.from_user.id
    language_code = await orm_get_user_language(tg_id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Update the user's phone number in the database
    user = await orm_get_user_by_tg_id(tg_id)
    user.phone_number = phone_number
    await orm_update_user(user)

    # Confirm saving the phone number
    await message.answer(messages['number_saved'])

    # Now we need to move the user to the next state (waiting_for_location) if location is not available
    if not user.latitude or not user.longitude:
        await state.set_state(OrderState.waiting_for_location)
        await message.answer(
            messages['request_location'],  # Provide a message prompting for location
            reply_markup=kb.get_location_keyboard(language_code=language_code)  # Send the location request keyboard
        )
    else:
        # If location is already provided, show the basket immediately
        await show_basket(message, state)


@user_private.message(OrderState.waiting_for_location, F.location)
async def process_location(message: Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    tg_id = message.from_user.id
    language_code = await orm_get_user_language(tg_id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Update the user's location in the database
    user = await orm_get_user_by_tg_id(tg_id)
    user.latitude = latitude
    user.longitude = longitude
    await orm_update_user(user)

    # Confirm saving the location
    await message.answer(messages['location_saved'])

    # Proceed to show the basket
    await show_basket(message, state)


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
        await message.delete()
        language_code = await orm_get_user_language(tg_id)
        messages = MESSAGES.get(language_code, MESSAGES['ru'])
        await message.answer(messages['basket_empty'], reply_markup=ReplyKeyboardRemove())
        await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))
        return

    # Fetch user language
    language_code = await orm_get_user_language(tg_id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Get the user's active promo code
    user = await orm_get_user_by_tg_id(tg_id)
    discount = Decimal(0)  # Initialize discount as Decimal
    if user and user.active_promo_code_id:
        promo_code = await orm_get_promo_code_by_id(user.active_promo_code_id)
        if promo_code and (not promo_code.expiry_date or promo_code.expiry_date > datetime.now()):
            discount = Decimal(str(promo_code.discount))  # Convert discount to Decimal

    text = messages['basket_items'] + "\n\n"
    total_cost = Decimal(0)

    for item in order_items:
        product = await orm_get_product_by_id(item.product_id)

        # Apply discount if available
        if discount > 0:
            item_price = product.price * (Decimal(1) - discount / Decimal(100))
        else:
            item_price = product.price

        item_cost = item_price * item.quantity  # Now using discounted price
        total_cost += item_cost  # Sum up correctly

        # Select product name based on language
        product_name = product.name_uz if language_code == 'uz' else product.name_ru

        # Format individual item prices
        formatted_price = locale.format_string('%d', product.price, grouping=True)
        formatted_item_cost = locale.format_string('%d', item_cost, grouping=True)

        text += (
            f"{messages['product_name']}: {product_name}\n\n"
            f"{messages['product_price']}: {formatted_price} {messages['currency']}.\n"
            f"{messages['product_quantity']}: {item.quantity}\n"
        )

        # Show discount line only if discount exists
        if discount > 0:
            discounted_price_formatted = locale.format_string('%d', item_price, grouping=True)
            text += f"{messages['discounted_price']}: {discounted_price_formatted} {messages['currency']}\n"

        text += f"{messages['total_cost']}: {formatted_item_cost} {messages['currency']}\n\n"

    # Format total cost with thousands separator
    formatted_total_cost = locale.format_string('%d', total_cost, grouping=True)
    text += f"{messages['total_order_cost']}: {formatted_total_cost} {messages['currency']}"

    await message.delete()
    await message.answer(text, reply_markup=kb.create_basket_buttons(language_code))


def register_handlers_user_private(bot: Bot):
    @user_private.callback_query(F.data == 'buy_product')
    async def user_buy_product(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        order_id = data.get('order_id')
        user = await orm_get_user_by_tg_id(callback.from_user.id)
        order_items = await orm_get_order_items_by_order_id(order_id)

        if not order_items:
            await callback.answer(MESSAGES['ru']['basket_empty'])
            return

        # ✅ Calculate initial total cost
        total_cost = sum(Decimal(item.total_cost) for item in order_items)
        discounted_cost = total_cost  # Default to initial cost

        # ✅ Check for an active promo code
        promo_code = None  # Initialize before usage
        promo_code_text = ""

        if user and user.active_promo_code_id:
            promo_code = await orm_get_promo_code_by_id(user.active_promo_code_id)
            if promo_code and (not promo_code.expiry_date or promo_code.expiry_date > datetime.now()):
                discount_percentage = Decimal(promo_code.discount)
                discounted_cost = total_cost * (Decimal(1) - discount_percentage / Decimal(100))
                promo_code_text = f"{MESSAGES['ru']['promo_applied']}: {promo_code.code} (-{discount_percentage}%)\n"

        # ✅ Create a new order
        new_order = await orm_create_order(user.id, discounted_cost)

        # 📍 Get and format user's location
        user_location = await orm_get_user_location(user.id)
        location_text = ""
        if user_location:
            latitude, longitude = user_location
            location_name = await get_address_from_coordinates(latitude, longitude)
            location_text = f"{MESSAGES['ru']['location']}: {location_name}\n"

        # 📢 Constructing group message
        group_messages = MESSAGES['ru']
        group_text = f"{group_messages['order_id']}: {new_order.id}\n"

        for item in order_items:
            product = await orm_get_product_by_id(item.product_id)
            category_name = await orm_get_category_name(product.category_id, 'ru')
            product_name = product.name_ru

            await orm_save_excel_order(
                order_id=new_order.id,
                category_name_ru=category_name,
                product_name_ru=product_name,
                product_quantity=item.quantity,
                initial_cost=item.total_cost,
                promo_code_name=promo_code.code if promo_code else None,
                promo_discount_percentage=float(promo_code.discount) if promo_code else None,
                total_cost=item.total_cost * (Decimal(1) - (
                            Decimal(promo_code.discount) / Decimal(100))) if promo_code else item.total_cost,
                customer_name=callback.from_user.first_name,
                username=callback.from_user.username,
                phone_number=user.phone_number
            )

            group_text += (
                # f"{group_messages['category']}: {category_name}\n"
                f"{group_messages['product_name']}: {product_name}\n"
                f"{group_messages['quantity']}: {item.quantity}\n"
                f"{group_messages['total_cost']}: {locale.format_string('%d', item.total_cost, grouping=True)} {group_messages['currency']}\n\n"
            )

        # ✅ Add promo code and discounted cost if applied
        group_text += f"\n💰 {group_messages['total_order_cost']}: {locale.format_string('%d', total_cost, grouping=True)} {group_messages['currency']}\n"
        if promo_code_text:
            group_text += promo_code_text
            group_text += f"💸 {group_messages['discounted_cost']}: {locale.format_string('%d', discounted_cost, grouping=True)} {group_messages['currency']}\n"

        group_text += (
            f"{group_messages['customer_name']}: {callback.from_user.first_name},\n"
            f"{group_messages['username']}: {f'@{callback.from_user.username}' if callback.from_user.username else group_messages['no_username']}\n"
            f"☎️ {group_messages['phone']}: {user.phone_number}\n"
            f"{location_text}"
        )

        # 🚀 Send messages to group chats
        for group in GROUP_CHAT_IDS_WITH_THREADS:
            try:
                await bot.send_message(
                    chat_id=group["chat_id"],
                    text=group_text,
                    message_thread_id=group.get("message_thread_id")
                )
            except TelegramMigrateToChat as e:
                new_group_id = e.migrate_to_chat_id
                GROUP_CHAT_IDS_WITH_THREADS.remove(group)
                GROUP_CHAT_IDS_WITH_THREADS.append(
                    {"chat_id": new_group_id, "message_thread_id": group.get("message_thread_id")}
                )
                await bot.send_message(
                    chat_id=new_group_id,
                    text=group_text,
                    message_thread_id=group.get("message_thread_id")
                )

        # ✅ Send confirmation to the user (without order details)
        user_confirmation = f"{group_messages['order_sent_confirmation']}\n\n"

        # Добавляем список товаров
        user_confirmation += f"{group_messages['order_items']}:\n"
        for item in order_items:
            product = await orm_get_product_by_id(item.product_id)
            product_name = product.name_ru  # Используем русский язык
            user_confirmation += f"• {product_name} ({item.quantity} {group_messages['quantity_unit']})\n"

        if promo_code_text:
            user_confirmation += (
                f"\n{group_messages['initial_cost']}: {locale.format_string('%d', total_cost, grouping=True)} {group_messages['currency']}\n"
                f"{promo_code_text}"
                f"{group_messages['discounted_cost']}: {locale.format_string('%d', discounted_cost, grouping=True)} {group_messages['currency']}\n"
            )

        if location_text:
            user_confirmation += f"\n{location_text}\n"

        await callback.answer(group_messages['order_sent'])
        await callback.message.answer(user_confirmation)
        await callback.message.delete()
        await callback.message.answer(group_messages['welcome'], reply_markup=kb.main_menu_keyboard('ru'))

        # ✅ Clear the order items from the basket
        await orm_clean_order_items_by_order_id(order_id)

    @user_private.message(UserQuestionState.awaiting_question)
    async def forward_user_question(message: Message, state: FSMContext):
        # Forward the user's message to the specified chat and thread
        target_chat_id = -1002408666314
        target_thread_id = 6
        user_info = f"👤 {message.from_user.full_name}\n"
        if message.from_user.username:
            user_info += f"🔗 @{message.from_user.username}\n"
            user_info += f"🆔 {message.from_user.id}\n\n"

        try:
            # Use the bot instance here, which is passed to the function
            await bot.send_message(
                chat_id=target_chat_id,
                text=user_info + message.text,
                message_thread_id=target_thread_id
            )
            # Notify the user that their question was sent
            language_code = await orm_get_user_language(message.from_user.id)
            messages = MESSAGES.get(language_code, MESSAGES['ru'])
            await message.answer(messages['question_sent'], reply_markup=kb.main_menu_keyboard(language_code))
        except Exception as e:
            # Handle any exceptions (e.g., chat ID issues)
            await message.answer("⚠️ An error occurred while sending your question. Please try again later.")

            # Reset the state
        await state.clear()


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


@user_private.callback_query(F.data == 'refer')
async def get_refer(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    # Get the user's language (if available)
    language_code = await orm_get_user_language(callback.from_user.id)

    # Retrieve the user from the database asynchronously
    user = await orm_get_user_by_tg_id(callback.from_user.id)

    if not user:
        # If no user found, exit early or send an error message
        await callback.message.answer("User not found in the system.")
        return

    referral_code = user.referral_code
    referral_link = f"https://t.me/TayyorBoxBot?start=ref_{referral_code}"  # Construct referral link

    # Get the correct messages dictionary based on the user's language
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Count how many users were referred by the current user
    referred_users_count = await orm_get_referred_users_count(user.id)

    # Count how many referred users have made at least one order
    referred_users_with_orders_count = await orm_get_referred_users_with_orders_count(user.id)

    # First message: Referral statistics
    status_message = (
        f"{messages['refer_message']}\n\n"
        f"{messages['referred_users_count']}: {referred_users_count}\n"
        f"{messages['referred_users_with_orders_count']}: {referred_users_with_orders_count}"
    )

    await callback.message.answer(status_message)

    # Second message: Referral link and instructions
    link_message = (
        f"{messages['your_referral_code']}: {referral_code}\n\n"
        f"{messages['share_with_friends']}\n\n"
        f"{messages['your_referral_link']}: [Click here]({referral_link})👈"
    )

    await callback.message.answer(link_message, parse_mode="MarkdownV2")

    # Send main menu keyboard
    await callback.message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))


class UserQuestionState(StatesGroup):
    awaiting_question = State()


@user_private.callback_query(F.data == 'contacts')
async def get_contact_help(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Prompt the user to send their question
    await callback.message.answer(messages['send_question'])
    await state.set_state(UserQuestionState.awaiting_question)  # Set state to await the user's question


@user_private.callback_query(F.data == 'settings')
async def open_settings(callback: CallbackQuery):
    user = await orm_get_user_by_tg_id(callback.from_user.id)
    language_code = user.language  # Получаем язык пользователя

    await callback.message.edit_text(
        text="⚙️ Настройки:\nВыберите нужный пункт" if language_code == "ru" else "⚙️ Sozlamalar:\nKerakli bo'limni tanlang",
        reply_markup=kb.settings_keyboard(language_code)
    )


@user_private.callback_query(F.data == 'change_language')
async def choose_language(callback: CallbackQuery):
    await callback.message.edit_text(
        text="Выберите Язык\nTilni tanlang",
        reply_markup=kb.language_selection_keyboard()
    )


@user_private.callback_query(F.data == 'change_personal_info')
async def change_personal_info(callback: CallbackQuery):
    user = await orm_get_user_by_tg_id(callback.from_user.id)
    language_code = user.language
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Получаем местоположение пользователя
    user_location = await orm_get_user_location(user.id)

    if user_location:
        latitude, longitude = user_location
        location_text = await get_address_from_coordinates(latitude, longitude)
    else:
        location_text = messages['no_location']

    text = (
        f"{messages['choose_info_to_change']}\n\n"
        f"{messages['current_phone']}: {user.phone_number}\n"
        f"{messages['location']}: {location_text}"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=kb.personal_info_keyboard(language_code)
    )


@user_private.callback_query(F.data == 'change_phone')
async def change_phone(callback: CallbackQuery, state: FSMContext):
    user = await orm_get_user_by_tg_id(callback.from_user.id)
    language_code = user.language
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Отправляем отдельное сообщение с клавиатурой
    await callback.message.answer(
        messages['send_phone_prompt'],  # Using dictionary variable
        reply_markup=kb.get_contact_keyboard(language_code)  # Отправляем клавиатуру с кнопкой
    )

    await state.set_state(PersonalInfoState.waiting_for_phone_number)


@user_private.message(PersonalInfoState.waiting_for_phone_number, F.contact)
async def save_new_phone(message: Message, state: FSMContext):
    new_phone = message.contact.phone_number  # Получаем номер из объекта контакта
    user = await orm_get_user_by_tg_id(message.from_user.id)

    await orm_update_user_phone(user.id, new_phone)  # Обновляем номер в БД

    language_code = await orm_get_user_language(message.from_user.id)  # Получаем язык пользователя
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await message.answer(messages['phone_updated'], reply_markup=ReplyKeyboardRemove())  # Use dict variable
    await state.clear()

    # Отправляем главное меню
    await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))


@user_private.callback_query(F.data == 'change_location')
async def change_location(callback: CallbackQuery, state: FSMContext):
    user = await orm_get_user_by_tg_id(callback.from_user.id)
    language_code = user.language
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await callback.message.edit_text(messages['send_location_prompt'])  # Using dictionary variable

    # Отправляем отдельное сообщение с клавиатурой
    await callback.message.answer(
        messages['send_location_button'],
        reply_markup=kb.get_location_keyboard(language_code)
    )

    await state.set_state(PersonalInfoState.waiting_for_location)


@user_private.message(PersonalInfoState.waiting_for_location, F.location)
async def save_new_location(message: Message, state: FSMContext):
    user = await orm_get_user_by_tg_id(message.from_user.id)

    latitude = message.location.latitude
    longitude = message.location.longitude

    await orm_update_user_location(user.id, latitude, longitude)  # Обновляем координаты в БД

    language_code = await orm_get_user_language(message.from_user.id)  # Получаем язык пользователя
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await message.answer(messages['location_updated'], reply_markup=ReplyKeyboardRemove())  # Use dict variable
    await state.clear()

    # Отправляем главное меню
    await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))


# @user_private.callback_query(F.data == 'private_add_product')
# async def to_category(callback: CallbackQuery, state: FSMContext):
#     await callback.answer('')
#     data = await state.get_data()
#     message_type = data.get('message_type', 'text')
#
#     # Get the user's preferred language
#     language_code = await orm_get_user_language(callback.from_user.id)
#     messages = MESSAGES.get(language_code, MESSAGES['ru'])
#     if message_type == 'photo':
#         # Delete photo message
#         await callback.message.delete()
#         await callback.message.answer(
#             text=messages['category_menu'],
#             reply_markup=await kb.user_categories(back_callback='to_main',
#                                                   page=1,
#                                                   categories_per_page=4,
#                                                   language=language_code)
#         )
#     else:
#         await callback.message.edit_text(
#             text=messages['category_menu'],
#             reply_markup=await kb.user_categories(back_callback='to_main',
#                                                   page=1,
#                                                   categories_per_page=4,
#                                                   language=language_code)
#         )


@user_private.message(F.location)
async def location_received(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    latitude = message.location.latitude
    longitude = message.location.longitude

    # Save the location to the database
    response = await save_user_location(tg_id, latitude, longitude)

    # Get user's language for the response
    language_code = await orm_get_user_language(tg_id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await message.answer(response, reply_markup=kb.main_menu_keyboard(language_code))

    # Proceed with any next actions (e.g., showing basket)
    await show_basket(message, state)


class PromoCodeState(StatesGroup):
    enter_promo_code = State()  # Step 1: Enter the promo code text


@user_private.callback_query(F.data == 'promo_code')
async def activate_promo_code(callback: CallbackQuery, state: FSMContext):
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await state.update_data(language_code=language_code)  # Сохраняем язык в FSMContext

    await callback.answer()
    await callback.message.answer("Введите промокод:")
    await state.set_state(PromoCodeState.enter_promo_code)


@user_private.message(PromoCodeState.enter_promo_code)
async def process_promo_code(message: Message, state: FSMContext):
    promo_code = message.text.strip()

    # Получаем язык из FSMContext
    user_data = await state.get_data()
    language_code = user_data.get("language_code", "ru")  # Если нет в state, ставим 'ru' по умолчанию
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    # Проверяем промокод
    valid_promo_code = await orm_get_promo_code_by_text(promo_code)
    if valid_promo_code:
        await orm_activate_promo_code_for_user(message.from_user.id, valid_promo_code.id)
        await message.answer(f"Промокод '{promo_code}' успешно активирован!")
    else:
        await message.answer("Неверный промокод. Пожалуйста, попробуйте еще раз.")

    await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))
    await state.clear()


@user_private.callback_query(F.data == 'my_orders')
async def user_my_orders(callback: CallbackQuery):
    user = await orm_get_user_by_tg_id(callback.from_user.id)
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    await callback.message.delete()

    # Получаем заказы пользователя из таблицы ExcelOrder, только со статусом "pending"
    excel_orders = await orm_get_excel_orders_by_user_phone(user.phone_number)

    # Фильтруем заказы со статусом "pending"
    pending_orders = [order for order in excel_orders if order.status == "pending"]

    if not pending_orders:
        await callback.answer(messages['no_orders'])
        return

    grouped_orders = {}

    for order in pending_orders:
        if order.order_id not in grouped_orders:
            grouped_orders[order.order_id] = {
                "items": [],
                "total_cost": Decimal(0),
                "promo_code": order.promo_code_name,
                "promo_discount": Decimal(order.promo_discount_percentage or 0),
                "customer_name": order.customer_name,
                "username": order.username,
                "phone_number": order.phone_number,
            }

        grouped_orders[order.order_id]["items"].append({
            # "category": order.category_name_ru,
            "product_name": order.product_name_ru,
            "quantity": order.product_quantity,
            "initial_cost": Decimal(order.initial_cost),
            "total_cost": Decimal(order.total_cost)
        })
        grouped_orders[order.order_id]["total_cost"] += Decimal(order.total_cost)

    # Получаем местоположение пользователя
    user_location = await orm_get_user_location(user.id)
    location_text = ""
    if user_location:
        latitude, longitude = user_location
        location_name = await get_address_from_coordinates(latitude, longitude)
        location_text = f"📍 {messages['location']}: {location_name}\n"

    order_texts = []

    for order_id, order_data in grouped_orders.items():
        text = f"{messages['order_id']}: {order_id}\n\n"

        for item in order_data["items"]:
            text += (
                # f"{messages['category']}: {item['category']}\n"
                f"{messages['product_name']}: {item['product_name']}\n"
                f"{messages['quantity']}: {item['quantity']}\n"
                f"{messages['total_cost']}: {locale.format_string('%d', item['total_cost'], grouping=True)} {messages['currency']}\n\n"
            )

        total_cost = order_data["total_cost"]
        discount_text = ""

        if order_data["promo_discount"] > 0:
            discounted_total_cost = total_cost * (Decimal(1) - order_data["promo_discount"] / Decimal(100))
            formatted_discounted_total = locale.format_string('%d', discounted_total_cost, grouping=True)
            discount_text = f"{messages['promo_applied']}: {order_data['promo_code']} (-{order_data['promo_discount']}%)\n💸 {messages['discounted_price']}: {formatted_discounted_total} {messages['currency']}\n"

        formatted_total_cost = locale.format_string('%d', total_cost, grouping=True)
        text += f"💰 {messages['total_order_cost']}: {formatted_total_cost} {messages['currency']}\n"

        if discount_text:
            text += discount_text

        text += (
            f"👤 {messages['customer_name']}: {order_data['customer_name']}\n"
            f"🎭 {messages['username']}: @{order_data['username'] if order_data['username'] else 'N/A'}\n"
            f"☎️ {messages['phone_number']}: {order_data['phone_number']}\n"
        )

        if location_text:
            text += location_text  # Добавляем локацию в текст заказа

        order_texts.append(text)

    for order_text in order_texts:
        await callback.message.answer(order_text)

    await callback.message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))
    await callback.answer()


def calculate_discounted_price(price: float, discount: float) -> float:
    return price * (1 - discount / 100)
