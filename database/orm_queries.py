from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, delete, update
from sqlalchemy.orm import joinedload

from database.engine import SessionMaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Category, Product, User, Order, OrderItem, ExcelOrder, PromoCode, BonusProduct, UserBonus
import uuid
from sqlalchemy.future import select


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
                          category_id: int, video_url: str):
    async with SessionMaker() as session:
        product = Product(
            name_ru=name_ru,
            name_uz=name_uz,
            description_ru=description_ru,
            description_uz=description_uz,
            price=price,
            category_id=category_id,
            video_url=video_url  # Save the video URL
        )
        session.add(product)
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
        new_user = User(
            tg_id=tg_id,
            referral_code=str(uuid.uuid4())[:8]  # Generate a unique referral code
        )
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


async def orm_save_excel_order(
        order_id,
        category_name_ru,
        product_name_ru,
        product_quantity,
        initial_cost,
        promo_code_name,
        promo_discount_percentage,
        total_cost,
        customer_name,
        username,
        phone_number,
        bonus_product_name=None,  # New parameter for bonus product name
        location_name=None  # New parameter for location name
):
    async with SessionMaker() as session:
        new_excel_order = ExcelOrder(
            order_id=order_id,
            category_name_ru=category_name_ru,
            product_name_ru=product_name_ru,
            product_quantity=product_quantity,
            initial_cost=initial_cost,
            promo_code_name=promo_code_name,
            promo_discount_percentage=promo_discount_percentage,
            total_cost=total_cost,
            customer_name=customer_name,
            username=username,
            phone_number=phone_number,
            bonus_product_name=bonus_product_name,  # Save bonus product name
            location_name=location_name  # Save location name
        )
        session.add(new_excel_order)
        await session.commit()


async def orm_get_all_excel_orders():
    async with SessionMaker() as session:
        async with session.begin():
            result = await session.execute(
                select(
                    ExcelOrder.order_id,
                    ExcelOrder.category_name_ru,
                    ExcelOrder.product_name_ru,
                    ExcelOrder.product_quantity,
                    ExcelOrder.initial_cost,
                    ExcelOrder.promo_code_name,
                    ExcelOrder.promo_discount_percentage,
                    ExcelOrder.total_cost,
                    ExcelOrder.customer_name,
                    ExcelOrder.username,
                    ExcelOrder.phone_number,
                    ExcelOrder.status,
                    ExcelOrder.created_at,
                    ExcelOrder.location_name,  # ✅ Added location name
                    ExcelOrder.bonus_product_name,  # ✅ Added bonus product name
                    User.latitude,
                    User.longitude
                ).outerjoin(User, ExcelOrder.phone_number == User.phone_number)  # ✅ Changed to outer join
            )

            orders = result.fetchall()

            orders_list = [
                {
                    "order_id": order.order_id,
                    "category_name_ru": order.category_name_ru,
                    "product_name_ru": order.product_name_ru,
                    "product_quantity": order.product_quantity,
                    "initial_cost": order.initial_cost or 0.0,  # ✅ Handles None
                    "promo_code_name": order.promo_code_name or "N/A",  # ✅ Handles None
                    "promo_discount_percentage": order.promo_discount_percentage or 0.0,  # ✅ Handles None
                    "total_cost": order.total_cost,
                    "customer_name": order.customer_name,
                    "username": order.username or "N/A",
                    "phone_number": order.phone_number,
                    "status": order.status or "pending",
                    "order_created_at": order.created_at,
                    "location_name": order.location_name or "N/A",  # ✅ Added location name
                    "bonus_product_name": order.bonus_product_name or "N/A",  # ✅ Added bonus product name
                    "latitude": order.latitude or "N/A",
                    "longitude": order.longitude or "N/A",
                }
                for order in orders
            ]
            return orders_list


async def orm_delete_all_excel_orders():
    async with SessionMaker() as session:
        async with session.begin():
            await session.execute(delete(ExcelOrder))
            await session.commit()


