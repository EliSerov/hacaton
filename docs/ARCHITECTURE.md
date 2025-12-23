# Архитектура MVP

CSV → chunking → embeddings (локально) → Qdrant → embeddings(query) → Qdrant search → контекст → локальная LLM → Telegram.

Этичность:
- саммари только по найденным источникам
- явные ссылки + авторство
- если контекста мало — сообщаем об этом
