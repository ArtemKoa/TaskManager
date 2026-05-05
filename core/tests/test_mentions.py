import pytest
from django.urls import reverse
from core.models import Notification, ProjectMember, Role, Project, User, Task

@pytest.mark.django_db
def test_mention_creates_notification(client, user_roles):
    """TC‑5: @упоминание в комментарии создаёт уведомление"""
    member_role = Role.objects.get(name='Member')
    
    author = User.objects.create_user(username='author', password='pass')
    mentioned = User.objects.create_user(username='mentioned', password='pass')
    project = Project.objects.create(name='Test', created_by=author)
    # Владелец (author) уже участник, добавляем mentioned
    ProjectMember.objects.create(user=mentioned, project=project, role=member_role)
    
    task = Task.objects.create(title='Task', project=project, author=author)
    
    client.login(username='author', password='pass')
    url = reverse('core:add_comment', args=[task.id])
    response = client.post(url, {'text': 'Hello @mentioned'})
    
    assert Notification.objects.filter(user=mentioned, is_read=False).exists()