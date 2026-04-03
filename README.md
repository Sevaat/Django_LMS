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

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Sevaat/Django_LMS.git
cd Django_LMS
```
2. Установите Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```
3. Установите зависимости:
```bash
poetry install
```
4. Создайте файл .env:
```bash
cp .env.example .env
# Отредактируйте .env под ваши настройки
```
5. Запустите миграции:
```bash
python manage.py migrate
```
6. Запустите сервер:
```bash
python manage.py runserver
```

## 🖥️ Настройка продакшн-сервера
Предварительные требования  
    Ubuntu 22.04/24.04 LTS  
    Docker и Docker Compose  
    Домен (опционально)  

1. Подготовка сервера
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo apt install -y docker-compose-plugin

# Перезагрузитесь или выйдите и зайдите заново для применения прав
newgrp docker
```
2. Создание директории проекта
```bash
# Создайте директорию для проекта
sudo mkdir -p /var/www/lms
sudo chown -R $USER:$USER /var/www/lms

# Перейдите в директорию
cd /var/www/lms
```
3. Настройка SSH ключей для GitHub Actions
```bash
# Создайте SSH ключ для деплоя
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github-actions

# Добавьте публичный ключ в authorized_keys
cat ~/.ssh/github-actions.pub >> ~/.ssh/authorized_keys

# Проверьте права доступа
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Скопируйте приватный ключ (понадобится для GitHub Secrets)
cat ~/.ssh/github-actions
```
4. Настройка домена и SSL (опционально)
```bash
# Установка Certbot
sudo apt install -y certbot

# Остановите Docker контейнеры, если они запущены
cd /var/www/lms
docker compose down

# Получение SSL сертификата
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Копирование сертификатов для Docker
sudo mkdir -p /var/www/lms/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /var/www/lms/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /var/www/lms/ssl/
sudo chown -R $USER:$USER /var/www/lms/ssl

# Настройка автоматического обновления сертификатов
sudo crontab -e
# Добавьте строку:
# 0 2 * * * certbot renew --quiet --post-hook "cd /var/www/lms && docker compose restart nginx"
```
5. Настройка фаервола
```bash
# Базовая защита
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw --force enable

# Проверка статуса
sudo ufw status verbose
```
6. Создание директорий для логов и медиа
```bash
cd /var/www/lms
mkdir -p logs media static nginx ssl
```

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

Управление контейнерами
```bash
# Просмотр статуса
docker compose ps

# Просмотр логов всех сервисов
docker compose logs -f

# Просмотр логов конкретного сервиса
docker compose logs -f backend

# Перезапуск всех сервисов
docker compose restart

# Перезапуск конкретного сервиса
docker compose restart backend

# Остановка всех сервисов
docker compose down

# Обновление после изменений
docker compose up -d --build

# Очистка неиспользуемых образов
docker image prune -f
```

## 🌐 Доступ к сервисам
После успешного деплоя:  
Сервис	URL  
Сайт	https://your-domain.com  
Админка Django	https://your-domain.com/admin  
Flower (мониторинг Celery)	https://your-domain.com/flower/  
API документация	https://your-domain.com/api/docs/  

Данные для входа  
Django Admin: создайте суперпользователя  
Flower: используйте FLOWER_USER и FLOWER_PASSWORD из секретов  

## 📝 Полезные команды
Django
```bash
# Создание суперпользователя
docker compose exec backend poetry run python manage.py createsuperuser

# Проверка миграций
docker compose exec backend poetry run python manage.py showmigrations

# Откат миграций
docker compose exec backend poetry run python manage.py migrate app_name zero

# Сбор статики вручную
docker compose exec backend poetry run python manage.py collectstatic --noinput

# Проверка настроек
docker compose exec backend poetry run python manage.py check --deploy
```
База данных
```bash
# Подключение к PostgreSQL
docker compose exec db psql -U lms_user -d lms_db

# Создание бэкапа базы данных
docker compose exec db pg_dump -U lms_user lms_db > backup_$(date +%Y%m%d).sql

# Восстановление бэкапа
cat backup.sql | docker compose exec -T db psql -U lms_user lms_db

