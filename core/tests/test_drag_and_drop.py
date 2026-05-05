import pytest
from django.urls import reverse
from core.models import ProjectMember, Role, Project, User, Task

@pytest.mark.django_db
def test_any_member_can_change_task_status(client, user_roles):
    """TC‑4: Любой участник может менять статус задачи перетаскиванием"""
    owner_role = Role.objects.get(name='Owner')
    member_role = Role.objects.get(name='Member')
    
    owner = User.objects.create_user(username='owner', password='pass')
    member = User.objects.create_user(username='member', password='pass')
    project = Project.objects.create(name='Test', created_by=owner)
    # Владелец уже добавлен автоматически, добавляем только member
    ProjectMember.objects.create(user=member, project=project, role=member_role)
    
    task = Task.objects.create(title='Task', project=project, author=owner, status='todo')
    
    client.login(username='member', password='pass')
    url = reverse('core:update_task_status', args=[task.id])
    response = client.post(url, {'status': 'done'}, content_type='application/json')
    
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == 'done'