async def orm_get_user_by_tg_id(tg_id: int) -> User:
    async with SessionMaker() as session:
        result = await session.execute(select(User).filter(User.tg_id == tg_id))
        user = result.scalar()
        return user


# Query to fetch user by referral code
async def orm_get_user_by_referral_code(referral_code: str) -> User:
    async with SessionMaker() as session:
        result = await session.execute(select(User).filter(User.referral_code == referral_code))
        user = result.scalar()
        return user


async def is_user_location_missing(tg_id: int) -> bool:
    user = await orm_get_user_by_tg_id(tg_id)
    if user:
        # Check if either longitude or latitude is None
        if user.longitude is None or user.latitude is None:
            return True
        return False
    return None  # User not found


async def orm_update_user_location(tg_id: int, latitude: float, longitude: float):
    user = await orm_get_user_by_tg_id(tg_id)
    if user:
        user.latitude = latitude
        user.longitude = longitude
        async with SessionMaker() as session:
            try:
                async with session.begin():
                    session.add(user)
                    await session.commit()
                    return True  # Location successfully updated
            except Exception as e:
                print(f"Error updating user's location: {e}")
                await session.rollback()
                return False
    return False  # User not found


async def save_user_location(tg_id: int, latitude: float, longitude: float):
    if await is_user_location_missing(tg_id):
        updated = await orm_update_user_location(tg_id, latitude, longitude)
        if updated:
            return "Location updated successfully!"
        else:
            return "Failed to update location."
    else:
        return "User already has location information."


async def orm_save_user(user: User):
    async with SessionMaker() as session:
        async with session.begin():
            session.add(user)


async def orm_get_referred_users_count(user_id: int):
    # Query to count the number of users who were referred by the current user
    async with SessionMaker() as session:
        # Perform the query to find all users referred by the current user
        result = await session.execute(select(User).filter(User.referred_by == user_id))

        # Get the count of referred users
        referred_users_count = len(result.scalars().all())

    return referred_users_count


async def orm_delete_order_by_id(order_id: int):
    async with SessionMaker() as session:
        order = await session.get(Order, order_id)
        if order:
            await session.delete(order)
            await session.commit()


async def update_excel_order_status_to_cancelled(order_id: int):
    async with SessionMaker() as session:
        await session.execute(
            update(ExcelOrder)
            .where(ExcelOrder.order_id == order_id)
            .values(status="cancelled")
        )
        await session.commit()


async def update_order_status_to_finished(order_id: int):
    async with SessionMaker() as session:
        await session.execute(
            update(ExcelOrder)
            .where(ExcelOrder.order_id == order_id)
            .values(status="finished")
        )
        await session.commit()


async def orm_get_user_location(user_id: int):
    async with SessionMaker() as session:
        # Query the User table to get latitude and longitude for the given user
        result = await session.execute(
            select(User.latitude, User.longitude).filter(User.id == user_id)
        )
        # Fetch the result as a tuple (latitude, longitude)
        location = result.fetchone()  # Use fetchone() instead of scalars().first()

        if location:
            latitude = location[0]  # Latitude (Decimal)
            longitude = location[1]  # Longitude (Decimal)
            return latitude, longitude
        return None


async def orm_update_user_phone(user_id: int, new_phone: str):
    async with SessionMaker() as session:
        user = await session.get(User, user_id)
        if user:
            user.phone_number = new_phone
            await session.commit()


async def orm_update_user_location(user_id: int, latitude: float, longitude: float):
    async with SessionMaker() as session:
        user = await session.get(User, user_id)
        if user:
            user.latitude = latitude
            user.longitude = longitude
            await session.commit()


async def orm_get_order_by_id(order_id):
    async with SessionMaker() as session:
        return await session.get(
            Order, order_id, options=[joinedload(Order.user)]
        )


