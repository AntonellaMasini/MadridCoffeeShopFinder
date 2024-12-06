from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from sqlalchemy.orm import Session

from CoffeeShopApp.database import SessionLocal
from CoffeeShopApp.models import AggregatedRatings, CoffeeReviews, CoffeeShops
from CoffeeShopApp.schemas import CoffeeReviewsRequest

from .users import get_current_user

user_dependency = Annotated[dict, Depends(get_current_user)]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter()


# OOP (refractorization) shops add one where user filters for all the coffees with ratings > 2
class ReviewService:
    def __init__(self, db: db_dependency):
        self.db = db

    def get_shop_id(self, coffeeshop: str):
        # SELECT id FROM coffee_shops WHERE name = coffeeshop
        shop_id = (
            self.db.query(CoffeeShops.id)
            .filter(CoffeeShops.name == coffeeshop)
            .scalar()
        )  # returns first element of tuple
        if not shop_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Coffee shop not found"
            )
        return shop_id

    def get_reviews_for_coffeeshop(self, coffeeshop: str):
        shop_id = self.get_shop_id(coffeeshop)
        # SELECT * FROM coffee_shops_table WHERE coffee_shop = coffeeshop
        reviews_coffeeshop = (
            self.db.query(CoffeeReviews)
            .filter(CoffeeReviews.coffee_shop_id == shop_id)
            .all()
        )  # returns a list of objects
        if not reviews_coffeeshop:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        return reviews_coffeeshop

    def create_review(self, review_request: CoffeeReviewsRequest, user_id: int):
        shop_id = self.get_shop_id(review_request.coffeeshop)
        # check if user has already written a review for that coffee shop:
        existing_review = (
            self.db.query(CoffeeReviews)
            .filter(CoffeeReviews.coffee_shop_id == shop_id)
            .filter(CoffeeReviews.user_id == user_id)
            .first()
        )
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A review by the current user already exists. Please update it instead.",
            )

        # INSERT INTO reviews (col1, col2....) VALUES (val1, val2...)
        # exclude coffeeshop because the SQLAlchemy model doesnt have this field
        review = CoffeeReviews(
            **review_request.dict(exclude={"coffeeshop"}),
            coffee_shop_id=shop_id,
            user_id=user_id,
            timestamp=datetime.now().isoformat()
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        # update aggregated reviews
        updated_agg_rating = self.update_aggregated_rating(shop_id, review.rating)
        return {
            "Review Created": review,
            "Updated aggregated rating": updated_agg_rating,
        }

    # use transaction logic to ensure that update review and update aggregated review occur together. NO PARTIAL UPDATES
    def update_review(self, review_request: CoffeeReviewsRequest, user_id: int):
        shop_id = self.get_shop_id(review_request.coffeeshop)

        # Start a transaction block
        with self.db.begin():
            # get review written by user
            # SELECT * FROM coffee-reviews WHERE coffee_shop_id == id AND WHERE user_id == user.get(id)
            review = (
                self.db.query(CoffeeReviews)
                .filter(CoffeeReviews.coffee_shop_id == shop_id)
                .filter(CoffeeReviews.user_id == user_id)
                .first()
            )
            if review is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found. Please create review instead.",
                )

            # UPDATE reviews SET col1=val1, col2=val2... WHERE user_id == user.get(id)
            old_rating = review.rating  # store old review
            review.rating = review_request.rating
            review.comment = review_request.comment
            review.timestamp = datetime.now().isoformat()
            # self.db.commit() #delete because transaction block commits it automatically at the end of block
            self.db.refresh(review)

            # update aggregated reviews
            updated_agg_rating = self.update_aggregated_rating(
                shop_id, review.rating, old_rating
            )

        return {
            "updated review": review,
            "updated aggregated rating": updated_agg_rating,
        }

    def delete_review(self, coffeeshop: str, user_id: int):
        shop_id = self.get_shop_id(coffeeshop)

        # Start a transaction block
        with self.db.begin():
            # get review written by user
            # SELECT * FROM coffee-reviews WHERE coffee_shop_id == id AND WHERE user_id == user.get(id)
            review = (
                self.db.query(CoffeeReviews)
                .filter(CoffeeReviews.coffee_shop_id == shop_id)
                .filter(CoffeeReviews.user_id == user_id)
                .first()
            )
            if not review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Review not found."
                )
            self.db.query(CoffeeReviews).filter(
                CoffeeReviews.coffee_shop_id == shop_id
            ).filter(CoffeeReviews.user_id == user_id).delete()
            # self.db.commit()

            # update aggregated reviews
            old_rating = review.rating
            updated_agg_rating = self.update_aggregated_rating(shop_id, old_rating)

        return {
            "detail": "Successfully deleted review",
            "Updated aggregated rating": updated_agg_rating,
        }

    def update_aggregated_rating(
        self,
        shop_id: int,
        rating: Optional[int] = None,
        old_rating: Optional[int] = None,
    ):
        # SELECT * FOR aggregated_ratings WHERE coffee_shop_id = shop_id
        agg_rating = (
            self.db.query(AggregatedRatings)
            .filter(AggregatedRatings.coffee_shop_id == shop_id)
            .first()
        )

        # if users adds the very first rating to a coffee_shop
        if not agg_rating:
            # This means no reviews yet, so the first review is the aggregated rating
            agg_rating = AggregatedRatings(
                coffee_shop_id=shop_id, aggregated_rating=rating, total_reviews=1
            )
            self.db.add(agg_rating)

        elif old_rating is not None:
            # if user is deleting its own review
            if rating is None:
                agg_rating.total_reviews -= 1
                if agg_rating.total_reviews > 0:
                    new_agg_rating = round(
                        (
                            (
                                agg_rating.aggregated_rating
                                * (agg_rating.total_reviews + 1)
                            )
                            - old_rating
                        )
                        / agg_rating.total_reviews,
                        3,
                    )
                    agg_rating.aggregated_rating = new_agg_rating
                # EDGE CASE: user deletes rating for the only aggregated entry that exists for coffeeshop
                else:
                    self.db.delete(agg_rating)
                    self.db.commit()
                    return agg_rating  # returns None

            else:
                # if user is updating its own review
                new_agg_rating = round(
                    (
                        (agg_rating.aggregated_rating * agg_rating.total_reviews)
                        - old_rating
                        + rating
                    )
                    / agg_rating.total_reviews,
                    3,
                )
                agg_rating.aggregated_rating = new_agg_rating

        # if user is adding a new review to a coffeeshop that already has a rating entry
        else:
            agg_rating.total_reviews += 1
            new_agg_rating = round(
                (agg_rating.aggregated_rating * (agg_rating.total_reviews - 1) + rating)
                / agg_rating.total_reviews,
                3,
            )
            agg_rating.aggregated_rating = new_agg_rating

        self.db.commit()
        self.db.refresh(agg_rating)
        return agg_rating


