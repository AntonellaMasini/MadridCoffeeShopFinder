from fastapi import FastAPI, Depends
from routers import coffee_shops, users, reviews, geospatial
from .database import engine, SessionLocal
from CoffeeShopApp import models
from typing import Annotated
from sqlalchemy.orm import Session
from routers.users import get_current_user

app = FastAPI()     #create an instance of our application
models.Base.metadata.create_all(bind=engine) #only will be run if db has not been created. If you want to enhance db (aka create a new column)
                                             #you will need to delete the db file and run this script again.
                                             #OR use Alembic!

#function to open a connection to database (which is a server that stores data). Kinda like a phone call.
# close it after it is returned to client. Why? To avoid blocks, deadlocks, occupying all the connections, memory.
def get_db():
    db= SessionLocal() #opens connection, SessionLocal is a factory function provided by SQLAlchemy that creates session objects. A session is a temporary workspace
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)] #dependancy injection to grab and run first db using FastApi, inside FastApi's framework. Avoids repeating  "db: Session = Depends(get_db)" in every fastapi endpoint func parameter
user_dependency = Annotated[dict, Depends(get_current_user)]


#imports all operations of router files into main
app.include_router(coffee_shops.router, prefix="/coffees-madrid", tags=["CoffeeShops"]) 
app.include_router(users.router, prefix="/coffees-madrid", tags=["Users"])
app.include_router(reviews.router, prefix="/coffees-madrid", tags=["Reviews"])
app.include_router(geospatial.router, prefix="/coffees-madrid", tags=["Geospatial"])
