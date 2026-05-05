import pytest
from django.urls import reverse
from core.models import Project, User, ProjectMember, Role, Task

@pytest.mark.django_db
def test_home_redirects_to_landing_for_anonymous(client):
    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    # Проверяем по содержанию, что это лендинг
    content = response.content.decode()
    assert 'TaskManager' in content or 'Начать бесплатно' in content

@pytest.mark.django_db
def test_home_shows_projects_for_logged_in(client):
    user = User.objects.create_user(username='user', password='pass')
    project = Project.objects.create(name='User Project', created_by=user)
    client.login(username='user', password='pass')
    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'User Project' in content

@pytest.mark.django_db
def test_create_project_view(client):
    user = User.objects.create_user(username='creator', password='pass')
    client.login(username='creator', password='pass')
    url = reverse('core:create_project')
    response = client.post(url, {'name': 'New Project', 'description': 'Desc'})
    assert response.status_code == 302  # редирект на страницу проекта
    project = Project.objects.get(name='New Project')
    assert project.created_by == user

@pytest.fixture
def create_roles():
    roles = ['Owner', 'Admin', 'Project Manager', 'Member']
    created = []
    for name in roles:
        role, _ = Role.objects.get_or_create(name=name)
        created.append(role)
    return created

# ========== Дополнительные тесты для представлений ==========

@pytest.mark.django_db
def test_create_project_view(client, user_roles):
    user = User.objects.create_user(username='creator', password='pass')
    client.login(username='creator', password='pass')
    url = reverse('core:create_project')
    response = client.post(url, {'name': 'New Project', 'description': 'Desc'})
    assert response.status_code == 302  # редирект на project_detail
    project = Project.objects.get(name='New Project')
    assert project.created_by == user
    # Проверяем, что владелец добавлен в ProjectMember
    owner_role = Role.objects.get(name='Owner')
    assert ProjectMember.objects.filter(user=user, project=project, role=owner_role).exists()

@pytest.mark.django_db
def test_project_detail_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    member = User.objects.create_user(username='member', password='pass')
    project = Project.objects.create(name='Test Project', created_by=owner)
    member_role = Role.objects.get(name='Member')
    ProjectMember.objects.create(user=member, project=project, role=member_role)
    client.login(username='member', password='pass')
    url = reverse('core:project_detail', args=[project.id])
    response = client.get(url)
    assert response.status_code == 200
    assert 'Test Project' in response.content.decode()

@pytest.mark.django_db
def test_task_detail_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    member = User.objects.create_user(username='member', password='pass')
    project = Project.objects.create(name='Project', created_by=owner)
    member_role = Role.objects.get(name='Member')
    ProjectMember.objects.create(user=member, project=project, role=member_role)
    task = Task.objects.create(title='Task 1', project=project, author=owner)
    client.login(username='member', password='pass')
    url = reverse('core:task_detail', args=[task.id])
    response = client.get(url)
    assert response.status_code == 200
    assert 'Task 1' in response.content.decode()

@pytest.mark.django_db
def test_edit_task_view_get(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    project = Project.objects.create(name='Project', created_by=owner)
    task = Task.objects.create(title='Old Title', project=project, author=owner)
    client.login(username='owner', password='pass')
    url = reverse('core:edit_task', args=[task.id])
    response = client.get(url)
    assert response.status_code == 200
    assert 'Old Title' in response.content.decode()

@pytest.mark.django_db
def test_edit_task_view_post(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    project = Project.objects.create(name='Project', created_by=owner)
    task = Task.objects.create(title='Old Title', project=project, author=owner)
    client.login(username='owner', password='pass')
    url = reverse('core:edit_task', args=[task.id])
    response = client.post(url, {
        'title': 'New Title',
        'description': 'Desc',
        'status': 'done',
        'assignee': owner.id,
    })
    assert response.status_code == 302
    task.refresh_from_db()
    assert task.title == 'New Title'

@pytest.mark.django_db
def test_delete_task_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    project = Project.objects.create(name='Project', created_by=owner)
    task = Task.objects.create(title='To Delete', project=project, author=owner)
    client.login(username='owner', password='pass')
    url = reverse('core:delete_task', args=[task.id])
    response = client.post(url)
    assert response.status_code == 302  # редирект
    assert Task.objects.filter(id=task.id).count() == 0

@pytest.mark.django_db
def test_add_comment_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    project = Project.objects.create(name='Project', created_by=owner)
    task = Task.objects.create(title='Task', project=project, author=owner)
    client.login(username='owner', password='pass')
    url = reverse('core:add_comment', args=[task.id])
    response = client.post(url, {'text': 'Test comment'})
    assert response.status_code == 302
    assert task.comments.count() == 1
    assert task.comments.first().text == 'Test comment'

@pytest.mark.django_db
def test_notifications_view(client, user_roles):
    user = User.objects.create_user(username='user', password='pass')
    from core.models import Notification
    Notification.objects.create(user=user, message='Test notif')
    client.login(username='user', password='pass')
    url = reverse('core:notifications')
    response = client.get(url)
    assert response.status_code == 200
    assert 'Test notif' in response.content.decode()

@pytest.mark.django_db
def test_profile_view_get(client, user_roles):
    user = User.objects.create_user(username='user', password='pass')
    client.login(username='user', password='pass')
    url = reverse('core:profile')
    response = client.get(url)
    assert response.status_code == 200
    assert 'Мой профиль' in response.content.decode()

@pytest.mark.django_db
def test_user_public_profile_view(client, user_roles):
    user1 = User.objects.create_user(username='user1', password='pass')
    user2 = User.objects.create_user(username='user2', password='pass')
    project = Project.objects.create(name='Common Project', created_by=user1)
    ProjectMember.objects.create(user=user2, project=project, role=Role.objects.get(name='Member'))
    client.login(username='user1', password='pass')
    url = reverse('core:user_public_profile', args=[user2.id])
    response = client.get(url)
    assert response.status_code == 200
    assert 'user2' in response.content.decode()