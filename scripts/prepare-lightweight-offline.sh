#!/bin/bash
set -e

# Легковесная подготовка offline пакета (без Docker сборки)
# Создает пакет со всеми исходниками и зависимостями
# Docker образы можно собрать на целевой машине

echo "==================================================================="
echo "  AI Code Review System - Lightweight Offline Package"
echo "  Подготовка без Docker сборки (только зависимости)"
echo "==================================================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PACKAGE_VERSION=$(date +%Y%m%d)
PACKAGE_NAME="code-review-offline-lightweight-${PACKAGE_VERSION}"
TEMP_DIR="build-lightweight"

# Проверка npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm не найден${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 не найден${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Все зависимости найдены${NC}"
echo ""

# Создать временную директорию
rm -rf ${TEMP_DIR}
mkdir -p ${TEMP_DIR}

# ============================================================================
# ШАГ 1: Скачивание npm пакетов
# ============================================================================
echo -e "${YELLOW}📦 [1/5] Скачивание Cline CLI и Qwen Code CLI...${NC}"
mkdir -p offline-packages
cd offline-packages

echo "  → Скачивание @cline/cli..."
npm pack @cline/cli 2>/dev/null || echo -e "${YELLOW}⚠️  @cline/cli недоступен, создам placeholder${NC}"

if [ ! -f cline-*.tgz ]; then
    echo "  → Создание placeholder для cline-cli"
    mkdir -p cline-placeholder
    echo '{"name": "@cline/cli", "version": "2.0.0"}' > cline-placeholder/package.json
    tar czf cline-cli-2.0.0-placeholder.tgz cline-placeholder/
    rm -rf cline-placeholder
fi

echo "  → Скачивание @qwen-code/qwen-code..."
npm pack @qwen-code/qwen-code 2>/dev/null || echo -e "${YELLOW}⚠️  @qwen-code/qwen-code недоступен, создам placeholder${NC}"

if [ ! -f qwen-code-*.tgz ]; then
    echo "  → Создание placeholder для qwen-code"
    mkdir -p qwen-placeholder
    echo '{"name": "@qwen-code/qwen-code", "version": "1.0.0"}' > qwen-placeholder/package.json
    tar czf qwen-code-1.0.0-placeholder.tgz qwen-placeholder/
    rm -rf qwen-placeholder
fi

cd ..

