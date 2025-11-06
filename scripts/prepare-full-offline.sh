#!/bin/bash
set -e

# Подготовка ПОЛНОСТЬЮ офлайн сборки с Cline CLI
# Этот скрипт нужно запустить в среде с интернетом
# Создаёт полный пакет для развертывания на изолированных системах

echo "==================================================================="
echo "  AI Code Review System - Подготовка Offline Deployment Пакета"
echo "==================================================================="
echo ""

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Переменные
PACKAGE_VERSION=$(date +%Y%m%d)
PACKAGE_NAME="code-review-offline-${PACKAGE_VERSION}"
TEMP_DIR="build-offline"

# Проверки
echo -e "${BLUE}Проверка зависимостей...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не найден. Установите Docker и Docker Compose${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm не найден. Установите Node.js${NC}"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo -e "${RED}❌ pip не найден. Установите Python 3.11+${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Все зависимости найдены${NC}"
echo ""

# Создать временную директорию
mkdir -p ${TEMP_DIR}

# ============================================================================
# ШАГ 1: Скачивание npm пакетов (Cline CLI и Qwen Code CLI)
# ============================================================================
echo -e "${YELLOW}📦 [1/7] Скачивание Cline CLI и Qwen Code CLI...${NC}"
mkdir -p offline-packages
cd offline-packages

echo "  → Скачивание @cline/cli..."
npm pack @cline/cli 2>/dev/null || echo -e "${RED}⚠️  Внимание: @cline/cli может быть недоступен${NC}"

echo "  → Скачивание @qwen-code/qwen-code..."
npm pack @qwen-code/qwen-code 2>/dev/null || echo -e "${RED}⚠️  Внимание: @qwen-code/qwen-code может быть недоступен${NC}"

cd ..

