#Handles all coffee shop-related endpoints
from fastapi import APIRouter, HTTPException, status, Response
from typing import List
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.orm import Session


from CoffeeShopApp.models import CoffeeShopRequest, CoffeeShops
from CoffeeShopApp.main import db_dependency, user_dependency

router = APIRouter(
    prefix='/coffee-shops',
    #tags=['coffee_shops']
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
        return self.db.query(CoffeeShops).filter(CoffeeShops.name==self.name)

    def create_coffee_shop(self):
        coffee = CoffeeShops(**CoffeeShopRequest.dict())

    #     #todo_request.dict()   --> converts todo_request pydantic object (JSON format) into python dictionary
    #     #**todo_request.dict() --> unpacks dictionary into keyword arguments for the Todos model, mapping fields (title) to corresponding columns in the Todos SQLAlchemy model.
    #     #db.add(todo_model)    --> adds todo_model object (instance of Todo class), to table (still not commited tho, local)
    #     #db.commit()           --> commits changes to database

@router.get("/coffee-shops/", response_model=List[CoffeeShop])
def list_coffee_shops():
    # Logic to list all coffee shops
    pass

# Parameter1: starts database session, passed into function as db variable
# Parameter2: coffee_shop_request represents the JSON input data sent by the client.
# FastAPI ensures this data matches the Pydantic schema `CoffeeShopRequest`. If validation fails, FastAPI returns an error BEFORE calling the function.
@router.post("/coffee-shops/")
def create_coffee_shop(user:user_dependency, db: db_dependency, coffee_shop_request: CoffeeShopRequest):
    # create instance of class CoffeeShops
    # user_dependency returns a dict: {"username": username, "id": user_id} . We can access this with normal dict call but it is always better to use get method
    coffee_shop_model = CoffeeShops(**coffee_shop_request.dict(), user_id= user.get(id))     
    db.add(coffee_shop_model)       
    db.commit(coffee_shop_model)    



#coffee_shop_request.dict()   --> converts coffee_shop_request pydantic object (JSON format) into python dictionary
#**coffee_shop_request.dict() --> unpacks dictionary into keyword arguments for the CoffeShops model, mapping fields (title) to corresponding columns in the CoffeShops SQLAlchemy model (table).
#adds coffee_shop_model object (instance of CoffeeShops class), to table (still not commited tho, local)
#add changes to database
