FROM python:3.11-slim

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/bot.txt

COPY common/ /app/common/
COPY services/telegram_bot_service/app/ /app/telegram_bot_service/

ENV PYTHONPATH=/app

CMD ["python", "-m", "telegram_bot_service.main"]
