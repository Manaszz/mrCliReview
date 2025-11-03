#!/bin/bash
set -e

echo "=== Подготовка офлайн сборки ==="

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка наличия npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm не найден. Установите Node.js${NC}"
    exit 1
fi

# Создать папку если не существует
mkdir -p offline-packages

# Перейти в папку
cd offline-packages

echo -e "${YELLOW}📦 Скачивание npm пакетов...${NC}"

# Скачать Cline CLI
echo "Скачивание @cline/cli..."
npm pack @cline/cli

# Скачать Qwen Code CLI
echo "Скачивание @qwen-code/qwen-code..."
npm pack @qwen-code/qwen-code

# Проверить результат
echo ""
echo -e "${GREEN}✅ Пакеты скачаны:${NC}"
ls -lh *.tgz

# Вернуться в корень
cd ..

echo ""
echo -e "${GREEN}=== Подготовка завершена ===${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Перенесите всю папку проекта (включая offline-packages/) на целевой сервер"
echo "2. Запустите: docker-compose build"
echo "3. Запустите: docker-compose up -d"
echo ""
echo "Размер для переноса:"
du -sh offline-packages/


