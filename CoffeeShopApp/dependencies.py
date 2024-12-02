from fastapi import Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
#from .routers.users import get_current_user
from typing import Annotated



def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)] 