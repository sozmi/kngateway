FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только необходимые пакеты
# curl нужен для healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код (папка src)
COPY src/ /app/src/

# Указываем PYTHONPATH для корректного импорта модулей
ENV PYTHONPATH=/app

# Запускаем main.py как модуль
CMD ["python", "-m", "src.main"]