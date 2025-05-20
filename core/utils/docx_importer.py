from docx import Document
from core.models import Test, Question, AnswerOption

def import_test_from_docx(filepath):
    doc = Document(filepath)
    test = None
    current_question = None

    for para in doc.paragraphs:
        text = para.text.strip()

        if not text:
            continue

        if text.startswith("# Тест:"):
            title = text.replace("# Тест:", "").strip()
            test = Test.objects.create(title=title)
            print(f"Создан тест: {title}")

        elif text.startswith("Вопрос:"):
            q_text = text.replace("Вопрос:", "").strip()
            current_question = Question.objects.create(
                test=test,
                text=q_text,
                question_type='single'  # по умолчанию
            )

        elif text.startswith("="):
            if current_question:
                current_question.question_type = 'text'
                current_question.save()

        elif text.startswith("-") or text.startswith("+"):
            is_correct = "✔" in text or "+" in text or "[x]" in text or "(x)" in text
            option_text = text.lstrip("-+").replace("✔", "").replace("[x]", "").replace("(x)", "").strip()
            AnswerOption.objects.create(
                question=current_question,
                text=option_text,
                is_correct=is_correct
            )

            # если более одного правильного — multiple
            if current_question.options.filter(is_correct=True).count() > 1:
                current_question.question_type = 'multiple'
                current_question.save()

    return test
