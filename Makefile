.PHONY: help dev build test clean install docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pnpm install

dev: ## Start development servers
	pnpm dev

build: ## Build all services
	pnpm build

test: ## Run tests
	pnpm test

lint: ## Lint code
	pnpm lint

format: ## Format code
	pnpm format

clean: ## Clean build artifacts
	pnpm clean
	rm -rf node_modules
	rm -rf apps/*/node_modules
	rm -rf packages/*/node_modules

docker-up: ## Start Docker services
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-rebuild: ## Rebuild and restart Docker services
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

db-migrate: ## Run database migrations
	pnpm db:migrate

db-seed: ## Seed database
	pnpm db:seed

db-reset: ## Reset database
	pnpm db:reset

generate-types: ## Generate TypeScript types
	pnpm generate:types

generate-api: ## Generate API client
	pnpm generate:api

# Go service commands
go-test-gateway: ## Test API Gateway
	cd apps/api-gateway && go test -v ./...

go-test-notification: ## Test Notification Service
	cd apps/notification-service && go test -v ./...

go-fmt: ## Format Go code
	cd apps/api-gateway && gofmt -w .
	cd apps/notification-service && gofmt -w .

# Python service commands
py-test-core: ## Test Core Service
	cd apps/core-service && pytest -v

py-test-ai: ## Test AI Service
	cd apps/ai-service && pytest -v

py-lint-core: ## Lint Core Service
	cd apps/core-service && black . && isort . && mypy . && ruff check .

py-lint-ai: ## Lint AI Service
	cd apps/ai-service && black . && isort . && mypy . && ruff check .
