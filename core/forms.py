from django import forms
from .models import Project, Task, Comment, UserProfile, Tag
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'position', 'bio', 'experience']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),   # ← ключевое изменение
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название проекта'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание проекта (необязательно)'}),
        }
        labels = {
            'name': 'Название',
            'description': 'Описание',
        }

class TaskForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Теги"
    )
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'due_date', 'planned_start_date', 'assignee', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок задачи'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Подробное описание'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'planned_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': 'Заголовок',
            'description': 'Описание',
            'status': 'Статус',
            'due_date': 'Срок выполнения',
            'planned_start_date': 'Плановая дата начала',
            'assignee': 'Исполнитель',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Напишите комментарий...'}),
        }
        labels = {
            'text': '',
        }
