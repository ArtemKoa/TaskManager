from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Project, Task, Comment, ProjectMember, Role, Notification, UserProfile, TaskAttachment, Tag
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import re
from .forms import CustomUserCreationForm, UserProfileForm, UserEditForm, TaskForm, CommentForm, ProjectForm
import os


def search_users(request):
    query = request.GET.get('q', '')
    project_id = request.GET.get('project_id')
    if not query or not project_id:
        return JsonResponse([], safe=False)
    project = get_object_or_404(Project, id=project_id)
    existing_users = ProjectMember.objects.filter(project=project).values_list('user_id', flat=True)
    users = User.objects.filter(username__icontains=query).exclude(id__in=existing_users).exclude(id=request.user.id)[:10]
    # Дополнительно поиск по email (если email совпадает, тоже добавить в результаты, но избегая дубликатов)
    email_users = User.objects.filter(email__icontains=query).exclude(id__in=existing_users).exclude(id=request.user.id).exclude(id__in=[u.id for u in users])[:10]
    users = list(users) + list(email_users)
    data = [{'id': u.id, 'username': u.username, 'email': u.email} for u in users]
    return JsonResponse(data, safe=False)

@login_required
def invite_member(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if get_user_role_in_project(request.user, project) not in ['Owner', 'Admin']:
        return redirect('core:project_detail', pk=project.pk)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        invited_user = get_object_or_404(User, pk=user_id)
        # Проверяем, не состоит ли уже в проекте
        if not ProjectMember.objects.filter(user=invited_user, project=project).exists():
            # Создаём уведомление-приглашение
            Notification.objects.create(
                user=invited_user,
                message=f'Приглашение в проект "{project.name}". Нажмите "Принять", чтобы присоединиться.',
                project=project,
                is_read=False
            )
    return redirect('core:manage_members', pk=project.pk)


@login_required
def leave_project(request, pk):
    """Выход из проекта"""
    project = get_object_or_404(Project, pk=pk)
    membership = ProjectMember.objects.filter(user=request.user, project=project).first()
    if membership and membership.role.name != 'Owner':
        membership.delete()
    return redirect('core:home')


# Главная страница (список проектов пользователя)
def home(request):
    if request.user.is_authenticated:
        projects = Project.objects.filter(members__user=request.user)
        return render(request, 'core/project_list.html', {'projects': projects})
    else:
        return render(request, 'core/landing.html')

#----------------- Личный профиль пользователя ---------------------------
@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            # удаление аватара
            if request.POST.get('avatar-clear') == 'on':
                if profile.avatar:
                    avatar_path = profile.avatar.path
                    if os.path.isfile(avatar_path):
                        os.remove(avatar_path)
                    profile.avatar = None
            user_form.save()
            profile_form.save()
            return redirect('core:profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    return render(request, 'core/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_profile': profile,
    })


