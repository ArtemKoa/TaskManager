import pytest
from django.contrib.auth.models import User
from pytest_factoryboy import register
from core.models import Project, Task, ProjectMember, Tag, Role
from core.tests.factories import (
    UserFactory, ProjectFactory, TaskFactory,
    ProjectMemberFactory, TagFactory
)

# Регистрируем фабрики как фикстуры для удобного использования в тестах
register(UserFactory)
register(ProjectFactory)
register(TaskFactory)
register(ProjectMemberFactory)
register(TagFactory)

@pytest.fixture
def user_roles(db):
    """Фикстура для создания стандартных ролей в базе данных"""
    roles = ['Owner', 'Admin', 'Project Manager', 'Member']
    created_roles = []
    for role_name in roles:
        role, _ = Role.objects.get_or_create(name=role_name)
        created_roles.append(role)
    return created_roles