.PHONY: help install test lint format clean run seed docker-build docker-run

help: ## Show this help message
	@echo "BandMate - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e .

test: ## Run tests
	pytest tests/ -v --cov=app --cov-report=term-missing

test-watch: ## Run tests in watch mode
	pytest tests/ -v --cov=app --cov-report=term-missing -f

lint: ## Run linting checks
	black --check --diff .
	isort --check-only --diff .
	flake8 .

format: ## Format code with black and isort
	black .
	isort .

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "instance" -exec rm -rf {} +
	rm -f bandmate.db

run: ## Run the development server
	export FLASK_APP=manage.py && export FLASK_ENV=development && flask run

seed: ## Seed the database with demo data
	python manage.py seed

db-init: ## Initialize database tables
	python manage.py create-tables

db-reset: ## Reset database (drop all tables and recreate)
	python manage.py reset

docker-build: ## Build Docker image
	docker build -t bandmate .

docker-run: ## Run Docker container
	docker run -p 5000:5000 --env-file .env bandmate

docker-compose-up: ## Start with Docker Compose
	docker-compose up --build

docker-compose-down: ## Stop Docker Compose
	docker-compose down

ci: ## Run CI checks locally
	black --check --diff .
	isort --check-only --diff .
	flake8 .
	pytest tests/ -v --cov=app --cov-report=term-missing

setup: ## Initial setup for development
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/python manage.py create-tables
	.venv/bin/python manage.py seed
	@echo "Setup complete! Activate with: source .venv/bin/activate"

deploy-check: ## Check deployment readiness
	@echo "Checking deployment readiness..."
	@python -c "import app; print('✅ App imports successfully')"
	@python -c "from app import create_app; app = create_app(); print('✅ App factory works')"
	@echo "✅ Ready for deployment!"
