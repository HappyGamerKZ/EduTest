import csv
import random
import tempfile
import traceback
from django.core.files.base import ContentFile

from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import localtime
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test

from weasyprint import HTML
from django.forms import ModelForm, modelformset_factory
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')

from .models import (
    CustomUser, StudentProfile, SchoolClass,
    Test, Question, AnswerOption,
    TestSession, UserAnswer, Certificate
)

from .forms import (
    StudentCreationForm, TestCreationForm,
    QuestionForm, AnswerOptionFormSet,
    DocxUploadForm, TestSessionForm
)

@login_required
@user_passes_test(lambda u: u.is_teacher)
def edit_questions(request, test_id):
    teacher = request.user.teacherprofile
    test = get_object_or_404(Test, id=test_id, created_by=teacher)
    questions = test.questions.all()

    QuestionFormSet = modelformset_factory(Question, form=QuestionForm, extra=1, can_delete=True)

    if request.method == 'POST':
        q_formset = QuestionFormSet(request.POST, queryset=questions, prefix='questions')

        if q_formset.is_valid():
            instances = q_formset.save(commit=False)
            for obj in q_formset.deleted_objects:
                obj.delete()
            for q in instances:
                q.test = test
                q.save()
            q_formset.save_m2m()
            return redirect('teacher_dashboard')
    else:
        q_formset = QuestionFormSet(queryset=questions, prefix='questions')

    return render(request, 'core/edit_questions.html', {
        'formset': q_formset,
        'test': test
    })

@login_required
@user_passes_test(lambda u: u.is_teacher)
def edit_test(request, test_id):
    teacher_profile = request.user.teacherprofile
    test = get_object_or_404(Test, id=test_id, created_by=teacher_profile)

    if request.method == 'POST':
        form = TestCreationForm(request.POST, instance=test, teacher=teacher_profile)
        if form.is_valid():
            form.save()
            return redirect('teacher_dashboard')
    else:
        form = TestCreationForm(instance=test, teacher=teacher_profile)

    return render(request, 'core/edit_test.html', {'form': form, 'test': test})

@login_required
@user_passes_test(lambda u: u.is_teacher)
def teacher_results_view(request):
    teacher = request.user.teacherprofile
    tests = teacher.test_set.all()
    sessions = TestSession.objects.filter(test__in=tests).order_by('-started_at')

    return render(request, 'core/teacher_results.html', {
        'sessions': sessions,
    })

@login_required
@user_passes_test(lambda u: u.is_student)
def test_history(request):
    sessions = TestSession.objects.filter(full_name=request.user.username).order_by('-started_at')
    return render(request, 'core/test_history.html', {'sessions': sessions})

@login_required
@user_passes_test(lambda u: u.is_student)
def start_test(request, test_id):
    profile = request.user.studentprofile
    test = get_object_or_404(Test, id=test_id, classes=profile.school_class)

    # Уже проходил?
    existing = TestSession.objects.filter(
        test=test,
        full_name=request.user.username,
        group=profile.school_class.name,
        subject=test.subject.name
    ).first()
    if existing:
        return redirect('test_result', session_id=existing.id)

    # Создание новой сессии
    session = TestSession.objects.create(
        test=test,
        full_name=request.user.username,
        school='',  # можно добавить school из профиля
        group=profile.school_class.name,
        subject=test.subject.name,
        started_at=timezone.now()
    )

    # Отбор вопросов и сохранение их в сессию
    questions = list(test.questions.all())
    if test.random_question_count and len(questions) > test.random_question_count:
        questions = random.sample(questions, test.random_question_count)

    request.session[f'shown_questions_{session.id}'] = [q.id for q in questions]
    request.session[f'current_q_{session.id}'] = 0

    return redirect('test_page', session_id=session.id)



@login_required
@user_passes_test(lambda u: u.is_teacher)
def add_question(request, test_id):
    from .models import Test
    test = Test.objects.get(id=test_id)

    if test.created_by.user != request.user:
        return redirect('teacher_dashboard')  # защита

    if request.method == 'POST':
        q_form = QuestionForm(request.POST)
        formset = AnswerOptionFormSet(request.POST)

        if q_form.is_valid():
            question = q_form.save(commit=False)
            question.test = test
            question.save()

            formset = AnswerOptionFormSet(request.POST, instance=question)
            if formset.is_valid():
                formset.save()
                return redirect('add_question', test_id=test.id)
    else:
        q_form = QuestionForm()
        formset = AnswerOptionFormSet()

    return render(request, 'core/add_question.html', {
        'q_form': q_form,
        'formset': formset,
        'test': test,
    })

