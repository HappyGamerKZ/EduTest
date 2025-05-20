from django.contrib import admin
from .models import Test, Question, AnswerOption, TestSession, UserAnswer
from .models import Certificate

class CertificateAdmin(admin.ModelAdmin):
    list_display = ('session', 'download_link')

    def download_link(self, obj):
        if obj.pdf:
            return f'<a href="{obj.pdf.url}" target="_blank">📥 Скачать</a>'
        return "Нет файла"

    download_link.allow_tags = True
    download_link.short_description = "Сертификат"

class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'test')
    inlines = [AnswerOptionInline]

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'time_limit', 'pass_score')
    inlines = [QuestionInline]

# ✅ Правильный Inline — отображение UserAnswer напрямую
class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    show_change_link = True

class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'test', 'score_percent', 'passed', 'started_at', 'finished_at')
    inlines = [UserAnswerInline]

class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('session', 'question', 'text_answer_display')

    def text_answer_display(self, obj):
        if obj.text_answer:
            return obj.text_answer
        return ", ".join(o.text for o in obj.selected_options.all())

    text_answer_display.short_description = "Ответ пользователя"

admin.site.register(UserAnswer, UserAnswerAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AnswerOption)
admin.site.register(TestSession, TestSessionAdmin)
admin.site.register(Certificate, CertificateAdmin)
