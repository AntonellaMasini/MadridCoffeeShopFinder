from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from sqlalchemy.exc import IntegrityError
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

    def normalize_name(self, coffeeshop: str):
        # print(coffeeshop.strip().lower())
        return coffeeshop.replace(" ", "").lower()

    def get_shop_id(self, normalized_coffeeshop: str):
        # SELECT id FROM coffee_shops WHERE name = coffeeshop
        shop_id = (
            self.db.query(CoffeeShops.id)
            .filter(CoffeeShops.normalized_name == normalized_coffeeshop)
            .scalar()
        )  # returns first element of tuple
        if not shop_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Coffee shop not found"
            )
        return shop_id

    def get_reviews_for_coffeeshop(self, coffeeshop: str):
        normalized_coffeeshop = self.normalize_name(coffeeshop)
        shop_id = self.get_shop_id(normalized_coffeeshop)
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
        normalized_coffeeshop = self.normalize_name(review_request.coffeeshop)
        shop_id = self.get_shop_id(normalized_coffeeshop)

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
        # exclude coffeeshop because the SQLAlchemy model doesnt have this field, only coffee shop id
        review = CoffeeReviews(
            **review_request.dict(exclude={"coffeeshop"}),  # **kwargs
            coffee_shop_id=shop_id,
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
        )

        self.db.add(review)
        self.db.flush()

        # Update aggregated reviews
        agg_rating_dict = self.update_aggregated_rating(shop_id, review.rating)

        # Convert review to a dictionary
        coffeeshop_capitalized_name = (
            self.db.query(CoffeeShops.name).filter(CoffeeShops.id == shop_id).scalar()
        )
        review_dict = {
            "id": review.id,
            "coffeeshop": coffeeshop_capitalized_name,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
            "timestamp": review.timestamp,
        }

        return {"review": review_dict, "aggregated rating": agg_rating_dict}

    def update_review(self, review_request: CoffeeReviewsRequest, user_id: int):
        normalized_coffeeshop = self.normalize_name(review_request.coffeeshop)
        shop_id = self.get_shop_id(normalized_coffeeshop)

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

        old_rating = review.rating  # store old rating
        # UPDATE reviews SET col1=val1, col2=val2... WHERE user_id == user.get(id)
        review.rating = review_request.rating
        review.comment = review_request.comment
        review.timestamp = datetime.now().isoformat()

        # update aggregated reviews
        agg_rating_dict = self.update_aggregated_rating(
            shop_id, review.rating, old_rating
        )
        self.db.flush()

        # Convert review to a dictionary
        coffeeshop_capitalized_name = (
            self.db.query(CoffeeShops.name).filter(CoffeeShops.id == shop_id).scalar()
        )
        review_dict = {
            "id": review.id,
            "coffeeshop": coffeeshop_capitalized_name,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
            "timestamp": review.timestamp,
        }

        return {"review": review_dict, "aggregated rating": agg_rating_dict}

    def delete_review(self, coffeeshop: str, user_id: int):
        normalized_coffeeshop = self.normalize_name(coffeeshop)
        shop_id = self.get_shop_id(normalized_coffeeshop)

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
        old_rating = review.rating

        self.db.query(CoffeeReviews).filter(
            CoffeeReviews.coffee_shop_id == shop_id
        ).filter(CoffeeReviews.user_id == user_id).delete()

        # update aggregated reviews

        agg_rating_dict = self.update_aggregated_rating(shop_id, None, old_rating)
        review_dict = {"detail": "Successfully deleted review"}
        return (review_dict, agg_rating_dict)

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
            if rating is None:
                raise ValueError("Rating must be provided for the first review.")
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
                    dict_agg_rating = {
                        "coffee_shop_id": shop_id,
                        "aggregated_rating": None,
                        "total_reviews": 0,
                    }
                    return dict_agg_rating

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

        self.db.flush()
        dict_agg_rating = {
            "coffee_shop_id": agg_rating.coffee_shop_id,
            "aggregated_rating": agg_rating.aggregated_rating,
            "total_reviews": agg_rating.total_reviews,
        }
        return dict_agg_rating


# API ENDPOINTS -----------------------------------------------------------------------------------------------------------------------


# get reviews for X coffeeshop
@router.get("/{coffeeshop}")
def get_reviews_for_coffeeshop(db: db_dependency, coffeeshop):
    service = ReviewService(db)
    reviews = service.get_reviews_for_coffeeshop(coffeeshop)
    return reviews


# add review for X coffeeshop. User can only write one review for a coffeeshop
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_review_for_coffeeshop(
    user: user_dependency, db: db_dependency, review_request: CoffeeReviewsRequest
):
    service = ReviewService(db)
    user_id = user.get("id")
    try:
        with db.begin():
            review = service.create_review(review_request, user_id)
            return review

    except IntegrityError as e:
        # Handle specific database errors (like unique constraint violation)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create review. Database integrity error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review. Unexpected error: {str(e)}",
        )


# update review for x coffeeshop (can only update my reviews)
@router.put("/")
def update_review_for_coffeeshop(
    user: user_dependency, db: db_dependency, review_request: CoffeeReviewsRequest
):
    """User can only update their own reviews"""
    service = ReviewService(db)
    user_id = user.get("id")
    try:
        with db.begin():
            review = service.update_review(review_request, user_id)
            return review

    except IntegrityError as e:
        # Handle specific database errors (like unique constraint violation)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update review in transaction. Database integrity error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update review in transaction. Unexpected error: {str(e)}",
        )


# delete review for X coffeeshop (can only delete my reviews)
@router.delete("/{coffeeshop}")
def delete_review_for_coffeeshop(
    user: user_dependency, db: db_dependency, coffeeshop: str
):
    """User can only delete their own reviews"""
    service = ReviewService(db)
    user_id = user.get("id")
    try:
        with db.begin():
            print("YEEEEEEES")
            print(coffeeshop)
            print(user_id)
            result = service.delete_review(coffeeshop, user_id)
        return result

    except IntegrityError as e:
        # Handle specific database errors (like unique constraint violation)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete review in transaction. Database integrity error: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete review in transaction. Unexpected error: {str(e)}",
        )
