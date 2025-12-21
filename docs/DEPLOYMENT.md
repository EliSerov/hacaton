# Руководство по развёртыванию

## Требования
- Docker + Docker Compose
- (опционально) NVIDIA GPU + nvidia-container-toolkit для ускорения LLM

## Подготовка
1) Скопируйте `.env.example` → `.env` и заполните значения.
2) Положите LLM GGUF в `./models/model.gguf` (или измените `LLM_MODEL_PATH`).

## Запуск
```bash
docker compose up -d rabbitmq qdrant
docker compose run --rm indexer-service
docker compose up -d rag-service telegram-bot-service
```

## Проверка
- RabbitMQ UI: http://localhost:15672 (admin/admin)
- Qdrant: http://localhost:6333

## Типичные проблемы
- **LLM file not found**: проверьте `LLM_MODEL_PATH` и volume `./models:/models:ro`.
- **OOM на 8GB VRAM**: уменьшите `LLM_N_GPU_LAYERS`, `LLM_N_CTX`, `LLM_MAX_TOKENS`.
- **Ничего не найдено**: убедитесь, что indexer загрузил данные в Qdrant и что фильтры корректны.
