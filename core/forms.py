from django import forms
from .models import TestSession, Test
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentProfile, SchoolClass
from django.forms import ModelForm, inlineformset_factory
from .models import Question, AnswerOption

class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type']

AnswerOptionFormSet = inlineformset_factory(
    Question, AnswerOption,
    fields=['text', 'is_correct'],
    extra=1,
    can_delete=True
)

class TestCreationForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'subject', 'classes', 'time_limit', 'pass_score', 'random_question_count']

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher:
            self.fields['subject'].queryset = teacher.subjects.all()
            self.fields['classes'].queryset = teacher.classes.all()
            self.fields['classes'].widget.attrs['size'] = 5

class StudentCreationForm(UserCreationForm):
    username = forms.CharField(label="Логин")
    email = forms.EmailField(required=False)
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none(), label="Класс")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'school_class', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['school_class'].queryset = teacher.classes.all()

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