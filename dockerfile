FROM python:3.11-slim
WORKDIR /app
COPY requisitos.txt .
RUN pip install --no-cache-dir -r requisitos.txt
COPY . .
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080}
