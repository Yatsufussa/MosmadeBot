# Languages definition
LANGUAGES = {
    'ru': 'Русский',
    'uz': 'Oʻzbek tili',
}

# Messages in Russian
MESSAGES_RU = {
    'welcome': "Добро пожаловать в интернет магазин Mosmade!",
    'language_prompt': "Выберите язык интерфейса:",
    'language_selected': "Язык интерфейса установлен: Русский",
    'main_menu': "Главное меню",
    'category_menu': "Выберите Категорию Товара",
    'category': "Категория",
    'product_menu': "Выберите модель товара",
    'product_name': 'Модель',
    'product_description': 'Описание модели',
    'product_price': 'Цена',
    'product_quantity': 'Количество',
    'quantity': 'Количество',
    'product_not_found': 'Товар не найден',
    'request_phone_number': 'Поделитесь номером телефона',
    'basket_empty': 'Корзина пуста.',
    'basket_items': 'Ваши товары в корзине🛍',
    'total_cost': 'Общая стоимость',
    'total_order_cost': '💰Общая стоимость ВСЕХ продуктов',
    'buy_product': 'Купить',
    'private_add_product': 'Добавить еще',
    'clean_basket': '🗑Очистить Корзину',
    'customer_name': 'Имя Заказчика',
    'contact_prompt': 'Пожалуйста, отправьте ваш номер телефона:',
    'order_id': 'Номер заказа',
    'username': '🎭Username',
    'phone': 'Номер Телефона',
    'order_sent': 'Ваш Заказ Отправлен!\nОжидайте обратной связи',
    'order_sent_confirmation': 'Ваш Заказ Отправлен!',
    'add_to_basket': '🛒Добавить в Корзину',
    'back': 'Назад',
    'basket_cleaned': '🗑Корзина Очищена',
    'basket_cleaned_confirmation': 'Корзина Пуста',
    'choose_gender': 'Выберите тип категории Мужская или Женская',
    'show_basket': '🛍 Перейти к Корзине',
    'number_saved': 'Ваш Номер Сохранен',
    'currency': 'Сум',
}


# Messages in Uzbek
MESSAGES_UZ = {
    'welcome': "Mosmade do'koniga xush kelibsiz!",
    'language_prompt': "Interfeys tilini tanlang:",
    'language_selected': "Interfeys tili tanlandi: Oʻzbek tili",
    'main_menu': "Asosiy menyu",
    'category_menu': "Kategoriyani tanlang",
    'category': "Kategoriya",
    'product_menu': "Mahsulotni tanlang",
    'product_name': 'Model',
    'product_description': 'Model tavsifi',
    'product_price': 'Narxi',
    'product_quantity': 'Miqdori',
    'quantity': 'Miqdori',
    'product_not_found': 'Mahsulot topilmadi',
    'request_phone_number': 'Telefon Raqamini Yuboring',
    'basket_empty': "🗑Savat bo'sh.",
    'basket_items': 'Savatdagi mahsulotlar🛍',
    'total_cost': 'Umumiy narx',
    'total_order_cost': '💰Barcha mahsulotlar UMUMIY narxi',
    'buy_product': 'Sotib olish',
    'private_add_product': 'Yana qo\'shish',
    'clean_basket': 'Savatni tozalash',
    'customer_name': 'Ismi',
    'contact_prompt': 'Iltimos, telefon raqamingizni yuboring:',
    'order_id': 'Buyurtma raqami',
    'username': '🎭 Username',
    'phone': 'Telefon Raqami',
    'order_sent': 'Zakaziz Qabul qilinde!\nQaytib Aloqaga Chiqamz',
    'order_sent_confirmation': 'Zakaziz Qabul qilinde!',
    'add_to_basket': '🛒 Savatga Qushish',
    'back': 'Orqaga Qaytish',
    'basket_cleaned': '🗑Savat yangilandi',
    'basket_cleaned_confirmation': 'Savatingiz bush',
    'choose_gender': 'Ayollarni kategoriyasimi Yo Erkaklarnikimi tanlang',
    'show_basket': '🛍 Savatga Utish',
    'number_saved': 'Telefon Raqamingiz Saqlandi',
    'currency': "So'm",
}
GENDER_MAPPING = {
    'male': 'мужской',
    'female': 'женский'
}

# Combined messages dictionary
MESSAGES = {
    'ru': MESSAGES_RU,
    'uz': MESSAGES_UZ,
}