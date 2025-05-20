from datetime import timezone
from django.shortcuts import get_object_or_404, redirect, render
from .models import TestSession, Question, UserAnswer, AnswerOption
from django.http import FileResponse, HttpResponseRedirect
from django.urls import reverse
from .forms import DocxUploadForm, TestSessionForm
from django.contrib import messages
from django.core.files.storage import default_storage
import tempfile
import traceback
import random
from django.utils import timezone
import csv
from django.http import HttpResponse
from .models import TestSession, UserAnswer
from django.db.models import Q
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from django.utils.timezone import localtime
from .models import Certificate
from django.core.files.base import ContentFile
import io

def generate_certificate_view(request, session_id):
    session = get_object_or_404(TestSession, id=session_id)

    if not session.passed:
        return HttpResponse("Тест не пройден. Сертификат недоступен.", status=403)

    # Проверим — уже есть сертификат?
    certificate, created = Certificate.objects.get_or_create(session=session)

    if not created and certificate.pdf:
        # Возвращаем существующий
        return FileResponse(certificate.pdf.open(), content_type='application/pdf')

    # Генерируем HTML
    html_string = render_to_string('core/certificate_template.html', {
        'session': session,
        'date': localtime(session.finished_at).strftime("%d.%m.%Y")
    })

    html = HTML(string=html_string)
    pdf_file = html.write_pdf()

    # Сохраняем в БД
    certificate.pdf.save(f"certificate_{session.id}.pdf", ContentFile(pdf_file))

    return FileResponse(certificate.pdf.open(), content_type='application/pdf')


def test_history_view(request):
    # Ищем тесты по ФИО + школе + группе + предмету из сессии
    full_name = request.session.get("full_name")
    school = request.session.get("school")
    group = request.session.get("group")
    subject = request.session.get("subject")

    if not all([full_name, school, group, subject]):
        return redirect("start_test")

    sessions = TestSession.objects.filter(
        full_name=full_name,
        school=school,
        group=group,
        subject=subject
    ).order_by("-started_at")

    return render(request, "core/test_history.html", {"sessions": sessions})

def start_test_view(request):
    if request.method == 'POST':
        form = TestSessionForm(request.POST)
        if form.is_valid():
            session = form.save()

            # ✅ Сохраняем данные участника в сессию для истории
            request.session['full_name'] = session.full_name
            request.session['school'] = session.school
            request.session['group'] = session.group
            request.session['subject'] = session.subject

            return redirect('test_page', session_id=session.id)
    else:
        form = TestSessionForm()
    return render(request, 'core/start_test.html', {'form': form})


def test_page_view(request, session_id):
    session = get_object_or_404(TestSession, id=session_id)

    # Определим, сколько секунд осталось
    if session.test.time_limit:
        time_limit_seconds = session.test.time_limit * 60
        elapsed = (timezone.now() - session.started_at).total_seconds()
        remaining = max(0, int(time_limit_seconds - elapsed))
    else:
        remaining = None

    questions = list(session.test.questions.all())
    question_count = session.test.random_question_count
    questions = random.sample(questions, min(len(questions), question_count))

    if request.method == 'POST':
        for question in questions:
            ...
        return redirect('test_result', session_id=session.id)

    return render(request, 'core/test_page.html', {
        'session': session,
        'questions': questions,
        'time_limit_seconds': remaining
    })
    
def test_result_view(request, session_id):
    session = get_object_or_404(TestSession, id=session_id)
    questions = session.test.questions.all()
    total = questions.count()
    correct = 0

    for question in questions:
        try:
            user_answer = UserAnswer.objects.get(session=session, question=question)
        except UserAnswer.DoesNotExist:
            continue

        if question.question_type in ['single', 'multiple']:
            correct_options = set(question.options.filter(is_correct=True).values_list('id', flat=True))
            user_options = set(user_answer.selected_options.values_list('id', flat=True))
            if correct_options == user_options:
                correct += 1

        elif question.question_type == 'text':
            # Текстовые ответы не проверяются автоматически
            pass

    score_percent = round((correct / total) * 100, 2) if total else 0
    passed = score_percent >= session.test.pass_score
    session.score_percent = score_percent
    session.passed = passed
    session.finished_at = timezone.now()
    session.save()

    return render(request, 'core/test_result.html', {
        'session': session,
        'correct': correct,
        'total': total,
        'score_percent': score_percent,
        'passed': passed
    })

def import_docx_view(request):
    result = {}
    if request.method == 'POST':
        form = DocxUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = form.cleaned_data['file']
                # временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_path = temp_file.name

                from .utils.docx_importer import import_test_from_docx
                test = import_test_from_docx(temp_path)

                result = {
                    'test_title': test.title,
                    'questions_count': test.questions.count()
                }
                messages.success(request, f"Импорт успешно завершён: '{test.title}', {test.questions.count()} вопрос(ов).")

            except Exception as e:
                traceback.print_exc()
                messages.error(request, f"Ошибка при импорте: {e}")
        else:
            messages.error(request, "Форма невалидна. Проверьте файл.")

    else:
        form = DocxUploadForm()

    return render(request, 'core/import_docx.html', {'form': form, 'result': result})

def export_csv_view(request, test_id):
    # Только админ может экспортировать (опционально)
    if not request.user.is_staff:
        return HttpResponse("Доступ запрещён", status=403)

    sessions = TestSession.objects.filter(test_id=test_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="results_test_{test_id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['ФИО', 'Школа', 'Группа', 'Предмет', 'Процент', 'Статус', 'Начато', 'Завершено'])

    for session in sessions:
        writer.writerow([
            session.full_name,
            session.school,
            session.group,
            session.subject,
            session.score_percent or 0,
            'Пройден' if session.passed else 'Не пройден',
            session.started_at.strftime('%Y-%m-%d %H:%M'),
            session.finished_at.strftime('%Y-%m-%d %H:%M') if session.finished_at else '-'
        ])

    return response