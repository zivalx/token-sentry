.PHONY: help build up down logs test clean install dev

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker containers
	docker-compose build

up: ## Start all services
	DEMO_MODE=true docker-compose up

up-build: ## Build and start all services
	DEMO_MODE=true docker-compose up --build

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

test: ## Run backend tests
	cd backend && pytest test_app.py -v

test-docker: ## Run tests in Docker
	docker-compose exec backend pytest test_app.py -v

clean: ## Remove containers, volumes, and images
	docker-compose down -v --rmi all

install-backend: ## Install backend dependencies locally
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies locally
	cd frontend && npm install

install: install-backend install-frontend ## Install all dependencies locally

dev-backend: ## Run backend in development mode
	cd backend && python app.py

dev-frontend: ## Run frontend in development mode
	cd frontend && npm run dev

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

restart: down up ## Restart all services

status: ## Show status of services
	docker-compose ps
