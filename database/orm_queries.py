from sqlalchemy import func, delete
from sqlalchemy.future import select
from database.engine import SessionMaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Category, Product, User, Order, OrderItem, ExcelOrder


async def orm_update_user_language(tg_id: int, language_code: str):
    async with SessionMaker() as session:
        # Create a select statement
        stmt = select(User).where(User.tg_id == tg_id)

        # Execute the statement
        result = await session.execute(stmt)

        # Get the first matching user
        user = result.scalars().first()

        if user:
            user.language = language_code
            # Commit the changes
            await session.commit()


async def orm_get_user_language(tg_id: int) -> str:
    async with SessionMaker() as session:
        result = await session.execute(select(User.language).where(User.tg_id == tg_id))
        user_language = result.scalar_one_or_none()
        if user_language:
            return user_language
        else:
            return 'ru'


async def orm_get_categories():
    async with SessionMaker() as session:
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        return categories


async def orm_get_category_by_id(category_id: int):
    async with SessionMaker() as session:
        category = await session.scalar(select(Category).where(Category.id == category_id))
        return category


async def orm_add_category(data):
    async with SessionMaker() as session:
        session.add(Category(**data))
        await session.commit()


async def orm_update_category_name_ru(category_id: int, new_name_ru: str):
    async with SessionMaker() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if category:
            category.name_ru = new_name_ru
            await session.commit()
            return True
        else:
            return False


async def orm_get_category_name(category_id: int, language_code: str = 'ru') -> str:
    async with SessionMaker() as session:
        # Select category asynchronously
        result = await session.execute(
            select(Category).filter(Category.id == category_id)
        )
        category = result.scalar()

        if not category:
            return "Unknown Category"

        # Determine which name to return based on language_code
        if language_code == 'uz':
            return category.name_uz
        else:
            return category.name_ru


async def orm_update_category_name_uz(category_id: int, new_name_uz: str):
    async with SessionMaker() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if category:
            category.name_uz = new_name_uz
            await session.commit()
            return True
        else:
            return False


async def orm_update_category_sex(category_id: int, new_sex: str):
    async with SessionMaker() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if category:
            category.sex = new_sex
            await session.commit()
            return True
        else:
            return False


async def orm_delete_category(category_id: int):
    async with SessionMaker() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if category:
            await session.delete(category)
            await session.commit()
            return True
        else:
            return False


async def orm_get_products():
    async with SessionMaker() as session:
        result = await session.execute(select(Category))
        products = result.scalars().all()
        return products


async def orm_get_product_by_id(item_id: int):
    async with SessionMaker() as session:
        query = select(Product, Category).join(Category).where(Product.id == item_id)
        result = await session.execute(query)
        return result.scalars().first()


async def orm_add_product(name_ru: str, name_uz: str, description_ru: str, description_uz: str, price: float,
                          category_id: int, image_url: str):
    async with SessionMaker() as session:
        new_product = Product(
            name_ru=name_ru,
            name_uz=name_uz,
            description_ru=description_ru,
            description_uz=description_uz,
            price=price,
            category_id=category_id,
            image_url=image_url
        )
        session.add(new_product)
        await session.commit()


async def orm_get_products_by_category_id(category_id: int, offset: int, limit: int):
    async with SessionMaker() as session:
        result = await session.execute(
            select(Product).where(Product.category_id == category_id).offset(offset).limit(limit)
        )
        return result.scalars().all()


async def orm_count_products_by_category_id(category_id: int):
    async with SessionMaker() as session:
        result = await session.execute(
            select(func.count(Product.id)).where(Product.category_id == category_id)
        )
        return result.scalar()


# region ORM PRODUCT UPDATE QUERIES

async def orm_update_product_name_ru(product_id: int, new_name_ru: str) -> bool:
    async with SessionMaker() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        if product:
            product.name_ru = new_name_ru
            await session.commit()
            return True
    return False


async def orm_update_product_name_uz(product_id: int, new_name_uz: str) -> bool:
    async with SessionMaker() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        if product:
            product.name_uz = new_name_uz
            await session.commit()
            return True
    return False


async def orm_update_product_price(product_id: int, new_price: float) -> bool:
    async with SessionMaker() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        if product:
            product.price = new_price
            await session.commit()
            return True
    return False


async def orm_update_product_description_ru(product_id: int, new_description_ru: str) -> bool:
    async with SessionMaker() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        if product:
            product.description_ru = new_description_ru
            await session.commit()
            return True
    return False


async def orm_update_product_description_uz(product_id: int, new_description_uz: str) -> bool:
    async with SessionMaker() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        if product:
            product.description_uz = new_description_uz
            await session.commit()
            return True
    return False


async def orm_update_product_photo(product_id: int, new_photo: str) -> bool:
    async with SessionMaker() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        if product:
            product.image_url = new_photo
            await session.commit()
            return True
    return False


# endregion
async def orm_delete_product_by_id(product_id: int):
    async with SessionMaker() as session:
        product = await session.get(Product, product_id)
        if product:
            await session.delete(product)  # Correctly awaiting the delete operation
            await session.commit()
            return True
        else:
            return False


