from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Test, Question, AnswerOption, TestSession, UserAnswer, Certificate

# ✅ Сертификаты
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('session', 'download_link')

    def download_link(self, obj):
        if obj.pdf:
            return mark_safe(f'<a href="{obj.pdf.url}" target="_blank">📥 Скачать</a>')
        return "Нет файла"

    download_link.short_description = "Сертификат"

# ✅ Ответы на вопрос (AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('text',)

# ✅ Ответы пользователя (UserAnswer)
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

# ✅ Inline для вариантов ответа внутри вопроса
class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2

# ✅ Inline для ответов пользователя внутри TestSession
class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    show_change_link = True

# ✅ Админка для вопросов
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'test')
    inlines = [AnswerOptionInline]
    search_fields = ('text',)

# ✅ Админка для тестов
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'time_limit', 'pass_score')
    inlines = [QuestionInline]
    search_fields = ('title',)

# ✅ Админка для сессий тестов
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'test', 'score_percent', 'passed', 'started_at', 'finished_at')
    inlines = [UserAnswerInline]
    list_filter = ('test', 'passed')
    search_fields = ('full_name', 'school', 'group', 'subject')

# 📌 Регистрация всех моделей
admin.site.register(Test, TestAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AnswerOption, AnswerOptionAdmin)
admin.site.register(TestSession, TestSessionAdmin)
admin.site.register(UserAnswer, UserAnswerAdmin)
admin.site.register(Certificate, CertificateAdmin)
