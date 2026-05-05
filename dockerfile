# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости (для PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Собираем статические файлы
RUN python manage.py collectstatic --noinput

# Запускаем Gunicorn
CMD ["gunicorn", "taskmanager.wsgi:application", "--bind", "0.0.0.0:8000"]