async def orm_set_user(tg_id):
    async with SessionMaker() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()


async def orm_count_categories(sex: str = None):
    async with SessionMaker() as session:
        query = select(func.count(Category.id))
        if sex:
            query = query.where(Category.sex == sex)
        result = await session.execute(query)
        total_count = result.scalar()

        # Debug print
        print(f"ORM Count Query: {query}\nTotal Count: {total_count}")

        return total_count


async def orm_u_get_categories(offset: int, limit: int, sex: str = None):
    async with SessionMaker() as session:
        query = select(Category).offset(offset).limit(limit)
        if sex:
            query = query.where(Category.sex == sex)
        result = await session.execute(query)
        categories = result.scalars().all()

        # Debug print
        print(f"ORM Get Categories Query: {query}\nCategories: {categories}")

        return categories


async def get_or_create_order(user_id: int) -> Order:
    async with SessionMaker() as session:
        # Try to get the existing order with total_price == 0 for the user
        query = select(Order).where(Order.user_id == user_id, Order.total_price == 0)
        result = await session.execute(query)
        order = result.scalars().first()

        # If no such order exists, create a new one
        if order is None:
            order = Order(user_id=user_id, total_price=0)
            session.add(order)
            await session.commit()
            await session.refresh(order)

        return order


async def add_product_to_order(order: Order, product_id: int, quantity: int):
    async with SessionMaker() as session:
        product_query = select(Product).where(Product.id == product_id)
        product_result = await session.execute(product_query)
        product = product_result.scalars().one()

        total_cost = product.price * quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            total_cost=total_cost
        )
        session.add(order_item)

        order.total_price += total_cost
        await session.commit()


async def add_product_to_basket(user_id: int, product_id: int, quantity: int):
    order = await get_or_create_order(user_id)
    await add_product_to_order(order, product_id, quantity)


async def orm_create_order_item(order_id: int, product_id: int, quantity: int, total_cost: float):
    async with SessionMaker() as session:
        new_order_item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            total_cost=total_cost
        )
        session.add(new_order_item)
        await session.commit()
        await session.refresh(new_order_item)
        return new_order_item


async def orm_get_order_items_by_order_id(order_id):
    async with SessionMaker() as session:
        result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        return result.scalars().all()


async def orm_create_order(user_id: int, total_price: float) -> Order:
    async with SessionMaker() as session:
        new_order = Order(user_id=user_id, total_price=total_price)
        session.add(new_order)
        await session.commit()
        await session.refresh(new_order)
        return new_order


# Function to get order items by order ID

# Function to clear order items by order ID
async def orm_clean_order_items_by_order_id(order_id: int):
    async with SessionMaker() as session:
        await session.execute(delete(OrderItem).filter(OrderItem.order_id == order_id))
        await session.commit()


async def orm_create_user_by_tg_id(tg_id: int) -> User:
    async with SessionMaker() as session:
        new_user = User(tg_id=tg_id)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user


async def orm_get_all_user_ids():
    async with SessionMaker() as session:
        result = await session.execute(select(User.tg_id))
        return result.scalars().all()


async def orm_get_user_id_by_tg_id(tg_id: int) -> int:
    async with SessionMaker() as session:
        result = await session.execute(select(User).filter(User.tg_id == tg_id))
        user = result.scalar()
        if user:
            return user.id
        else:
            return None


async def orm_get_user_by_tg_id(tg_id: int) -> User:
    async with SessionMaker() as session:
        result = await session.execute(select(User).filter(User.tg_id == tg_id))
        user = result.scalar()
        return user


async def orm_update_user(user: User):
    try:
        async with SessionMaker() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
    except SQLAlchemyError as e:
        print(f"Error updating user: {e}")
        await session.rollback()
        raise


async def orm_save_excel_order(order_id, category_name_ru, product_name_ru, product_quantity, total_cost, customer_name,
                               username, phone_number):
    async with SessionMaker() as session:
        async with session.begin():
            new_order = ExcelOrder(
                order_id=order_id,
                category_name_ru=category_name_ru,
                product_name_ru=product_name_ru,
                product_quantity=product_quantity,
                total_cost=total_cost,
                customer_name=customer_name,
                username=username,
                phone_number=phone_number
            )
            session.add(new_order)
            await session.commit()


async def orm_get_all_excel_orders():
    async with SessionMaker() as session:
        async with session.begin():
            result = await session.execute(select(ExcelOrder))
            orders = result.scalars().all()
            orders_list = [
                {
                    "order_id": order.order_id,
                    "category_name_ru": order.category_name_ru,
                    "product_name_ru": order.product_name_ru,
                    "product_quantity": order.product_quantity,
                    "total_cost": order.total_cost,
                    "customer_name": order.customer_name,
                    "username": order.username,
                    "phone_number": order.phone_number,
                    "order_created_at": order.created_at
                }
                for order in orders
            ]
            return orders_list


async def orm_delete_all_excel_orders():
    async with SessionMaker() as session:
        async with session.begin():
            await session.execute(delete(ExcelOrder))
            await session.commit()
