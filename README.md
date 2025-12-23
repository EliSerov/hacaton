# Cloud.ru RAG MVP (GPU 6GB): Qdrant + FastAPI + Aiogram

## Что это
MVP AI-агента на основе RAG:
- ingest CSV статей в Qdrant (cosine similarity)
- retrieval top-k + генерация аннотированного резюме со ссылками на источники
- Telegram-бот (Aiogram) из вашего кода
- FastAPI backend (RAG API)

## Требования
- Docker + docker compose
- NVIDIA GPU 6GB (6144 MiB) и nvidia-container-toolkit

Проверка GPU:
```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi
```

## CSV
- UTF-8, разделитель `,`
- колонки: `id,title,author,platform,url,content,pub_date,subtopic`
- можно несколько файлов: положите все CSV в `./data/`

## Запуск
```bash
cp .env.example .env
# заполните BOT_TOKEN (обязательно) и при желании ALLOWED_USER_IDS / API_KEY
docker compose up --build
```

## Бот
- /start, /help, /search
- фильтры кнопками: Автор / Дата / Тема
- кнопка ✅ Выполнить поиск

## API
- GET /health
- POST /rag/search (совместим с RAGClient)
