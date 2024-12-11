import pytest
from sqlalchemy.exc import OperationalError

from CoffeeShopApp.database import engine


def test_database_connection():
    """Test if the database connection is successful."""
    try:
        conn = engine.connect()
        conn.close()
    except OperationalError:
        pytest.fail("Database connection failed.")
