# Tech Media RAG MVP (Cloud.ru)

MVP AI-агента для интеллектуального поиска и анализа статей технологических СМИ на базе **RAG**.

## Возможности (MVP)
- Поиск статей по запросу (**RAG**): эмбеддинги запроса → поиск ближайших документов в **Qdrant** → генерация ответа.
- Краткое **аннотационное резюме** с **ссылками на источники** (цитирование вида `[1][2]...`, где `[n]` соответствует `articles[n-1]`).
- Фильтры: **автор**, **дата**, **тематика** (topic = `subtopic` из CSV).
- Доп. функции:
  - рекомендации похожих публикаций;
  - генерация вопросов/мини-теста по найденным материалам.
- Интерфейс: **Telegram-бот**.
- Безопасность: аутентификация/авторизация (Telegram user_id + allowlist), service-to-service API key через AMQP headers, логирование с trace_id.

## Архитектура
Сервисы:
1. `telegram-bot-service` — UI/диалоги Telegram, хранение фильтров, RPC-запросы в RAG.
2. `rag-service` — один процесс (один CUDA-контекст): retrieval в Qdrant + LLM summary/quiz/recommend.
3. `indexer-service` — батч-индексация CSV → чанки → эмбеддинги → upsert в Qdrant.

Транспорт: **RabbitMQ** (RPC поверх AMQP). Хранилище векторов: **Qdrant**.

Подробности: см. `docs/ARCHITECTURE.md`.

## Быстрый старт (Docker)
### 0) Подготовьте модель (локально)
Проект ожидает локальный **GGUF**-файл LLM в каталоге `./models/`.

По умолчанию (см. `.env.example`) путь:
- `./models/model.gguf`

> Примечание: модель в репозиторий не включена из-за размера.

### 1) Настройте переменные окружения
Скопируйте:
```bash
cp .env.example .env
```
Заполните:
- `TELEGRAM_BOT_TOKEN`
- `SERVICE_API_KEY` (общий секрет для bot → rag)
- при необходимости: `ALLOWED_TELEGRAM_IDS` (CSV-список id), либо оставьте пустым для режима “без allowlist”.

### 2) Запустите инфраструктуру
```bash
docker compose up -d rabbitmq qdrant
```

### 3) Индексация CSV
Положите ваши CSV в `./data/` (можно несколько файлов).

Запустите индексатор:
```bash
docker compose run --rm indexer-service
```

### 4) Запуск RAG и бота
```bash
docker compose up -d rag-service telegram-bot-service
```

## Использование в Telegram
- Пишите обычным текстом — это `query`.
- Фильтры:
  - `/filters` — показать текущие фильтры
  - `/set_author Иванов`
  - `/set_date 2024-12-01`
  - `/set_topic ИИ`
  - `/clear_filters`

Доп. функции:
- `/recommend` — рекомендации похожих статей по последнему запросу
- `/quiz` — мини-тест по последнему результату

## Материалы
- Презентация: `docs/presentation.pptx`
- Архитектура: `docs/ARCHITECTURE.md`
- Шаги создания: `docs/BUILD_STEPS.md`
- Руководство по развёртыванию: `docs/DEPLOYMENT.md`
- План развития: `docs/ROADMAP.md`

## Лицензия
MIT (см. `LICENSE`).
