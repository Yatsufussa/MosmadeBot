from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database.orm_queries import orm_get_products_by_category_id, orm_count_products_by_category_id, \
    orm_count_categories, orm_u_get_categories

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from language_dictionary.language import LANGUAGES

ITEMS_PER_PAGE = 4
all_categories = None


# Создаем клавиатуру с кнопкой запроса контакта
get_contact_keyboard = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='📱 Отправить мой номер телефона', request_contact=True)
    ]
], resize_keyboard=True)


# region Admin Keyboard
admin_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Товары', callback_data='product')],
    [InlineKeyboardButton(text='Категория', callback_data='category'),
     InlineKeyboardButton(text='Рассылка', callback_data='newsletter')]
])

admin_category = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить Категорию', callback_data='add_category'),
     InlineKeyboardButton(text='Изменить Категорию', callback_data='change_category')],
    [InlineKeyboardButton(text='Удалить Категорию', callback_data='delete_category'),
     InlineKeyboardButton(text='На главную Админ панель', callback_data='to_admin_main')]
])

admin_category_change = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Имя Категории', callback_data='change_c_name')],
    [InlineKeyboardButton(text='Пол Категории', callback_data='change_c_sex'),
     InlineKeyboardButton(text='Назад', callback_data='to_admin_category')]
])

admin_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить Товар', callback_data='add_product'),
     InlineKeyboardButton(text='Изменить Товар', callback_data='change_product')],
    [InlineKeyboardButton(text='Удалить Товар', callback_data='delete_product'),
     InlineKeyboardButton(text='На главную', callback_data='to_admin_main')]
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

# def language_selection_keyboard():
#     keyboard = InlineKeyboardMarkup()
#     for lang_code, lang_name in LANGUAGES.items():
#         keyboard.add(InlineKeyboardButton(text=lang_name, callback_data=f'select_language_{lang_code}'))
#     return keyboard


def language_selection_keyboard() -> InlineKeyboardMarkup:
    # Get flag emojis for Russia and Uzbekistan
    flag_ru = "🇷🇺" # Emoji code for Russian flag
    flag_uz = " 🇺🇿" # Emoji code for Uzbek flag

    # Create buttons with flag emojis
    ru = InlineKeyboardButton(text=f"{flag_ru} Русский", callback_data="select_language_ru")
    uz = InlineKeyboardButton(text=f"{flag_uz} O'zbek", callback_data='select_language_uz')

    # Create InlineKeyboardMarkup with the buttons
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [ru, uz],
    ])

    return markup


def main_menu_keyboard(language_code: str) -> InlineKeyboardMarkup:
    if language_code == 'ru':
        buttons = [
            [
                InlineKeyboardButton(text="Каталог", callback_data='catalog'),
                InlineKeyboardButton(text="Контакты", callback_data='contacts')
            ],
            [
                InlineKeyboardButton(text="Корзина", callback_data='basket'),
                InlineKeyboardButton(text="Наши Ткани", callback_data='textile')
            ],
            [
                InlineKeyboardButton(text="Язык", callback_data='language')
            ]
        ]
    elif language_code == 'uz':
        buttons = [
            [
                InlineKeyboardButton(text="Katalog", callback_data='catalog'),
                InlineKeyboardButton(text="Aloqalar", callback_data='contacts')
            ],
            [
                InlineKeyboardButton(text="Savat", callback_data='basket'),
                InlineKeyboardButton(text="Matolarimiz", callback_data='textile')
            ],
            [
                InlineKeyboardButton(text="Til", callback_data='language')
            ]
        ]
    else:
        buttons = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)



create_basket_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Купить', callback_data='buy_product'),
     InlineKeyboardButton(text='Добавить еще', callback_data='private_add_product')],
    [InlineKeyboardButton(text='Очистить Корзину', callback_data='clean_basket')],
])


# Generate Products

