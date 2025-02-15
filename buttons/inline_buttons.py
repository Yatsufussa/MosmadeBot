from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from language_dictionary.language import MESSAGES
from database.orm_queries import orm_get_products_by_category_id, orm_count_products_by_category_id, \
    orm_count_categories, orm_u_get_categories

all_categories = None


def get_contact_keyboard(language_code: str) -> ReplyKeyboardMarkup:
    if language_code == 'ru':
        keyboard = ReplyKeyboardMarkup(keyboard=[
            [
                KeyboardButton(text='📱 Отправить мой номер телефона', request_contact=True)
            ]
        ], resize_keyboard=True)
    elif language_code == 'uz':
        keyboard = ReplyKeyboardMarkup(keyboard=[
            [
                KeyboardButton(text='📱 Telefon Raqamimni Yuborish', request_contact=True)
            ]
        ], resize_keyboard=True)
    else:
        keyboard = ReplyKeyboardMarkup(keyboard=[
            [
                KeyboardButton(text='📱 Отправить мой номер телефона', request_contact=True)
            ]
        ], resize_keyboard=True)

    return keyboard


def get_location_keyboard(language_code: str) -> ReplyKeyboardMarkup:
    if language_code == 'ru':
        keyboard = ReplyKeyboardMarkup(keyboard=[
            [
                KeyboardButton(text='📍 Отправить мое местоположение', request_location=True)
            ]
        ], resize_keyboard=True)
    elif language_code == 'uz':
        keyboard = ReplyKeyboardMarkup(keyboard=[
            [
                KeyboardButton(text='📍 Mening manzilimni yuboring', request_location=True)
            ]
        ], resize_keyboard=True)
    else:
        keyboard = ReplyKeyboardMarkup(keyboard=[
            [
                KeyboardButton(text='📍 Отправить мое местоположение', request_location=True)
            ]
        ], resize_keyboard=True)

    return keyboard



# region Admin Keyboard
admin_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Товары', callback_data='product')],
    [InlineKeyboardButton(text='Категория', callback_data='category'),
     InlineKeyboardButton(text='Рассылка', callback_data='newsletter')]
])

admin_category = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить', callback_data='add_category'),
     InlineKeyboardButton(text='Изменить', callback_data='change_category')],
    [InlineKeyboardButton(text='Удалить', callback_data='delete_category'),
     InlineKeyboardButton(text='Назад', callback_data='to_admin_main')]
])

admin_category_change = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Имя Категории', callback_data='change_c_name')],
    [InlineKeyboardButton(text='Назад', callback_data='to_admin_category')]
])

admin_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить Товар', callback_data='add_product'),
     InlineKeyboardButton(text='Изменить Товар', callback_data='change_product')],
    [InlineKeyboardButton(text='Удалить Товар', callback_data='delete_product'),
     InlineKeyboardButton(text='Назад', callback_data='to_admin_main')]
])

admin_product_change = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Имя', callback_data='change_p_name'),
     InlineKeyboardButton(text='Описание', callback_data='change_p_description')],
    [InlineKeyboardButton(text='Цену', callback_data='change_p_price'),
     InlineKeyboardButton(text='Фотографию', callback_data='change_p_photo')],
    [InlineKeyboardButton(text='Назад', callback_data='to_admin_product')],
])

admin_product_delete = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Удалить', callback_data='delete_product')],
    [InlineKeyboardButton(text='Назад', callback_data='to_admin_product')],
])


# endregion


def language_selection_keyboard() -> InlineKeyboardMarkup:
    # Get flag emojis
    flag_ru = "🇷🇺"
    flag_uz = " 🇺🇿"

    ru = InlineKeyboardButton(text=f"{flag_ru} Русский", callback_data="select_language_ru")
    uz = InlineKeyboardButton(text=f"{flag_uz} O'zbek", callback_data='select_language_uz')

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [ru, uz],
    ])

    return markup





