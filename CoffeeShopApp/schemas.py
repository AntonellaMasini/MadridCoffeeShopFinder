from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum as PyEnum
from .models import LevelsEnum


#pydantic model for data validation
#create coffee shop request object to validate coffee shop request. If input data matches validation, then we transform it into a coffee shop object
class CoffeeShopRequest(BaseModel):
    name : str 
    address : str
    wifi_quality : LevelsEnum # Using Pydantic Enum
    has_ac : bool
    laptop_friendly_seats: LevelsEnum 
    dog_friendly: bool
    noise_level: str
    outlet_availability: LevelsEnum  

    # class Config:
    #     orm_mode = True  # This allows SQLAlchemy models to be serialized


class CoffeeReviewsRequest(BaseModel):
    coffee_shop_id: int
    user_id : int
    rating : int = Field (gt=0, lt=-6)
    comment: str = Field (min_length = 10, max_length = 100)
    timestamp: datetime

class CreateUserRequest(BaseModel):
    username : str
    email : str
    first_name: str
    last_name: str
    password: str
    #date_created: str

class Token(BaseModel):
    access_token : str
    token_type : str

