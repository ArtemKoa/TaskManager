import pytest
from django.urls import reverse
from core.models import User, Project, ProjectMember, Role, Task

# ========== Дополнительные тесты для покрытия оставшихся представлений ==========

@pytest.mark.django_db
def test_update_project_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    project = Project.objects.create(name='Old Name', created_by=owner)
    client.login(username='owner', password='pass')
    url = reverse('core:update_project', args=[project.id])
    response = client.post(url, {'name': 'New Name', 'description': 'New Desc'})
    assert response.status_code == 302  # редирект на project_detail
    project.refresh_from_db()
    assert project.name == 'New Name'

@pytest.mark.django_db
def test_delete_project_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    project = Project.objects.create(name='To Delete', created_by=owner)
    client.login(username='owner', password='pass')
    url = reverse('core:delete_project', args=[project.id])
    response = client.post(url)
    assert response.status_code == 302  # редирект на home
    assert not Project.objects.filter(id=project.id).exists()

@pytest.mark.django_db
def test_manage_members_view_accessible_for_owner(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    project = Project.objects.create(name='Project', created_by=owner)
    client.login(username='owner', password='pass')
    url = reverse('core:manage_members', args=[project.id])
    response = client.get(url)
    assert response.status_code == 200
    assert 'Участники проекта' in response.content.decode()

@pytest.mark.django_db
def test_add_member_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass', email='owner@ex.com')
    new_user = User.objects.create_user(username='new', password='pass', email='new@ex.com')
    project = Project.objects.create(name='Project', created_by=owner)
    member_role = Role.objects.get(name='Member')
    client.login(username='owner', password='pass')
    url = reverse('core:add_member', args=[project.id])
    response = client.post(url, {'email': 'new@ex.com', 'role_id': member_role.id})
    assert response.status_code == 302
    assert ProjectMember.objects.filter(project=project, user=new_user).exists()

@pytest.mark.django_db
def test_remove_member_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    member = User.objects.create_user(username='member', password='pass')
    project = Project.objects.create(name='Project', created_by=owner)
    member_role = Role.objects.get(name='Member')
    ProjectMember.objects.create(user=member, project=project, role=member_role)
    client.login(username='owner', password='pass')
    url = reverse('core:remove_member', args=[project.id, member.id])
    response = client.get(url)  # предполагается GET-запрос на удаление (или POST, смотрите реализацию)
    assert response.status_code == 302
    assert not ProjectMember.objects.filter(project=project, user=member).exists()

@pytest.mark.django_db
def test_change_member_role_view(client, user_roles):
    owner = User.objects.create_user(username='owner', password='pass')
    member = User.objects.create_user(username='member', password='pass')
    project = Project.objects.create(name='Project', created_by=owner)
    member_role = Role.objects.get(name='Member')
    admin_role = Role.objects.get(name='Admin')
    ProjectMember.objects.create(user=member, project=project, role=member_role)
    client.login(username='owner', password='pass')
    url = reverse('core:change_member_role', args=[project.id, member.id])
    response = client.post(url, {'role_id': admin_role.id})
    assert response.status_code == 302
    member_entry = ProjectMember.objects.get(project=project, user=member)
    assert member_entry.role == admin_role