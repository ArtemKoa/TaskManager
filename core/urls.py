from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('project/new/', views.create_project, name='create_project'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('project/<int:project_pk>/task/new/', views.create_task, name='create_task'),
    path('task/<int:pk>/edit/', views.edit_task, name='edit_task'),
    path('task/<int:pk>/delete/', views.delete_task, name='delete_task'),
    path('task/<int:task_pk>/comment/', views.add_comment, name='add_comment'),
    path('notifications/', views.notifications, name='notifications'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='core/password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='core/password_change_done.html'), name='password_change_done'),
    path('user/<int:user_id>/', views.user_public_profile, name='user_public_profile'),
    path('task/<int:pk>/delete-attachment/<int:attachment_pk>/', views.delete_attachment, name='delete_attachment'),
    # Управление проектом
    path('project/<int:pk>/edit/', views.update_project, name='update_project'),
    path('project/<int:pk>/delete/', views.delete_project, name='delete_project'),
    # Управление участниками
    path('project/<int:pk>/members/', views.manage_members, name='manage_members'),
    path('project/<int:pk>/members/add/', views.add_member, name='add_member'),
    path('project/<int:pk>/members/<int:user_pk>/remove/', views.remove_member, name='remove_member'),
    path('project/<int:pk>/members/<int:user_pk>/change-role/', views.change_member_role, name='change_member_role'),
    #API
    path('api/task/<int:pk>/update-status/', views.update_task_status, name='update_task_status'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
