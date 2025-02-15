import locale
from typing import Union

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
    orm_update_user_location, orm_update_user_phone

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
    language_code = await orm_get_user_language(tg_id)
    await state.update_data(language_code=language_code)

    messages = MESSAGES.get(language_code, MESSAGES['ru'])  # По умолчанию русский

    if first_time:
        await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))
    else:
        try:
            await message.edit_text(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))
        except Exception as e:
            print(f"Ошибка при редактировании сообщения: {e}")
            await message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))


@user_private.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')

    # Get the user's preferred language
    language_code = await orm_get_user_language(callback.from_user.id)
    messages = MESSAGES.get(language_code, MESSAGES['ru'])  # Default to Russian if language code is not found

    data = await state.get_data()
    message_type = data.get('message_type', 'text')  # Retrieve the message type from the state

    if message_type == 'photo':
        # Delete the previous message
        await callback.message.delete()

        # Show categories directly without asking for gender
        await callback.message.answer(
            text=messages['category_menu'],
            reply_markup=await kb.user_categories(back_callback='to_main', page=1, categories_per_page=4,
                                                  language=language_code)
        )
    else:
        # Edit the existing message to show categories directly
        await callback.message.edit_text(
            text=messages['category_menu'],
            reply_markup=await kb.user_categories(back_callback='to_main', page=1, categories_per_page=4,
                                                  language=language_code)
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
        reply_markup=await kb.items(category_id, page=1, items_per_row=3, language=language_code,
                                    back_callback='catalog')
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

        await state.update_data(product_id=product_id,
                                product_name=product_name,
                                quantity=1)

        price_formatted = locale.format_string('%d', product.price, grouping=True)  # Format price without decimals
        text = (
            f"{messages['product_name']}: {product_name}\n"
            f"{messages['product_description']}: {product_description}\n"
            f"{messages['product_price']}: {price_formatted} {messages['currency']}\n"
            f"{messages['product_quantity']}: {1}\n\n"  # Default quantity is set to 1
        )
        if product.image_url:
            data = await state.get_data()
            quantity = data.get('quantity', 1)
            keyboard = kb.create_product_buttons(quantity, language_code=language_code)
            await state.update_data(message_type='photo')  # Update state with message type
            await callback.message.delete()
            await callback.message.answer_photo(photo=product.image_url,
                                                caption=text,
                                                reply_markup=keyboard)
        else:
            await state.update_data(message_type='text')  # Update state with message type
            await callback.message.edit_text(text, reply_markup=None)
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

        total_price = product.price * quantity
        total_price_formatted = locale.format_string('%d', total_price,
                                                     grouping=True)  # Format total price without decimals

        text = (
            f"{messages['product_name']}: {product_name}\n"
            f"{messages['product_description']}: {product_description}\n"
            f"{messages['product_price']}: {total_price_formatted} {messages['currency']}\n"
            f"{messages['product_quantity']}: {quantity}\n\n"
        )

        if product.image_url:
            keyboard = kb.create_product_buttons(quantity, language_code)
            await callback.message.edit_caption(caption=text,
                                                reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, reply_markup=None)
    else:
        await callback.message.edit_text(
            messages['product_not_found'],
            reply_markup=await kb.user_categories(back_callback='to_main',
                                                  page=1,
                                                  categories_per_page=4,
                                                  language=language_code)
        )


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

        # Directly update the product view text after updating the quantity
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
            f"{messages['product_name']}: {product_name}\n\n"
            f"{messages['product_price']}: {formatted_price} {messages['currency']}.\n"
            f"{messages['product_quantity']}: {item.quantity}\n"
            f"{messages['total_cost']}: {formatted_item_cost} {messages['currency']}\n\n"
        )

    # Format total order cost with thousands separator
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

        total_cost = sum(item.total_cost for item in order_items)
        new_order = await orm_create_order(user.id, total_cost)
        language_code = await orm_get_user_language(callback.from_user.id)
        messages = MESSAGES.get(language_code, MESSAGES['ru'])

        # 🛒 Constructing the order details
        user_text = f"{messages['order_id']}: {new_order.id}\n"

        for item in order_items:
            product = await orm_get_product_by_id(item.product_id)
            category_name = await orm_get_category_name(product.category_id, language_code)
            product_name = product.name_uz if language_code == 'uz' else product.name_ru

            user_text += (
                f"{messages['category']}: {category_name}\n"
                f"{messages['product_name']}: {product_name}\n"
                f"{messages['quantity']}: {item.quantity}\n"
                f"{messages['total_cost']}: {locale.format_string('%d', item.total_cost, grouping=True)} {messages['currency']}\n\n"
            )

        user_text += f"{messages['total_order_cost']}: {locale.format_string('%d', total_cost, grouping=True)} {messages['currency']}\n\n"
        user_text += (f"{messages['customer_name']}: {callback.from_user.first_name},\n"
                      f"{messages['username']}: {f'@{callback.from_user.username}' if callback.from_user.username else messages['no_username']}\n"
                      f"{messages['phone']}: {user.phone_number}")

        # 📍 Get and format user's location
        user_location = await orm_get_user_location(user.id)
        if user_location:
            latitude, longitude = user_location
            location_name = await get_address_from_coordinates(latitude, longitude)

            # Append formatted location name to user message
            user_text += f"\n{messages['location']}: {location_name}"

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
                total_cost=item.total_cost,
                customer_name=callback.from_user.first_name,
                username=callback.from_user.username,
                phone_number=user.phone_number
            )

            group_text += (
                f"{group_messages['category']}: {category_name}\n"
                f"{group_messages['product_name']}: {product_name}\n"
                f"{group_messages['quantity']}: {item.quantity}\n"
                f"{group_messages['total_cost']}: {locale.format_string('%d', item.total_cost, grouping=True)} {messages['currency']}\n\n"
            )

        group_text += f"💰{group_messages['total_order_cost']}: {locale.format_string('%d', total_cost, grouping=True)} {messages['currency']}\n\n"
        group_text += (f"{group_messages['customer_name']}: {callback.from_user.first_name},\n"
                       f"{group_messages['username']}: {f'@{callback.from_user.username}' if callback.from_user.username else group_messages['no_username']}\n"
                       f"☎️{group_messages['phone']}: {user.phone_number}")

        # 📍 Append formatted location name to group message
        if user_location:
            group_text += f"\n{group_messages['location']}: {location_name}"

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
                    {"chat_id": new_group_id, "message_thread_id": group.get("message_thread_id")})
                await bot.send_message(
                    chat_id=new_group_id,
                    text=group_text,
                    message_thread_id=group.get("message_thread_id")
                )

        # 📩 Send confirmation to user
        await bot.send_message(chat_id=callback.from_user.id, text=group_text)

        await orm_clean_order_items_by_order_id(order_id)
        await callback.answer(messages['order_sent'])
        await callback.message.answer(messages['order_sent_confirmation'])
        await callback.message.delete()
        await callback.message.answer(messages['welcome'], reply_markup=kb.main_menu_keyboard(language_code))

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


@user_private.callback_query(F.data == 'private_add_product')
async def to_category(callback: CallbackQuery, state: FSMContext):
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
            reply_markup=await kb.user_categories(back_callback='to_main',
                                                  page=1,
                                                  categories_per_page=4,
                                                  language=language_code)
        )
    else:
        await callback.message.edit_text(
            text=messages['category_menu'],
            reply_markup=await kb.user_categories(back_callback='to_main',
                                                  page=1,
                                                  categories_per_page=4,
                                                  language=language_code)
        )


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
