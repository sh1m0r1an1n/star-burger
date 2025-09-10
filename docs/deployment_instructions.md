# 🚀 Инструкция по деплою Star Burger

> **Примечание**: Конфиденциальные данные (IP, домены, ключи) настройте в файле `star_burger/.env`

## 📋 Быстрый старт

```bash
# 1. Подготовка сервера
apt update && apt install -y python3 python3-venv nodejs npm postgresql postgresql-contrib nginx

# 2. Загрузка кода (замените на ваши данные)
git clone https://github.com/your-repo/star-burger.git /opt/star-burger

# 3. Настройка проекта
cd /opt/star-burger
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
npm ci --dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

# 4. База данных
sudo -u postgres psql -c "CREATE USER star_burger_user WITH PASSWORD 'star_burger_password';"
sudo -u postgres psql -c "CREATE DATABASE star_burger_db OWNER star_burger_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE star_burger_db TO star_burger_user;"

# 5. Настройка окружения
# Создайте star_burger/.env с вашими настройками

# 6. Применение миграций
python manage.py migrate
python manage.py collectstatic --noinput

# 7. Запуск сервисов
systemctl enable postgresql && systemctl start postgresql
systemctl enable nginx && systemctl start nginx
# Настройте systemd сервис для Django (см. ниже)
```

---

## 🔧 Подробная инструкция

### 1. Подготовка сервера

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка необходимого ПО
apt install -y python3 python3-venv python3-pip
apt install -y nodejs npm
apt install -y postgresql postgresql-contrib
apt install -y nginx
apt install -y certbot python3-certbot-nginx
```

### 2. Загрузка проекта

```bash
# Клонирование репозитория
git clone https://github.com/your-repo/star-burger.git /opt/star-burger
cd /opt/star-burger

# Загрузка медиа-файлов (если есть)
# Используйте scp или rsync для копирования файлов
```

### 3. Настройка Python окружения

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 4. Настройка фронтенда

```bash
# Установка npm пакетов
npm ci --dev

# Сборка фронтенда
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
```

### 5. Настройка PostgreSQL

```bash
# Создание пользователя и базы данных
sudo -u postgres psql -c "CREATE USER star_burger_user WITH PASSWORD 'star_burger_password';"
sudo -u postgres psql -c "CREATE DATABASE star_burger_db OWNER star_burger_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE star_burger_db TO star_burger_user;"
sudo -u postgres psql -c "GRANT ALL ON SCHEMA public TO star_burger_user;"
```

### 6. Настройка окружения Django

```bash
# Создание .env файла
nano star_burger/.env
```

<details>
<summary>📄 Содержимое .env файла</summary>

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-server-ip,localhost,127.0.0.1,your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com,http://your-server-ip
YANDEX_GEOCODER_API_KEY=your-yandex-api-key
ROLLBAR_ACCESS_TOKEN=your-token-here
ROLLBAR_ENVIRONMENT=production
ROLLBAR_BRANCH=main
DATABASE_URL=postgres://star_burger_user:star_burger_password@localhost:5432/star_burger_db
USER=star_burger_user
PASSWORD='star_burger_password'
```

</details>

```bash
# Применение миграций
python manage.py migrate

# Сбор статических файлов
python manage.py collectstatic --noinput
```

### 7. Настройка Systemd сервисов

#### 7.1 Конфигурация Gunicorn

**Что такое gunicorn.conf.py:**
Gunicorn - это WSGI-сервер для запуска Django приложений в продакшене. Файл `gunicorn.conf.py` содержит настройки производительности, безопасности и стабильности работы приложения. Этот файл создается только на сервере и не должен попадать в git репозиторий.

**Зачем нужен:**
- Настройка количества рабочих процессов (workers)
- Ограничение размера запросов для безопасности
- Настройка таймаутов и перезапусков
- Оптимизация производительности для продакшена

```bash
nano /opt/star-burger/gunicorn.conf.py
```

<details>
<summary>📄 Конфигурация gunicorn.conf.py</summary>

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

raw_env = [
    "DJANGO_SETTINGS_MODULE=star_burger.settings",
]

preload_app = True
```

</details>

#### 7.2 Django сервис

```bash
nano /etc/systemd/system/star-burger.service
```

<details>
<summary>📄 Конфигурация star-burger.service</summary>

```ini
[Unit]
Description=Star Burger Django Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/star-burger
Environment="PATH=/opt/star-burger/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="DEBUG=False"
ExecStart=/opt/star-burger/venv/bin/gunicorn --config /opt/star-burger/gunicorn.conf.py star_burger.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

</details>

```bash
# Активация сервиса
systemctl daemon-reload
systemctl enable star-burger.service
systemctl start star-burger.service
```

### 8. Настройка Nginx

```bash
nano /etc/nginx/sites-available/star-burger
```

<details>
<summary>📄 Конфигурация Nginx</summary>

