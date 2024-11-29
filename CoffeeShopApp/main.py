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


app.include_router(coffee_shops.router) #imports all operations of coffee_shops file into main
app.include_router(users.router, prefix="/coffees-madrid", tags=["Users"])
app.include_router(reviews.router, prefix="/coffees-madrid", tags=["Reviews"])
app.include_router(geospatial.router, prefix="/coffees-madrid", tags=["Geospatial"])


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
