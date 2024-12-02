#Handles all coffee shop-related endpoints
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.param_functions import Depends
#from CoffeeShopApp.dependencies import db_dependency
from typing import Annotated, List
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.orm import Session
from datetime import datetime
from CoffeeShopApp.models import CoffeeShops
from CoffeeShopApp.schemas import CoffeeShopRequest
from CoffeeShopApp.database import SessionLocal
from .users import get_current_user


user_dependency = Annotated[dict, Depends(get_current_user)]

# function to open a connection to database (which is a server that stores data). Kinda like a phone call.
# close it after it is returned to client. Why? To avoid blocks, deadlocks, occupying all the connections, memory.
def get_db():
    db= SessionLocal() #opens connection, SessionLocal is a factory function provided by SQLAlchemy that creates session objects. A session is a temporary workspace
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)] #dependancy injection to grab and run first db using FastApi, inside FastApi's framework. Avoids repeating  "db: Session = Depends(get_db)" in every fastapi endpoint func parameter



router = APIRouter()

#OOP structure
class CoffeeShop():
    def __init__(self, name: str, address: str, wifi: bool, ac: bool, outlets: bool, dog_friendly: bool, db: Session):
        self.name = name
        self.address = address
        self.wifi = wifi
        self.ac = ac
        self.outlets = outlets
        self.dog_friendly = dog_friendly
        self.db = db

    def get_list_coffee_shops(self):
        #SELECT * FROM coffee_shops_table
        return self.db.query(CoffeeShops).all() #returns a list of objects

    def get_coffe_shop_info(self):
        #SELECT * FROM coffee_shops_table WHERE coffee_shop_name = starbucks
        return self.db.query(CoffeeShops).filter(CoffeeShops.name==self.name)

    def create_coffee_shop(self):
        coffee = CoffeeShops(**CoffeeShopRequest.dict())
    #     #todo_request.dict()   --> converts todo_request pydantic object (JSON format) into python dictionary
    #     #**todo_request.dict() --> unpacks dictionary into keyword arguments for the Todos model, mapping fields (title) to corresponding columns in the Todos SQLAlchemy model.
    #     #db.add(todo_model)    --> adds todo_model object (instance of Todo class), to table (still not commited tho, local)
    #     #db.commit()           --> commits changes to database



#API ENDPOINTS -----------------------------------------------------------------------------------------------------------------------

@router.get("/coffee-shops/")
def list_coffee_shops(db:db_dependency):
    #SELECT * FROM coffee_shops_table
    return db.query(CoffeeShops).all() #returns a list of objects

# Parameter1: starts database session, passed into function as db variable
# Parameter2: coffee_shop_request represents the JSON input data sent by the client.
# FastAPI ensures this data matches the Pydantic schema `CoffeeShopRequest`. If validation fails, FastAPI returns an error BEFORE calling the function.
@router.post("/coffee-shops/")
def create_coffee_shop(user:user_dependency, db: db_dependency, coffee_shop_request: CoffeeShopRequest):
    # create instance of class CoffeeShops
    # user_dependency returns a dict: {"username": username, "id": user_id} . We can access this with normal dict call but it is always better to use get method
    shop = CoffeeShops(**coffee_shop_request.dict(), user_id= user.get('id'))     
    db.add(shop)       
    db.commit()  
    db.refresh(shop)  
    return shop


#coffee_shop_request.dict()   --> converts coffee_shop_request pydantic object (JSON format) into python dictionary
#**coffee_shop_request.dict() --> unpacks dictionary into keyword arguments for the CoffeShops model, mapping fields (title) to corresponding columns in the CoffeShops SQLAlchemy model (table).
#adds coffee_shop_model object (instance of CoffeeShops class), to table (still not commited tho, local)
#add changes to database
