from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.orm_queries import orm_get_categories, orm_get_category_by_id, orm_get_products_by_category_id, \
    orm_count_products_by_category_id

ITEMS_PER_PAGE = 4

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

all_categories = None


async def fetch_categories():
    global all_categories
    all_categories = await orm_get_categories()


async def products_by_category(category_id: int, page: int, items_per_row: int = 2):
    offset = (page - 1) * ITEMS_PER_PAGE
    all_products = await orm_get_products_by_category_id(category_id, offset, ITEMS_PER_PAGE)
    total_products = await orm_count_products_by_category_id(category_id)

    inline_keyboard = []
    row = []
    for product in all_products:
        row.append(InlineKeyboardButton(text=product.p_name, callback_data=f'product_{product.id}'))
        if len(row) == items_per_row:
            inline_keyboard.append(row)
            row = []

    # If there are remaining buttons in the row, add them to the keyboard
    if row:
        inline_keyboard.append(row)

    # Add pagination buttons
    total_pages = (total_products + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text='⬅️ Назад', callback_data=f'pchcategory_{category_id}_{page - 1}'))
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text='➡️ Далее', callback_data=f'pchcategory_{category_id}_{page + 1}'))
    pagination_buttons.append(InlineKeyboardButton(text='Назад к Категориям', callback_data='change_product'))

    inline_keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def products_to_delete(category_id: int, page: int):
    offset = (page - 1) * ITEMS_PER_PAGE
    all_products = await orm_get_products_by_category_id(category_id, offset, ITEMS_PER_PAGE)
    total_products = await orm_count_products_by_category_id(category_id)

    inline_keyboard = []
    for product in all_products:
        inline_keyboard.append([InlineKeyboardButton(text=product.p_name, callback_data=f'catalog_products_{product.id}')])

    # Add pagination buttons
    total_pages = (total_products + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text='⬅️ Назад', callback_data=f'catalog_categories_{category_id}_{page - 1}'))
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text='➡️ Далее', callback_data=f'catalog_categories_{category_id}_{page + 1}'))
    pagination_buttons.append(InlineKeyboardButton(text='Назад к Категориям', callback_data='change_product'))

    inline_keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)




async def products_for_catalog(category_id: int, page: int):
    offset = (page - 1) * ITEMS_PER_PAGE
    all_products = await orm_get_products_by_category_id(category_id, offset, ITEMS_PER_PAGE)
    total_products = await orm_count_products_by_category_id(category_id)

    inline_keyboard = []
    for product in all_products:
        inline_keyboard.append([InlineKeyboardButton(text=product.p_name, callback_data=f'dproduct_{product.id}')])

    # Add pagination buttons
    total_pages = (total_products + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text='⬅️ Назад', callback_data=f'pdcategory_{category_id}_{page - 1}'))
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text='➡️ Далее', callback_data=f'pdcategory_{category_id}_{page + 1}'))
    pagination_buttons.append(InlineKeyboardButton(text='Назад к Категориям', callback_data='change_product'))

    inline_keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)




admin_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Товары', callback_data='product')],
    [InlineKeyboardButton(text='Категория', callback_data='category'),
     InlineKeyboardButton(text='Каталог', callback_data='catalog')]
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


async def categories():
    all_categories = await orm_get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                          callback_data=f'category_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_admin_category'))
    return keyboard.adjust(2).as_markup()


async def categorie():
    all_categories = await orm_get_category_by_id()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                          callback_data=f'categoryby_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_main'))
    return keyboard.adjust(2).as_markup()


# Fetch categories once


# Fetch categories once


# Define inline button functions
async def select_category_keyboard():
    if all_categories is None:
        await fetch_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                          callback_data=f'select_category_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_main'))
    return keyboard.adjust(2).as_markup()


async def pcategory_keyboard():
    if all_categories is None:
        await fetch_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                          callback_data=f'pcategory_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_admin_product'))
    return keyboard.adjust(2).as_markup()


async def pchcategory_keyboard():
    if all_categories is None:
        await fetch_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                          callback_data=f'pchcategory_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_admin_product'))

    return keyboard.adjust(2).as_markup()


async def pdcategory_keyboard():
    if all_categories is None:
        await fetch_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                          callback_data=f'pdcategory_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_admin_product'))
    return keyboard.adjust(2).as_markup()


async def select_categories():
    all_categories = await orm_get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f'select_category_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_admin_category'))
    return keyboard.adjust(2).as_markup()


def create_products_keyboard(products):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for product in products:
        button = InlineKeyboardButton(text=product.p_name, callback_data=f"product:{product.id}")
        keyboard.add(button)
    keyboard.add(InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
    return keyboard


# CATALOG
async def catalog_categories_menu():
    all_categories = await orm_get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f'catalog_categories_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='main_menu'))
    return keyboard.adjust(2).as_markup()


def catalog_products_menu(products):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for product in products:
        button = InlineKeyboardButton(text=product.p_name, callback_data=f"catalog_products_{product.id}")
        keyboard.add(button)
    keyboard.add(InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
    return keyboard

def get_callback_btns(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


def get_url_btns(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, url in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, url=url))

    return keyboard.adjust(*sizes).as_markup()


# Создать микс из CallBack и URL кнопок
def get_inlineMix_btns(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, value in btns.items():
        if '://' in value:
            keyboard.add(InlineKeyboardButton(text=text, url=value))
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=value))

    return keyboard.adjust(*sizes).as_markup()
