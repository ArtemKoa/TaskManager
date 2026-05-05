import pytest
from django.urls import reverse
from core.models import ProjectMember, Role, Project, User

@pytest.mark.django_db
def test_member_cannot_manage_members(client, user_roles):
    """TC‑2: Member не может добавлять участников"""
    owner_role = Role.objects.get(name='Owner')
    member_role = Role.objects.get(name='Member')
    
    owner = User.objects.create_user(username='owner', password='pass')
    member = User.objects.create_user(username='member', password='pass')
    project = Project.objects.create(name='Test Project', created_by=owner)
    # Owner уже автоматически добавлен в ProjectMember. Добавляем только member.
    ProjectMember.objects.create(user=member, project=project, role=member_role)
    
    client.login(username='member', password='pass')
    url = reverse('core:add_member', args=[project.id])
    response = client.post(url, {'email': 'new@example.com', 'role_id': member_role.id})
    
    assert response.status_code == 302  # редирект из-за недостатка прав
    assert ProjectMember.objects.filter(project=project).count() == 2  # только owner + member