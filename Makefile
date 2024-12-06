# Variables
APP_NAME = CoffeeShopApp.main:app     # path to FastAPI app 
HOST = 127.0.0.1         
PORT = 8000              
RELOAD = --reload        # Use --reload for development to enable hot reloading


# Targets
.PHONY: run help lint format

# Targets
run:
	uvicorn $(APP_NAME) --host $(HOST) --port $(PORT) $(RELOAD)

# Install Dependencies
install-deps:
	pip install -r requirements.txt

# Run tests
test:
	pytest

# Format the code with isort and black
# isort: orders imports
# black: code formatter. Reformats code to follow a consistent style, reducing manual formatting efforts
format:
	isort . --verbose
	black . --verbose

# Linting tool that enforces PEP 8 standards and can help identify bugs and style issues in your code.
lint:
	flake8 . --config pyproject.toml --verbose 


# Help target (default target)
help:
	@echo "Available commands:"
	@echo "  make run          - Run the app with hot reloading (development)"
	@echo "  make install-deps - Install dependencies from requirements.txt"
	@echo "  make test         - Run tests with pytest"
	@echo "  make format       - Format the code with black and isort"
	@echo "  make lint         - Run flake8 for linting"