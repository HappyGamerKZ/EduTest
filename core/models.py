from django.db import models
from django.utils import timezone
import uuid
import os

# Типы вопросов
QUESTION_TYPES = (
    ('single', 'Один правильный ответ'),
    ('multiple', 'Несколько правильных ответов'),
    ('text', 'Свободный ввод текста'),
)

class Test(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit = models.PositiveIntegerField(help_text="Время на тест в минутах", null=True, blank=True)
    pass_score = models.PositiveIntegerField(help_text="Минимальный процент для прохождения", default=50)
    random_question_count = models.PositiveIntegerField(
        default=10,
        help_text="Сколько вопросов показывать при прохождении теста"
    )

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
