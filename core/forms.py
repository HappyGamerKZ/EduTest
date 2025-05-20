from django import forms
from .models import TestSession, Test
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegisterForm(UserCreationForm):
    is_teacher = forms.BooleanField(required=False, label="Я преподаватель")

    class Meta:
        model = User
        fields = ("username", "is_teacher", "password1", "password2")

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