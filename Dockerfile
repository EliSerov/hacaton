FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# PyTorch CUDA wheels:
# CUDA библиотеки подтянутся pip-зависимостями nvidia-*; нужен только NVIDIA драйвер на хосте и запуск с --gpus.
RUN python -m pip install -r /app/requirements.txt

COPY app /app/app
COPY bot /app/bot
COPY docs /app/docs
COPY README.md /app/README.md

RUN mkdir -p /app/data

EXPOSE 8000
