from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import declared_attr, relationship
from sqlalchemy.orm import DeclarativeBase


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
    tg_id = Column(Integer, unique=True, nullable=False)
    phone_number = Column(String(15), nullable=True)
    language = Column(String(2), nullable=False, default='ru')  # Storing user's preferred language

    orders = relationship("Order", back_populates="user")


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    sex = Column(String(255), nullable=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    price = Column(DECIMAL(10, 2))
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String(255), nullable=False)

    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    description_ru = Column(Text)
    description_uz = Column(Text)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


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
    total_cost = Column(Float, nullable=False)
    customer_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)