async def generate_product_keyboard(category_id: int, page: int, items_per_page: int, callback_prefix: str,
                                    navigation_callback: str, items_per_row: int = 3, back_callback: str = '',language: str = 'ru'):
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
            product_name = product.name_ru  # Default to Russian if language code is invalid
        row.append(InlineKeyboardButton(text=product_name, callback_data=f'{callback_prefix}_{product.id}'))
        if len(row) == items_per_row:
            inline_keyboard.append(row)
            row = []

    if row:
        inline_keyboard.append(row)

    total_pages = (total_products + items_per_page - 1) // items_per_page
    pagination_buttons = []

    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text='⬅️ Назад', callback_data=f'{navigation_callback}_{category_id}_{page - 1}'))

    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text='➡️ Далее', callback_data=f'{navigation_callback}_{category_id}_{page + 1}'))

    if back_callback:
        pagination_buttons.append(InlineKeyboardButton(text='Назад к Категориям', callback_data=back_callback))

    inline_keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def products_by_category(category_id: int, page: int, items_per_row: int = 2):
    return await generate_product_keyboard(category_id, page, ITEMS_PER_PAGE, 'product', 'products', items_per_row,
                                           back_callback='change_product')


async def products_to_delete(category_id: int, page: int, items_per_row: int = 2):
    return await generate_product_keyboard(category_id, page, ITEMS_PER_PAGE, 'dproduct', 'dproducts', items_per_row,
                                           back_callback='delete_product')


async def items(category_id: int, page: int, items_per_row: int = 2):
    return await generate_product_keyboard(category_id, page, ITEMS_PER_PAGE, 'item', 'itemscategory', items_per_row,
                                           back_callback='catalog')


def create_product_buttons(category_id: int, quantity: int) -> InlineKeyboardMarkup:
    plus = InlineKeyboardButton(text="➕", callback_data='plus_one')
    summa = InlineKeyboardButton(text=f"{quantity}", callback_data='summa')
    minus = InlineKeyboardButton(text="➖", callback_data='minus')
    dobavit_v_korzinu = InlineKeyboardButton(text="Добавить в корзину", callback_data='dobavit_v_korzinu')
    exit_russian = InlineKeyboardButton(text="Назад", callback_data=f'catalog')

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [minus, summa, plus],
        [dobavit_v_korzinu],
        [exit_russian]
    ])

    return markup


# Categories Generator
async def generate_category_keyboard(page: int, categories_per_page: int, callback_prefix: str,
                                     navigation_callback: str, back_callback: str, language: str = 'ru'):
    offset = (page - 1) * categories_per_page
    all_categories = await orm_u_get_categories(offset, categories_per_page)
    total_categories = await orm_count_categories()

    inline_keyboard = []
    row = []

    for category in all_categories:
        if language == 'ru':
            category_name = category.name_ru
        elif language == 'uz':
            category_name = category.name_uz
        else:
            category_name = category.name_ru  # Default to Russian if language code is invalid

        row.append(InlineKeyboardButton(text=category_name, callback_data=f'{callback_prefix}_{category.id}'))
        if len(row) == 2:
            inline_keyboard.append(row)
            row = []

    if row:
        inline_keyboard.append(row)

    total_pages = (total_categories + categories_per_page - 1) // categories_per_page
    pagination_buttons = []

    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text='⬅️ Назад', callback_data=f'{navigation_callback}_{page - 1}_{language}')
        )

    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text='➡️ Далее', callback_data=f'{navigation_callback}_{page + 1}_{language}')
        )

    pagination_buttons.append(
        InlineKeyboardButton(text='Назад к главному меню', callback_data=back_callback)
    )

    inline_keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def admin_add_product_categories(page: int = 1, categories_per_page: int = 5):
    return await generate_category_keyboard(page, categories_per_page, 'pcategory', 'pcategories',
                                            back_callback='to_admin_product')


async def pchcategory_keyboard(page: int = 1, categories_per_page: int = 5,back_callback: str = ''):
    return await generate_category_keyboard(page, categories_per_page, 'pchcategory', 'pchcategories',
                                            back_callback)


async def pdcategory_keyboard(page: int, categories_per_page: int = 5,back_callback: str = ''):
    return await generate_category_keyboard(page, categories_per_page, 'pdcategory', 'pdcategories',
                                            back_callback)


async def categories(page: int, categories_per_page: int = 5, back_callback: str = ''):
    return await generate_category_keyboard(page, categories_per_page, 'admincategory', 'admincategories',
                                            back_callback)


async def select_categories(page: int, categories_per_page: int = 5,back_callback: str = ''):
    return await generate_category_keyboard(page, categories_per_page, 'selectcategory', 'selectcategories',
                                            back_callback)


async def user_categories(page: int, categories_per_page: int = 5, back_callback: str = ''):
    return await generate_category_keyboard(page, categories_per_page, 'UserCategory', 'usercategories', back_callback)



