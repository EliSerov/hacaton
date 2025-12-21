# Контракты сообщений (RabbitMQ RPC)

Все вызовы идут через exchange `rag.rpc` (direct).  
Бот публикует запрос с `reply_to` и `correlation_id`; RAG отвечает в `reply_to` с тем же `correlation_id`.

JSON-контракты ниже — **payload** сообщений (без AMQP properties/headers).

## Поиск (routing_key = `search`)

Запрос от бота в RAG:
```json
{
  "query": "нейросети",
  "filters": {
    "author": "Иванов",
    "date": "2024-12-01",
    "topic": "ИИ"
  }
}
```

Ответ RAG → бот:
```json
{
  "summary": "Найдено 3 статьи по нейросетям.\nИсточники: [1][2][3]",
  "articles": [
    {
      "title": "Как ИИ изменил финтех",
      "url": "https://example.com/1",
      "author": "Иванов",
      "date": "2024-12-01",
      "topic": "ИИ"
    }
  ]
}
```

Примечание: ссылки `[n]` в `summary` соответствуют элементам `articles` (1‑индексация).

## Рекомендации (routing_key = `recommend`)

Запрос:
```json
{
  "url": "https://example.com/1",
  "top_k": 5
}
```

Ответ: **тот же формат**, что и `search` (`summary + articles`).

## Тест / вопросы (routing_key = `quiz`)

Запрос:
```json
{
  "urls": ["https://example.com/1", "https://example.com/2"],
  "n_questions": 8
}
```

Ответ: **тот же формат**, что и `search` (`summary + articles`).  
Сгенерированный тест (вопросы/варианты/ответы) возвращается в поле `summary`, а `articles` используются как источники.
