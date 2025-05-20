from django import forms
from .models import TestSession, Test

class TestSessionForm(forms.ModelForm):
    test = forms.ModelChoiceField(queryset=Test.objects.all(), empty_label="Выберите тест")

    class Meta:
        model = TestSession
        fields = ['full_name', 'school', 'group', 'subject', 'test']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'test': forms.Select(attrs={'class': 'form-control'}),
        }

class DocxUploadForm(forms.Form):
    file = forms.FileField(label="Файл DOCX", required=True)