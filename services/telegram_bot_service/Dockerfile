FROM python:3.11-slim

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/bot.txt

COPY common/ /app/common/
# Copy the Python package directly so `python -m telegram_bot_service.main` works.
COPY services/telegram_bot_service/app/telegram_bot_service/ /app/telegram_bot_service/

ENV PYTHONPATH=/app

# Run as a script to avoid module-resolution issues in diverse Docker setups.
CMD ["python", "/app/telegram_bot_service/main.py"]