# ------------- Публичный просмотр профиля пользователя -------------
def user_public_profile(request, user_id):
    """Публичный просмотр профиля другого пользователя"""
    target_user = get_object_or_404(User, id=user_id)
    # Проверяем, имеют ли текущий пользователь и целевой общий проект
    common_projects = Project.objects.filter(
        members__user=request.user
    ).filter(
        members__user=target_user
    )
    if not common_projects.exists() and request.user != target_user:
        # Если нет общих проектов и это не сам пользователь – доступ запрещён
        return render(request, 'core/access_denied.html', {'message': 'У вас нет прав для просмотра этого профиля.'})
    
    try:
        profile = target_user.profile
    except UserProfile.DoesNotExist:
        profile = None
    
    return render(request, 'core/user_public_profile.html', {
        'target_user': target_user,
        'profile': profile,
    })


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('core:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

# Функция получения роли пользователя в проекте
def get_user_role_in_project(user, project):
    try:
        member = ProjectMember.objects.get(user=user, project=project)
        return member.role.name
    except ProjectMember.DoesNotExist:
        return None

# Проверка, может ли пользователь редактировать задачу (изменять/удалять)
def can_edit_task(user, task):
    role = get_user_role_in_project(user, task.project)
    return role in ['Owner', 'Admin', 'Project Manager']

# Проверка, может ли пользователь удалить проект
def can_delete_project(user, project):
    role = get_user_role_in_project(user, project)
    return role == 'Owner'

# Проверка, может ли пользователь управлять участниками (добавлять/удалять)
def can_manage_members(user, project):
    role = get_user_role_in_project(user, project)
    return role in ['Owner', 'Admin']

def can_create_task(user, project):
    role = get_user_role_in_project(user, project)
    return role in ['Owner', 'Admin', 'Project Manager']


# Создание проекта
@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()    # здесь уже автоматически добавится Owner в ProjectMember
            return redirect('core:project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'core/project_form.html', {'form': form, 'title': 'Создать проект'})


# Детали проекта (список задач)
@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not ProjectMember.objects.filter(user=request.user, project=project).exists():
        return redirect('core:home')
    tasks = project.tasks.all()
    
    # Фильтр по тегу
    tag_id = request.GET.get('tag')
    if tag_id:
        tasks = tasks.filter(tags__id=tag_id)
    
    # Уникальные теги, используемые в задачах этого проекта
    project_tags = Tag.objects.filter(tasks__project=project).distinct()
    
    return render(request, 'core/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'project_tags': project_tags,
        'selected_tag': tag_id
    })

# Создание задачи в проекте
@login_required
def create_task(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not can_create_task(request.user, project):
        return redirect('core:project_detail', pk=project.pk)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.author = request.user
            task.save()
            form.save_m2m()   # сохраняем ManyToMany (теги)
            return redirect('core:project_detail', pk=project.pk)
    else:
        form = TaskForm()
        form.fields['assignee'].queryset = User.objects.filter(project_memberships__project=project)
    return render(request, 'core/task_form.html', {'form': form, 'title': 'Новая задача'})

# Редактирование задач
@login_required
def edit_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_edit_task(request.user, task):
        return redirect('core:project_detail', pk=task.project.pk)
    old_assignee = task.assignee
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()
            if updated_task.assignee != old_assignee and updated_task.assignee:
                Notification.objects.create(
                    user=updated_task.assignee,
                    message=f'Вас назначили исполнителем задачи "{updated_task.title}" в проекте "{updated_task.project.name}".',
                    task=updated_task,
                )
            return redirect('core:project_detail', pk=task.project.pk)
    else:
        form = TaskForm(instance=task)
        form.fields['assignee'].queryset = User.objects.filter(project_memberships__project=task.project)
    return render(request, 'core/task_form.html', {'form': form, 'title': 'Редактировать задачу'})

# Удаление задачи
@login_required
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_edit_task(request.user, task):
        return redirect('core:project_detail', pk=task.project.pk)
    project = task.project
    if not ProjectMember.objects.filter(user=request.user, project=project).exists():
        return redirect('core:home')
    if request.method == 'POST':
        task.delete()
        return redirect('core:project_detail', pk=project.pk)
    return render(request, 'core/task_confirm_delete.html', {'task': task})

# Добавление комментария
@login_required
def add_comment(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not ProjectMember.objects.filter(user=request.user, project=task.project).exists():
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            
            # --- Обработка упоминаний ---
            text = comment.text
            # Находим все вхождения @username
            mentioned_usernames = re.findall(r'@(\w+)', text)
            for username in mentioned_usernames:
                try:
                    mentioned_user = User.objects.get(username=username)
                    # Не отправляем уведомление самому себе
                    if mentioned_user != request.user:
                        Notification.objects.create(
                            user=mentioned_user,
                            message=f'{request.user.username} упомянул вас в комментарии к задаче "{task.title}"',
                            task=task,
                            is_read=False
                        )
                except User.DoesNotExist:
                    pass  # игнорируем несуществующих пользователей
            # ----------------------------
            
    return redirect('core:project_detail', pk=task.project.pk)

@require_POST
def update_task_status(request, pk):
    try:
        task = Task.objects.get(pk=pk)
        # Проверяем, является ли пользователь участником проекта (любая роль)
        if not ProjectMember.objects.filter(user=request.user, project=task.project).exists():
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status not in ['todo', 'in_progress', 'done']:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        task.status = new_status
        task.save()
        return JsonResponse({'success': True})
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)



@login_required
def notifications(request):
    notifications = request.user.notifications.order_by('-created_at')
    # Отмечаем все как прочитанные (по желанию)
    notifications.update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifications})


@login_required

def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not ProjectMember.objects.filter(user=request.user, project=task.project).exists():
        return redirect('core:home')
    
    role = get_user_role_in_project(request.user, task.project)
    is_assignee = (task.assignee == request.user)
    
    # Право на загрузку файлов: высокая роль ИЛИ исполнитель
    can_upload = role in ['Owner', 'Admin', 'Project Manager'] or is_assignee
    
    if request.method == 'POST' and 'upload_files' in request.POST:
        if can_upload:
            files = request.FILES.getlist('files')
            for f in files:
                TaskAttachment.objects.create(
                    task=task,
                    file=f,
                    filename=f.name,
                    uploaded_by=request.user
                )
        return redirect('core:task_detail', pk=task.pk)
    
    return render(request, 'core/task_detail.html', {
        'task': task,
        'can_upload': can_upload,
        'can_delete_attachment': can_upload,  # право на удаление то же
    })

