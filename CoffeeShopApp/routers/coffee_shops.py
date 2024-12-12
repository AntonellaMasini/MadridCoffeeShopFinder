from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, Response

from CoffeeShopApp.database import SessionLocal
from CoffeeShopApp.models import AggregatedRatings, CoffeeShops
from CoffeeShopApp.schemas import CoffeeShopFilterRequest, CoffeeShopRequest

from .users import get_current_user

user_dependency = Annotated[dict, Depends(get_current_user)]


# function to open a connection to database (which is a server that stores data). Kinda like a phone call.
# close it after it is returned to client. Why? To avoid blocks, deadlocks, occupying all the connections, memory.
def get_db():
    db = (
        SessionLocal()
    )  # opens connection, SessionLocal is a factory function provided by SQLAlchemy that creates session objects. A session is a temporary workspace
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[
    Session, Depends(get_db)
]  # dependancy injection to grab and run first db using FastApi, inside FastApi's framework. Avoids repeating  "db: Session = Depends(get_db)" in every fastapi endpoint func parameter

router = APIRouter()


# API ENDPOINTS -----------------------------------------------------------------------------------------------------------------------


# #filter by parameter, injecting dependency gets rid of post body, since default is = Body()
@router.get("/coffee-shops/")
def get_coffee_shops_filter(
    db: db_dependency, coffee_shop_filter_request: CoffeeShopFilterRequest = Depends()
):
    # query coffee shop objects that fulfill given requirements/ filters
    # First join tables and then do the filtering

    # Start the query for CoffeeShops
    query = db.query(
        CoffeeShops.id,
        CoffeeShops.name,
        CoffeeShops.address,
        CoffeeShops.wifi_quality,
        CoffeeShops.has_ac,
        CoffeeShops.laptop_friendly_seats,
        CoffeeShops.dog_friendly,
        CoffeeShops.noise_level,
        CoffeeShops.outlet_availability,
        AggregatedRatings.aggregated_rating,
        AggregatedRatings.total_reviews,
    ).outerjoin(AggregatedRatings, CoffeeShops.id == AggregatedRatings.coffee_shop_id)

    # filter
    if coffee_shop_filter_request.wifi_quality is not None:
        query = query.filter(
            CoffeeShops.wifi_quality >= coffee_shop_filter_request.wifi_quality
        )

    if coffee_shop_filter_request.has_ac is not None:
        query = query.filter(CoffeeShops.has_ac == coffee_shop_filter_request.has_ac)

    if coffee_shop_filter_request.laptop_friendly_seats is not None:
        query = query.filter(
            CoffeeShops.laptop_friendly_seats
            >= coffee_shop_filter_request.laptop_friendly_seats
        )

    if coffee_shop_filter_request.dog_friendly is not None:
        query = query.filter(
            CoffeeShops.dog_friendly == coffee_shop_filter_request.dog_friendly
        )

    if coffee_shop_filter_request.noise_level is not None:
        query = query.filter(
            CoffeeShops.noise_level <= coffee_shop_filter_request.noise_level
        )

    if coffee_shop_filter_request.outlet_availability is not None:
        query = query.filter(
            CoffeeShops.outlet_availability
            >= coffee_shop_filter_request.outlet_availability
        )

    if coffee_shop_filter_request.min_combined_rating is not None:
        query = query.filter(
            AggregatedRatings.aggregated_rating
            >= coffee_shop_filter_request.min_combined_rating
        )

    # same thing as saying in SQL:
    # SELECT col1, col2, ... FOR coffee_shops_table FULL OUTER JOIN aggregated_reviews_table
    # ON coffee_shops_table.id = aggregated_reviews_table.coffee_shop_id
    # WHERE (coffee_shops.wifi_quality = :wifi_quality OR :wifi_quality IS NULL) AND
    #  (coffee_shops.has_ac = :has_ac OR :has_ac IS NULL) AND...........

    result = (
        query.all()
    )  # list of tuples, each tuple corresponds to the selected columns [(col1,col2,col3...), (col1,col2,col3...), ...]

    if not result:
        # raise HTTPException(
        #     status_code=status.HTTP_204_NO_CONTENT,
        #     detail="No coffeeshops match filter",
        # )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # Format the result to return a list of dictionaries
    coffee_shops = []
    for shop in result:
        coffee_shop = {
            "id": shop.id,
            "name": shop.name,
            "address": shop.address,
            "wifi_quality": shop.wifi_quality,
            "has_ac": shop.has_ac,
            "laptop_friendly_seats": shop.laptop_friendly_seats,
            "dog_friendly": shop.dog_friendly,
            "noise_level": shop.noise_level,
            "outlet_availability": shop.outlet_availability,
            "aggregated_rating": (
                shop.aggregated_rating
                if shop.aggregated_rating is not None
                else "No ratings yet"
            ),
            "total_reviews": (
                shop.total_reviews if shop.total_reviews is not None else 0
            ),
        }
        coffee_shops.append(coffee_shop)
    return {"coffee_shops": coffee_shops}


