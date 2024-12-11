import pytest
from fastapi import status
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from CoffeeShopApp.main import app
from CoffeeShopApp.models import Users
from CoffeeShopApp.routers.users import get_current_user, get_db
from tests.conftest import TestingSessionLocal


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

# # create FastAPI test client to simulate requests to API endpoints.
# # test client will use the TestingSessionLocal for the database and the mocked user
client = TestClient(app)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# adding and deleting a user to test db
@pytest.fixture
def test_user():
    hashed_password = bcrypt_context.hash("12345")
    user = Users(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        hashed_password=hashed_password,
        date_created="2024-01-01T00:00:00",
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    db.query(Users).delete()  # Deletes all rows in the Users table
    db.commit()


# test get_user endopint
def test_get_user(test_user):
    response = client.get("/coffees-madrid/auth/testuser")
    assert response.status_code == status.HTTP_200_OK
    actual = response.json()
    expected = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "date_created": "2024-01-01T00:00:00",
    }
    assert expected == actual


# test get_user endopint when username is None
def test_get_user_not_found():
    response = client.get("/coffees-madrid/auth/None")
    assert response.status_code == status.HTTP_204_NO_CONTENT


# test create_user endpoint succesfully
def test_create_user(test_user):
    request_data = {
        "username": "newuser",
        "email": "newuser@gmail.com",
        "first_name": "New",
        "last_name": "User",
        "password": "12345",
    }
    response = client.post("/coffees-madrid/auth", json=request_data)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()
    model = db.query(Users).filter(Users.username == "newuser").first()
    # Assert that the user is in the database
    assert model is not None
    assert model.username == request_data.get("username")
    assert model.email == request_data.get("email")
    assert model.first_name == request_data.get("first_name")
    assert model.last_name == request_data.get("last_name")
    # Check if the hashed password matches the expected hash
    assert bcrypt_context.verify(request_data.get("password"), model.hashed_password)


# test create_user endpoint integrity error (same email)
def test_create_user_bad_request(test_user):
    request_data = {
        "username": "newuser",
        "email": "test@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "12345",
    }
    response = client.post("/coffees-madrid/auth", json=request_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# Authentification fails:
def test_wrong_password(test_user):
    request_data_auth = {
        "username": "testuser",
        "password": "wrongpassword",
    }

    # Send the POST request for authentication
    response_auth = client.post("/coffees-madrid/auth/token", data=request_data_auth)

    assert (
        response_auth.status_code == status.HTTP_401_UNAUTHORIZED
    )  # Unauthorized due to wrong password
    assert response_auth.json() == {
        "detail": "Invalid credentials. User not found or authentication failed"
    }


# Authentification succeeds:
def test_correct_password(test_user):
    request_data_auth = {
        "username": "testuser",
        "password": "12345",
    }
    # Send the POST request for authentication
    response_auth = client.post("/coffees-madrid/auth/token", data=request_data_auth)
    assert response_auth.status_code == status.HTTP_200_OK
    # Check if the response contains an access token
    response_json = response_auth.json()
    assert "access_token" in response_json
