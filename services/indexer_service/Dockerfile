FROM python:3.11-slim

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/indexer.txt

COPY common/ /app/common/
# Copy the Python package directly so `python -m indexer_service.main` works.
COPY services/indexer_service/app/indexer_service/ /app/indexer_service/

ENV PYTHONPATH=/app

# Run as a script to avoid module-resolution issues in diverse Docker setups.
CMD ["python", "/app/indexer_service/main.py"]
