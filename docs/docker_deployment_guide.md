# 🐳 Деплой Star Burger с Docker и Docker Compose

> **Цель**: Автоматизировать развёртывание проекта Star Burger на dev-машине и сервере с помощью Docker и Docker Compose

## 📋 План работы

### Этап 1: Подготовка локальной разработки
1. Создание Dockerfile для Django
2. Создание Dockerfile для фронтенда (Node.js)
3. Настройка docker-compose.yaml для dev-окружения
4. Тестирование на локальной машине

### Этап 2: Подготовка продакшн-окружения
1. Создание docker-compose.prod.yaml
2. Настройка Nginx контейнера
3. Настройка PostgreSQL контейнера
4. Создание скриптов деплоя

### Этап 3: Деплой на сервер
1. Настройка сервера
2. Развёртывание с помощью Docker Compose
3. Настройка SSL сертификатов
4. Автоматизация обновлений

---

## 🏗️ Архитектура решения

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx (80/443)│    │  Django (8000)  │    │ PostgreSQL (5432)│
│   - Статика     │◄──►│  - API          │◄──►│  - База данных  │
│   - SSL         │    │  - Админка      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
┌─────────────────┐    ┌─────────────────┐
│  Frontend Build │    │   Media Files   │
│  - Parcel       │    │  - Изображения  │
│  - React        │    │                 │
└─────────────────┘    └─────────────────┘
```

---

## 🚀 Этап 1: Локальная разработка

### 1.1 Создание Dockerfile для Django

Создайте файл `Dockerfile` в корне проекта:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание пользователя для безопасности
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

# Порт для приложения
EXPOSE 8000

# Команда запуска
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 1.2 Создание Dockerfile для фронтенда

Создайте файл `Dockerfile.frontend`:

```dockerfile
FROM node:17-alpine

WORKDIR /app

# Копирование package.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci --only=production

# Копирование исходного кода
COPY bundles-src/ ./bundles-src/

# Сборка фронтенда
RUN npx parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

# Создание пользователя
RUN adduser -D -u 1000 nodeuser && chown -R nodeuser:nodeuser /app
USER nodeuser

# Команда для разработки (watch mode)
CMD ["npx", "parcel", "watch", "bundles-src/index.js", "--dist-dir", "bundles", "--public-url", "./"]
```

### 1.3 Создание docker-compose.yaml для разработки

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: star_burger_dev
      POSTGRES_USER: star_burger_user
      POSTGRES_PASSWORD: star_burger_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    environment:
      - DEBUG=True
      - DATABASE_URL=postgres://star_burger_user:star_burger_password@db:5432/star_burger_dev
      - SECRET_KEY=dev-secret-key-change-in-production
      - ALLOWED_HOSTS=localhost,127.0.0.1
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - db
    command: python manage.py runserver 0.0.0.0:8000

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    volumes:
      - ./bundles-src:/app/bundles-src
      - ./bundles:/app/bundles
    ports:
      - "1234:1234"
    command: npx parcel watch bundles-src/index.js --dist-dir bundles --public-url="./" --host 0.0.0.0

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### 1.4 Создание конфигурации Nginx для разработки

Создайте папку `nginx` и файл `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:1234;
    }

    server {
        listen 80;
        server_name localhost;

        # Статические файлы Django
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
        }

        # Медиа файлы
        location /media/ {
            alias /app/media/;
            expires 30d;
        }

        # Фронтенд бандлы (в dev режиме)
        location /bundles/ {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Основное приложение
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 1.5 Запуск локальной разработки

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# В отдельном терминале - применение миграций
docker-compose exec backend python manage.py migrate

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Сборка статических файлов
docker-compose exec backend python manage.py collectstatic --noinput
```

---

## 🏭 Этап 2: Продакшн-окружение

### 2.1 Создание Dockerfile для продакшна

Создайте файл `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Сборка статических файлов
RUN python manage.py collectstatic --noinput

# Финальный образ
FROM python:3.11-slim

WORKDIR /app

# Установка только runtime зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование Python зависимостей
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копирование кода и статических файлов
COPY --from=builder /app /app

# Создание пользователя
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "star_burger.wsgi:application"]
```

### 2.2 Создание docker-compose.prod.yaml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: star_burger_prod
      POSTGRES_USER: star_burger_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://star_burger_user:${POSTGRES_PASSWORD}@db:5432/star_burger_prod
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - YANDEX_GEOCODER_API_KEY=${YANDEX_GEOCODER_API_KEY}
      - ROLLBAR_ACCESS_TOKEN=${ROLLBAR_ACCESS_TOKEN}
      - ROLLBAR_ENVIRONMENT=${ROLLBAR_ENVIRONMENT}
    volumes:
      - media_volume:/app/media
    depends_on:
      - db
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### 2.3 Создание конфигурации Nginx для продакшна

Создайте файл `nginx/nginx.prod.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # HTTP -> HTTPS redirect
    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl;
        server_name your-domain.com www.your-domain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        client_max_body_size 10M;

        # Статические файлы Django
        location /static/ {
            alias /app/staticfiles/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Медиа файлы
        location /media/ {
            alias /app/media/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Основное приложение
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
    }
}
```

### 2.4 Создание .env файла для продакшна

Создайте файл `.env`:

```env
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com,http://your-server-ip
POSTGRES_PASSWORD=your-secure-postgres-password
YANDEX_GEOCODER_API_KEY=your-yandex-api-key
ROLLBAR_ACCESS_TOKEN=your-rollbar-token
ROLLBAR_ENVIRONMENT=production
```

---

## 🚀 Этап 3: Деплой на сервер

### 3.1 Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y curl wget git nano htop

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Создание директории проекта
sudo mkdir -p /opt/star-burger
sudo chown $USER:$USER /opt/star-burger

# Перезагрузка для применения изменений
sudo reboot
```

