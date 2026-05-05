import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from core.models import Project, Task, ProjectMember, Tag, Role, Comment

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'defaultpassword')
    is_active = True

class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Faker('text')
    created_by = factory.SubFactory(UserFactory)

class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"Tag {n}")
    color = "#6c757d"

class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker('text')
    status = 'todo'
    project = factory.SubFactory(ProjectFactory)
    author = factory.SubFactory(UserFactory)
    assignee = None

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Добавляет теги к задаче после её создания"""
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)

class ProjectMemberFactory(DjangoModelFactory):
    class Meta:
        model = ProjectMember

    user = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    role = factory.Iterator(Role.objects.all())

class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)
    text = factory.Faker('sentence')