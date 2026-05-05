#!/bin/bash
set -e

# Установка зависимостей
pip install -r requirements.txt

# Сбор статических файлов
python manage.py collectstatic --noinput

# Применение миграций
python manage.py migrate

# Создание суперпользователя, если заданы переменные окружения
if [[ -n "$DJANGO_SUPERUSER_USERNAME" && -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
    python manage.py createsuperuser --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
fi

# Создание ролей
python manage.py shell -c "
from core.models import Role
for name in ['Owner', 'Admin', 'Project Manager', 'Member']:
    Role.objects.get_or_create(name=name)
"
