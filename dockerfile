# Usar una imagen aún más ligera basada en Debian Bullseye/Bookworm slim
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc (ahorra espacio)
ENV PYTHONDONTWRITEBYTECODE=1
# Evitar que Python almacene buffers (esencial para ver logs en tiempo real en Render)
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias solo para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos
COPY requisitos.txt .

# Instalar dependencias sin cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requisitos.txt

# Copiar el resto del proyecto
COPY . .

# Puerto por defecto de Render
ENV PORT=10000

# Comando para ejecutar la app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "2", "--timeout", "120"]
