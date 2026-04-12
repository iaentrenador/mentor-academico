FROM python:3.11-slim

# Instalar dependencias necesarias para compilar psycopg2 y otras extensiones de C
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Render asigna el puerto en la variable $PORT. 
# Usamos la sintaxis de "shell form" (sin corchetes) para que 
# la variable de entorno sea interpretada correctamente.
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
