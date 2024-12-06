# Handles all user-related endpoints
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from CoffeeShopApp.database import SessionLocal
from CoffeeShopApp.models import Users
from CoffeeShopApp.schemas import CreateUserRequest, Token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/auth",
    # tags=['users']
)

# from terminal to get ranodm: openssl ran -hex 32
SECRET_KEY = "c50f442d8c21674efe3301ed5c15c46e6a844c5faab48ee1f448b814bc3d2299"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto"
)  # CryptContext is a class passed by passlib library. Handles hashing and verifying passwords
# bcrypt is the algorythm (scheme) chosen for password hashing

oauth2_bearer = OAuth2PasswordBearer(
    tokenUrl="/coffees-madrid/auth/token"
)  # when used as a dependency, will let FastAPI extract tokens from requests .


def authenticate_user(username: str, password: str, db):
    # SELECT * FROM users WHERE user_name = username
    user = db.query(Users).filter(Users.username == username).first()
    # is user in db?
    if not user:  # if user == None (or any false values for that matter):
        return False
    # is password correct?
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    else:
        return user


# get encoded token (JWT)
def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    expires = datetime.now(timezone.utc) + expires_delta
    encode = {"sub": username, "id": user_id, "exp": expires}
    return jwt.encode(
        encode, SECRET_KEY, algorithm=ALGORITHM
    )  # jwt is a module that is imported from python-jose library. call encode function to create token with provided info


# get decoded token (JWT)
def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(
            token, SECRET_KEY
        )  # get decoded payload as a readable string
        # print(f"Decoded Payload: {payload}")
        username: str = payload.get(
            "sub"
        )  # include type hint is good practice for API development
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. User not found or authentication failed",
            )
        # print(user_id)
        return {"username": username, "id": user_id}

    # catch any issue that occurs when decoding the JWT.
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Could not validate credentials",
        )


# API ENDPOINTS -----------------------------------------------------------------------------------------------------------------------
# create user object and add it as a row to user table
@router.post("/")
def create_user(db: db_dependency, user: CreateUserRequest):
    new_user = Users(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=bcrypt_context.hash(user.password),
        date_created=datetime.now().isoformat(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# allow user to authenticate themself and login into saved user
@router.post("/token", response_model=Token)
def login_for_access_token(
    db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):  # same as saying OAuth2PasswordRequestForm = Depends()
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. User not found or authentication failed",
        )
    else:
        token = create_access_token(user.username, user.id, timedelta(minutes=20))
        return {
            "access_token": token,
            "token_type": "bearer",
        }  # successfully return token


# return user info (path parameter)
@router.get("/{username}")
def get_user(db: db_dependency, username: str):
    # SELECT * FROM Users WHERE user_id = user_id
    user = db.query(Users).filter(Users.username == username).first()
    return user


# OOP
# class Users():
#     def __init__(self, username: str, email: str, first_name: str, last_name: str, hashed_password:str, db: Session):
#         self.username = username
#         self.email = email
#         self.first_name = first_name
#         self.last_name = last_name
#         self.hashed_password = hashed_password
#         self.db = db

# def create_access_token(username:str, user_id:int, expires_delta:timedelta):
#     encode= {'sub': username, 'id': user_id}
#     expires= datetime.now(timezone.utc)+expires_delta
#     encode.update({'exp':expires})
#     return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
