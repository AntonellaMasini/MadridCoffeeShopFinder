from typing import Optional

from pydantic import BaseModel, Field

from .models import LevelsEnum


# pydantic model for data validation
# create coffee shop request object to validate coffee shop request. If input data matches validation, then we transform it into a coffee shop object
class CoffeeShopRequest(BaseModel):
    name: str
    address: str
    wifi_quality: LevelsEnum  # Using Pydantic Enum
    has_ac: bool
    laptop_friendly_seats: LevelsEnum
    dog_friendly: bool
    noise_level: str
    outlet_availability: LevelsEnum
    # class Config:
    #     orm_mode = True  # This allows SQLAlchemy models to be serialized


class CoffeeShopFilterRequest(BaseModel):
    wifi_quality: Optional[LevelsEnum] = Field(
        None, description="Filter by WiFi quality"
    )
    has_ac: Optional[bool] = Field(None, description="Filter by AC availability")
    laptop_friendly_seats: Optional[LevelsEnum] = Field(
        None, description="Filter by laptop friendly seats quantity"
    )
    dog_friendly: Optional[bool] = Field(None, description="Filter by dog friendly")
    noise_level: Optional[LevelsEnum] = Field(None, description="Filter by noise level")
    outlet_availability: Optional[LevelsEnum] = Field(
        None, description="Filter by outlet availability"
    )
    min_combined_rating: Optional[float] = Field(
        None, ge=1, le=5, description="Filter by minimum rating"
    )


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
    # date_created: str


class Token(BaseModel):
    access_token: str
    token_type: str
