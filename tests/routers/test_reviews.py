import pytest
from fastapi import status
from fastapi.testclient import TestClient

from CoffeeShopApp.main import app
from CoffeeShopApp.models import AggregatedRatings, CoffeeReviews, CoffeeShops
from CoffeeShopApp.routers.reviews import get_db
from CoffeeShopApp.routers.users import get_current_user
from tests.conftest import TestingSessionLocal


# override dependencies
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {"username": "amasini", "id": 1}


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


# adding and deleting a coffeshop to test db
@pytest.fixture
def test_reviews():
    # create coffeeshop
    test_coffeeshop = CoffeeShops(
        name="Coffee Test",
        normalized_name="coffeetest",
        address="address test",
        wifi_quality=1,
        has_ac=True,
        laptop_friendly_seats=1,
        dog_friendly=True,
        noise_level=1,
        outlet_availability=1,
        user_id=1,
    )

    test_coffeeshop2 = CoffeeShops(
        name="Coffee Test2",
        normalized_name="coffeetest2",
        address="address test",
        wifi_quality=1,
        has_ac=True,
        laptop_friendly_seats=1,
        dog_friendly=True,
        noise_level=1,
        outlet_availability=1,
        user_id=1,
    )

    test_review = CoffeeReviews(
        user_id=1,
        coffee_shop_id=1,
        rating=1,
        comment="terrible!",
        timestamp="2024-01-01T00:00:00",
    )
    test_aggrating = AggregatedRatings(
        coffee_shop_id=1, aggregated_rating=1, total_reviews=1
    )
    db = TestingSessionLocal()
    db.add(test_review)
    db.add(test_coffeeshop)
    db.add(test_coffeeshop2)
    db.add(test_aggrating)
    db.commit()
    # Yield both objects as a tuple
    yield test_review, test_coffeeshop, test_coffeeshop2
    db.query(CoffeeReviews).delete()
    db.query(CoffeeShops).delete()
    db.query(AggregatedRatings).delete()
    db.commit()
    db.close()


# test get reviews for coffeeshop
def test_get_reviews_for_coffeeshop(test_reviews):
    response = client.get(f"/coffees-madrid/reviews/{test_reviews[1].name}")
    assert response.status_code == status.HTTP_200_OK
    actual = response.json()
    expected = [
        {
            "user_id": 1,
            "coffee_shop_id": 1,
            "comment": "terrible!",
            "rating": 1,
            "id": 1,
            "timestamp": "2024-01-01T00:00:00",
        }
    ]
    assert actual == expected


# test get reviews for a coffeeshop that exists but does not have reviews yet
def test_get_none_reviews_for_coffeeshop(test_reviews):
    response = client.get(f"/coffees-madrid/reviews/{test_reviews[2].name}")
    assert response.status_code == status.HTTP_204_NO_CONTENT


# test get reviews for a nonexistent coffeeshop
def test_get_reviews_for_none_coffeeshop(test_reviews):
    response = client.get("/coffees-madrid/reviews/nocoffee")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_review_for_coffeeshop(test_reviews):
    review_request = {
        "coffeeshop": test_reviews[2].name,
        "rating": 5,
        "comment": "amazing!",
    }
    response = client.post("/coffees-madrid/reviews/", json=review_request)
    assert response.status_code == status.HTTP_201_CREATED
    actual = response.json()

    # Validate review values
    review = actual["review"]
    assert review["id"] == 2
    assert review["coffeeshop"] == "Coffee Test2"
    assert review["user_id"] == 2
    assert review["rating"] == 5
    assert review["comment"] == "amazing!"

    # Validate aggregated values
    aggregated = actual["aggregated rating"]
    assert aggregated["coffee_shop_id"] == 2
    assert aggregated["aggregated_rating"] == 5.0
    assert aggregated["total_reviews"] == 1

    # verify review and aggratings were added to correct dbs
    db = TestingSessionLocal()
    coffeereviews = db.query(CoffeeReviews).all()
    assert len(coffeereviews) == 2
    aggratings = db.query(AggregatedRatings).all()
    assert len(aggratings) == 2


# test deletion of review
def test_delete_reviews(test_reviews):
    print(test_reviews[1].user_id)

    app.dependency_overrides[get_current_user] = override_get_current_user
    response = client.delete(f"/coffees-madrid/reviews/{test_reviews[1].name}")
    assert response.status_code == status.HTTP_200_OK
    db = TestingSessionLocal()
    model = (
        db.query(CoffeeReviews).filter(CoffeeShops.name == test_reviews[1].name).first()
    )
    assert model is None


# test deletion of review (not user's)
def test_delete_reviews_diff_user(test_reviews):
    def override_get_current_user():
        return {"username": "differentuser", "id": 2}

    app.dependency_overrides[get_current_user] = override_get_current_user
    response = client.delete(f"/{test_reviews[1].name}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
