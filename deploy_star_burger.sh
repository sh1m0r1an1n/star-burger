#!/bin/bash

set -e

echo "🚀 Начинаем деплой Star Burger..."

cd /opt/star-burger

echo "📥 Обновляем код из репозитория..."
git pull origin master

echo "🎨 Собираем фронтенд..."
docker run --rm -v $(pwd):/app -w /app node:16.16.0-alpine sh -c "
    npm ci --only=production
    npx parcel build bundles-src/index.js --dist-dir bundles --public-url='./'
"

echo "🛑 Останавливаем старые контейнеры..."
docker-compose -f docker-compose.prod.yaml down

echo "🔨 Собираем новые образы..."
docker-compose -f docker-compose.prod.yaml build

echo "▶️ Запускаем новые контейнеры..."
docker-compose -f docker-compose.prod.yaml up -d

echo "⏳ Ждем готовности базы данных..."
sleep 10

echo "🗄️ Применяем миграции..."
docker-compose -f docker-compose.prod.yaml exec -T backend python manage.py migrate

echo "👤 Создаем суперпользователя..."
docker-compose -f docker-compose.prod.yaml exec -T backend python manage.py createsuperuser --noinput --username admin --email admin@gmail.com || echo "Суперпользователь уже существует"
docker-compose -f docker-compose.prod.yaml exec -T backend python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='admin'); u.set_password('admin'); u.save()" || echo "Пароль уже установлен"

echo "📊 Загружаем данные из JSON..."
docker-compose -f docker-compose.prod.yaml exec -T backend python manage.py loaddata data_utf8_fixed.json || echo "Данные уже загружены"

echo "📁 Проверяем статические файлы..."
docker-compose -f docker-compose.prod.yaml exec -T backend python manage.py collectstatic --noinput

echo "🔄 Перезапускаем Nginx..."
docker-compose -f docker-compose.prod.yaml restart nginx

echo "📊 Уведомляем Rollbar о деплое..."
export $(grep -v '^#' /opt/star-burger/.env | xargs)
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
echo "🔗 IP адрес: http://45.131.42.195"
echo "👤 Админка: https://burger-star.ru/admin/ (admin/admin)"
