from django import template
from core.models import ProjectMember

register = template.Library()

@register.filter
def get_role(user, project):
    try:
        member = ProjectMember.objects.get(user=user, project=project)
        return member.role.name
    except ProjectMember.DoesNotExist:
        return ''