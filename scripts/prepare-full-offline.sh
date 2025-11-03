#!/bin/bash
set -e

# Подготовка ПОЛНОСТЬЮ офлайн сборки
# Этот скрипт нужно запустить в среде с интернетом

echo "=== Подготовка полностью офлайн сборки ==="

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Проверки
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не найден${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm не найден${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Шаг 1: Скачивание npm пакетов${NC}"
mkdir -p offline-packages
cd offline-packages
npm pack @cline/cli
npm pack @qwen-code/qwen-code
cd ..
echo -e "${GREEN}✅ npm пакеты скачаны${NC}"
ls -lh offline-packages/*.tgz

echo ""
echo -e "${YELLOW}📦 Шаг 2: Скачивание pip пакетов (опционально)${NC}"
read -p "Скачать Python пакеты для офлайн установки? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p offline-packages/pip
    pip download -r requirements.txt -d offline-packages/pip/
    echo -e "${GREEN}✅ pip пакеты скачаны${NC}"
    ls offline-packages/pip/ | wc -l
fi

echo ""
echo -e "${YELLOW}🐳 Шаг 3: Скачивание базового Docker образа${NC}"
# Скачать образ с Python + Node.js
docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim
echo -e "${GREEN}✅ Базовый образ скачан${NC}"

echo ""
echo -e "${YELLOW}🔨 Шаг 4: Сборка review-api образа${NC}"
docker-compose -f docker-compose.offline.yml build
echo -e "${GREEN}✅ Образ собран${NC}"

echo ""
echo -e "${YELLOW}💾 Шаг 5: Сохранение образов${NC}"
# Сохранить базовый образ
docker save -o base-python-nodejs.tar nikolaik/python-nodejs:python3.11-nodejs18-slim
echo "Базовый образ сохранён: base-python-nodejs.tar"

# Сохранить review-api образ
docker save -o review-api.tar code-review-api:latest
echo "API образ сохранён: review-api.tar"

echo ""
echo -e "${YELLOW}📦 Шаг 6: Создание transfer пакета${NC}"
tar -czf transfer-full-offline.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs' \
    base-python-nodejs.tar \
    review-api.tar \
    offline-packages/ \
    docker-compose.offline.yml \
    Dockerfile.offline \
    .env.example \
    README.md \
    OFFLINE_QUICK_START.md

echo -e "${GREEN}✅ Transfer пакет создан${NC}"
ls -lh transfer-full-offline.tar.gz

echo ""
echo -e "${GREEN}=== Подготовка завершена ===${NC}"
echo ""
echo "📤 Файл для переноса: transfer-full-offline.tar.gz"
echo ""
echo "Следующие шаги на целевом сервере:"
echo "1. tar -xzf transfer-full-offline.tar.gz"
echo "2. docker load -i base-python-nodejs.tar"
echo "3. docker load -i review-api.tar"
echo "4. cp .env.example .env && nano .env"
echo "5. docker-compose -f docker-compose.offline.yml up -d"
echo ""
du -sh transfer-full-offline.tar.gz


