# 🏗️ Инструкция по подготовке Offline Deployment Пакета

> Пошаговое руководство для создания полного offline пакета с Cline CLI для изолированных сред.

---

## 📋 Требования для подготовки

### Система с доступом в интернет

Для создания пакета вам потребуется:

- **ОС:** Linux (Ubuntu/Debian) или macOS
- **Docker:** 20.10+ и Docker Compose 2.0+
- **Node.js:** 18+ и npm 9+
- **Python:** 3.11+
- **Git:** Для клонирования репозитория
- **Свободное место:** 15-20GB для сборки и упаковки

---

## 🚀 Способ 1: Автоматическая сборка (РЕКОМЕНДУЕТСЯ)

### Шаг 1: Клонировать репозиторий

```bash
# Клонировать проект
git clone <repository-url>
cd mrCliReview
```

### Шаг 2: Запустить скрипт подготовки

```bash
# Сделать скрипт исполняемым (если нужно)
chmod +x scripts/prepare-full-offline.sh

# Запустить подготовку
./scripts/prepare-full-offline.sh
```

### Что делает скрипт:

**[1/7] Скачивание Cline CLI и Qwen Code CLI**
```bash
npm pack @cline/cli
npm pack @qwen-code/qwen-code
```

**[2/7] Скачивание Python зависимостей**
```bash
pip download -r requirements.txt -d offline-packages/pip/
```

**[3/7] Скачивание базового Docker образа**
```bash
docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim
```

**[4/7] Сборка Docker образа с Cline CLI**
```bash
docker-compose -f docker-compose.offline.yml build
```

**[5/7] Сохранение Docker образов**
```bash
docker save -o build-offline/base-python-nodejs.tar nikolaik/python-nodejs:python3.11-nodejs18-slim
docker save -o build-offline/code-review-api.tar code-review-api:latest
```

**[6/7] Создание инструкций для установки**
- Создаются скрипты `install-linux.sh` и `install-windows.ps1`
- Копируется документация и конфигурация

**[7/7] Создание финального архива**
```bash
tar -czf code-review-offline-YYYYMMDD.tar.gz build-offline/
```

### Шаг 3: Результат

После выполнения скрипта вы получите:

```
code-review-offline-20251106.tar.gz  (~2-3 GB)
```

Этот архив готов для переноса на изолированные системы!

---

## 🔧 Способ 2: Ручная сборка

Если автоматический скрипт не работает или нужна кастомизация.

### Шаг 1: Подготовка npm пакетов

```bash
# Создать папку
mkdir -p offline-packages

# Скачать Cline CLI
cd offline-packages
npm pack @cline/cli

# Скачать Qwen Code CLI
npm pack @qwen-code/qwen-code

cd ..
```

**Проверка:**
```bash
ls -lh offline-packages/*.tgz
# Должны быть: cline-cli-*.tgz, qwen-code-*.tgz
```

### Шаг 2: Подготовка Python пакетов

```bash
# Создать папку для pip пакетов
mkdir -p offline-packages/pip

# Скачать все зависимости
pip download -r requirements.txt -d offline-packages/pip/

# Проверить количество
ls offline-packages/pip/ | wc -l
# Должно быть ~30-40 файлов
```

### Шаг 3: Скачивание Docker образов

```bash
# Скачать базовый образ (Python + Node.js)
docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim

# Собрать образ системы
docker-compose -f docker-compose.offline.yml build --no-cache

# Проверить собранные образы
docker images | grep -E "(python-nodejs|code-review)"
```

### Шаг 4: Сохранение образов

```bash
# Создать временную папку
mkdir -p build-offline

# Сохранить базовый образ
docker save -o build-offline/base-python-nodejs.tar \
  nikolaik/python-nodejs:python3.11-nodejs18-slim

# Сохранить API образ
docker save -o build-offline/code-review-api.tar \
  code-review-api:latest

# Проверить размеры
ls -lh build-offline/*.tar
```

### Шаг 5: Подготовка файлов приложения

```bash
# Копировать offline packages
cp -r offline-packages build-offline/

# Копировать конфигурацию
cp docker-compose.offline.yml build-offline/
cp Dockerfile.offline build-offline/
cp env.example.annotated build-offline/.env.example

# Копировать документацию
cp README.md build-offline/
cp OFFLINE_QUICK_START.md build-offline/
cp OFFLINE_DEPLOYMENT_PACKAGE_README.md build-offline/INSTALL_README.txt

# Копировать приложение
mkdir -p build-offline/{app,prompts,rules}
cp -r app/* build-offline/app/
cp -r prompts/* build-offline/prompts/
cp -r rules/* build-offline/rules/
cp requirements.txt build-offline/
```

### Шаг 6: Создание скриптов установки

**install-linux.sh:**