# Проверка статуса
docker compose exec db pg_isready -U lms_user
```
Redis
```bash
# Подключение к Redis
docker compose exec redis redis-cli

# Проверка ключей
docker compose exec redis redis-cli KEYS "*"

# Очистка всех ключей (осторожно!)
docker compose exec redis redis-cli FLUSHALL
```
Celery
```bash
# Просмотр задач в очереди
docker compose exec celery poetry run celery -A config inspect active

# Отмена всех задач
docker compose exec celery poetry run celery -A config purge -f

# Просмотр статуса воркеров
docker compose exec celery poetry run celery -A config status
```

## 🔒 Безопасность

Принятые меры  
    Изоляция сервисов: PostgreSQL, Redis, Flower доступны только внутри Docker сети  
    Flower: Доступ через basic auth  
    Nginx: Reverse proxy с SSL/TLS  
    Firewall: Открыты только порты 22 (SSH), 80 (HTTP), 443 (HTTPS)  
    Защита от DoS: Лимиты запросов в iptables  
    SSH: Защита от brute-force через fail2ban  

Рекомендации
1. Регулярно обновляйте систему:
```bash
sudo apt update && sudo apt upgrade -y
```
2. Следите за логами:
```bash
# Docker логи
docker compose logs --tail=100

# Системные логи
sudo tail -f /var/log/auth.log
```
3. Настройте автоматическое обновление SSL:
```bash
sudo certbot renew --dry-run
```
4. Используйте fail2ban для защиты SSH:
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## 🚨 Устранение неполадок
Проблемы с подключением к серверу
```bash
# Проверьте, что сервер доступен
ping your-server-ip

# Проверьте SSH подключение
ssh -v user@your-server-ip

# Проверьте фаервол
sudo ufw status

# Проверьте логи SSH
sudo tail -f /var/log/auth.log
```
Контейнеры не запускаются
```bash
# Проверьте логи
docker compose logs

# Проверьте наличие .env файла
cat .env

# Проверьте права на директории
ls -la /var/www/lms

# Пересоберите контейнеры
docker compose down
docker compose up -d --build --force-recreate
```
База данных недоступна
```bash
# Проверьте статус PostgreSQL
docker compose logs db

# Проверьте подключение
docker compose exec db pg_isready -U lms_user

# Войдите в БД и проверьте
docker compose exec db psql -U lms_user -d lms_db -c "\l"
```
Миграции не применяются
```bash
# Примените миграции вручную
docker compose exec backend poetry run python manage.py migrate --noinput

# Проверьте, нет ли конфликтов
docker compose exec backend poetry run python manage.py makemigrations --dry-run
```

## 📂 Структура проекта
```text
Django_LMS/
├── .github/
│   └── workflows/
│       └── CI.yml              # GitHub Actions workflow
├── nginx/
│   └── nginx.conf              # Nginx конфигурация
├── config/                     # Django конфигурация
├── course/                     # Модуль курсов
├── users/                      # Модуль пользователей
├── static/                     # Статические файлы
├── media/                      # Медиа файлы
├── logs/                       # Логи приложения
├── docker-compose.yaml         # Docker Compose конфигурация
├── Dockerfile                  # Docker образ
├── pyproject.toml              # Poetry зависимости
├── .env.example                # Пример .env файла
└── manage.py                   # Django управляющий скрипт
```

## 🤝 Вклад в проект
1. Создайте ветку:
```bash
git checkout -b feature/your-feature-name
```
2. Внесите изменения и закоммитьте:
```bash
git add .
git commit -m "Add: описание изменений"
```
3. Запушите ветку:
```bash
git push origin feature/your-feature-name
```
4. Создайте Pull Request в ветку develop

Code Style  
    Python: PEP 8  
    Django: Официальные рекомендации Django  
    Коммиты: Следуйте Conventional Commits  

## 📄 Лицензия
MIT License. Подробнее в файле LICENSE

## 📞 Контакты
Автор: Ткаченко Всеволод  
GitHub: https://github.com/Sevaat  
Проект: https://github.com/Sevaat/Django_LMS  

## 🙏 Благодарности
Django и Django REST Framework  
Celery и Redis  
Docker и GitHub Actions  
Все контрибьютеры открытого кода  
