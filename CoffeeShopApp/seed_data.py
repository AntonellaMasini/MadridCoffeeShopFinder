import csv
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from passlib.context import CryptContext
from sqlalchemy.orm.session import Session

from CoffeeShopApp.database import SessionLocal
from CoffeeShopApp.models import CoffeeShops, Users

csv_path = (
    Path(__file__).parent.parent / "csvs" / "coffeeshops.csv"
)  # dynamic path construvtion, good for portability!
if not csv_path.is_file():
    print(f"ERROR: {csv_path} does not exist.")

bcrypt_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto"
)  # CryptContext is a class passed by passlib library. Handles hashing and verifying passwords


# bcrypt is the algorythm (scheme) chosen for password hashing
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def populate_coffee_shops(db: db_dependency):
    # Check if the CoffeeShops table has data, and if not, populate table
    existing_records = db.query(CoffeeShops).count()

    if existing_records == 0:
        try:
            # Create a default user
            hashed_password = bcrypt_context.hash("12345")
            user = Users(
                username="amasini",
                email="antomasini98@gmail.com",
                first_name="Antonella",
                last_name="Masini",
                hashed_password=hashed_password,
                date_created=datetime.now().isoformat(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            with open(csv_path, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:  # row is a dict
                    for (
                        key,
                        value,
                    ) in (
                        row.items()
                    ):  # Convert 'TRUE'/'FALSE' to Python booleans (True/False)
                        if value == "TRUE":
                            row[key] = True
                        elif value == "FALSE":
                            row[key] = False

                    row["user_id"] = user.id
                    db.add(CoffeeShops(**row))
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise Exception(f"An error occurred while populating coffee shops: {str(e)}")
