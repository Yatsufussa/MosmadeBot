import random
import string
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DECIMAL, TIMESTAMP, Text, BigInteger, Numeric, \
    Boolean, DateTime
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

Base = declarative_base()


def generate_referral_code():
    """Generate a unique referral code."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

class Base(DeclarativeBase):
    metatada = None

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    phone_number = Column(String(15), nullable=True)
    language = Column(String(2), nullable=False, default='ru')  # Storing user's preferred language
    longitude = Column(Numeric(10, 6), nullable=True) # Longitude of the user's location
    latitude = Column(Numeric(10, 6), nullable=True)  # Latitude of the user's location

    referral_code = Column(String(8), unique=True, default=generate_referral_code)  # Unique referral code for the user
    referred_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Foreign key to the user who referred them

    # Relationship to track who referred the user
    referrer = relationship("User", backref="referred_users", remote_side=[id])

    orders = relationship("Order", back_populates="user")

    active_promo_code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=True)  # New column
    active_promo_code = relationship("PromoCode", foreign_keys=[active_promo_code_id])

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    price = Column(DECIMAL(10, 2))
    category_id = Column(Integer, ForeignKey("categories.id"))
    video_url = Column(String(255), nullable=False)

    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    description_ru = Column(Text)
    description_uz = Column(Text)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    promo_codes = relationship("PromoCode", back_populates="product")  # New relationship

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_price = Column(DECIMAL(10, 2))

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    total_cost = Column(DECIMAL(10, 2))

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class ExcelOrder(Base):
    __tablename__ = 'excel_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False)
    category_name_ru = Column(String(255), nullable=False)
    product_name_ru = Column(String(255), nullable=False)
    product_quantity = Column(Integer, nullable=False)
    initial_cost = Column(Float, nullable=False)  # New column for the initial cost
    promo_code_name = Column(String(50), nullable=True)  # New column for promo code name
    promo_discount_percentage = Column(Float, nullable=True)  # New column for discount percentage
    total_cost = Column(Float, nullable=False)  # The final cost after applying the discount
    customer_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # Default status set to 'pending'


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)  # Promo code text
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # Optional product ID
    discount = Column(Float, nullable=False)  # Discount percentage
    is_global = Column(Boolean, default=False)  # Whether the promo code applies to all products
    expiry_date = Column(DateTime, nullable=True)  # Expiry date (optional)

    product = relationship("Product", back_populates="promo_codes")

class BonusProduct(Base):
    __tablename__ = 'bonus_products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_ru = Column(String(255), nullable=False)  # Название бонуса на русском
    name_uz = Column(String(255), nullable=False)  # Название бонуса на узбекском
    description_ru = Column(Text, nullable=True)  # Описание на русском
    description_uz = Column(Text, nullable=True)  # Описание на узбекском
    image_url = Column(String(255), nullable=True)  # Фото бонуса (если нужно)
    active = Column(Boolean, default=True)  # Активен ли бонус
    required_referrals = Column(Integer, default=0)  # Количество рефералов, необходимых для получения бонуса


class UserBonus(Base):
    __tablename__ = 'user_bonuses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    bonus_product_id = Column(Integer, ForeignKey('bonus_products.id'), nullable=False)
    is_used = Column(Boolean, default=False)  # Использовал ли пользователь бонус
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="bonuses")
    bonus_product = relationship("BonusProduct")
