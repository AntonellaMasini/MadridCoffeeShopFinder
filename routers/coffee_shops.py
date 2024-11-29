#Handles all coffee shop-related endpoints
from fastapi import APIRouter, HTTPException, status, Response
from typing import List
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.orm import Session


from CoffeeShopApp.models import CoffeeShopCreate, CoffeeShops
from CoffeeShopApp.main import db_dependency

router = APIRouter(
    prefix='/coffees-madrid',
    tags=['coffee_shops']
)


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
        
        pass



@router.get("/coffee-shops/", response_model=List[CoffeeShop])
def list_coffee_shops():
    # Logic to list all coffee shops
    pass

@router.post("/coffee-shops/", response_model=CoffeeShop)
def create_coffee_shop(coffee_shop: CoffeeShopCreate):
    # Logic to add a coffee shop
    pass

# # Parameter1: starts database session, passed into function as db variable
# # Parameter2: todo_request represents the JSON input data sent by the client.
# # FastAPI ensures this data matches the Pydantic schema `TodoRequest`.
# # If validation fails, FastAPI returns an error before calling the function.
# @app.post("todo/)")
# def create_todo(db: db_dependency, todo_request: TodoRequest):
#     todo_model=Todos(**todo_request.dict()) 
#     db.add(todo_model)
#     db.commit()
#     #todo_request.dict()   --> converts todo_request pydantic object (JSON format) into python dictionary
#     #**todo_request.dict() --> unpacks dictionary into keyword arguments for the Todos model, mapping fields (title) to corresponding columns in the Todos SQLAlchemy model.
#     #db.add(todo_model)    --> adds todo_model object (instance of Todo class), to table (still not commited tho, local)
#     #db.commit()           --> commits changes to database
