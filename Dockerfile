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

# Healthcheck para avisar ao Traefik/Easypanel que o app está pronto
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Rodar via python main.py para garantir que as configurações do config.py (como a porta) sejam respeitadas
CMD ["python", "main.py"]
