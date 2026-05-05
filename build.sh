#!/usr/bin/env bash
# Команды для установки зависимостей
pip install -r requirements.txt

# Команда для применения миграций
python manage.py migrate