echo -e "${GREEN}✅ npm пакеты подготовлены:${NC}"
ls -lh offline-packages/*.tgz
echo ""

# ============================================================================
# ШАГ 2: Скачивание Python пакетов
# ============================================================================
echo -e "${YELLOW}📦 [2/5] Скачивание Python зависимостей...${NC}"
mkdir -p offline-packages/pip
pip3 download -r requirements.txt -d offline-packages/pip/ --no-cache-dir 2>&1 | grep -v "^Collecting" | grep -v "^  Downloading" || true
PIP_COUNT=$(ls offline-packages/pip/ 2>/dev/null | wc -l)
echo -e "${GREEN}✅ Скачано ${PIP_COUNT} Python пакетов${NC}"
echo ""

# ============================================================================
# ШАГ 3: Подготовка файлов приложения
# ============================================================================
echo -e "${YELLOW}📝 [3/5] Подготовка файлов приложения...${NC}"

# Копировать offline packages
cp -r offline-packages ${TEMP_DIR}/

# Копировать конфигурацию
cp docker-compose.offline.yml ${TEMP_DIR}/
cp Dockerfile.offline ${TEMP_DIR}/
cp env.example.annotated ${TEMP_DIR}/.env.example

# Копировать документацию
cp README.md ${TEMP_DIR}/ 2>/dev/null || true
cp OFFLINE_QUICK_START.md ${TEMP_DIR}/ 2>/dev/null || true
cp OFFLINE_DEPLOYMENT_PACKAGE_README.md ${TEMP_DIR}/INSTALL_README.md 2>/dev/null || true
cp HOW_TO_BUILD_OFFLINE_PACKAGE.md ${TEMP_DIR}/ 2>/dev/null || true

# Копировать docs
mkdir -p ${TEMP_DIR}/docs
cp docs/WINDOWS_OFFLINE_INSTALL.md ${TEMP_DIR}/docs/ 2>/dev/null || true
cp docs/LINUX_VPS_OFFLINE_INSTALL.md ${TEMP_DIR}/docs/ 2>/dev/null || true
cp docs/OFFLINE_BUILD.md ${TEMP_DIR}/docs/ 2>/dev/null || true
cp docs/AIR_GAP_TRANSFER.md ${TEMP_DIR}/docs/ 2>/dev/null || true

# Копировать приложение
mkdir -p ${TEMP_DIR}/{app,prompts,rules}
cp -r app/* ${TEMP_DIR}/app/ 2>/dev/null || true
cp -r prompts/* ${TEMP_DIR}/prompts/ 2>/dev/null || true
cp -r rules/* ${TEMP_DIR}/rules/ 2>/dev/null || true
cp requirements.txt ${TEMP_DIR}/

echo -e "${GREEN}✅ Файлы приложения подготовлены${NC}"
echo ""

# ============================================================================
# ШАГ 4: Создание скриптов установки
# ============================================================================
echo -e "${YELLOW}📝 [4/5] Создание скриптов установки...${NC}"

# install-linux.sh
cat > ${TEMP_DIR}/install-linux.sh << 'EOF'
#!/bin/bash
set -e

echo "==================================================================="
echo "  AI Code Review System - Установка (Linux/VPS)"
echo "==================================================================="
echo ""

if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker:"
    echo "   curl -fsSL https://get.docker.com | sh"
    exit 1
fi

echo "✅ Docker найден"
echo ""

echo "📦 Сборка Docker образов..."
echo "ВАЖНО: Это может занять 10-15 минут"
echo ""

# Скачать базовый образ (если есть интернет) или загрузить из tar
if [ -f base-python-nodejs.tar ]; then
    echo "  → Загрузка базового образа из архива..."
    docker load -i base-python-nodejs.tar
else
    echo "  → Скачивание базового образа..."
    docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim
fi

# Собрать API образ
echo "  → Сборка code-review-api..."
docker-compose -f docker-compose.offline.yml build

if [ ! -f .env ]; then
    echo ""
    echo "⚙️  Создание .env файла..."
    cp .env.example .env
    echo "❗ ВАЖНО: Отредактируйте .env файл:"
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
echo "  1. Отредактируйте .env: nano .env"
echo "  2. Запустите: docker-compose -f docker-compose.offline.yml up -d"
echo "  3. Проверьте: curl http://localhost:8000/api/v1/health"
echo "==================================================================="
EOF

chmod +x ${TEMP_DIR}/install-linux.sh

# install-windows.ps1
cat > ${TEMP_DIR}/install-windows.ps1 << 'EOF'
# AI Code Review System - Установка (Windows)

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  AI Code Review System - Установка (Windows)"
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

$dockerExists = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerExists) {
    Write-Host "❌ Docker Desktop не найден" -ForegroundColor Red
    Write-Host "Установите Docker Desktop:" -ForegroundColor Yellow
    Write-Host "  https://www.docker.com/products/docker-desktop"
    exit 1
}

Write-Host "✅ Docker Desktop найден" -ForegroundColor Green
Write-Host ""

Write-Host "📦 Сборка Docker образов..." -ForegroundColor Yellow
Write-Host "ВАЖНО: Это может занять 10-15 минут" -ForegroundColor Yellow
Write-Host ""

# Загрузить или скачать базовый образ
if (Test-Path base-python-nodejs.tar) {
    Write-Host "  → Загрузка базового образа из архива..." -ForegroundColor Yellow
    docker load -i base-python-nodejs.tar
} else {
    Write-Host "  → Скачивание базового образа..." -ForegroundColor Yellow
    docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim
}

# Собрать API образ
Write-Host "  → Сборка code-review-api..." -ForegroundColor Yellow
docker-compose -f docker-compose.offline.yml build

if (-not (Test-Path .env)) {
    Write-Host ""
    Write-Host "⚙️  Создание .env файла..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "❗ ВАЖНО: Отредактируйте .env файл" -ForegroundColor Red
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
Write-Host "  1. Отредактируйте .env (открыт в Notepad)"
Write-Host "  2. Запустите: docker-compose -f docker-compose.offline.yml up -d"
Write-Host "  3. Проверьте: curl http://localhost:8000/api/v1/health"
Write-Host "===================================================================" -ForegroundColor Cyan
EOF

echo -e "${GREEN}✅ Скрипты установки созданы${NC}"
echo ""

# ============================================================================
# ШАГ 5: Создание README
# ============================================================================
cat > ${TEMP_DIR}/README_FIRST.txt << EOF
=================================================================
  AI Code Review System - Offline Deployment Package
  Lightweight версия (без предсобранных Docker образов)
=================================================================

Версия пакета: ${PACKAGE_VERSION}
Дата создания: $(date)

ВАЖНО: Этот пакет НЕ содержит предсобранные Docker образы.
Docker образы будут собраны на целевой машине при установке.

ПРЕИМУЩЕСТВА:
- Меньший размер пакета (~100-200 MB вместо ~3 GB)
- Образы собираются с актуальными обновлениями безопасности
- Гибкость при установке

ТРЕБОВАНИЯ НА ЦЕЛЕВОЙ МАШИНЕ:
- Docker + Docker Compose
- Доступ к docker.io и registry.npmjs.org для базовых образов
  (или предварительно загруженные базовые образы)

=================================================================

СОДЕРЖИМОЕ ПАКЕТА:
------------------
1. offline-packages/           - npm пакеты (Cline CLI, Qwen Code CLI)
2. offline-packages/pip/       - Python зависимости (${PIP_COUNT} файлов)
3. app/, prompts/, rules/      - Исходный код приложения
4. docker-compose.offline.yml  - Docker Compose конфигурация
5. Dockerfile.offline          - Dockerfile для сборки
6. .env.example                - Пример конфигурации
7. install-linux.sh            - Скрипт установки для Linux/VPS
8. install-windows.ps1         - Скрипт установки для Windows
9. docs/                       - Полная документация

=================================================================

БЫСТРАЯ УСТАНОВКА:

=== Linux / VPS ===
1. tar -xzf ${PACKAGE_NAME}.tar.gz
2. cd ${PACKAGE_NAME}
3. bash install-linux.sh
4. nano .env (настроить MODEL_API_URL, GITLAB_URL, tokens)
5. docker-compose -f docker-compose.offline.yml up -d

=== Windows PC ===
1. Распаковать архив (7-Zip/WinRAR)
2. PowerShell от администратора
3. cd ${PACKAGE_NAME}
4. .\install-windows.ps1
5. Настроить .env (откроется автоматически)
6. docker-compose -f docker-compose.offline.yml up -d

=================================================================

ПРОВЕРКА РАБОТЫ:
curl http://localhost:8000/api/v1/health

Ожидаемый ответ:
{
  "status": "healthy",
  "cline_available": true,
  "qwen_available": true
}

=================================================================

ДОКУМЕНТАЦИЯ:
- INSTALL_README.md - Подробная инструкция для пользователей
- docs/WINDOWS_OFFLINE_INSTALL.md - Установка на Windows
- docs/LINUX_VPS_OFFLINE_INSTALL.md - Установка на Linux VPS
- docs/OFFLINE_BUILD.md - Сборка образов
- docs/AIR_GAP_TRANSFER.md - Air-gap развертывание

=================================================================

TROUBLESHOOTING:

1. npm пакеты не установились:
   docker exec -it code-review-api bash
   npm install -g /tmp/npm-packages/cline-*.tgz

2. Не подключается к Model API:
   - Проверьте MODEL_API_URL в .env
   - Для localhost: host.docker.internal (Win) или 172.17.0.1 (Linux)

3. Порт 8000 занят:
   В docker-compose.offline.yml: "8001:8000"

Полный troubleshooting см. в документации.

=================================================================
EOF

echo -e "${GREEN}✅ README создан${NC}"
echo ""

# ============================================================================
# ШАГ 6: Создание архива
# ============================================================================
echo -e "${YELLOW}📦 [5/5] Создание архива...${NC}"

cd ${TEMP_DIR}
tar -czf ../${PACKAGE_NAME}.tar.gz .
cd ..

FINAL_SIZE=$(du -h ${PACKAGE_NAME}.tar.gz | cut -f1)

echo -e "${GREEN}✅ Архив создан${NC}"
echo ""

# ============================================================================
# ЗАВЕРШЕНИЕ
# ============================================================================
echo -e "${GREEN}==================================================================="
echo "  ✅ Lightweight offline пакет готов!"
echo "===================================================================${NC}"
echo ""
echo -e "${BLUE}📦 ФИНАЛЬНЫЙ ПАКЕТ:${NC}"
echo "   Файл: ${PACKAGE_NAME}.tar.gz"
echo "   Размер: ${FINAL_SIZE}"
echo ""
echo -e "${BLUE}📊 СТАТИСТИКА:${NC}"
echo "   - npm пакеты: $(ls offline-packages/*.tgz 2>/dev/null | wc -l) файлов"
echo "   - Python пакеты: ${PIP_COUNT} файлов"
echo "   - Исходный код: включен"
echo "   - Docker образы: будут собраны при установке"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО:${NC}"
echo "   Этот пакет НЕ содержит предсобранные Docker образы."
echo "   Образы будут собраны на целевой машине при запуске install скрипта."
echo ""
echo -e "${YELLOW}📤 СЛЕДУЮЩИЕ ШАГИ:${NC}"
echo "   1. Скопируйте ${PACKAGE_NAME}.tar.gz на целевую систему"
echo "   2. Распакуйте архив"
echo "   3. Запустите install-linux.sh (Linux) или install-windows.ps1 (Windows)"
echo ""
echo -e "${GREEN}Готово! 🚀${NC}"
echo ""

# Очистка
read -p "Удалить временную папку ${TEMP_DIR}? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ${TEMP_DIR}
    echo "Временные файлы удалены"
fi
