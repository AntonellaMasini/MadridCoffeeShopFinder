import pytest
from fastapi import status
from fastapi.testclient import TestClient

from CoffeeShopApp.main import app
from CoffeeShopApp.models import CoffeeShops
from CoffeeShopApp.routers.coffee_shops import get_db
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
def test_coffeeshop():
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
    db = TestingSessionLocal()
    db.add(test_coffeeshop)
    db.commit()
    yield test_coffeeshop
    db.query(CoffeeShops).delete()
    db.commit()
    db.close()


# test creation of coffeeshop
def test_create_coffee_shop(test_coffeeshop):
    request_data = {
        "name": "New Coffee",
        "address": "address new coffee",
        "wifi_quality": 1,
        "has_ac": True,
        "laptop_friendly_seats": 1,
        "dog_friendly": True,
        "noise_level": 1,
        "outlet_availability": 1,
    }
    response = client.post("/coffees-madrid/coffee-shops/", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED
    db = TestingSessionLocal()
    model = (
        db.query(CoffeeShops)
        .filter(CoffeeShops.name == request_data.get("name"))
        .first()
    )
    assert model is not None
    # assert that model attributes == request data attributes
    for key, value in request_data.items():
        assert getattr(model, key) == value


# # test deletion of coffeeshop
# def test_delete_coffee_shop(test_coffeeshop):
#     response = client.delete("/coffees-madrid/coffee-shops/Coffee Test")
#     assert response.status_code == status.HTTP_200_OK
#     db = TestingSessionLocal()
#     model = db.query(CoffeeShops).filter(CoffeeShops.name == "Coffee Test").first()
#     assert model is None
#     assert response.json() == {
#         "detail": "Coffee shop and its related data deleted successfully"
#     }

# # test deletion of non existing coffeeshop,
# def test_delete_no_coffee_shop(test_coffeeshop):
#     response = client.delete("/coffees-madrid/coffee-shops/NoCoffee")
#     assert response.status_code == status.HTTP_404_NOT_FOUND
#     db = TestingSessionLocal()
#     model = db.query(CoffeeShops).filter(CoffeeShops.name == "Coffee Test").first()
#     assert model is not None
#     assert response.json() == {"detail": "Coffee shop not found"}

#Refactored tests above into one:
@pytest.mark.parametrize(
    "shop_name, expected_status, expected_detail",
    [
        ("Coffee Test", status.HTTP_200_OK, "Coffee shop and its related data deleted successfully"),
        ("NoCoffee", status.HTTP_404_NOT_FOUND, "Coffee shop not found"),
    ],
)
def test_delete_coffee_shop_parametrized(test_coffeeshop, shop_name, expected_status, expected_detail):
    response = client.delete(f"/coffees-madrid/coffee-shops/{shop_name}")
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail

    db = TestingSessionLocal()
    model = db.query(CoffeeShops).filter(CoffeeShops.name == "Coffee Test").first()

    if expected_status == status.HTTP_200_OK:
        # If the deletion was successful, the coffee shop should no longer exist
        assert model is None
    else:
        # If the coffee shop doesn't exist, the deletion should not affect the database
        assert model is not None
        



# test deletion of coffeeshop, different user
def test_delete_coffee_shop_different_user(test_coffeeshop):
    def override_get_current_user():
        return {"username": "differentuser", "id": 2}

    app.dependency_overrides[get_current_user] = override_get_current_user
    response = client.delete("/coffees-madrid/coffee-shops/Coffee Test")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "You can only delete coffee shops you added"}
    db = TestingSessionLocal()
    model = db.query(CoffeeShops).filter(CoffeeShops.name == "Coffee Test").first()
    assert model is not None


def test_get_coffeeshops(test_coffeeshop):
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
    db = TestingSessionLocal()
    db.add(test_coffeeshop2)
    db.commit()
    response = client.get("/coffees-madrid/coffee-shops/all")
    assert response.status_code == status.HTTP_200_OK
    coffee_shops = response.json()
    shop_names = []
    for shop in coffee_shops:
        shop_names.append(shop["name"])
    assert "Coffee Test" in shop_names
    assert "Coffee Test2" in shop_names


# def test_get_coffeeshop_filter(test_coffeeshop):
#     # Add a second coffee shop with higher wifi quality
#     coffee_shop_2 = CoffeeShops(
#         name="Best Coffee",
#         normalized_name="bestcoffee",
#         address="address test",
#         wifi_quality=3,
#         has_ac=True,
#         laptop_friendly_seats=3,
#         dog_friendly=True,
#         noise_level=3,
#         outlet_availability=3,
#         user_id=1,
#     )
#     db = TestingSessionLocal()
#     db.add(coffee_shop_2)
#     db.commit()

#     # Send request to filter by wifi_quality > 1
#     response = client.get("/coffees-madrid/coffee-shops/", params={"wifi_quality": 2})
#     assert response.status_code == status.HTTP_200_OK
#     coffee_shops = response.json()["coffee_shops"]

#     # Verify the result contains only the shop with wifi_quality >= 4
#     assert len(coffee_shops) == 1
#     assert coffee_shops[0]["name"] == "Best Coffee"

#     # Send request to filter by has_ac == True
#     response = client.get("/coffees-madrid/coffee-shops/", params={"has_ac": True})
#     assert response.status_code == status.HTTP_200_OK
#     coffee_shops = response.json()["coffee_shops"]
#     # Verify the result contains othe two coffeeshops, since both are true
#     assert len(coffee_shops) == 2
#     assert coffee_shops[1]["name"] == "Best Coffee"
#     assert coffee_shops[0]["name"] == "Coffee Test"

#     # Edge case: No coffeeshops match
#     response = client.get("/coffees-madrid/coffee-shops/", params={"has_ac": False})
#     assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.parametrize(
    "filter_params, expected_names, expected_status",
    [
        ({"wifi_quality": 2}, ["Best Coffee"], status.HTTP_200_OK),
        ({"has_ac": True}, ["Coffee Test", "Best Coffee"], status.HTTP_200_OK),
        ({"has_ac": False}, [], status.HTTP_204_NO_CONTENT),
        ({"noise_level": 3}, ["Best Coffee", 'Coffee Test'], status.HTTP_200_OK),
        ({"dog_friendly": False}, [], status.HTTP_204_NO_CONTENT),
        ({"laptop_friendly_seats": 3, "has_ac": True}, ["Best Coffee"], status.HTTP_200_OK),
    ],
)
def test_get_coffeeshop_filter_parametrized(test_coffeeshop, filter_params, expected_names, expected_status):
    # Add a second coffee shop to the database
    coffee_shop_2 = CoffeeShops(
        name="Best Coffee",
        normalized_name="bestcoffee",
        address="address test",
        wifi_quality=3,
        has_ac=True,
        laptop_friendly_seats=3,
        dog_friendly=True,
        noise_level=3,
        outlet_availability=3,
        user_id=1,
    )
    db = TestingSessionLocal()
    db.add(coffee_shop_2)
    db.commit()

    # Send request with filter parameters
    response = client.get("/coffees-madrid/coffee-shops/", params=filter_params)
    
    assert response.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        coffee_shops = response.json()["coffee_shops"]
        actual_names = [shop["name"] for shop in coffee_shops]
        assert set(actual_names) == set(expected_names)
    else:
        assert response.text == ""