```nginx
server {
    listen 80;
    server_name your-server-ip your-domain.com www.your-domain.com;

    client_max_body_size 10M;

    location /static/ {
        alias /opt/star-burger/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/star-burger/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

</details>

```bash
# Активация конфигурации
ln -s /etc/nginx/sites-available/star-burger /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx
```

### 9. Настройка SSL (HTTPS)

#### 9.1 Получение сертификата

```bash
# Для домена (замените на ваш домен)
certbot certonly --manual --preferred-challenges=dns -d your-domain.com -d www.your-domain.com
```

**Примечание**: Если порт 80 заблокирован провайдером, используйте DNS-01 challenge.

#### 9.2 Настройка Nginx для HTTPS

```bash
nano /etc/nginx/sites-available/star-burger
```

<details>
<summary>📄 HTTPS конфигурация Nginx</summary>

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com www.your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    client_max_body_size 10M;

    location /static/ {
        alias /opt/star-burger/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/star-burger/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

</details>

```bash
systemctl restart nginx
```

### 10. Автоматизация

#### 10.1 Автоматическое обновление сертификатов

```bash
# Создание сервиса обновления
cat > /etc/systemd/system/certbot-renewal.service << 'EOF'
[Unit]
Description=Certbot Renewal with DNS-01 Challenge
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --preferred-challenges=dns --quiet --no-random-sleep-on-renew
ExecStartPost=/bin/systemctl reload nginx.service
User=root
Group=root
Restart=no
RestartSec=0
EOF

# Создание таймера
cat > /etc/systemd/system/certbot-renewal.timer << 'EOF'
[Unit]
Description=Timer for Certbot Renewal
Requires=certbot-renewal.service

[Timer]
OnBootSec=300
OnUnitActiveSec=1w
RandomizedDelaySec=3600

[Install]
WantedBy=timers.target
EOF

# Активация
systemctl daemon-reload
systemctl enable certbot-renewal.timer
systemctl start certbot-renewal.timer
```

#### 10.2 Очистка сессий Django

```bash
# Создание сервиса очистки
cat > /etc/systemd/system/starburger-clearsessions.service << 'EOF'
[Unit]
Description=Star Burger Django Clear Sessions
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=oneshot
User=root
Group=root
WorkingDirectory=/opt/star-burger
Environment="PATH=/opt/star-burger/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/star-burger/venv/bin/python manage.py clearsessions

[Install]
WantedBy=multi-user.target
EOF

# Создание таймера
cat > /etc/systemd/system/starburger-clearsessions.timer << 'EOF'
[Unit]
Description=Timer for Star Burger Django Clear Sessions
Requires=starburger-clearsessions.service

[Timer]
OnBootSec=300
OnUnitActiveSec=1d
RandomizedDelaySec=3600

[Install]
WantedBy=timers.target
EOF

# Активация
systemctl daemon-reload
systemctl enable starburger-clearsessions.timer
systemctl start starburger-clearsessions.timer
```

---

## 🔧 Если порт 80 заблокирован провайдером

### Получение SSL-сертификата с DNS-01 challenge

```bash
# Вместо HTTP-01 используйте DNS-01 challenge
certbot certonly --manual --preferred-challenges=dns -d burger-star.ru -d www.burger-star.ru
```

**Процесс:**
1. Certbot генерирует TXT-запись для `_acme-challenge.burger-star.ru`
2. Добавьте эту запись в DNS панели домена
3. Certbot проверяет запись и выдает сертификат
4. Никакого доступа к порту 80 не требуется

### Автоматическое обновление с DNS-01

**⚠️ Внимание:** Полная автоматизация DNS-01 требует интеграции с DNS API провайдера. Для ручного управления используйте:

```bash
# Создание сервиса с ручным подтверждением
cat > /etc/systemd/system/certbot-renewal.service << 'EOF'
[Unit]
Description=Certbot Renewal with DNS-01 Challenge
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --preferred-challenges=dns --quiet --no-random-sleep-on-renew
ExecStartPost=/bin/systemctl reload nginx.service
User=root
Group=root
Restart=no
RestartSec=0
EOF

# Таймер для еженедельного запуска
cat > /etc/systemd/system/certbot-renewal.timer << 'EOF'
[Unit]
Description=Timer for Certbot Renewal
Requires=certbot-renewal.service

[Timer]
OnBootSec=300
OnUnitActiveSec=1w
RandomizedDelaySec=3600

[Install]
WantedBy=timers.target
EOF

# Активация
systemctl daemon-reload
systemctl enable certbot-renewal.timer
systemctl start certbot-renewal.timer
```

**Для полной автоматизации** потребуется:
- DNS API токен от провайдера домена
- Плагин certbot для вашего DNS провайдера
- Настройка автоматического добавления TXT-записей

## ✅ Проверка работы

### Быстрая проверка всех сервисов

```bash
# Статус всех сервисов
systemctl status postgresql star-burger.service nginx

# Проверка доступности
curl -I http://your-server-ip
curl -I https://your-domain.com

# Проверка логов
journalctl -u star-burger.service -f
```

### Автоматическое обновление

Для автоматического деплоя используйте скрипт `deploy_star_burger.sh`:

```bash
# Запуск автоматического деплоя
/root/deploy_star_burger.sh
```

**Что делает скрипт:**
- Обновляет код из репозитория
- Устанавливает зависимости Python и Node.js
- Собирает фронтенд
- Собирает статические файлы Django
- Применяет миграции
- Перезапускает сервисы
- Уведомляет Rollbar о деплое

### Ручное обновление

```bash
# Перезапуск сервисов
systemctl restart star-burger.service
systemctl restart nginx

# Обновление кода
cd /opt/star-burger
git pull
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python manage.py collectstatic --noinput
systemctl restart star-burger.service

# Проверка таймеров
systemctl list-timers | grep -E "(certbot|starburger)"
```

---

## 📊 Архитектура системы

- **Nginx** (порт 80/443) - реверс-прокси, статические файлы, SSL
- **Gunicorn** (127.0.0.1:8000) - Django приложение
- **PostgreSQL** - база данных
- **Systemd** - управление сервисами и автоматизация

**Порядок запуска**: PostgreSQL → Django → Nginx

**Автоматическое обновление**: 
- SSL сертификаты - еженедельно
- Очистка сессий - ежедневно