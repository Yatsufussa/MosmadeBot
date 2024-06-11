from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.future import select

from database.engine import SessionMaker
from database.models import Category, Product, User, Order, OrderItem



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


async def orm_update_category_name(session: AsyncSession, category_id: int, new_name: str):
    async with session.begin():
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if category:
            category.name = new_name
            await session.commit()
            return True
        else:
            return False


async def orm_update_category_sex(session: AsyncSession, category_id: int, new_sex: str):
    async with session.begin():
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if category:
            category.sex = new_sex
            await session.commit()
            return True
        else:
            return False


async def orm_delete_category(session: AsyncSession, category_id: int):
    async with session.begin():
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

async def orm_get_product_by_id(product_id: int):
    async with SessionMaker() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        return product


async def orm_add_product(name: str, description: str, price: float, category_id: int, image_url: str):
    async with SessionMaker() as session:
        new_product = Product(
            p_name=name,
            p_description=description,
            p_price=price,
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
