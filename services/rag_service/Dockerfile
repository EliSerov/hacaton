FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    build-essential cmake ninja-build git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python зависимости проекта
COPY requirements/ /app/requirements/
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir -r /app/requirements/rag.txt

# === КРИТИЧЕСКИ ВАЖНО ===
# Сборка llama-cpp-python ИЗ ИСХОДНИКОВ с CUDA (cublas)
ENV LLAMA_CUBLAS=1
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
ENV FORCE_CMAKE=1

RUN pip uninstall -y llama-cpp-python || true && \
    pip install --no-cache-dir --no-binary=llama-cpp-python llama-cpp-python

# Код
COPY common/ /app/common/
COPY services/rag_service/app/rag_service/ /app/rag_service/

# Модель монтируется / копируется в /models
COPY models/ /models/

ENV PYTHONPATH=/app

CMD ["python3", "/app/rag_service/main.py"]