async def orm_promocode_exists(promo_code: str) -> bool:
    async with SessionMaker() as session:
        result = await session.execute(
            select(PromoCode).where(PromoCode.code == promo_code)
        )
        return result.scalar() is not None


async def orm_product_exists(product_id: int) -> bool:
    async with SessionMaker() as session:
        result = await session.execute(
            select(Product).where(Product.id == product_id))
        return result.scalar() is not None


async def orm_add_promocode(promo_code: str, product_id: int | None, discount: float, is_global: bool = False,
                            expiry_date: datetime | None = None):
    async with SessionMaker() as session:
        new_promocode = PromoCode(
            code=promo_code,
            product_id=product_id,
            discount=discount,
            is_global=is_global,
            expiry_date=expiry_date
        )
        session.add(new_promocode)
        await session.commit()


async def orm_get_all_promocodes():
    async with SessionMaker() as session:
        result = await session.execute(select(PromoCode))
        return result.scalars().all()


async def orm_delete_promocode(promo_code_id: int):
    async with SessionMaker() as session:
        async with session.begin():
            # First, update users who are using this promo code
            await session.execute(
                update(User).where(User.active_promo_code_id == promo_code_id).values(active_promo_code_id=None)
            )

            # Fetch the promo code
            result = await session.execute(
                select(PromoCode).where(PromoCode.id == promo_code_id)
            )
            promo_code = result.scalar()

            if promo_code:
                await session.delete(promo_code)
                await session.commit()
                return True
            return False


async def orm_get_promo_code_by_text(promo_code: str):
    async with SessionMaker() as session:
        result = await session.execute(
            select(PromoCode).where(PromoCode.code == promo_code)
        )
        return result.scalar_one_or_none()


async def orm_activate_promo_code_for_user(user_id: int, promo_code_id: int):
    async with SessionMaker() as session:
        # Fetch the user by their Telegram ID
        user = await session.scalar(
            select(User).where(User.tg_id == user_id)
        )

        if user:
            # Update the user's active promo code
            user.active_promo_code_id = promo_code_id
            await session.commit()
            return True
        return False


async def orm_get_promo_code_by_id(promo_code_id: int):
    async with SessionMaker() as session:
        result = await session.execute(
            select(PromoCode).where(PromoCode.id == promo_code_id)
        )
        return result.scalar_one_or_none()


async def orm_get_orders_by_user_id(user_id: int):
    async with SessionMaker() as session:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(joinedload(Order.user))  # Load related user data
            .order_by(Order.created_at.desc())  # Order by most recent first
        )
        return result.scalars().all()


async def orm_get_promo_discount(promo_code: str) -> Decimal:
    async with SessionMaker() as session:
        result = await session.execute(
            select(PromoCode.discount)
            .where(PromoCode.code == promo_code)
        )
        discount = result.scalar()
        return Decimal(discount) if discount else Decimal(0)


async def orm_get_excel_orders_by_user_phone(phone_number: str):
    async with SessionMaker() as session:
        result = await session.execute(
            select(ExcelOrder)
            .where(ExcelOrder.phone_number == phone_number, ExcelOrder.status == "pending")
        )
        return result.scalars().all()


async def orm_get_referred_users_with_orders_count(user_id: int):
    # Query to count the number of referred users who have at least one order
    async with SessionMaker() as session:
        result = await session.execute(
            select(User).join(Order, Order.user_id == User.id)  # Join User with Order
            .filter(User.referred_by == user_id)  # Filter by the current user
            .distinct()  # Ensure unique users
        )
        referred_users_with_orders_count = len(
            result.scalars().all())  # Count the number of referred users who have orders
    return referred_users_with_orders_count


async def orm_check_user_bonus(user_id: int, bonus_product_id: int):
    """
    Проверяет, получал ли пользователь этот бонус.
    """
    async with SessionMaker() as session:
        result = await session.execute(
            select(UserBonus).where(
                UserBonus.user_id == user_id,
                UserBonus.bonus_product_id == bonus_product_id,
                UserBonus.is_used == False
            )
        )
        return result.scalars().first()