def admin_category_add_product_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🧑🏻‍🦰 Мужчины", callback_data='adminaddpgender_male'),
         InlineKeyboardButton(text="👩🏻‍🦰 Женщины", callback_data='adminaddpgender_female')],
        [InlineKeyboardButton(text="Назад", callback_data='to_admin_product')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_category_gender_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🧑🏻‍🦰 Мужчины", callback_data='admingender_male'),
         InlineKeyboardButton(text="👩🏻‍🦰 Женщины", callback_data='admingender_female')],
        [InlineKeyboardButton(text="Назад", callback_data='to_admin_category')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_category_delete_product_gender_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🧑🏻‍🦰 Мужчины", callback_data='admindelpgender_male'),
         InlineKeyboardButton(text="👩🏻‍🦰 Женщины", callback_data='admindelpgender_female')],
        [InlineKeyboardButton(text="Назад", callback_data='to_admin_product')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_category_change_product_gender_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🧑🏻‍🦰 Мужчины", callback_data='adminchpgender_male'),
         InlineKeyboardButton(text="👩🏻‍🦰 Женщины", callback_data='adminchpgender_female')],
        [InlineKeyboardButton(text="Назад", callback_data='to_admin_product')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_category_delete_gender_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🧑🏻‍🦰 Мужчины", callback_data='admindelgender_male'),
         InlineKeyboardButton(text="👩🏻‍🦰 Женщины", callback_data='admindelgender_female')],
        [InlineKeyboardButton(text="Назад", callback_data='to_admin_category')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_menu_keyboard(language_code: str) -> InlineKeyboardMarkup:
    if language_code == 'ru':
        buttons = [
            [
                InlineKeyboardButton(text="🚀 Tayyor BOX", callback_data='catalog'),
                InlineKeyboardButton(text="☎️ Помощь", callback_data='contacts')
            ],
            [
                InlineKeyboardButton(text="🛒 Корзина", callback_data='basket'),
                InlineKeyboardButton(text="REF ссылка", callback_data='refer')
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data='settings')
            ]
        ]
    elif language_code == 'uz':
        buttons = [
            [
                InlineKeyboardButton(text="🚀 Tayyor BOX", callback_data='catalog'),
                InlineKeyboardButton(text="☎️ Yordam", callback_data='contacts')
            ],
            [
                InlineKeyboardButton(text="🛒 Savat", callback_data='basket'),
                InlineKeyboardButton(text="REF ssilkam", callback_data='refer')
            ],
            [
                InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data='settings')
            ]
        ]
    else:
        buttons = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_basket_buttons(language_code: str) -> InlineKeyboardMarkup:
    if language_code == 'ru':
        buttons = [
            [InlineKeyboardButton(text='💰Купить', callback_data='buy_product'),
             InlineKeyboardButton(text='🛍Добавить еще', callback_data='private_add_product')],
            [InlineKeyboardButton(text='🗑Очистить Корзину', callback_data='clean_basket')],
        ]
    elif language_code == 'uz':
        buttons = [
            [InlineKeyboardButton(text='💰Sotib olish', callback_data='buy_product'),
             InlineKeyboardButton(text="🛍Qo'shimcha qo'shish", callback_data='private_add_product')],
            [InlineKeyboardButton(text='🗑Savatni tozalash', callback_data='clean_basket')],
        ]
    else:
        buttons = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)


ITEMS_PER_PAGE = 6


