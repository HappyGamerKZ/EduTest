from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    CustomUser, SchoolClass, Subject,
    TeacherProfile, StudentProfile,
    Test, Question, AnswerOption,
    TestSession, UserAnswer, Certificate
)

# ✅ Пользователи
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_teacher', 'is_student', 'is_staff')
    list_filter = ('is_teacher', 'is_student', 'is_staff')
    search_fields = ('username', 'email')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()

# ✅ Классы
@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('subjects',)

# ✅ Предметы
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# ✅ Учителя
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('subjects', 'classes')

# ✅ Ученики
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school_class', 'added_by')
    search_fields = ('user__username', 'school_class__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'teacherprofile'):
            return qs.filter(added_by=request.user.teacherprofile)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return obj.added_by.user == request.user
        return super().has_change_permission(request, obj)

# ✅ Сертификаты
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('session', 'download_link')

    def download_link(self, obj):
        if obj.pdf:
            return mark_safe(f'<a href="{obj.pdf.url}" target="_blank">📥 Скачать</a>')
        return "Нет файла"

    download_link.short_description = "Сертификат"

# ✅ Ответы на вопрос
@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('text',)

# ✅ Ответы пользователя
@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('session', 'question', 'text_answer_display', 'is_correct')
    list_filter = ('session__test', 'question__question_type')
    search_fields = ('session__full_name', 'question__text')

    def text_answer_display(self, obj):
        if obj.text_answer:
            return obj.text_answer
        return ", ".join(o.text for o in obj.selected_options.all())

    text_answer_display.short_description = "Ответ пользователя"

    def is_correct(self, obj):
        if obj.question.question_type in ['single', 'multiple']:
            correct_ids = set(obj.question.options.filter(is_correct=True).values_list('id', flat=True))
            user_ids = set(obj.selected_options.values_list('id', flat=True))
            return correct_ids == user_ids
        return "-"
    is_correct.boolean = True
    is_correct.short_description = "Правильно?"

# ✅ Inline для вопросов внутри теста
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

# ✅ Inline для вариантов ответа
class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2

# ✅ Inline для ответов внутри TestSession
class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    show_change_link = True

# ✅ Вопросы
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'test')
    inlines = [AnswerOptionInline]
    search_fields = ('text',)

# ✅ Тесты
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'time_limit', 'pass_score')
    inlines = [QuestionInline]
    search_fields = ('title',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'teacherprofile'):
            return qs.filter(created_by=request.user.teacherprofile)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return obj.created_by.user == request.user
        return super().has_change_permission(request, obj)

# ✅ Сессии тестов
@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'test', 'score_percent', 'passed', 'started_at', 'finished_at')
    inlines = [UserAnswerInline]
    list_filter = ('test', 'passed')
    search_fields = ('full_name', 'school', 'group', 'subject')