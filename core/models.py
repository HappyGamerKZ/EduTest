from django.db import models
from django.utils import timezone
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

# Расширение модели пользователя
class CustomUser(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# Модель для класса (группы)
class SchoolClass(models.Model):
    name = models.CharField(max_length=50)  # Пример: "10А", "1 курс ИС-21"
    subjects = models.ManyToManyField('Subject', related_name='classes')

    def __str__(self):
        return self.name

# Модель для предмета
class Subject(models.Model):
    name = models.CharField(max_length=100)  # Пример: "Математика", "Физика", "Python"

    def __str__(self):
        return self.name


# Профиль учителя
class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject)
    classes = models.ManyToManyField(SchoolClass)

    def __str__(self):
        return self.user.username

# Профиль ученика
class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    added_by = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.user.username


# Типы вопросов
QUESTION_TYPES = (
    ('single', 'Один правильный ответ'),
    ('multiple', 'Несколько правильных ответов'),
    ('text', 'Свободный ввод текста'),
)

class Test(models.Model):
    title = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    classes = models.ManyToManyField(SchoolClass)
    created_by = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    time_limit = models.PositiveIntegerField(null=True, blank=True)
    random_question_count = models.PositiveIntegerField(default=10)
    pass_score = models.PositiveIntegerField(default=50)

    def __str__(self):
        return self.title

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    shuffle_answers = models.BooleanField(default=True)

    def __str__(self):
        return self.text

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'✔️' if self.is_correct else '❌'})"

class TestSession(models.Model):
    full_name = models.CharField(max_length=255)
    school = models.CharField(max_length=255)
    group = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    score_percent = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    shown_questions = models.ManyToManyField(Question, blank=True)

    def __str__(self):
        return f"{self.full_name[:30]} — {self.test.title}"

class UserAnswer(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(AnswerOption, blank=True)
    text_answer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ответ: {self.question.text[:50]}"

def certificate_upload_path(instance, filename):
    return f"certificates/session_{instance.session.id}/{filename}"

class Certificate(models.Model):
    session = models.OneToOneField(TestSession, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to=certificate_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"Сертификат — {self.session.full_name}"
