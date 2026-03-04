FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

ENV PYTHONUNBUFFERED=1

# Desativar Heathcheck do Docker nativamente para evitar mortes súbitas do Easypanel
HEALTHCHECK NONE

# Usar formato de string (shell) para que a variável $PORT seja expandida corretamente
CMD uvicorn main:app --host 0.0.0.0 --port $PORT --loop asyncio