@router.get("/coffee-shops/all")
def get_all_coffee_shops(db: db_dependency):
    # SELECT * FROM coffee_shops_table
    return db.query(CoffeeShops).all()  # returns a list of objects


# Parameter1: starts database session, passed into function as db variable
# Parameter2: coffee_shop_request represents the JSON input data sent by the client.
# FastAPI ensures this data matches the Pydantic schema `CoffeeShopRequest`. If validation fails, FastAPI returns an error BEFORE calling the function.
@router.post("/coffee-shops/", status_code=status.HTTP_201_CREATED)
def create_coffee_shop(
    user: user_dependency, db: db_dependency, coffee_shop_request: CoffeeShopRequest
):
    # create instance of class CoffeeShops
    # user_dependency returns a dict: {"username": username, "id": user_id} . We can access this with normal dict call but it is always better to use get method

    shop = CoffeeShops(
        **coffee_shop_request.dict(),
        normalized_name=coffee_shop_request.name.replace(" ", "").lower(),
        user_id=user.get("id"),
    )
    # coffee_shop_request.dict()   --> converts coffee_shop_request pydantic object (JSON format) into python dictionary
    # **coffee_shop_request.dict() --> unpacks dictionary into keyword arguments for the CoffeShops model, mapping fields (title) to corresponding columns in the CoffeShops SQLAlchemy model (table).
    # adds coffee_shop_model object (instance of CoffeeShops class), to table (still not commited tho, local)
    # add changes to database
    try:
        with db.begin():
            db.add(shop)
        db.refresh(shop)
        return shop

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create coffee shop: {str(e)}",
        )


# delete coffee shop entry only if client added it, but whenever coffee shop is deleted, all of its things are also deleted (like raitng)
@router.delete("/coffee-shops/{coffeeshop}")
def delete_coffee_shop(user: user_dependency, db: db_dependency, coffeeshop: str):
    """User can only delete their own coffeeshop entries"""
    user_id = user.get("id")
    # Get the coffee shop
    normalized_name = coffeeshop.replace(" ", "").lower()
    coffee_shop = (
        db.query(CoffeeShops)
        .filter(CoffeeShops.normalized_name == normalized_name)
        .first()
    )
    # Check if coffee shop exists
    if not coffee_shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Coffee shop not found"
        )
    # Check if user created the coffee shop:
    if coffee_shop.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete coffee shops you added",
        )
    # Cascade delete will automatically delete associated ratings and aggregated ratings

    try:
        db.commit()  # Ensure any pending transactions are committed
        db.delete(coffee_shop)  # Delete the coffee shop
        db.commit()  # Commit the deletion

        return {"detail": "Coffee shop and its related data deleted successfully"}

    except SQLAlchemyError as e:
        # Catch other SQLAlchemy-specific errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete coffee shop and related data. Database error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete coffee shop and related data. An unexpected error occurred: {str(e)}",
        )
