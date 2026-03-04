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

# Rodar via python main.py para garantir que as configurações do config.py (como a porta) sejam respeitadas
CMD ["python", "main.py"]
