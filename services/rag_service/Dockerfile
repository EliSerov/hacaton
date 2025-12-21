FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip3 install --no-cache-dir -r /app/requirements/rag.txt

COPY common/ /app/common/
COPY services/rag_service/app/ /app/rag_service/

ENV PYTHONPATH=/app

CMD ["python3", "-m", "rag_service.main"]