# API ENDPOINTS -----------------------------------------------------------------------------------------------------------------------


# get reviews for X coffeeshop
@router.get("/{coffeeshop}")
def get_reviews_for_coffeeshop(db: db_dependency, coffeeshop):
    service = ReviewService(db)
    return service.get_reviews_for_coffeeshop(coffeeshop)


# add review for X coffeeshop. User can only write one review for a coffeeshop
@router.post("/")
def create_review_for_coffeeshop(
    user: user_dependency, db: db_dependency, review_request: CoffeeReviewsRequest
):
    service = ReviewService(db)
    user_id = user.get("id")
    return service.create_review(review_request, user_id)


# update review for x coffeeshop (can only update my reviews)
@router.put("/")
def update_review_for_coffeeshop(
    user: user_dependency, db: db_dependency, review_request: CoffeeReviewsRequest
):
    service = ReviewService(db)
    user_id = user.get("id")
    return service.update_review(review_request, user_id)


# delete review for X coffeeshop (can only delete my reviews)
@router.delete("/{coffeeshop}")
def delete_review_for_coffeeshop(
    user: user_dependency, db: db_dependency, coffeeshop: str
):
    service = ReviewService(db)
    user_id = user.get("id")
    return service.delete_review(coffeeshop, user_id)


# #API ENDPOINTS -----------------------------------------------------------------------------------------------------------------------