```bash
cat > build-offline/install-linux.sh << 'EOF'
#!/bin/bash
set -e

echo "==================================================================="
echo "  AI Code Review System - Установка (Linux/VPS)"
echo "==================================================================="

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker:"
    echo "   curl -fsSL https://get.docker.com | sh"
    exit 1
fi

echo "✅ Docker найден"

# Загрузка образов
echo "📦 Загрузка Docker образов..."
docker load -i base-python-nodejs.tar
docker load -i code-review-api.tar

# Настройка .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚙️  Создан .env файл. Отредактируйте его: nano .env"
fi

echo "✅ Установка завершена!"
echo "Следующие шаги:"
echo "  1. nano .env"
echo "  2. docker-compose -f docker-compose.offline.yml up -d"
EOF

chmod +x build-offline/install-linux.sh
```

**install-windows.ps1:**

```powershell
cat > build-offline/install-windows.ps1 << 'EOF'
# AI Code Review System - Установка (Windows)

Write-Host "AI Code Review System - Установка" -ForegroundColor Cyan

$dockerExists = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerExists) {
    Write-Host "❌ Docker Desktop не найден" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker Desktop найден" -ForegroundColor Green

Write-Host "📦 Загрузка Docker образов..." -ForegroundColor Yellow
docker load -i base-python-nodejs.tar
docker load -i code-review-api.tar

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    notepad.exe .env
}

Write-Host "✅ Установка завершена!" -ForegroundColor Green
EOF
```

### Шаг 7: Создание README

```bash
cat > build-offline/INSTALL_README.txt << 'EOF'
=================================================================
  AI Code Review System - Offline Deployment Package
=================================================================

БЫСТРАЯ УСТАНОВКА:

=== Linux ===
1. tar -xzf code-review-offline-YYYYMMDD.tar.gz
2. cd code-review-offline-YYYYMMDD
3. bash install-linux.sh
4. nano .env (настроить MODEL_API_URL, GITLAB_URL, tokens)
5. docker-compose -f docker-compose.offline.yml up -d

=== Windows ===
1. Распаковать архив (7-Zip)
2. PowerShell от администратора
3. cd code-review-offline-YYYYMMDD
4. .\install-windows.ps1
5. Настроить .env
6. docker-compose -f docker-compose.offline.yml up -d

ДОКУМЕНТАЦИЯ:
- README.md - Полное описание
- docs/WINDOWS_OFFLINE_INSTALL.md - Детальная инструкция для Windows
- docs/LINUX_VPS_OFFLINE_INSTALL.md - Детальная инструкция для Linux

=================================================================
EOF
```

### Шаг 8: Создание архива

```bash
# Перейти в папку сборки
cd build-offline

# Создать архив
PACKAGE_NAME="code-review-offline-$(date +%Y%m%d)"
tar -czf ../${PACKAGE_NAME}.tar.gz .

# Вернуться в корень
cd ..

# Проверить результат
ls -lh ${PACKAGE_NAME}.tar.gz
```

---

## ✅ Проверка пакета

Перед передачей проверьте целостность пакета:

### 1. Проверить содержимое архива

```bash
tar -tzf code-review-offline-20251106.tar.gz | head -20
```

Должны присутствовать:
```
base-python-nodejs.tar
code-review-api.tar
offline-packages/cline-cli-*.tgz
offline-packages/qwen-code-*.tgz
offline-packages/pip/
docker-compose.offline.yml
install-linux.sh
install-windows.ps1
.env.example
app/
prompts/
rules/
```

### 2. Создать checksum

```bash
sha256sum code-review-offline-20251106.tar.gz > checksums.txt
cat checksums.txt
```

### 3. Тестовая установка (опционально)

```bash
# Создать тестовую директорию
mkdir -p /tmp/test-install
cd /tmp/test-install

# Распаковать
tar -xzf /path/to/code-review-offline-20251106.tar.gz

# Загрузить образы
docker load -i base-python-nodejs.tar
docker load -i code-review-api.tar

# Проверить образы
docker images | grep -E "(python-nodejs|code-review)"

# Очистка
cd /tmp
rm -rf test-install
```

---

## 📦 Структура финального пакета

```
code-review-offline-20251106.tar.gz
│
└── code-review-offline-20251106/
    │
    ├── 🐳 Docker образы (TAR files)
    │   ├── base-python-nodejs.tar     (~450 MB)
    │   └── code-review-api.tar        (~2.5 GB)
    │
    ├── 📦 Зависимости
    │   └── offline-packages/
    │       ├── cline-cli-*.tgz        (~2 MB)
    │       ├── qwen-code-*.tgz        (~2 MB)
    │       └── pip/                   (~80 MB, 30-40 файлов)
    │
    ├── 💻 Исходный код
    │   ├── app/                       # FastAPI приложение
    │   ├── prompts/                   # AI промпты
    │   ├── rules/                     # Правила ревью
    │   └── requirements.txt
    │
    ├── ⚙️ Конфигурация
    │   ├── docker-compose.offline.yml
    │   ├── Dockerfile.offline
    │   └── .env.example
    │
    ├── 🚀 Скрипты установки
    │   ├── install-linux.sh
    │   └── install-windows.ps1
    │
    └── 📚 Документация
        ├── INSTALL_README.txt
        ├── README.md
        └── OFFLINE_QUICK_START.md
```