@login_required
def delete_attachment(request, pk, attachment_pk):
    attachment = get_object_or_404(TaskAttachment, pk=attachment_pk, task__pk=pk)
    task = attachment.task
    if not ProjectMember.objects.filter(user=request.user, project=task.project).exists():
        return redirect('core:home')
    
    role = get_user_role_in_project(request.user, task.project)
    is_assignee = (task.assignee == request.user)
    can_delete = role in ['Owner', 'Admin', 'Project Manager'] or is_assignee
    
    if can_delete:
        if attachment.file:
            attachment.file.delete()
        attachment.delete()
    return redirect('core:task_detail', pk=pk)

# ------------------- Управление проектом -------------------

@login_required
def update_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    # Только Owner или Admin могут редактировать проект
    role = get_user_role_in_project(request.user, project)
    if role not in ['Owner', 'Admin']:
        return redirect('core:project_detail', pk=project.pk)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('core:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'core/project_form.html', {'form': form, 'title': 'Редактировать проект'})

@login_required
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    # Только Owner может удалить проект
    role = get_user_role_in_project(request.user, project)
    if role != 'Owner':
        return redirect('core:project_detail', pk=project.pk)
    
    if request.method == 'POST':
        project.delete()
        return redirect('core:home')
    return render(request, 'core/project_confirm_delete.html', {'project': project})

# ------------------- Управление участниками -------------------

@login_required
def manage_members(request, pk):
    project = get_object_or_404(Project, pk=pk)
    role = get_user_role_in_project(request.user, project)
    if role not in ['Owner', 'Admin']:
        return redirect('core:project_detail', pk=project.pk)
    
    members = ProjectMember.objects.filter(project=project).select_related('user', 'role')
    # Все роли для выпадающего списка
    all_roles = Role.objects.all()
    
    return render(request, 'core/manage_members.html', {
        'project': project,
        'members': members,
        'all_roles': all_roles,
    })

@login_required
def add_member(request, pk):
    project = get_object_or_404(Project, pk=pk)
    role = get_user_role_in_project(request.user, project)
    if role not in ['Owner', 'Admin']:
        return redirect('core:project_detail', pk=project.pk)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        role_id = request.POST.get('role_id')
        try:
            user = User.objects.get(email=email)
            new_role = Role.objects.get(pk=role_id)
            # Проверяем, не состоит ли уже
            obj, created = ProjectMember.objects.get_or_create(
                user=user,
                project=project,
                defaults={'role': new_role}
            )
            if not created:
                # Если уже есть, можно обновить роль
                obj.role = new_role
                obj.save()
            return redirect('core:manage_members', pk=project.pk)
        except User.DoesNotExist:
            # Упрощённо: показываем ошибку
            return render(request, 'core/manage_members.html', {
                'project': project,
                'members': ProjectMember.objects.filter(project=project),
                'all_roles': Role.objects.all(),
                'error': f'Пользователь с email {email} не найден.'
            })
    return redirect('core:manage_members', pk=project.pk)

@login_required
def remove_member(request, pk, user_pk):
    project = get_object_or_404(Project, pk=pk)
    role = get_user_role_in_project(request.user, project)
    if role not in ['Owner', 'Admin']:
        return redirect('core:project_detail', pk=project.pk)
    
    # Нельзя удалить самого себя (владельца)
    if request.user.pk == user_pk:
        # Можно запретить, но можно и разрешить — тогда пользователь выйдет из проекта
        pass
    
    ProjectMember.objects.filter(project=project, user__pk=user_pk).delete()
    return redirect('core:manage_members', pk=project.pk)

@login_required
def change_member_role(request, pk, user_pk):
    project = get_object_or_404(Project, pk=pk)
    role = get_user_role_in_project(request.user, project)
    if role not in ['Owner', 'Admin']:
        return redirect('core:project_detail', pk=project.pk)
    
    if request.method == 'POST':
        new_role_id = request.POST.get('role_id')
        try:
            new_role = Role.objects.get(pk=new_role_id)
            member = ProjectMember.objects.get(project=project, user__pk=user_pk)
            # Владельца может менять только он сам или другой владелец - упростим: не менять роль Owner
            if member.role.name == 'Owner' and request.user != member.user:
                pass  # нельзя сменить владельца, если ты не он
            else:
                member.role = new_role
                member.save()
        except (Role.DoesNotExist, ProjectMember.DoesNotExist):
            pass
    return redirect('core:manage_members', pk=project.pk)


@login_required
def accept_invitation(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    if notification.project:
        project = notification.project
        # Проверяем, не состоит ли уже в проекте
        if not ProjectMember.objects.filter(user=request.user, project=project).exists():
            member_role = Role.objects.get(name='Member')
            ProjectMember.objects.create(user=request.user, project=project, role=member_role)
        notification.delete()  # удаляем уведомление после принятия
    return redirect('core:notifications')

@login_required
def decline_invitation(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    # Просто удаляем уведомление
    notification.delete()
    return redirect('core:notifications')
