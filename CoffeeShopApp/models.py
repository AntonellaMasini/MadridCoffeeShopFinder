# ORM models (my Python classes that map to database tables)
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import CheckConstraint

from CoffeeShopApp.database import Base

# Base is a class created by the declarative_base() function in database.py
# each class/model inherits Base class, allowing SQLAlchemy to understand that the class represents a db table.


class CoffeeShops(Base):
    __tablename__ = "coffee_shops"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=False)
    wifi_quality = Column(Integer, nullable=False)
    has_ac = Column(Boolean, nullable=False)
    laptop_friendly_seats = Column(Integer, nullable=False)
    dog_friendly = Column(Boolean, nullable=False)
    noise_level = Column(Integer, nullable=False)
    outlet_availability = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Add a Check Constraint to ensure values are 1, 2, or 3
    __table_args__ = (
        CheckConstraint("wifi_quality IN (1, 2, 3)", name="wifi_quality_check"),
        CheckConstraint(
            "laptop_friendly_seats IN (1, 2, 3)", name="laptop_seats_check"
        ),
        CheckConstraint("noise_level IN (1, 2, 3)", name="noise_level_check"),
        CheckConstraint(
            "outlet_availability IN (1, 2, 3)", name="outlet_availability_check"
        ),
    )

    # Define the relationships with cascade delete:
    # 1 parameter: target model class,    #2 parameter: cascading behavior
    coffee_reviews = relationship(
        "CoffeeReviews", backref="coffee_shop", cascade="all, delete, delete-orphan"
    )
    aggregated_ratings = relationship(
        "AggregatedRatings", backref="coffee_shop", cascade="all, delete, delete-orphan"
    )
    # Target model class (first argument)


class CoffeeReviews(Base):
    __tablename__ = "coffee_reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    coffee_shop_id = Column(Integer, ForeignKey("coffee_shops.id", ondelete="CASCADE"))
    rating = Column(Integer, nullable=False)
    comment = Column(String)
    timestamp = Column(String, nullable=False)  # DateTime?


class AggregatedRatings(Base):
    __tablename__ = "aggregated_ratings"
    coffee_shop_id = Column(
        Integer,
        ForeignKey("coffee_shops.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    aggregated_rating = Column(Float, nullable=False)
    total_reviews = Column(Integer, nullable=False)


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(
        String, nullable=False
    )  # encrypting password that we cannot de-encrypt(no way of dev...or hacker, to see the real password)
    date_created = Column(String, nullable=False)