**После перезагрузки:**

```bash
# Проверка установки Docker
docker --version
docker-compose --version

# Переход в директорию проекта
cd /opt/star-burger

# Клонирование репозитория
git clone https://github.com/sh1m0r1an1n/star-burger.git .

# Создание файла с переменными окружения
cp .env.example .env
# Отредактируйте .env с вашими настройками
nano .env

# Установка прав на выполнение для скрипта деплоя
chmod +x deploy.sh
```

### 3.2 Создание скрипта деплоя

Создайте файл `deploy.sh`:

```bash
#!/bin/bash

set -e

echo "🚀 Начинаем деплой Star Burger..."

# Переход в директорию проекта
cd /opt/star-burger

# Обновление кода из репозитория
echo "📥 Обновляем код из репозитория..."
git pull origin master

# Сборка фронтенда
echo "🎨 Собираем фронтенд..."
docker run --rm -v $(pwd):/app -w /app node:16.16.0-alpine sh -c "
    npm ci --only=production
    npx parcel build bundles-src/index.js --dist-dir bundles --public-url='./'
"

# Остановка старых контейнеров
echo "🛑 Останавливаем старые контейнеры..."
docker-compose -f docker-compose.prod.yaml down

# Сборка новых образов
echo "🔨 Собираем новые образы..."
docker-compose -f docker-compose.prod.yaml build

# Запуск новых контейнеров
echo "▶️ Запускаем новые контейнеры..."
docker-compose -f docker-compose.prod.yaml up -d

# Применение миграций
echo "🗄️ Применяем миграции..."
docker-compose -f docker-compose.prod.yaml exec -T backend python manage.py migrate

# Сборка статических файлов
echo "📁 Собираем статические файлы..."
docker-compose -f docker-compose.prod.yaml exec -T backend python manage.py collectstatic --noinput

# Перезапуск Nginx для применения изменений
echo "🔄 Перезапускаем Nginx..."
docker-compose -f docker-compose.prod.yaml restart nginx

# Уведомление Rollbar о деплое
echo "📊 Уведомляем Rollbar о деплое..."
export $(grep -v '^#' .env | xargs)
COMMIT_HASH=$(git rev-parse HEAD)
curl -X POST "https://api.rollbar.com/api/1/deploy/" \
  -H "Content-Type: application/json" \
  -d "{
    \"access_token\": \"$ROLLBAR_ACCESS_TOKEN\",
    \"environment\": \"$ROLLBAR_ENVIRONMENT\",
    \"revision\": \"$COMMIT_HASH\",
    \"local_username\": \"$(whoami)\",
    \"comment\": \"Docker deployment\"
  }"

echo "✅ Деплой завершен успешно!"
echo "🌐 Сайт доступен по адресу: https://burger-star.ru"
```

### 3.3 Настройка SSL сертификатов (DNS Challenge)

```bash
# Установка Certbot
sudo apt install certbot

# Получение сертификата через DNS challenge (когда 80 порт заблокирован)
sudo certbot certonly --manual --preferred-challenges dns \
  -d burger-star.ru \
  -d www.burger-star.ru

# Certbot попросит добавить TXT запись в DNS:
# _acme-challenge.www.burger-star.ru → [значение из certbot]
# 
# После добавления записи подождите 10-15 минут для распространения DNS
# Затем нажмите Enter для продолжения

# Копирование сертификатов в папку nginx
sudo mkdir -p /opt/star-burger/nginx/ssl
sudo cp /etc/letsencrypt/live/burger-star.ru/fullchain.pem /opt/star-burger/nginx/ssl/
sudo cp /etc/letsencrypt/live/burger-star.ru/privkey.pem /opt/star-burger/nginx/ssl/
sudo chown -R $USER:$USER /opt/star-burger/nginx/ssl/
```

### 3.4 Автоматическое обновление SSL (Systemd Timer)

**⚠️ Важно:** Manual сертификаты не обновляются автоматически. Нужно настроить systemd timer.

#### Автоматическая настройка через скрипт деплоя:

Файлы systemd уже включены в репозиторий:
- `systemd/certbot-renewal.service` - сервис для обновления сертификатов
- `systemd/certbot-renewal.timer` - таймер для запуска раз в неделю

