# LMS Platform

Платформа управления обучением с курсами, уроками, подписками и интеграцией платежей через Stripe.

## 📋 Содержание
- [Требования](#требования)
- [Шаги по запуску проекта через docker-compose](#шаги-по-запуску-проекта-через-docker-compose)
- [Команда для запуска проекта](#команда-для-запуска-проекта)
- [Проверка работоспособности сервисов](#проверка-работоспособности-сервисов)
- [Переменные окружения](#переменные-окружения)
- [Устранение неполадок](#устранение-неполадок)

## 🔧 Требования

- **Docker** (версия 20.10 или выше)
- **Docker Compose** (версия 2.0 или выше)
- **Git**
- **4+ GB** свободной оперативной памяти
- **10+ GB** свободного места на диске

Проверка установки:
```bash
docker --version
docker-compose --version
```

## 🚀 Шаги по запуску проекта через docker-compose

#### Шаг 1: Клонируйте репозиторий

```bash
git clone <your-repository-url>
cd Django_LMS
```

#### Шаг 2: Настройте переменные окружения

```bash
# Скопируйте шаблон .env
cp .env.example .env

# Отредактируйте .env файл
nano .env
```

#### Шаг 3: Проверьте свободные порты

```bash
# Проверка портов PostgreSQL (5433) и Redis (6380)
sudo lsof -i :5433
sudo lsof -i :6380

# Если порты заняты, остановите локальные сервисы:
sudo systemctl stop postgresql
sudo systemctl stop redis
```

#### Шаг 4: Запустите проект (основная команда)

```bash
# Сборка и запуск всех контейнеров
docker-compose up --build
```

#### Шаг 5: Примените миграции

```bash
# В новом терминале или после нажатия Ctrl+C
docker-compose exec backend poetry run python manage.py migrate
```

#### Шаг 6: Создайте суперпользователя

```bash
docker-compose exec backend poetry run python manage.py csu
# или
docker-compose exec backend poetry run python manage.py createsuperuser
```

#### Шаг 7: Соберите статические файлы

```bash
docker-compose exec backend poetry run python manage.py collectstatic --noinput
```

## 🎮 Команда для запуска проекта

#### Основная команда запуска

```bash
# Запуск в интерактивном режиме (с выводом логов)
docker-compose up --build
```

#### Основная команда запуска

```bash
# Запуск в фоновом режиме
docker-compose up -d --build

# Запуск конкретного сервиса
docker-compose up -d --build backend

# Перезапуск после изменений
docker-compose restart
```

#### Команды для остановки

```bash
# Остановка без удаления данных
docker-compose down

# Остановка с полной очисткой
docker-compose down -v
```

## ✅ Проверка работоспособности сервисов

#### 1. Django веб-приложение

Проверка через браузер:

    http://localhost:8000 - главная страница

    http://localhost:8000/admin - админ-панель

    http://localhost:8000/api/docs/ - Swagger документация

Проверка через командную строку:

```bash
curl -I http://localhost:8000
# Ожидаемый ответ: HTTP/1.1 200 OK
```

#### 2. PostgreSQL (База данных)

Проверка подключения:
```bash
docker-compose exec db pg_isready -U ${DATABASE_USER} -d ${DATABASE_NAME}
# Ожидаемый ответ: /var/run/postgresql:5432 - accepting connections
```
Проверка списка баз данных:
```bash
docker-compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -c "\l"
# Должен отобразиться список баз данных
```
Проверка версии:
```bash
docker-compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -c "SELECT version();"
```

#### 3. Redis (Кэш и брокер сообщений)

Проверка связи:
```bash
docker-compose exec redis redis-cli ping
# Ожидаемый ответ: PONG
```
Проверка статистики:
```bash
docker-compose exec redis redis-cli info stats | grep total_commands_processed
```
Проверка количества ключей:
```bash
docker-compose exec redis redis-cli dbsize
# Ожидаемый ответ: (integer) 0 или больше
```

#### 4. Celery Worker (Обработчик задач)

Проверка логов:
```bash
docker-compose logs celery | tail -20
# Ожидаемые строки:
# - "celery@... ready."
# - "Connected to redis://redis:6379/0"
```
Проверка активных задач:
```bash
docker-compose exec celery celery -A config inspect active
# Ожидаемый ответ: -> active: <empty>
```
Проверка статистики воркера:
```bash
docker-compose exec celery celery -A config inspect stats | grep "total"
```

#### 5. Celery Beat (Планировщик задач)

Проверка логов:
```bash
docker-compose logs celery-beat | tail -20
# Ожидаемые строки:
# - "celery beat v5.6.2 is starting."
# - "Scheduler: Scheduler sending due tasks"
```
Проверка запланированных задач:
```bash
docker-compose logs celery-beat | tail -20
docker-compose exec celery-beat celery -A config beat --info 2>&1 | head -20
```

#### 6. Flower (Мониторинг Celery)

Проверка через браузер:

    Откройте http://localhost:5555

    Должен открыться веб-интерфейс с графиками и статистикой

Проверка через командную строку:
```bash
curl -I http://localhost:5555
# Ожидаемый ответ: HTTP/1.1 200 OK
```

#### 7. Комплексная проверка всех сервисов

Проверка статуса контейнеров:
```bash
docker-compose ps
# Ожидаемый вывод - все сервисы со статусом "Up":
# Name                   Command               State    Ports
# ------------------------------------------------------------
# lms_backend     gunicorn config.wsgi:app ...   Up    0.0.0.0:8000->8000/tcp
# lms_celery      celery -A config worker  ...   Up
# lms_celery_beat celery -A config beat    ...   Up
# lms_db          docker-entrypoint.sh postgres  Up    0.0.0.0:5432->5432/tcp
# lms_flower      celery -A config flower  ...   Up    0.0.0.0:5555->5555/tcp
# lms_redis       docker-entrypoint.sh redis ... Up    0.0.0.0:6379->6379/tcp
```
Проверка использования ресурсов:
```bash
docker stats --no-stream
# Должна отобразиться статистика CPU и памяти для всех контейнеров
```
Проверка логов на наличие ошибок:
```bash
docker-compose logs --tail=100 | grep -i error
# Не должно быть критических ошибок
```
Проверка сети:
```bash
docker network ls | grep django_lms_default
# Должна быть сеть со статусом "created"
```
Проверка томов:
```bash
docker volume ls | grep django_lms
# Должны отобразиться все созданные тома:
# django_lms_postgres_data
# django_lms_redis_data
# django_lms_static_volume
# django_lms_media_volume
```

#### 8. Проверка API эндпоинтов

Проверка авторизации:
```bash
curl -X POST http://localhost:8000/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lms.ru","password":"admin"}'
# Ожидаемый ответ: JSON с access и refresh токенами
```
Проверка списка курсов:
```bash
curl http://localhost:8000/course/
# Ожидаемый ответ: JSON список курсов
```

## 🌍 Переменные окружения

#### Шаблон .env файла

```dotenv
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost 127.0.0.1 0.0.0.0

# Database
DATABASE_NAME=lms_db
DATABASE_USER=lms_user
DATABASE_PASSWORD=your-password
DATABASE_HOST=db
DATABASE_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe
STRIPE_PUBLIC_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key

# Site
SITE_URL=http://localhost:8000
```

## 🔍 Устранение неполадок

#### Проблема: Порты уже заняты
```bash
# Решение: остановить локальные сервисы
sudo systemctl stop postgresql
sudo systemctl stop redis
```

#### Проблема: Ошибка подключения к БД
```bash
# Решение: создать БД и применить миграции
docker-compose exec db createdb -U lms_user lms_db
docker-compose exec backend poetry run python manage.py migrate
```

#### Проблема: Ошибка прав Docker
```bash
# Решение: добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

#### Проблема: Нет места на диске
```bash
# Решение: очистить неиспользуемые ресурсы Docker
docker system prune -a -f --volumes
```

Автор: Tkachenko Vsevolod  
Версия: 1.0.0