@login_required
@user_passes_test(lambda u: u.is_teacher)
def create_test(request):
    teacher_profile = request.user.teacherprofile

    if request.method == 'POST':
        form = TestCreationForm(request.POST, teacher=teacher_profile)
        if form.is_valid():
            test = form.save(commit=False)
            test.created_by = teacher_profile
            test.save()
            form.save_m2m()
            return redirect('teacher_dashboard')
    else:
        form = TestCreationForm(teacher=teacher_profile)

    return render(request, 'core/create_test.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_teacher)
def add_student(request):
    teacher_profile = request.user.teacherprofile

    if request.method == 'POST':
        form = StudentCreationForm(request.POST, teacher=teacher_profile)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_student = True
            user.save()

            # Привязываем к учителю и классу
            school_class = form.cleaned_data['school_class']
            StudentProfile.objects.create(
                user=user,
                school_class=school_class,
                added_by=teacher_profile
            )

            return redirect('teacher_dashboard')
    else:
        form = StudentCreationForm(teacher=teacher_profile)

    return render(request, 'core/add_student.html', {'form': form})

# Проверки ролей
def is_teacher(user):
    return user.is_authenticated and user.is_teacher

def is_student(user):
    return user.is_authenticated and user.is_student

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    profile = request.user.teacherprofile
    tests = profile.test_set.all()
    return render(request, 'core/teacher_dashboard.html', {'tests': tests})

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    profile = request.user.studentprofile
    school_class = profile.school_class
    tests = Test.objects.filter(classes=school_class).select_related('subject')
    return render(request, 'core/student_dashboard.html', {'tests': tests})

@login_required
def dashboard_redirect_view(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/')  # Админ в админку
    elif user.is_teacher:
        return redirect('teacher_dashboard')
    elif user.is_student:
        return redirect('student_dashboard')
    return redirect('login')

def generate_certificate_view(request, session_id):
    session = get_object_or_404(TestSession, id=session_id)

    # Только если пройден
    if not session.passed:
        return HttpResponse("Тест не пройден. Сертификат недоступен.", status=403)

    # Ученик может получить только свой сертификат
    user = request.user
    if user.is_student and session.full_name != user.username:
        return HttpResponse("Нет доступа", status=403)

    # Учитель — только если он автор теста
    if user.is_teacher and session.test.created_by_id != user.teacherprofile.id:
        return HttpResponse("Нет доступа", status=403)

    # Суперпользователь — всегда можно
    certificate, created = Certificate.objects.get_or_create(session=session)

    if not created and certificate.pdf:
        return FileResponse(certificate.pdf.open(), content_type='application/pdf')

    # Создание PDF
    html_string = render_to_string('core/certificate_template.html', {
        'session': session,
        'date': localtime(session.finished_at).strftime("%d.%m.%Y")
    })

    pdf_file = HTML(string=html_string).write_pdf()
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

@login_required
@user_passes_test(lambda u: u.is_student)
def test_page_view(request, session_id):
    session = get_object_or_404(TestSession, id=session_id)
    
    if session.finished_at or session.score_percent is not None:
        return redirect('test_result', session_id=session.id)
    all_questions = list(session.test.questions.all())
    question_count = session.test.random_question_count or len(all_questions)

    if f'shown_questions_{session.id}' not in request.session:
        shown = random.sample(all_questions, min(len(all_questions), question_count))
        request.session[f'shown_questions_{session.id}'] = [q.id for q in shown]
        request.session[f'current_q_{session.id}'] = 0

    question_ids = request.session[f'shown_questions_{session.id}']
    current_index = request.session.get(f'current_q_{session.id}', 0)
    current_question = get_object_or_404(Question, id=question_ids[current_index])

    if request.method == 'POST':
        q_key = f"q{current_question.id}"
        if current_question.question_type in ['single', 'multiple']:
            selected_ids = request.POST.getlist(q_key)
            if selected_ids:
                ua, _ = UserAnswer.objects.get_or_create(session=session, question=current_question)
                ua.selected_options.set(AnswerOption.objects.filter(id__in=selected_ids))
                ua.save()
        elif current_question.question_type == 'text':
            text_response = request.POST.get(q_key, '').strip()
            if text_response:
                ua, _ = UserAnswer.objects.get_or_create(session=session, question=current_question)
                ua.text_answer = text_response
                ua.save()

        # Навигация
        if 'next' in request.POST:
            if current_index < len(question_ids) - 1:
                request.session[f'current_q_{session.id}'] += 1
        elif 'prev' in request.POST:
            if current_index > 0:
                request.session[f'current_q_{session.id}'] -= 1
        elif 'finish' in request.POST:
            # Завершение
            correct = 0
            total = 0
            for qid in question_ids:
                q = Question.objects.get(id=qid)
                ua = UserAnswer.objects.filter(session=session, question=q).first()
                total += 1
                if q.question_type in ['single', 'multiple']:
                    correct_ids = set(q.options.filter(is_correct=True).values_list('id', flat=True))
                    if ua and set(ua.selected_options.values_list('id', flat=True)) == correct_ids:
                        correct += 1
                elif q.question_type == 'text':
                    if ua and ua.text_answer:
                        correct += 1  # или добавить текстовую проверку

            session.finished_at = timezone.now()
            session.score_percent = round((correct / total) * 100, 2) if total else 0
            session.passed = session.score_percent >= session.test.pass_score
            session.save()
            return redirect('test_result', session_id=session.id)

    return render(request, 'core/test_page.html', {
        'session': session,
        'question': current_question,
        'current': current_index + 1,
        'total': len(question_ids),
    })
    
@login_required
def test_result(request, session_id):
    session = get_object_or_404(TestSession, id=session_id)
    user = request.user

    if user.is_student:
        # Ученик видит только свой результат
        if session.full_name != user.username:
            return redirect('student_dashboard')

    elif user.is_teacher:
        # Учитель видит результат, если он автор теста
        if session.test.created_by != user.teacherprofile:
            return redirect('teacher_dashboard')

    elif not user.is_superuser:
        # Все прочие — отказ
        return redirect('login')

    return render(request, 'core/test_result.html', {'session': session})




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