# #get reviews for X coffeeshop
# @router.get("/{coffeeshop}")
# def get_reviews_for_coffeeshop(db:db_dependency, coffeeshop):
#     #SELECT id FROM coffee_shops WHERE name = coffeeshop
#     shop_id = db.query(CoffeeShops.id).filter(CoffeeShops.name==coffeeshop).scalar() #returns first num of tuple
#     if shop_id is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coffee shop not found")

#     #SELECT * FROM coffee_shops_table WHERE coffee_shop = coffeeshop
#     reviews_coffeeshop= db.query(CoffeeReviews).filter(CoffeeReviews.coffee_shop_id==shop_id).all() #returns a list of objects

#     if not reviews_coffeeshop:
#         raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
#     return reviews_coffeeshop


# #add review for X coffeeshop. User can only write one review for a coffeeshop
# @router.post("/")
# def create_review_for_coffeeshop(user:user_dependency, db:db_dependency, review_request: CoffeeReviewsRequest):
#     #SELECT id FROM coffee_shops WHERE name = coffeeshop
#     shop_id= db.query(CoffeeShops.id).filter(CoffeeShops.name==review_request.coffeeshop).scalar()
#     if shop_id is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coffee shop not found")

#     #check if user has already written a review for that coffee shop:
#     user_id=user.get("id")
#     review_model= db.query(CoffeeReviews).filter(CoffeeReviews.coffee_shop_id==shop_id).filter(CoffeeReviews.user_id==user_id).first()

#     if review_model:
#         raise  HTTPException(status_code=status.HTTP_409_CONFLICT, detail= "A review for this coffee shop by the current user already exists. Please update it instead.")

#     #INSERT INTO reviews (col1, col2....) VALUES (val1, val2...)
#     #exclude coffeeshop because the SQLAlchemy model doesnt have this field
#     review = CoffeeReviews(**review_request.dict(exclude={"coffeeshop"}), coffee_shop_id=shop_id, user_id= user_id, timestamp = datetime.now().isoformat())
#     db.add(review)
#     db.commit()
#     db.refresh(review)
#     return review


# #update review for x coffeeshop (can only update my reviews)
# @router.put("/")
# def update_review_for_coffeeshop(user:user_dependency, db:db_dependency, review_request: CoffeeReviewsRequest):
#     #SELECT id FROM coffee_shops WHERE name = coffeeshop
#     shop_id = db.query(CoffeeShops.id).filter(CoffeeShops.name==review_request.coffeeshop).scalar()
#     if shop_id is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coffee shop not found")

#     user_id=user.get("id")
#     #find review written by user
#     #SELECT * FROM coffee-reviews WHERE coffee_shop_id == id AND WHERE user_id == user.get(id)
#     review = db.query(CoffeeReviews).filter(CoffeeReviews.coffee_shop_id==shop_id).filter(CoffeeReviews.user_id==user_id).first()
#     if review is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found. Please create review for this coffee shop.")

#     #UPDATE reviews SET col1=val1, col2=val2... WHERE user_id == user.get(id)
#     review.rating = review_request.rating
#     review.comment = review_request.comment
#     review.timestamp = datetime.now().isoformat()

#     db.add(review)
#     db.commit()
#     db.refresh(review)
#     return review


# #delete review for X coffeeshop (can only delete my reviews)
# @router.delete("/{coffeeshop}")
# def delete_review_for_coffeeshop(user:user_dependency, db:db_dependency, coffeeshop: str):
#     #SELECT id FROM coffee_shops WHERE name = coffeeshop
#     shop_id = db.query(CoffeeShops.id).filter(CoffeeShops.name==coffeeshop).scalar()
#     if shop_id is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coffee shop not found")

#     user_id=user.get("id")
#     #find review written by user
#     #SELECT * FROM coffee-reviews WHERE coffee_shop_id == id AND WHERE user_id == user.get(id)
#     review = db.query(CoffeeReviews).filter(CoffeeReviews.coffee_shop_id==shop_id).filter(CoffeeReviews.user_id==user_id).first()
#     if review is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found. Please create review for this coffee shop.")

#     db.query(CoffeeReviews).filter(CoffeeReviews.coffee_shop_id==shop_id).filter(CoffeeReviews.user_id==user_id).delete()
#     db.commit()

#     return {"detail": "succesfully deleted review"}
