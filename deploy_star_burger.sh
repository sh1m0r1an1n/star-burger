#!/bin/bash

set -e

echo "🚀 Начинаем деплой Star Burger..."

cd /opt/star-burger

echo "📥 Обновляем код из репозитория..."
git pull origin master

echo "🐍 Активируем виртуальное окружение..."
source venv/bin/activate

echo "📦 Устанавливаем Python зависимости..."
pip install -r requirements.txt

echo "📦 Устанавливаем Node.js зависимости..."
npm ci --dev

echo "🔨 Собираем фронтенд..."
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

echo "📁 Собираем статические файлы Django..."
python manage.py collectstatic --noinput

echo "🗄️ Применяем миграции..."
python manage.py migrate

echo "🔄 Перезапускаем сервисы..."
systemctl restart star-burger.service

echo "📊 Уведомляем Rollbar о деплое..."
COMMIT_HASH=$(git rev-parse HEAD)
curl -X POST "https://api.rollbar.com/api/1/deploy/" \
  -H "Content-Type: application/json" \
  -d "{
    \"access_token\": \"$ROLLBAR_ACCESS_TOKEN\",
    \"environment\": \"$ROLLBAR_ENVIRONMENT\",
    \"revision\": \"$COMMIT_HASH\",
    \"local_username\": \"$(whoami)\",
    \"comment\": \"Deploy from deploy_star_burger.sh\"
  }"

echo "✅ Деплой завершен успешно!"
echo "🌐 Сайт доступен по адресу: http://burger-star.ru"
