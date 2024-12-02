#ORM models (my Python classes that map to database tables)
from sqlalchemy.sql.sqltypes import DateTime, Enum
from enum import Enum as PyEnum
from CoffeeShopApp.database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum

#Base is a class created by the declarative_base() function in database.py
#each class/model inherits Base class, allowing SQLAlchemy to understand that the class represents a db table.

class LevelsEnum(PyEnum):
    low = "low"
    medium = "medium"
    high = "high"

class CoffeeShops(Base):
    __tablename__= 'coffee_shops'
    id= Column(Integer, primary_key = True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    wifi_quality = Column(Enum(LevelsEnum))
    has_ac = Column(Boolean)
    laptop_friendly_seats= Column(Enum(LevelsEnum))
    dog_friendly = Column(Boolean)
    noise_level = Column(String)
    outlet_availability = Column(Enum(LevelsEnum))
    user_id = Column(Integer, ForeignKey('users.id'))

class CoffeeReviews(Base):
    __tablename__= 'coffee_reviews'
    id= Column(Integer, primary_key = True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    coffee_shop_id= Column(Integer, ForeignKey('coffee_shops.id'))
    rating = Column(Integer)
    comment= Column(String)
    timestamp = Column(DateTime)


class Users(Base):
    __tablename__= 'users'
    id= Column(Integer, primary_key = True, index=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    first_name=Column(String)
    last_name=Column(String)
    hashed_password=Column(String) #encrypting password that we cannot de-encrypt(no way of dev...or hacker, to see the real password)
    date_created = Column(String)


