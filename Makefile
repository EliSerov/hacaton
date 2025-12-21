.PHONY: up infra index run down

infra:
	docker compose up -d rabbitmq qdrant

index:
	docker compose run --rm indexer-service

run:
	docker compose up -d rag-service telegram-bot-service

up: infra index run

down:
	docker compose down -v
