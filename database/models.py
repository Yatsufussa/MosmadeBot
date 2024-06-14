from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, declared_attr, DeclarativeBase, relationship
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn


class Base(DeclarativeBase):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    p_name = Column(String(255), nullable=False)
    p_description = Column(Text)
    p_price = Column(DECIMAL(10, 2))
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String(255))


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sex = Column(String(255), nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_price = Column(DECIMAL(10, 2))
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User")



class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    total_cost = Column(DECIMAL(10, 2))


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    phone_number = Column(String(15), nullable=True)