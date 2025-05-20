from django.urls import path
from .views import start_test_view
from .views import test_page_view
from .views import test_result_view
from .views import import_docx_view
from .views import export_csv_view
from .views import test_history_view
from .views import generate_certificate_view

urlpatterns = [
    path('', start_test_view, name='start_test'),
    path('test/<int:session_id>/', test_page_view, name='test_page'),
    path('result/<int:session_id>/', test_result_view, name='test_result'),
    path('import/', import_docx_view, name='import_docx'),
    path('export/test/<int:test_id>/', export_csv_view, name='export_csv'),
    path('history/', test_history_view, name='test_history'),
    path('certificate/<int:session_id>/', generate_certificate_view, name='generate_certificate'),

]