# Generate Products
async def generate_product_keyboard(category_id: int, page: int, items_per_page: int, callback_prefix: str,
                                    navigation_callback: str, items_per_row: int = 3, back_callback: str = '',
                                    language: str = 'ru'):
    offset = (page - 1) * items_per_page
    all_products = await orm_get_products_by_category_id(category_id, offset, items_per_page)
    total_products = await orm_count_products_by_category_id(category_id)

    inline_keyboard = []
    row = []

    for product in all_products:
        if language == 'ru':
            product_name = product.name_ru
        elif language == 'uz':
            product_name = product.name_uz
        else:
            product_name = product.name_ru

        # Ensure callback_data length is within 64 characters
        callback_data = f'{callback_prefix}_{product.id}'
        if len(callback_data) > 64:
            raise ValueError(f'callback_data length exceeds 64 characters: {callback_data}')

        row.append(InlineKeyboardButton(text=product_name, callback_data=callback_data))
        if len(row) == items_per_row:
            inline_keyboard.append(row)
            row = []

    if row:
        inline_keyboard.append(row)

    total_pages = (total_products + items_per_page - 1) // items_per_page
    pagination_buttons = [None, None, None]

    if page > 1:
        callback_data = f'{navigation_callback}_{category_id}_{page - 1}'
        if len(callback_data) > 64:
            raise ValueError(f'callback_data length exceeds 64 characters: {callback_data}')
        pagination_buttons[0] = InlineKeyboardButton(text='⬅️', callback_data=callback_data)

    if isinstance(back_callback, str) and back_callback:
        if language == 'ru':
            back_to_categories_text = '⬇️'
        elif language == 'uz':
            back_to_categories_text = '⬇️'
        else:
            back_to_categories_text = '⬇️'

        if len(back_callback) > 64:
            raise ValueError(f'callback_data length exceeds 64 characters: {back_callback}')
        pagination_buttons[1] = InlineKeyboardButton(text=back_to_categories_text, callback_data=back_callback)

    if page < total_pages:
        callback_data = f'{navigation_callback}_{category_id}_{page + 1}'
        if len(callback_data) > 64:
            raise ValueError(f'callback_data length exceeds 64 characters: {callback_data}')
        pagination_buttons[2] = InlineKeyboardButton(text='➡️', callback_data=callback_data)

    # Filter out None values and create a new list for arranged buttons
    arranged_pagination_buttons = [button for button in pagination_buttons if button is not None]

    inline_keyboard.append(arranged_pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def products_by_category(category_id: int, page: int, items_per_row: int = 3):
    return await generate_product_keyboard(category_id, page, ITEMS_PER_PAGE, 'product', 'products', items_per_row,
                                           back_callback='change_product')


async def products_to_delete(category_id: int, page: int, items_per_row: int = 3):
    return await generate_product_keyboard(category_id, page, ITEMS_PER_PAGE, 'dproduct', 'dproducts', items_per_row,
                                           back_callback='delete_product')


async def items(category_id: int, page: int, items_per_row: int = 3, language: str = '', back_callback: str = ''):
    return await generate_product_keyboard(category_id, page, ITEMS_PER_PAGE, 'item', 'itemscategory', items_per_row,
                                           back_callback, language)


def create_product_buttons(quantity: int, language_code: str = 'ru') -> InlineKeyboardMarkup:
    messages = MESSAGES.get(language_code, MESSAGES['ru'])

    plus = InlineKeyboardButton(text="➕", callback_data='plus_one')
    summa = InlineKeyboardButton(text=f"{quantity}", callback_data='summa')
    minus = InlineKeyboardButton(text="➖", callback_data='minus')
    add_to_cart = InlineKeyboardButton(text=messages['add_to_basket'], callback_data='dobavit_v_korzinu')
    show_cart = InlineKeyboardButton(text=messages['show_basket'], callback_data='basket')
    exit_button = InlineKeyboardButton(text=messages['back'], callback_data='catalog')

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [minus, summa, plus],
        [add_to_cart],
        [show_cart],
        [exit_button]
    ])

    return markup