async def orm_add_bonus_to_order(order_id: int, bonus_products: list):
    async with SessionMaker() as session:
        for bonus_product in bonus_products:
            order_item = OrderItem(
                order_id=order_id,
                product_id=bonus_product.id,  # Assuming bonus_products contains id of product
                quantity=1,  # Bonus products are added in quantity 1
                total_cost=0  # Bonus product is free
            )
            session.add(order_item)
        await session.commit()


async def orm_add_bonus_product(name_ru: str, name_uz: str, description_ru: str, description_uz: str, image_url: str,
                                required_referrals: int):
    async with SessionMaker() as session:
        new_bonus_product = BonusProduct(
            name_ru=name_ru,
            name_uz=name_uz,
            description_ru=description_ru,
            description_uz=description_uz,
            image_url=image_url,
            required_referrals=required_referrals
        )
        session.add(new_bonus_product)
        await session.commit()


async def orm_delete_bonus_product(bonus_id: int) -> bool:
    """
    Deletes a bonus product from the database by its ID.

    :param bonus_id: ID of the bonus product to delete.
    :return: True if the bonus product was deleted, False if it was not found.
    """
    async with SessionMaker() as session:
        result = await session.execute(
            delete(BonusProduct)
            .where(BonusProduct.id == bonus_id)
        )
        await session.commit()
        return result.rowcount > 0  # Returns True if a row was deleted


async def orm_get_referred_users_with_orders(user_id: int):
    async with SessionMaker() as session:
        result = await session.execute(
            select(User.id)
            .join(Order, Order.user_id == User.id)
            .filter(User.referred_by == user_id)
            .distinct()
        )
        return len(result.scalars().all())


async def orm_get_bonus_products_by_referral_count(referral_count: int):
    async with SessionMaker() as session:
        result = await session.execute(
            select(BonusProduct)
            .where(BonusProduct.required_referrals <= referral_count, BonusProduct.active == True)
            .order_by(BonusProduct.required_referrals.desc())
        )
        return result.scalars().first()


async def orm_add_bonus_to_user(user_id: int, bonus_product_id: int):
    async with SessionMaker() as session:
        existing_bonus = await session.execute(
            select(UserBonus).filter(UserBonus.user_id == user_id, UserBonus.bonus_product_id == bonus_product_id)
        )
        if not existing_bonus.scalars().first():
            new_bonus = UserBonus(user_id=user_id, bonus_product_id=bonus_product_id)
            session.add(new_bonus)
            await session.commit()
            return {
                "success": True,
                "message": {
                    "ru": f"Поздравляем! Вы получили бонус!",
                    "uz": f"Tabriklaymiz! Siz bonus oldingiz!"
                }
            }
    return {"success": False, "message": {"ru": "Бонус не найден", "uz": "Bonus topilmadi"}}


async def orm_get_user_bonus_count(user_id: int):
    """Получить количество бонусов, выданных пользователю."""
    async with SessionMaker() as session:
        result = await session.execute(
            select(func.count(UserBonus.id)).where(
                UserBonus.user_id == user_id
            )
        )
        return result.scalar()  # Количество выданных бонусов


async def orm_update_product_video(product_id: int, new_video: str):
    async with SessionMaker() as session:
        result = await session.execute(
            select(Product).filter(Product.id == product_id)
        )
        product = result.scalars().first()
        if product:
            product.video_id = new_video
            await session.commit()
            return True
    return False


async def orm_update_order_comment(order_id: int, comment: str):
    async with SessionMaker() as session:
        # Находим все элементы заказа, так как комментарий общий
        await session.execute(
            update(OrderItem)
            .where(OrderItem.order_id == order_id)
            .values(order_comment=comment)
        )
        await session.commit()





