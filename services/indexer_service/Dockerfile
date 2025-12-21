FROM python:3.11-slim

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/indexer.txt

COPY common/ /app/common/
COPY services/indexer_service/app/ /app/indexer_service/

ENV PYTHONPATH=/app

CMD ["python", "-m", "indexer_service.main"]
