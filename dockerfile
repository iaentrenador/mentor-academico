# Imagen base ligera de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos
COPY requisitos.txt .

# Instalar dependencias sin cache
RUN pip install --no-cache-dir -r requisitos.txt

# Copiar el resto del proyecto
COPY . .

# Puerto por defecto de Render
ENV PORT=10000

# Comando para ejecutar la app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
