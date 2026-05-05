-- Создание базы данных taskmanager
CREATE DATABASE taskmanager_db

-- =====================================================
-- Таблицы для веб-приложения TaskManager
-- =====================================================

-- 1. Пользователи (таблица auth_user, используется Django)
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE NULL
);

-- 2. Профили пользователей
CREATE TABLE user_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    avatar VARCHAR(100) NULL,
    position VARCHAR(100) NOT NULL DEFAULT '',
    experience TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 3. Роли
CREATE TABLE role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- 4. Проекты
CREATE TABLE project (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by_id INTEGER NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

-- 5. Участники проектов
CREATE TABLE project_member (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES role(id) ON DELETE RESTRICT,
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);

-- 6. Задачи
CREATE TABLE task (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'todo',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    due_date DATE NULL,
    planned_start_date DATE NULL,
    project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    author_id INTEGER NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    assignee_id INTEGER NULL REFERENCES auth_user(id) ON DELETE SET NULL
);
CREATE INDEX task_project_id_idx ON task(project_id);
CREATE INDEX task_assignee_id_idx ON task(assignee_id);
CREATE INDEX task_status_idx ON task(status);
CREATE INDEX task_due_date_idx ON task(due_date);

-- 7. Комментарии
CREATE TABLE comment (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX comment_task_id_idx ON comment(task_id);

-- 8. Уведомления
CREATE TABLE notification (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    message VARCHAR(255) NOT NULL,
    task_id INTEGER NULL REFERENCES task(id) ON DELETE CASCADE,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX notification_user_id_idx ON notification(user_id);

-- 9. Вложения к задачам
CREATE TABLE task_attachment (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    file VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL DEFAULT '',
    uploaded_by_id INTEGER NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX task_attachment_task_id_idx ON task_attachment(task_id);

-- 10. Теги
CREATE TABLE tag (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#000000'
);

-- 11. Связь задач с тегами (многие ко многим)
CREATE TABLE task_tag (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
    UNIQUE(task_id, tag_id)
);