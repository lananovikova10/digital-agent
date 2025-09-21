.PHONY: help install setup dev test clean docker-build docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

setup: ## Set up the project (install deps, init db)
	pip install -r requirements.txt
	cp .env.example .env
	@echo "Please edit .env file with your API keys"

dev: ## Start development environment
	docker compose up -d postgres redis
	sleep 5
	source venv/bin/activate && python scripts/init_db.py
	source venv/bin/activate && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	python -m pytest tests/ -v

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

docker-build: ## Build Docker images
	docker compose build

docker-up: ## Start all services with Docker
	docker compose up -d

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## Show Docker logs
	docker compose logs -f

run-agent: ## Run the agent manually
	python scripts/run_agent.py

init-db: ## Initialize the database
	python scripts/init_db.py

worker: ## Start Celery worker
	celery -A src.tasks.celery_app worker --loglevel=info

scheduler: ## Start Celery beat scheduler
	celery -A src.tasks.celery_app beat --loglevel=info

monitor: ## Start Celery monitoring (flower)
	celery -A src.tasks.celery_app flower