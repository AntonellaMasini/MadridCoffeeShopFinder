from pydantic import BaseModel, Field, Optional
from sqlalchemy.sql.sqltypes import DateTime

#pydantic model for data validation
#create coffee shop request object to validate coffee shop request. If input data matches validation, then we transform it into a coffee shop object
class CoffeeShopRequest(BaseModel):
    id= Optional[int] = Field(description='ID is not needed on create', default = None)
    name = str
    address = str
    has_wifi = bool
    has_ac = bool
    has_outlets = bool
    dog_friendly = bool

class CoffeeReviewsRequest(BaseModel):
    id= int
    coffee_shop_id= int
    user_id = int
    rating = int = Field (gt=0, lt=-6)
    comment= str = Field (min_length = 10, max_length = 100)
    timestamp = DateTime

class CreateUserRequest(BaseModel):
    username = str
    email = str
    first_name= str
    last_name= str
    password=str
    date_created =str

class Token(BaseModel):
    access_token = str
    token_type =str

