# LMS Project - Learning Management System

## 📚 О проекте

LMS (Learning Management System) - платформа для онлайн-обучения с возможностью создания курсов, уроков, управления подписками и интеграцией со Stripe.

### Технологии

- **Backend**: Django 5.x, Django REST Framework
- **База данных**: PostgreSQL 15
- **Кэш и очереди**: Redis, Celery
- **Мониторинг**: Flower
- **Веб-сервер**: Nginx
- **Контейнеризация**: Docker, Docker Compose
- **CI/CD**: GitHub Actions

---

## 🚀 Быстрый старт

### Локальный запуск

```bash
# Клонировать репозиторий
git clone https://github.com/Sevaat/Django_LMS.git
cd Django_LMS

# Скопировать .env.example в .env и настроить
cp .env.example .env

# Запустить через Docker Compose
docker compose up -d --build

# Создать суперпользователя
docker compose exec backend python manage.py createsuperuser
```

### Разработка
```bash
# Установить Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Установить зависимости
poetry install

# Запустить миграции
python manage.py migrate

# Запустить сервер
python manage.py runserver
```

## 🔧 CI/CD Pipeline
Проект настроен на автоматическое тестирование и деплой через GitHub Actions.  
Триггеры:
- Push в main → тесты + деплой на продакшн  
- Push в develop → тесты  
- Pull Request → тесты  

## 🔐 GitHub Secrets
Для работы CI/CD добавьте следующие секреты в репозиторий (Settings → Secrets and variables → Actions → New repository secret):  
Обязательные секреты  
Секрет | Описание  |	Пример  
DEPLOY_HOST |	IP адрес сервера |	123.123.123.123  
DEPLOY_USER |	Пользователь на сервере |	ubuntu или root  
DEPLOY_SSH_KEY |	Приватный SSH ключ |	-----BEGIN OPENSSH PRIVATE KEY-----  
SECRET_KEY |	Django secret key |	django-insecure-...  
DOMAIN |	Домен сайта	| lms.your-domain.com  
DATABASE_NAME |	Имя БД |	lms_db  
DATABASE_USER |	Пользователь БД	| lms_user  
DATABASE_PASSWORD |	Пароль БД |	secure-password  
FLOWER_USER |	Логин для Flower |	admin  
FLOWER_PASSWORD |	Пароль для Flower |	secure-password  

## 🖥️ Настройка сервера

### Установка Docker и Docker Compose
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```
### Подготовка SSH для деплоя
```bash
# На сервере добавить публичный ключ
mkdir -p ~/.ssh
echo "ssh-ed25519 AAA..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## 📂 Структура проекта
```text
Django_LMS/
├── .github/workflows/CI.yml    # GitHub Actions
├── nginx/nginx.conf            # Nginx конфигурация
├── config/                     # Django настройки
│   ├── settings.py
│   ├── urls.py
│   └── views.py
├── docker-compose.yaml         # Docker Compose
├── Dockerfile                  # Docker образ
└── README.md
```

## 🌐 Доступные endpoints
- Главная страница: /
- Health check: /health/
- Admin панель: /admin/
- API Docs: /api/docs/
- Flower мониторинг: :5555

## 📄 Лицензия
MIT License. Подробнее в файле LICENSE

## 📞 Контакты
Автор: Ткаченко Всеволод  
GitHub: https://github.com/Sevaat  
Проект: https://github.com/Sevaat/Django_LMS