if ls offline-packages/*.tgz 1> /dev/null 2>&1; then
    echo -e "${GREEN}✅ npm пакеты скачаны:${NC}"
    ls -lh offline-packages/*.tgz
else
    echo -e "${RED}❌ Не удалось скачать npm пакеты!${NC}"
    echo "Проверьте доступность пакетов в npm registry"
    exit 1
fi
echo ""

# ============================================================================
# ШАГ 2: Скачивание Python пакетов
# ============================================================================
echo -e "${YELLOW}📦 [2/7] Скачивание Python зависимостей...${NC}"
mkdir -p offline-packages/pip
pip download -r requirements.txt -d offline-packages/pip/ --no-cache-dir
PIP_COUNT=$(ls offline-packages/pip/*.whl offline-packages/pip/*.tar.gz 2>/dev/null | wc -l)
echo -e "${GREEN}✅ Скачано ${PIP_COUNT} Python пакетов${NC}"
echo ""

# ============================================================================
# ШАГ 3: Скачивание базового Docker образа
# ============================================================================
echo -e "${YELLOW}🐳 [3/7] Скачивание базового Docker образа...${NC}"
echo "  → Образ: nikolaik/python-nodejs:python3.11-nodejs18-slim"
docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim
echo -e "${GREEN}✅ Базовый образ скачан${NC}"
echo ""

# ============================================================================
# ШАГ 4: Сборка review-api образа
# ============================================================================
echo -e "${YELLOW}🔨 [4/7] Сборка Docker образа с Cline CLI...${NC}"
docker-compose -f docker-compose.offline.yml build --no-cache
echo -e "${GREEN}✅ Образ code-review-api собран${NC}"
echo ""

# ============================================================================
# ШАГ 5: Сохранение Docker образов
# ============================================================================
echo -e "${YELLOW}💾 [5/7] Сохранение Docker образов...${NC}"

# Сохранить базовый образ
echo "  → Сохранение базового образа..."
docker save -o ${TEMP_DIR}/base-python-nodejs.tar nikolaik/python-nodejs:python3.11-nodejs18-slim
BASE_SIZE=$(du -h ${TEMP_DIR}/base-python-nodejs.tar | cut -f1)
echo "    Размер: ${BASE_SIZE}"

# Сохранить review-api образ
echo "  → Сохранение review-api образа..."
docker save -o ${TEMP_DIR}/code-review-api.tar code-review-api:latest
API_SIZE=$(du -h ${TEMP_DIR}/code-review-api.tar | cut -f1)
echo "    Размер: ${API_SIZE}"

echo -e "${GREEN}✅ Docker образы сохранены${NC}"
echo ""

# ============================================================================
# ШАГ 6: Создание инструкций для установки
# ============================================================================
echo -e "${YELLOW}📝 [6/7] Создание инструкций для установки...${NC}"

# Скопировать необходимые файлы
cp -r offline-packages ${TEMP_DIR}/
cp docker-compose.offline.yml ${TEMP_DIR}/
cp Dockerfile.offline ${TEMP_DIR}/
cp env.example.annotated ${TEMP_DIR}/.env.example
cp README.md ${TEMP_DIR}/
cp OFFLINE_QUICK_START.md ${TEMP_DIR}/

# Копировать приложение (без .git)
mkdir -p ${TEMP_DIR}/app ${TEMP_DIR}/prompts ${TEMP_DIR}/rules
cp -r app/* ${TEMP_DIR}/app/
cp -r prompts/* ${TEMP_DIR}/prompts/
cp -r rules/* ${TEMP_DIR}/rules/
cp requirements.txt ${TEMP_DIR}/

# Создать скрипт установки для Linux
cat > ${TEMP_DIR}/install-linux.sh << 'EOF'
#!/bin/bash
set -e

echo "==================================================================="
echo "  AI Code Review System - Установка (Linux/VPS)"
echo "==================================================================="
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker:"
    echo "   curl -fsSL https://get.docker.com | sh"
    exit 1
fi

echo "✅ Docker найден"

# Загрузка образов
echo ""
echo "📦 Загрузка Docker образов..."
docker load -i base-python-nodejs.tar
docker load -i code-review-api.tar

# Настройка .env
if [ ! -f .env ]; then
    echo ""
    echo "⚙️  Создание .env файла..."
    cp .env.example .env
    echo "❗ ВАЖНО: Отредактируйте .env файл перед запуском:"
    echo "   nano .env"
    echo ""
    echo "Требуемые параметры:"
    echo "  - MODEL_API_URL"
    echo "  - MODEL_API_KEY"
    echo "  - GITLAB_URL"
    echo "  - GITLAB_TOKEN"
fi

echo ""
echo "==================================================================="
echo "✅ Установка завершена!"
echo ""
echo "Следующие шаги:"
echo "  1. Отредактируйте .env файл: nano .env"
echo "  2. Запустите систему: docker-compose -f docker-compose.offline.yml up -d"
echo "  3. Проверьте логи: docker-compose logs -f"
echo "  4. Откройте: http://localhost:8000/api/v1/health"
echo "==================================================================="
EOF

chmod +x ${TEMP_DIR}/install-linux.sh

# Создать скрипт установки для Windows
cat > ${TEMP_DIR}/install-windows.ps1 << 'EOF'
# AI Code Review System - Установка (Windows)

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  AI Code Review System - Установка (Windows)"
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker Desktop
$dockerExists = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerExists) {
    Write-Host "❌ Docker Desktop не найден" -ForegroundColor Red
    Write-Host "Установите Docker Desktop для Windows:"
    Write-Host "  https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Docker Desktop найден" -ForegroundColor Green

# Загрузка образов
Write-Host ""
Write-Host "📦 Загрузка Docker образов..." -ForegroundColor Yellow
docker load -i base-python-nodejs.tar
docker load -i code-review-api.tar

# Настройка .env
if (-not (Test-Path .env)) {
    Write-Host ""
    Write-Host "⚙️  Создание .env файла..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "❗ ВАЖНО: Отредактируйте .env файл перед запуском" -ForegroundColor Red
    Write-Host ""
    Write-Host "Требуемые параметры:" -ForegroundColor Yellow
    Write-Host "  - MODEL_API_URL"
    Write-Host "  - MODEL_API_KEY"
    Write-Host "  - GITLAB_URL"
    Write-Host "  - GITLAB_TOKEN"
    Write-Host ""
    notepad.exe .env
}

Write-Host ""
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "✅ Установка завершена!" -ForegroundColor Green
Write-Host ""
Write-Host "Следующие шаги:" -ForegroundColor Yellow
Write-Host "  1. Отредактируйте .env файл (уже открыт в Notepad)"
Write-Host "  2. Запустите: docker-compose -f docker-compose.offline.yml up -d"
Write-Host "  3. Проверьте: docker-compose logs -f"
Write-Host "  4. Откройте: http://localhost:8000/api/v1/health"
Write-Host "===================================================================" -ForegroundColor Cyan
EOF

echo -e "${GREEN}✅ Инструкции созданы${NC}"
echo ""

# ============================================================================
# ШАГ 7: Создание финального архива
# ============================================================================
echo -e "${YELLOW}📦 [7/7] Создание финального архива для передачи...${NC}"

# Создать README для пакета
cat > ${TEMP_DIR}/INSTALL_README.txt << EOF
=================================================================
  AI Code Review System - Offline Deployment Package
  Система автоматического ревью кода с Cline CLI
=================================================================

Версия пакета: ${PACKAGE_VERSION}
Дата создания: $(date)

СОДЕРЖИМОЕ ПАКЕТА:
------------------
1. base-python-nodejs.tar      - Базовый Docker образ (Python 3.11 + Node.js 18)
2. code-review-api.tar         - Docker образ системы ревью с Cline CLI
3. offline-packages/           - npm и pip пакеты
4. app/, prompts/, rules/      - Исходный код приложения
5. docker-compose.offline.yml  - Docker Compose конфигурация
6. .env.example                - Пример конфигурации
7. install-linux.sh            - Скрипт установки для Linux/VPS
8. install-windows.ps1         - Скрипт установки для Windows

РАЗМЕРЫ:
--------
- Базовый образ: ${BASE_SIZE}
- API образ: ${API_SIZE}
- npm пакеты: $(du -h offline-packages/*.tgz 2>/dev/null | awk '{sum+=$1} END {print sum}')MB
- Python пакеты: ${PIP_COUNT} файлов

БЫСТРАЯ УСТАНОВКА:
------------------

=== Linux / VPS сервер ===
1. Распакуйте архив:
   tar -xzf ${PACKAGE_NAME}.tar.gz
   cd ${PACKAGE_NAME}

2. Запустите установку:
   bash install-linux.sh

3. Настройте .env:
   nano .env

4. Запустите систему:
   docker-compose -f docker-compose.offline.yml up -d

=== Windows PC ===
1. Распакуйте архив (WinRAR/7-Zip)
2. Откройте PowerShell от имени администратора
3. Перейдите в папку: cd ${PACKAGE_NAME}
4. Запустите: .\install-windows.ps1
5. Настройте .env (откроется в Notepad)
6. Запустите: docker-compose -f docker-compose.offline.yml up -d

ТРЕБОВАНИЯ:
-----------
- Docker и Docker Compose
- 4GB RAM минимум (рекомендуется 8GB)
- 10GB свободного места на диске
- Доступ к внутреннему Model API (DeepSeek/Qwen)
- Доступ к внутреннему GitLab

ПРОВЕРКА РАБОТЫ:
----------------
curl http://localhost:8000/api/v1/health

Ожидаемый ответ:
{
  "status": "healthy",
  "cline_available": true,
  "qwen_available": true
}

ДОКУМЕНТАЦИЯ:
-------------
- README.md - Полное описание системы
- OFFLINE_QUICK_START.md - Быстрый старт
- .env.example - Аннотированная конфигурация

ПОДДЕРЖКА:
----------
При проблемах с установкой см. документацию в README.md
или логи: docker-compose logs -f

=================================================================
EOF

# Создать архив
cd ${TEMP_DIR}
echo "  → Архивирование..."
tar -czf ../${PACKAGE_NAME}.tar.gz .
cd ..

FINAL_SIZE=$(du -h ${PACKAGE_NAME}.tar.gz | cut -f1)
echo -e "${GREEN}✅ Финальный архив создан${NC}"
echo ""

# ============================================================================
# ЗАВЕРШЕНИЕ
# ============================================================================
echo -e "${GREEN}==================================================================="
echo "  ✅ Подготовка offline deployment пакета завершена!"
echo "===================================================================${NC}"
echo ""
echo -e "${BLUE}📦 ФИНАЛЬНЫЙ ПАКЕТ:${NC}"
echo "   Файл: ${PACKAGE_NAME}.tar.gz"
echo "   Размер: ${FINAL_SIZE}"
echo ""
echo -e "${BLUE}📊 СТАТИСТИКА:${NC}"
echo "   - Docker образы: 2 файла (${BASE_SIZE} + ${API_SIZE})"
echo "   - npm пакеты: $(ls offline-packages/*.tgz 2>/dev/null | wc -l) файлов"
echo "   - Python пакеты: ${PIP_COUNT} файлов"
echo ""
echo -e "${YELLOW}📤 СЛЕДУЮЩИЕ ШАГИ:${NC}"
echo "   1. Скопируйте ${PACKAGE_NAME}.tar.gz на целевую систему"
echo "   2. Распакуйте архив"
echo "   3. Запустите install-linux.sh (Linux) или install-windows.ps1 (Windows)"
echo ""
echo -e "${BLUE}💡 ВАЖНО:${NC}"
echo "   - Для Windows требуется Docker Desktop"
echo "   - Для Linux требуется Docker + Docker Compose"
echo "   - Настройте .env перед первым запуском"
echo ""
echo -e "${GREEN}Удачного развертывания! 🚀${NC}"
echo ""

# Очистка временных файлов
read -p "Удалить временную папку ${TEMP_DIR}? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ${TEMP_DIR}
    echo "Временные файлы удалены"
fi


