#create URL string that will connect fastAPI application to my database
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path


# Define the path to the CoffeeShopProject directory and the desired database location
db_path = Path(__file__).parent.parent / 'CoffeeShopApp' / 'coffee_shops.db'
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"    #create a location of this database on fastAPI application


#establish database connection in SQLAlchemy to enable communication btw the python app and the database
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind= engine) 

Base = declarative_base() #Base is a class created by the declarative_base() function 
                          #each class/model inherits Base class, allowing SQLAlchemy to understand that the class represents a db table

#/Users/antonellamasini/Desktop/CODE/Coffeeshopproject