async def generate_category_keyboard(page: int, categories_per_page: int, callback_prefix: str,
                                     navigation_callback: str, back_callback: str, language: str = 'ru',
                                     sex: str = None):
    offset = (page - 1) * categories_per_page
    all_categories = await orm_u_get_categories(offset, categories_per_page, sex)
    total_categories = await orm_count_categories(sex)

    inline_keyboard = []
    row = []

    for category in all_categories:
        if language == 'ru':
            category_name = category.name_ru
        elif language == 'uz':
            category_name = category.name_uz
        else:
            category_name = category.name_ru

        row.append(InlineKeyboardButton(text=category_name, callback_data=f'{callback_prefix}_{category.id}'))
        if len(row) == 2:
            inline_keyboard.append(row)
            row = []

    if row:
        inline_keyboard.append(row)

    total_pages = (total_categories + categories_per_page - 1) // categories_per_page
    pagination_buttons = [None, None, None]

    if page > 1:
        pagination_buttons[0] = InlineKeyboardButton(text='⬅️',
                                                     callback_data=f'{navigation_callback}_{page - 1}_{language}')

    if page < total_pages:
        pagination_buttons[2] = InlineKeyboardButton(text='➡️',
                                                     callback_data=f'{navigation_callback}_{page + 1}_{language}')

    if language == 'ru':
        back_to_main_menu_text = '⬇️'
    elif language == 'uz':
        back_to_main_menu_text = '⬇️'
    else:
        back_to_main_menu_text = '⬇️'  # Default to Russian if language code is invalid

    pagination_buttons[1] = InlineKeyboardButton(text=back_to_main_menu_text, callback_data=back_callback)

    arranged_pagination_buttons = [button for button in pagination_buttons if button is not None]

    inline_keyboard.append(arranged_pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def admin_add_product_categories(page: int, categories_per_page: int = 5, back_callback: str = '',
                                       language: str = '',
                                       sex: str = None):
    return await generate_category_keyboard(page, categories_per_page, 'paddcategory', 'paddcategories', back_callback,
                                            language, sex)


async def pchcategory_keyboard(page: int, categories_per_page: int = 5, back_callback: str = '', language: str = '',
                               sex: str = None):
    return await generate_category_keyboard(page, categories_per_page, 'pchcategory', 'pchcategories', back_callback,
                                            language, sex)


async def pdcategory_keyboard(page: int, categories_per_page: int = 5, back_callback: str = '', language: str = '',
                              sex: str = None):
    return await generate_category_keyboard(page, categories_per_page, 'pdcategorie', 'pdcategories', back_callback,
                                            language, sex)


async def categories(page: int, categories_per_page: int = 5, back_callback: str = '', language: str = '',
                     sex: str = None):
    return await generate_category_keyboard(page, categories_per_page, 'AdminCategory', 'AdminCategories',
                                            back_callback,
                                            language, sex)


async def select_categories(page: int, categories_per_page: int = 5, back_callback: str = '', language: str = '',
                            sex: str = None):
    return await generate_category_keyboard(page, categories_per_page, 'selectcategory', 'selectcategories',
                                            back_callback,
                                            language, sex)


async def user_categories(page: int, categories_per_page: int = 5, back_callback: str = '', language: str = '',
                          sex: str = None):
    return await generate_category_keyboard(page, categories_per_page, 'UserCategory', 'usercategories', back_callback,
                                            language, sex)


def settings_keyboard(language_code: str) -> InlineKeyboardMarkup:
    if language_code == 'ru':
        buttons = [
            [InlineKeyboardButton(text="🌍 Изменить язык", callback_data='change_language')],
            [InlineKeyboardButton(text="👤 Изменить личные данные", callback_data='change_personal_info')],
            [InlineKeyboardButton(text="🔙 Назад", callback_data='to_main')]
        ]
    elif language_code == 'uz':
        buttons = [
            [InlineKeyboardButton(text="🌍 Tilni o'zgartirish", callback_data='change_language')],
            [InlineKeyboardButton(text="👤 Shaxsiy ma'lumotlarni o'zgartirish", callback_data='change_personal_info')],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data='to_main')]
        ]
    else:
        buttons = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def personal_info_keyboard(language_code: str) -> InlineKeyboardMarkup:
    if language_code == 'ru':
        buttons = [
            [InlineKeyboardButton(text="📞 Изменить номер телефона", callback_data='change_phone')],
            [InlineKeyboardButton(text="📍 Изменить местоположение", callback_data='change_location')],
            [InlineKeyboardButton(text="🔙 Назад", callback_data='settings')]
        ]
    elif language_code == 'uz':
        buttons = [
            [InlineKeyboardButton(text="📞 Telefon raqamni o'zgartirish", callback_data='change_phone')],
            [InlineKeyboardButton(text="📍 Joylashuvni o'zgartirish", callback_data='change_location')],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data='settings')]
        ]
    else:
        buttons = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)