Скрипт `deploy.sh` автоматически устанавливает и активирует systemd файлы.

**Важно:** Systemd сервисы работают на хосте, а не в Docker контейнерах. Они автоматически копируют обновленные сертификаты в проект и перезапускают Nginx контейнер.

#### Ручная настройка (если нужно):

```bash
# Копирование systemd файлов
sudo cp systemd/certbot-renewal.service /etc/systemd/system/
sudo cp systemd/certbot-renewal.timer /etc/systemd/system/

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение и запуск timer
sudo systemctl enable certbot-renewal.timer
sudo systemctl start certbot-renewal.timer

# Проверка статуса
sudo systemctl status certbot-renewal.timer
```

#### Мониторинг и управление:

```bash
# Просмотр логов обновления
sudo journalctl -u certbot-renewal.service

# Ручной запуск обновления
sudo systemctl start certbot-renewal.service

# Проверка следующего запуска
sudo systemctl list-timers certbot-renewal.timer

# Отключение автоматического обновления
sudo systemctl disable certbot-renewal.timer
```

Настройте cron для автоматического обновления:

```bash
# Добавление в crontab
echo "0 12 * * * /opt/star-burger/renew-ssl.sh" | crontab -
```

---

## 🔧 Обновление README.md

Обновите файл `README.md`, добавив раздел о Docker:

```markdown
## 🐳 Запуск с Docker

### Локальная разработка

```bash
# Клонирование репозитория
git clone https://github.com/your-repo/star-burger.git
cd star-burger

# Запуск всех сервисов
docker-compose up --build

# Применение миграций (в отдельном терминале)
docker-compose exec backend python manage.py migrate

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser
```

Сайт будет доступен по адресу: http://localhost

### Продакшн деплой

```bash
# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env с вашими настройками

# Запуск деплоя
./deploy.sh
```

Сайт будет доступен по адресу: https://your-domain.com
```

---

## ✅ Проверка работы

### Локальная проверка

```bash
# Проверка статуса контейнеров
docker-compose ps

# Проверка логов
docker-compose logs backend
docker-compose logs frontend
docker-compose logs nginx

# Проверка доступности
curl -I http://localhost
```

### Серверная проверка

```bash
# Проверка статуса контейнеров
docker-compose -f docker-compose.prod.yaml ps

# Проверка логов
docker-compose -f docker-compose.prod.yaml logs backend
docker-compose -f docker-compose.prod.yaml logs nginx

# Проверка доступности
curl -I https://your-domain.com
```

---

## 🚨 Решение проблем

### Проблема: Фронтенд не собирается

**Решение:**
```bash
# Проверка версии Node.js
docker run --rm node:17-alpine node --version

# Очистка кэша Parcel
rm -rf bundles/
docker-compose exec frontend npx parcel clean
```

### Проблема: Django не подключается к БД

**Решение:**
```bash
# Проверка подключения к БД
docker-compose exec backend python manage.py dbshell

# Проверка переменных окружения
docker-compose exec backend env | grep DATABASE
```

### Проблема: Nginx не отдает статику

**Решение:**
```bash
# Проверка прав доступа
docker-compose exec nginx ls -la /app/staticfiles/

# Пересборка статических файлов
docker-compose exec backend python manage.py collectstatic --noinput
```

### Проблема: SSL сертификаты не работают

**Решение:**
```bash
# Проверка сертификатов
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# Обновление сертификатов (DNS challenge)
certbot certonly --manual --preferred-challenges dns -d burger-star.ru -d www.burger-star.ru

# Проверка статуса systemd timer
systemctl status certbot-renewal.timer

# Ручное обновление через systemd
systemctl start certbot-renewal.service
```

---

## 📊 Мониторинг и логирование

### Просмотр логов

```bash
# Логи всех сервисов
docker-compose -f docker-compose.prod.yaml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yaml logs -f backend

# Логи с временными метками
docker-compose -f docker-compose.prod.yaml logs -f --timestamps
```

### Мониторинг ресурсов

```bash
# Использование диска
docker system df

# Использование памяти
docker stats

# Очистка неиспользуемых ресурсов
docker system prune -a
```

---

## 🔄 Автоматизация

### GitHub Actions для автоматического деплоя

Создайте файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /opt/star-burger
          git pull origin main
          ./deploy.sh
```

---

## 📝 Заключение

Данная инструкция позволяет:

✅ **Локальная разработка:**
- Запуск проекта с помощью Docker Compose
- Автоматическая сборка фронтенда и бэкенда
- Изолированное окружение для разработки

✅ **Продакшн деплой:**
- Полная докеризация приложения
- Автоматическое обновление SSL сертификатов через systemd timer
- Сохранение данных в volumes
- Автоматизация деплоя одним скриптом
- Поддержка DNS challenge для SSL

✅ **Мониторинг:**
- Просмотр логов всех сервисов
- Мониторинг ресурсов
- Автоматическое обновление

Проект готов к использованию в продакшн-среде с полной автоматизацией деплоя и мониторинга.
