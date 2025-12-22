FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    build-essential cmake ninja-build \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ /app/requirements/
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir -r /app/requirements/rag.txt

COPY common/ /app/common/
COPY services/rag_service/app/rag_service/ /app/rag_service/
COPY models/ /models/

ENV PYTHONPATH=/app

CMD ["python3", "/app/rag_service/main.py"]
