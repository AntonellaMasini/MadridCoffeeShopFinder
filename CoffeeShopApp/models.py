#ORM models (my Python classes that map to database tables)
from sqlalchemy.sql.sqltypes import DateTime
from CoffeeShopApp.database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey

#Base is a class created by the declarative_base() function in database.py
#each class/model inherits Base class, allowing SQLAlchemy to understand that the class represents a db table.

class CoffeeShops(Base):
    __tablename__= 'coffee_shops'
    id= Column(Integer, primary_key = True, index=True)
    name = Column(String)
    address = Column(Float)
    has_wifi = Column(Boolean)
    has_ac = Column(Boolean)
    has_outlets = Column(Boolean)
    dog_friendly = Column(Boolean)
    #MAYBE ADD opening times


class CoffeeReviews(Base):
    __tablename__= 'coffee_reviews'
    id= Column(Integer, primary_key = True, index=True)
    user_id = Column(Integer, ForeignKey = 'users.id')
    coffee_shop_id= Column(Integer, ForeignKey = 'coffee_shops.id')
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
    hashed_password=Column(String) #encypting password that we cannot de-encrypt(no way of dev...or hacker, to see the real password)
    date_created = Column(String)


