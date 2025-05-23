# EduTest

**EduTest** — это веб-сервис для автоматизированного тестирования студентов и абитуриентов. Разработан с использованием Django.

## 🚀 Возможности

- 📄 Импорт тестов из DOCX
- 🎯 Поддержка вопросов с одним/множественным выбором и текстовым вводом
- ⏳ Ограничение по времени с серверной защитой
- 📊 Автоматическая проверка и анализ результатов
- 🧾 История прохождения тестов
- 📥 Экспорт результатов в CSV
- 🌙 Тёмная тема
- 🎓 Генерация PDF-сертификатов
- 🛠 Админ-панель для управления пользователями и тестами

## ⚙️ Установка

```bash
# Клонируй репозиторий
git clone https://github.com/yourusername/edutest.git
cd edutest

# Создай и активируй виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows

# Установи зависимости
pip install -r requirements.txt

# Примени миграции и запусти сервер
python manage.py migrate
python manage.py runserver

# структура
EduTest/
├── core/               # Приложение с логикой тестов
├── EduTest/            # Настройки Django
├── templates/          # HTML-шаблоны
├── static/             # Стили и скрипты
├── manage.py
└── requirements.txt
