from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator





# ----------- Личный профиль --------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")
    position = models.CharField(max_length=100, blank=True, verbose_name="Должность")
    experience = models.TextField(blank=True, verbose_name="Опыт работы")
    bio = models.TextField(blank=True, verbose_name="О себе")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Профиль {self.user.username}"

# ------------------- Справочник ролей -------------------
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name


# ------------------- Проект -------------------
class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')

    def save(self, *args, **kwargs):
        # Сначала сохраняем проект (чтобы у него появился id)
        super().save(*args, **kwargs)
        
        # Добавляем создателя как участника с ролью Owner, если ещё не добавлен
        if self.created_by:
            from .models import Role, ProjectMember  # локальный импорт, чтобы избежать циклической зависимости
            owner_role, _ = Role.objects.get_or_create(name='Owner')  # получаем роль Owner (она уже есть)
            ProjectMember.objects.get_or_create(
                user=self.created_by,
                project=self,
                defaults={'role': owner_role}
            )


# ------------------- Участник проекта -------------------
class ProjectMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships', verbose_name="Пользователь")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members', verbose_name="Проект")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, verbose_name="Роль в проекте")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата вступления")

    class Meta:
        unique_together = [['user', 'project']]
        verbose_name = "Участник проекта"
        verbose_name_plural = "Участники проектов"

    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.role.name})"

# ------------- Теги -------------------------
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")
    color = models.CharField(max_length=7, default="#6c757d", verbose_name="Цвет (HEX)")  # например, #ff0000

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


# ------------------- Задача -------------------
class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    due_date = models.DateField(null=True, blank=True, verbose_name="Срок выполнения")
    planned_start_date = models.DateField(null=True, blank=True, verbose_name="Плановая дата начала")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name="Проект")
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_tasks',
        verbose_name="Автор"
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name="Исполнитель"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks', verbose_name="Теги")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self):
        return self.title


# ------------------- Комментарий -------------------
class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name="Задача")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name="Автор")
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return f"Комментарий от {self.author.username} к задаче {self.task.title}"
    
# ------------------- Уведомления ------------------   
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)  # новое поле

    def __str__(self):
        return f"Уведомление для {self.user.username}: {self.message[:50]}"
    

# Сигнал при изменении аватара
@receiver(pre_save, sender=UserProfile)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # новый объект, пропускаем
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    old_avatar = old_instance.avatar
    new_avatar = instance.avatar
    if old_avatar and old_avatar != new_avatar:
        # удаляем старый файл
        if os.path.isfile(old_avatar.path):
            os.remove(old_avatar.path)

# Сигнал при удалении самого профиля
@receiver(post_delete, sender=UserProfile)
def delete_avatar_on_profile_delete(sender, instance, **kwargs):
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)

# -------------- Прикрепление файлов к задаче -----------------------
class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(
        upload_to='task_attachments/',
        validators=[FileExtensionValidator(allowed_extensions=['doc', 'docx', 'pdf', 'txt', 'jpg', 'png'])]
    )
    filename = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.filename
