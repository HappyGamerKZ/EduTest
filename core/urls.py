from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from core.views import teacher_dashboard


urlpatterns = [
    # Главная маршрутизация
    path('', views.dashboard_redirect_view, name='dashboard'),

    # Вход и выход
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Кабинеты
    path('dashboard/', views.dashboard_redirect_view, name='dashboard'),
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),

    # Работа с учениками
    path('teacher/add-student/', views.add_student, name='add_student'),

    # Работа с тестами
    path('teacher/create-test/', views.create_test, name='create_test'),
    path('teacher/test/<int:test_id>/add-question/', views.add_question, name='add_question'),
    path('teacher/test/<int:test_id>/edit/', views.edit_test, name='edit_test'),
    path('teacher/test/<int:test_id>/edit-questions/', views.edit_questions, name='edit_questions'),

    # Результаты для учителя
    path('teacher/results/', views.teacher_results_view, name='teacher_results'),

    # Ученик — прохождение теста
    path('student/test/<int:test_id>/start/', views.start_test, name='start_test'),
    path('test/<int:session_id>/', views.test_page_view, name='test_page'),
    path('student/test/result/<int:session_id>/', views.test_result, name='test_result'),
    path('student/history/', views.test_history, name='test_history'),

    # DOCX и экспорт
    path('import/', views.import_docx_view, name='import_docx'),
    path('export/test/<int:test_id>/', views.export_csv_view, name='export_csv'),

    # Сертификаты
    path('certificate/<int:session_id>/', views.generate_certificate_view, name='generate_certificate'),
]
