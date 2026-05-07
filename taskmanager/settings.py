import os
from pathlib import Path
import dj_database_url

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Безопасность: секретный ключ берётся из переменной окружения
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("Переменная окружения SECRET_KEY не задана!")

# Режим отладки – из переменной окружения (локально True, на сервере False)
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Разрешённые хосты – обязательны для Render
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',      # разрешает все поддомены render.com
]

# База данных – читаем DATABASE_URL (на Render она задаётся автоматически)
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',   # для локальной разработки без PostgreSQL
        conn_max_age=600,
        ssl_require=not DEBUG             # на сервере требуем SSL
    )
}

# Приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

# Middleware (whitenoise для статики)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # важна для статики на Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'taskmanager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.unread_notifications',
                'core.context_processors.user_profile',
            ],
        },
    },
]

WSGI_APPLICATION = 'taskmanager.wsgi.application'

# Аутентификация
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Интернационализация
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Статические файлы (CSS, JS)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Медиафайлы (загруженные пользователем)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Перенаправления после логина
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
