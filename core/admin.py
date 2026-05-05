from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Project, ProjectMember, Task, Comment, Role, Tag

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'created_by')

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'project', 'role', 'joined_at')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'due_date', 'project', 'assignee')
    list_filter = ('status', 'project', 'tags')
    filter_horizontal = ('tags',)   # это добавит удобный виджет

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'author', 'created_at')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)