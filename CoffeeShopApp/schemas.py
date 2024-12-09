from enum import IntEnum
from typing import Optional
from pydantic import BaseModel, Field, conint
from fastapi import Query


# pydantic model for data validation
# create coffee shop request object to validate coffee shop request. If input data matches validation, then we transform it into a coffee shop object
class CoffeeShopRequest(BaseModel):
    name: str
    address: str
    wifi_quality: conint(ge=1, le=3)
    has_ac: bool
    laptop_friendly_seats: conint(ge=1, le=3)
    dog_friendly: bool
    noise_level: conint(ge=1, le=3)
    outlet_availability: conint(ge=1, le=3)
    # class Config:
    #     orm_mode = True  # This allows SQLAlchemy models to be serialized


#class for query parameters (get endpoints)
class CoffeeShopFilterRequest:
    def __init__(
        self,
        wifi_quality: Optional[conint(ge=1, le=3)] = Query(
            None, description="Filter by minimum WiFi quality. Choose 1 (low), 2 (medium), or 3 (high)"
        ),
        has_ac: Optional[bool] = Query(None, description="Filter by AC availability"),
        laptop_friendly_seats: Optional[conint(ge=1, le=3)] = Query(
            None, description="Filter by minimum quantity of laptop friendly seats. Choose 1 (limited), 2 (moderate), or 3 (plenty)"
        ),
        dog_friendly: Optional[bool] = Query(None, description="Filter by dog friendly"),
        noise_level: Optional[conint(ge=1, le=3)] = Query(
            None, description="Filter by maximum noise level. Choose 1 (low), 2 (medium), or 3 (high)"
        ),
        outlet_availability: Optional[conint(ge=1, le=3)] = Query(
            None, description="Filter by minimum outlet availability. Choose 1 (limited), 2 (moderate), or 3 (plenty)"
        ),
        min_combined_rating: Optional[float] = Query(
            None, ge=1, le=5, description="Filter by minimum rating (min 1, max 5)"
        ),
    ):
        self.wifi_quality = wifi_quality
        self.has_ac = has_ac
        self.laptop_friendly_seats = laptop_friendly_seats
        self.dog_friendly = dog_friendly
        self.noise_level = noise_level
        self.outlet_availability = outlet_availability
        self.min_combined_rating = min_combined_rating

class CoffeeReviewsRequest(BaseModel):
    coffeeshop: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=100)


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


#RESPONSES

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    date_created: str

    class Config:
        from_attributes = True

