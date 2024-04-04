from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=True)
    password = Column(String(255), nullable=True)

    orders = relationship("Order", backref="user")
    reviews = relationship("Review", backref="user")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    image = Column(String(255), nullable=True) # 이미지 파일의 경로 저장
    splat = Column(String(255), nullable=True)
    video = Column(String(255), nullable=True) # 동영상 파일의 경로 저장
    description = Column(String(255), nullable=True)
    price = Column(Integer, nullable=True)

    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", backref="items")

    orders = relationship("Order", backref="item")
    reviews = relationship("Review", backref="item")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    price = Column(Integer, nullable=True)
    count = Column(Integer, nullable=True)
    pay = Column(Boolean, default=False, nullable=True)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=True)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(String(255), nullable=True)
    star = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
