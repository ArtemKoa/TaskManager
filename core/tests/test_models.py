import pytest
from core.models import Project, Task, Role, User, ProjectMember

@pytest.mark.django_db
def test_create_project_auto_adds_owner():
    user = User.objects.create_user(username='tester', password='pass')
    project = Project.objects.create(name='Test', created_by=user)
    # Проверяем, что владелец автоматически добавлен в ProjectMember с ролью Owner
    owner_role = Role.objects.get(name='Owner')
    member_exists = ProjectMember.objects.filter(user=user, project=project, role=owner_role).exists()
    assert member_exists

@pytest.mark.django_db
def test_task_str_method():
    user = User.objects.create_user(username='author')
    project = Project.objects.create(name='Project', created_by=user)
    task = Task.objects.create(title='My Task', project=project, author=user)
    assert str(task) == 'My Task'

@pytest.mark.django_db
def test_role_str_method():
    role = Role.objects.create(name='TestRole')
    assert str(role) == 'TestRole'