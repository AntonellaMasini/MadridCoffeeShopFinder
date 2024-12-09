from fastapi import FastAPI

from CoffeeShopApp import models

from .database import SessionLocal, engine
from .routers import coffee_shops, reviews, users

# from routers.users import get_current_user
from .seed_data import populate_coffee_shops

app = FastAPI()  # create an instance of our application
models.Base.metadata.create_all(
    bind=engine
)


# Populate tables if empty
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        populate_coffee_shops(db)
    finally:
        db.close()


# imports all operations of router files into main
app.include_router(coffee_shops.router, prefix="/coffees-madrid", tags=["CoffeeShops"])
app.include_router(users.router, prefix="/coffees-madrid/auth", tags=["Users"])
app.include_router(reviews.router, prefix="/coffees-madrid/reviews", tags=["Reviews"])
# app.include_router(geospatial.router, prefix="/coffees-madrid", tags=["Geospatial"])
