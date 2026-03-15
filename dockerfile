FROM python:3.11-slim
WORKDIR /app

# Instalar compiladores y librerías necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requisitos y luego instalar
COPY requisitos.txt .
RUN pip install --no-cache-dir -r requisitos.txt

# Copiar todo el proyecto
COPY . .

# Comando de arranque
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080}