**Итоговый размер:** ~2-3 GB в сжатом виде, ~5-6 GB распакованный.

---

## 🔍 Troubleshooting при сборке

### Проблема: npm пакеты не скачиваются

**Симптомы:**
```
npm ERR! 404 Not Found - GET https://registry.npmjs.org/@cline/cli
```

**Возможные причины:**
1. Пакет `@cline/cli` может называться по-другому
2. Пакет может быть приватным
3. Проблемы с npm registry

**Решение:**
```bash
# Проверить актуальное название пакета
npm search cline

# Если пакет приватный, используйте локальную копию
# Или установите пакет локально и запакуйте его:
npm pack ./path/to/cline-cli-source
```

### Проблема: Docker образ не собирается

**Симптомы:**
```
ERROR: CLI tools not installed!
```

**Решение:**
```bash
# Проверить наличие offline-packages
ls -la offline-packages/*.tgz

# Пересобрать с --no-cache
docker-compose -f docker-compose.offline.yml build --no-cache

# Проверить Dockerfile.offline
cat Dockerfile.offline | grep -A 5 "COPY offline-packages"
```

### Проблема: Недостаточно места

**Симптомы:**
```
no space left on device
```

**Решение:**
```bash
# Очистить неиспользуемые Docker ресурсы
docker system prune -a --volumes

# Проверить место
df -h

# Использовать другой диск для сборки
export DOCKER_TMPDIR=/path/to/large/disk
```

---

## 📤 Передача пакета

### Вариант 1: Физический носитель

```bash
# Скопировать на USB
cp code-review-offline-20251106.tar.gz /media/usb/
cp checksums.txt /media/usb/

# Безопасно извлечь
sync
umount /media/usb
```

### Вариант 2: Внутренняя сеть (scp)

```bash
# Передать через scp
scp code-review-offline-20251106.tar.gz user@server:/opt/
scp checksums.txt user@server:/opt/

# На целевом сервере проверить checksum
ssh user@server
cd /opt
sha256sum -c checksums.txt
```

### Вариант 3: Корпоративная система передачи

Используйте вашу корпоративную систему передачи файлов согласно внутренним процедурам.

---

## 📋 Чек-лист подготовки пакета

- [ ] Клонирован репозиторий
- [ ] Скачаны npm пакеты (@cline/cli, @qwen-code/qwen-code)
- [ ] Скачаны Python зависимости (pip download)
- [ ] Скачан базовый Docker образ
- [ ] Собран Docker образ с Cline CLI
- [ ] Образы сохранены в TAR файлы
- [ ] Скопированы файлы приложения (app, prompts, rules)
- [ ] Создана конфигурация (.env.example)
- [ ] Созданы скрипты установки (install-linux.sh, install-windows.ps1)
- [ ] Создана документация (README.md, инструкции)
- [ ] Создан финальный архив
- [ ] Создан checksum файл
- [ ] Проверена целостность архива
- [ ] (Опционально) Проведена тестовая установка

---

## 🎓 Следующие шаги

После создания пакета:

1. **Проверьте пакет** - распакуйте и протестируйте на чистой системе
2. **Создайте checksum** - для проверки целостности
3. **Подготовьте документацию** - убедитесь, что все инструкции актуальны
4. **Передайте пакет** - используйте безопасный способ передачи
5. **Поддержка** - будьте готовы помочь с установкой

---

## 💡 Советы

### Оптимизация размера пакета

```bash
# Сжать образы с gzip
docker save code-review-api:latest | gzip > code-review-api.tar.gz

# Использовать pigz для быстрого сжатия (если доступен)
docker save code-review-api:latest | pigz > code-review-api.tar.gz

# Использовать xz для максимального сжатия (медленнее)
docker save code-review-api:latest | xz > code-review-api.tar.xz
```

### Версионирование

```bash
# Использовать версию в имени пакета
VERSION="2.0.0"
DATE=$(date +%Y%m%d)
PACKAGE_NAME="code-review-offline-v${VERSION}-${DATE}"

tar -czf ${PACKAGE_NAME}.tar.gz build-offline/
```

### Документирование изменений

```bash
# Создать changelog
cat > build-offline/CHANGELOG.txt << EOF
Version 2.0.0 (2025-11-06)
==========================
- Добавлен Cline CLI
- Добавлен Qwen Code CLI
- Полная поддержка offline установки
- Автоматические скрипты установки для Windows и Linux
EOF
```

---

**Версия документа:** 1.0  
**Дата:** 2025-11-06  
**Автор:** AI Code Review System Team
