Coffee Shops App
===================

This is a FastAPI-based web application designed to help digital nomads find and review coffee shops in Madrid. Inspired by my experiences backpacking through Southeast Asia, I wanted a tool to easily filter coffee shops based on essential criteria for remote work, like wifi, AC availability, and laptop-friendly seating. While platforms like Google Reviews are helpful, they often lack specific details crucial for working from coffee shops!

Key features include:
- Coffee Shop Listings: View and search for coffee shops in Madrid, using filters for wifi, AC availability, dog friendliness, laptop allocated seats, and more.
- User Reviews: Users can rate and leave comments for coffee shops.
- Authentication: Simple user management with hashed passwords.
- CSV Data Import: Coffee shop data is populated from a CSV file on startup.


Tech Stack:
- FastAPI: A framework for building APIs.
- SQLAlchemy: An ORM for database interactions
- SQLite (default): Lightweight database for storing data.
- Passlib: Password hashing for security (bcrypt).
- Uvicorn: ASGI server to run the FastAPI app.
- CSV: Used to populate the database with coffee shop data.
- pytest: For testing the application.

Table of contents:
* [Project Structure](#Project-Structure)
* [Setup Instructions](#Setup-Instructions)
* [Test Cases](#Test-Cases) 


## Project Structure:
**COFFEESHOPPROJECT/**  
- **coffeeshopapp/**: Core application directory  
    - `coffeeshops.db`: Database file  
    - `database.py`: Database connection setup  
    - `main.py`: FastAPI application  
    - `models.py`: SQLAlchemy models for coffee shops and reviews  
    - `schemas.py`: Pydantic models for data validation  
    - `seeddata.py`: Data seeding script for initial population  
    - **routers/**: Directory for route handlers  
        - `coffeeshops.py`: Routes for coffee shop-related operations  
        - `reviews.py`: Routes for review-related operations  
        - `users.py`: Routes for user-related operations  

- **csvs/**: Directory for CSV files  
    - `coffeeshops.csv`: Sample CSV data for coffee shops  

- **myenv/**: Virtual environment directory  

- **tests/**: Directory for test files  
    - **routers/**: Tests for route handlers  
        - `test_coffeeshops.py`: Test cases for coffee shop routes  
        - `test_reviews.py`: Test cases for review routes  
        - `test_users.py`: Test cases for user routes  
    - `test_database.py`: Test cases for database connection and setup  
    - `conf_test.py`: config file for pytest

- `.gitignore`: Git ignore file  
- `Makefile`: Automation script for common tasks  
- `project.toml`: Project metadata and configuration  
- `README.md`: Project documentation (this file)  
- `requirements.txt`: Project dependencies


## Setup Instructions:

Follow the steps below to set up the project environment and get everything running:

1. Clone the Repository  
Clone this repository to your local machine:
```bash
git clone https://github.com/AntonellaMasini/MadridCoffeeShopFinder.git
cd coffeeshopapp
```

2. Set up a Virtual Environment  
Use a virtual environment to isolate project dependencies:
```bash
python3 -m venv fastapi_env
source myenv/bin/activate  # On Linux/macOS
myenv\Scripts\activate     # On Windows
```
3. Install Dependencies  
```bash
Once the virtual environment is activated, install the required dependencies by running:
pip install -r requirements.txt
```

4. Running the Application  
Once the setup is complete, you can run the FastAPI app with the following command inside root folder:
```bash
make run
```
This will start the FastAPI application using uvicorn at http://127.0.0.1:8000 or http://127.0.0.1:8000/docs (Swagger UI)

5. Populate the database with seed data
If you want to populate the database with some default coffee shop data, simply start the app, and the seed data will be inserted automatically if the database is empty.

6. Running Tests
To run the test suite with pytest:
```bash
make test
```
7. Code Formatting and Linting
You can format the code using black and isort and lint it using flake8 by running:
```bash
make format  # Format the code
make lint    # Run linting checks
```

## Test Cases:  
This project includes automated tests to verify the functionality of the application. The tests are organized by different components of the app, such as routers and database operations.

- **Tested Routes**:
    - **Coffee Shops**: Tests related to creating, deleting, and fetching coffee shops.  
    - **Reviews**: Tests for adding, deleting, and fetching reviews for specific coffee shops.  
    - **Users**: Tests for user authentication, password validation, and user management.  
    - **Database**: Verifies that the database connection works as expected.

### How to Run Tests
To run the tests, use the `make test` command:
```bash
make test/
```
### Troubleshooting
If a test fails, pytest will provide a detailed trace of the error, helping you identify which part of the code is causing the issue. If you encounter any issues, you can try running the tests individually for more granular results.
```bash
pytest tests/routers/test_coffee_shops.py  # Run tests for coffee shops
pytest tests/routers/test_reviews.py       # Run tests for reviews
pytest tests/routers/test_users.py         # Run tests for users
```

Thanks!