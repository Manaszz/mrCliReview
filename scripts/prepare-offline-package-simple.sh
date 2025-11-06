#!/bin/bash
set -e

# =============================================================================
# Упрощенный скрипт подготовки офлайн пакета (без Docker образов)
# =============================================================================
# Этот скрипт готовит все файлы, кроме Docker образов
# Docker образы нужно будет собрать на машине с Docker
#
# Использование:
#   chmod +x scripts/prepare-offline-package-simple.sh
#   ./scripts/prepare-offline-package-simple.sh
# =============================================================================

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Определить корень проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Переменные
PACKAGE_NAME="offline-deploy-package"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FINAL_ARCHIVE="${PACKAGE_NAME}-${TIMESTAMP}.tar.gz"

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}Подготовка офлайн пакета (файлы и инструкции)${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo "Корень проекта: ${PROJECT_ROOT}"
echo ""

# Проверка npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm не найден${NC}"
    exit 1
fi

echo -e "${GREEN}✅ npm найден: $(npm --version)${NC}"
echo ""

# Создать временную директорию для пакета
PACKAGE_DIR="${PACKAGE_NAME}-${TIMESTAMP}"
mkdir -p "${PACKAGE_DIR}"

echo -e "${YELLOW}📦 Шаг 1: Подготовка директории для npm пакетов${NC}"
mkdir -p "${PACKAGE_DIR}/offline-packages"

# Создать README с инструкциями по получению npm пакетов
cat > "${PACKAGE_DIR}/offline-packages/README.md" << 'EOFNPM'
# npm пакеты для офлайн установки

## ⚠️ ВАЖНО: npm пакеты не включены в этот архив

Вам нужно скачать npm пакеты отдельно и поместить их в эту директорию перед сборкой Docker образа.

## Требуемые пакеты

1. **Cline CLI** - пакет `@cline/cli` или `cline-cli`
2. **Qwen Code CLI** - пакет `@qwen-code/qwen-code` или `qwen-code`

## Как получить пакеты

### Вариант 1: Если пакеты доступны в npm registry

```bash
cd offline-packages
npm pack @cline/cli
npm pack @qwen-code/qwen-code
```

### Вариант 2: Если пакеты приватные или имеют другое название

1. Узнайте правильное название пакета у администратора проекта
2. Скачайте пакеты с помощью `npm pack` или получите их из внутреннего registry
3. Поместите файлы `*.tgz` в эту директорию

### Вариант 3: Если пакеты уже установлены глобально

```bash
# Найти путь к глобальным пакетам
npm root -g

# Скопировать пакеты или создать архив
```

## Проверка

После добавления пакетов проверьте:

```bash
ls -lh offline-packages/*.tgz
```

Должны быть файлы:
- `cline-cli-*.tgz` или `@cline-cli-*.tgz`
- `qwen-code-*.tgz` или `@qwen-code-*.tgz`

## Использование

Dockerfile.offline автоматически установит эти пакеты при сборке образа.
EOFNPM

cd "${PROJECT_ROOT}"
echo -e "${GREEN}✅ Директория для npm пакетов создана${NC}"
echo -e "${YELLOW}⚠️  npm пакеты нужно добавить вручную (см. offline-packages/README.md)${NC}"
echo ""

echo -e "${YELLOW}📝 Шаг 2: Копирование файлов проекта${NC}"
echo "  → Копирование файлов..."
cp "${PROJECT_ROOT}/Dockerfile.offline" "${PACKAGE_DIR}/"
cp "${PROJECT_ROOT}/docker-compose.offline.yml" "${PACKAGE_DIR}/"
cp "${PROJECT_ROOT}/requirements.txt" "${PACKAGE_DIR}/"
cp -r "${PROJECT_ROOT}/app" "${PACKAGE_DIR}/"
cp -r "${PROJECT_ROOT}/prompts" "${PACKAGE_DIR}/"
cp -r "${PROJECT_ROOT}/rules" "${PACKAGE_DIR}/"
cp "${PROJECT_ROOT}/.env.example" "${PACKAGE_DIR}/" 2>/dev/null || true
cp "${PROJECT_ROOT}/env.example.annotated" "${PACKAGE_DIR}/" 2>/dev/null || true
cp "${PROJECT_ROOT}/README.md" "${PACKAGE_DIR}/" 2>/dev/null || true
cp "${PROJECT_ROOT}/OFFLINE_QUICK_START.md" "${PACKAGE_DIR}/" 2>/dev/null || true

echo -e "${GREEN}✅ Файлы скопированы${NC}"
echo ""

echo -e "${YELLOW}📝 Шаг 3: Создание инструкций${NC}"

# Создать инструкции для Windows (из скрипта prepare-offline-deploy-package.sh)
cat > "${PACKAGE_DIR}/INSTALL_WINDOWS.md" << 'EOFWINDOWS'
# Установка на изолированном Windows PC

## Требования

- Windows 10/11 или Windows Server 2019+
- Docker Desktop для Windows (или Docker Engine)
- Минимум 10 GB свободного места на диске
- PowerShell 5.1+ или PowerShell Core 7+

## Шаг 1: Установка Docker Desktop

1. Скачайте Docker Desktop для Windows:
   - Перейдите на https://www.docker.com/products/docker-desktop
   - Скачайте установщик Docker Desktop

2. Установите Docker Desktop:
   - Запустите установщик `Docker Desktop Installer.exe`
   - Следуйте инструкциям мастера установки
   - После установки перезагрузите компьютер

3. Проверьте установку:
   ```powershell
   docker --version
   docker-compose --version
   ```

## Шаг 2: Распаковка архива

1. Скопируйте архив `offline-deploy-package-*.tar.gz` на ваш компьютер

2. Распакуйте архив:
   ```powershell
   # Используйте 7-Zip или WinRAR для распаковки .tar.gz
   # Или используйте PowerShell (требует .NET Core):
   tar -xzf offline-deploy-package-*.tar.gz
   ```

3. Перейдите в распакованную директорию:
   ```powershell
   cd offline-deploy-package-*
   ```

## Шаг 3: Сборка Docker образов

**ВАЖНО:** В этом пакете нет готовых Docker образов. Их нужно собрать.

### 3.1: Скачать базовый образ

```powershell
docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim
```

### 3.2: Сохранить базовый образ (для переноса на другую машину)

```powershell
docker save -o base-python-nodejs.tar nikolaik/python-nodejs:python3.11-nodejs18-slim
```

### 3.3: Собрать образ приложения

```powershell
docker-compose -f docker-compose.offline.yml build
```

### 3.4: Сохранить образ приложения (опционально)

```powershell
docker save -o review-api.tar code-review-api:latest
```

## Шаг 4: Настройка конфигурации

1. Скопируйте пример конфигурации:
   ```powershell
   copy .env.example .env
   ```

2. Откройте `.env` в текстовом редакторе (Notepad, VS Code) и заполните:

   ```env
   # Model API (обязательно)
   MODEL_API_URL=https://your-model-api.example.com/v1
   MODEL_API_KEY=your-api-key-here
   
   # Модели
   DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
   QWEN3_MODEL_NAME=qwen3-coder-32b
   
   # GitLab (обязательно)
   GITLAB_URL=https://gitlab.example.com
   GITLAB_TOKEN=glpat-your-token-here
   
   # CLI настройки
   DEFAULT_CLI_AGENT=CLINE
   CLINE_PARALLEL_TASKS=5
   QWEN_PARALLEL_TASKS=3
   REVIEW_TIMEOUT=300
   
   # Приложение
   LOG_LEVEL=INFO
   ```

   **ВАЖНО**: Замените все значения на ваши реальные данные!

## Шаг 5: Запуск контейнера

```powershell
# Запустить контейнер
docker-compose -f docker-compose.offline.yml up -d

# Проверить статус
docker-compose -f docker-compose.offline.yml ps

# Просмотреть логи
docker-compose -f docker-compose.offline.yml logs -f
```

## Шаг 6: Проверка работы

1. Проверьте health endpoint:
   ```powershell
   curl http://localhost:8000/health
   # Или в браузере: http://localhost:8000/health
   ```

2. Проверьте детальный health:
   ```powershell
   curl http://localhost:8000/api/v1/health
   ```

3. Проверьте CLI внутри контейнера:
   ```powershell
   docker exec code-review-api cline --version
   docker exec code-review-api qwen-code --version
   ```

Ожидаемый ответ health endpoint:
```json
{
  "status": "healthy",
  "cline_available": true,
  "qwen_available": true,
  "model_api_connected": true,
  "gitlab_connected": true
}
```

## Управление контейнером

### Остановить контейнер:
```powershell
docker-compose -f docker-compose.offline.yml stop
```

### Запустить контейнер:
```powershell
docker-compose -f docker-compose.offline.yml start
```

### Перезапустить контейнер:
```powershell
docker-compose -f docker-compose.offline.yml restart
```

### Остановить и удалить контейнер:
```powershell
docker-compose -f docker-compose.offline.yml down
```

### Просмотр логов:
```powershell
docker-compose -f docker-compose.offline.yml logs -f review-api
```

## Решение проблем

### Проблема: Docker не запускается

**Решение:**
1. Убедитесь, что Docker Desktop запущен (иконка в системном трее)
2. Проверьте, что WSL 2 установлен (для Windows 10/11)
3. Перезапустите Docker Desktop

### Проблема: Порт 8000 уже занят

**Решение:**
Измените порт в `docker-compose.offline.yml`:
```yaml
ports:
  - "8001:8000"  # Используйте другой порт
```

### Проблема: CLI не найдены в контейнере

**Решение:**
1. Проверьте, что npm пакеты есть в `offline-packages/`
2. Пересоберите образ:
   ```powershell
   docker-compose -f docker-compose.offline.yml build --no-cache
   ```

### Проблема: Не удается подключиться к Model API

**Решение:**
1. Проверьте доступность API:
   ```powershell
   curl -H "Authorization: Bearer YOUR_API_KEY" https://your-api.example.com/v1/models
   ```

2. Проверьте настройки в `.env` файле
3. Проверьте файрвол Windows (может блокировать исходящие соединения)

## Дополнительная информация

- Подробная документация: см. `README.md` и `OFFLINE_QUICK_START.md`
- Примеры конфигурации: см. `env.example.annotated`
- Логи приложения: `logs/` (если смонтированы)
EOFWINDOWS

# Создать инструкции для VPS
cat > "${PACKAGE_DIR}/INSTALL_VPS.md" << 'EOFVPS'
# Установка на изолированном VPS сервере

## Требования

- Linux сервер (Ubuntu 20.04+, Debian 11+, CentOS 8+, или аналогичный)
- Docker Engine 20.10+ или Docker CE
- Docker Compose 1.29+ (или docker compose plugin)
- Минимум 10 GB свободного места на диске
- Минимум 4 GB RAM (рекомендуется 8 GB+)
- Доступ к серверу по SSH с правами sudo

## Шаг 1: Установка Docker (если не установлен)

### Ubuntu/Debian:

```bash
# Обновить пакеты
sudo apt-get update

# Установить зависимости
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Добавить официальный GPG ключ Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Настроить репозиторий
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установить Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Добавить текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Выйти и войти снова, чтобы изменения вступили в силу
```

### CentOS/RHEL:

```bash
# Установить зависимости
sudo yum install -y yum-utils

# Добавить репозиторий Docker
sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# Установить Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Запустить Docker
sudo systemctl start docker
sudo systemctl enable docker

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
```

### Проверка установки:

```bash
docker --version
docker compose version
```

## Шаг 2: Распаковка архива

1. Скопируйте архив на сервер (например, через SCP):

   ```bash
   # С вашего компьютера
   scp offline-deploy-package-*.tar.gz user@your-server:/opt/
   ```

2. Подключитесь к серверу:

   ```bash
   ssh user@your-server
   ```

3. Распакуйте архив:

   ```bash
   cd /opt
   tar -xzf offline-deploy-package-*.tar.gz
   cd offline-deploy-package-*
   ```

## Шаг 3: Сборка Docker образов

**ВАЖНО:** В этом пакете нет готовых Docker образов. Их нужно собрать.

### 3.1: Скачать базовый образ

```bash
docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim
```

### 3.2: Сохранить базовый образ (для переноса на другую машину)

```bash
docker save -o base-python-nodejs.tar nikolaik/python-nodejs:python3.11-nodejs18-slim
```

### 3.3: Собрать образ приложения

```bash
docker-compose -f docker-compose.offline.yml build
```

### 3.4: Сохранить образ приложения (опционально)

```bash
docker save -o review-api.tar code-review-api:latest
```

## Шаг 4: Настройка конфигурации

1. Скопируйте пример конфигурации:

   ```bash
   cp .env.example .env
   ```

2. Отредактируйте `.env` файл:

   ```bash
   nano .env
   # или
   vi .env
   ```

3. Заполните обязательные параметры:

   ```env
   # Model API (обязательно)
   MODEL_API_URL=https://your-model-api.example.com/v1
   MODEL_API_KEY=your-api-key-here
   
   # Модели
   DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
   QWEN3_MODEL_NAME=qwen3-coder-32b
   
   # GitLab (обязательно)
   GITLAB_URL=https://gitlab.example.com
   GITLAB_TOKEN=glpat-your-token-here
   
   # CLI настройки
   DEFAULT_CLI_AGENT=CLINE
   CLINE_PARALLEL_TASKS=5
   QWEN_PARALLEL_TASKS=3
   REVIEW_TIMEOUT=300
   
   # Приложение
   LOG_LEVEL=INFO
   ```

   **ВАЖНО**: Замените все значения на ваши реальные данные!

4. Установите правильные права доступа:

   ```bash
   chmod 600 .env
   ```

## Шаг 5: Запуск контейнера

```bash
# Запустить контейнер в фоновом режиме
docker-compose -f docker-compose.offline.yml up -d

# Проверить статус
docker-compose -f docker-compose.offline.yml ps

# Просмотреть логи
docker-compose -f docker-compose.offline.yml logs -f
```

## Шаг 6: Проверка работы

1. Проверьте health endpoint:

   ```bash
   curl http://localhost:8000/health
   ```

2. Проверьте детальный health:

   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. Проверьте CLI внутри контейнера:

   ```bash
   docker exec code-review-api cline --version
   docker exec code-review-api qwen-code --version
   ```

Ожидаемый ответ health endpoint:
```json
{
  "status": "healthy",
  "cline_available": true,
  "qwen_available": true,
  "model_api_connected": true,
  "gitlab_connected": true
}
```

## Шаг 7: Настройка автозапуска (опционально)

### Использование systemd:

1. Создайте systemd service файл:

   ```bash
   sudo nano /etc/systemd/system/code-review-api.service
   ```

2. Добавьте содержимое:

   ```ini
   [Unit]
   Description=Code Review API Docker Compose
   Requires=docker.service
   After=docker.service

   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/opt/offline-deploy-package-*
   ExecStart=/usr/bin/docker compose -f docker-compose.offline.yml up -d
   ExecStop=/usr/bin/docker compose -f docker-compose.offline.yml down
   TimeoutStartSec=0

   [Install]
   WantedBy=multi-user.target
   ```

3. Активируйте сервис:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable code-review-api.service
   sudo systemctl start code-review-api.service
   ```

## Управление контейнером

### Остановить контейнер:

```bash
docker-compose -f docker-compose.offline.yml stop
```

### Запустить контейнер:

```bash
docker-compose -f docker-compose.offline.yml start
```

### Перезапустить контейнер:

```bash
docker-compose -f docker-compose.offline.yml restart
```

### Остановить и удалить контейнер:

```bash
docker-compose -f docker-compose.offline.yml down
```

### Просмотр логов:

```bash
# Все логи
docker-compose -f docker-compose.offline.yml logs -f

# Только review-api
docker-compose -f docker-compose.offline.yml logs -f review-api

# Последние 100 строк
docker-compose -f docker-compose.offline.yml logs --tail=100 review-api
```

## Настройка файрвола

Если используете файрвол (ufw, firewalld), откройте порт 8000:

### UFW (Ubuntu):

```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

### Firewalld (CentOS/RHEL):

```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## Решение проблем

### Проблема: Docker не запускается

**Решение:**
```bash
# Проверить статус Docker
sudo systemctl status docker

# Запустить Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### Проблема: Порт 8000 уже занят

**Решение:**
Измените порт в `docker-compose.offline.yml`:
```yaml
ports:
  - "8001:8000"  # Используйте другой порт
```

### Проблема: Permission denied при запуске docker

**Решение:**
```bash
# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Выйти и войти снова
exit
# Затем подключиться снова
```

### Проблема: CLI не найдены в контейнере

**Решение:**
1. Проверьте, что npm пакеты есть в `offline-packages/`
2. Пересоберите образ:
   ```bash
   docker-compose -f docker-compose.offline.yml build --no-cache
   ```

### Проблема: Не удается подключиться к Model API

**Решение:**
1. Проверьте доступность API:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" https://your-api.example.com/v1/models
   ```

2. Проверьте настройки в `.env` файле
3. Проверьте файрвол и сетевые настройки

### Проблема: Недостаточно места на диске

**Решение:**
```bash
# Очистить неиспользуемые Docker ресурсы
docker system prune -a

# Проверить использование диска
df -h
```

## Мониторинг и логи

### Просмотр использования ресурсов:

```bash
docker stats code-review-api
```

### Ротация логов (опционально):

Добавьте в `docker-compose.offline.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Дополнительная информация

- Подробная документация: см. `README.md` и `OFFLINE_QUICK_START.md`
- Примеры конфигурации: см. `env.example.annotated`
- Логи приложения: `logs/` (если смонтированы)

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose -f docker-compose.offline.yml logs`
2. Проверьте health endpoint: `curl http://localhost:8000/api/v1/health`
3. Убедитесь, что все переменные окружения заполнены правильно
4. Проверьте системные логи: `journalctl -u docker` или `journalctl -u code-review-api`
EOFVPS

# Создать README для пакета
cat > "${PACKAGE_DIR}/PACKAGE_README.md" << 'EOFPACKAGE'
# Офлайн пакет развертывания Code Review System

Этот пакет содержит все необходимое для развертывания Code Review System на изолированных системах без доступа к интернету.

## ⚠️ ВАЖНО: Docker образы не включены

В этом пакете **НЕТ готовых Docker образов**. Их нужно собрать на машине с Docker перед развертыванием.

### Как получить Docker образы:

1. **На машине с Docker и интернетом:**
   ```bash
   # Скачать базовый образ
   docker pull nikolaik/python-nodejs:python3.11-nodejs18-slim
   
   # Собрать образ приложения
   docker-compose -f docker-compose.offline.yml build
   
   # Сохранить образы (опционально)
   docker save -o base-python-nodejs.tar nikolaik/python-nodejs:python3.11-nodejs18-slim
   docker save -o review-api.tar code-review-api:latest
   ```

2. **Перенести образы на целевую систему** (если нужно)

## Содержимое пакета

- `offline-packages/` - npm пакеты для офлайн установки (@cline/cli, @qwen-code/qwen-code)
- `app/` - Исходный код приложения
- `prompts/` - Промпты для CLI агентов
- `rules/` - Правила code review
- `docker-compose.offline.yml` - Конфигурация Docker Compose для офлайн режима
- `Dockerfile.offline` - Dockerfile для офлайн сборки
- `requirements.txt` - Python зависимости
- `.env.example` - Пример конфигурации
- `INSTALL_WINDOWS.md` - Инструкции для Windows
- `INSTALL_VPS.md` - Инструкции для VPS сервера
- `README.md` - Основная документация проекта

## Быстрый старт

### Для Windows:
См. `INSTALL_WINDOWS.md`

### Для VPS/Linux:
См. `INSTALL_VPS.md`

## Основные шаги (общие)

1. **Установите Docker** (если не установлен)
2. **Распакуйте архив**
3. **Соберите Docker образы** (см. инструкции выше)
4. **Настройте `.env`** файл (скопируйте из `.env.example`)
5. **Запустите**: `docker-compose -f docker-compose.offline.yml up -d`
6. **Проверьте**: `curl http://localhost:8000/api/v1/health`

## Требования

- Docker Engine 20.10+ или Docker Desktop
- Docker Compose 1.29+ или docker compose plugin
- Минимум 10 GB свободного места
- Минимум 4 GB RAM (рекомендуется 8 GB+)

## Проверка установки

После запуска проверьте:

```bash
# Health check
curl http://localhost:8000/health

# Детальный health
curl http://localhost:8000/api/v1/health

# Проверка CLI
docker exec code-review-api cline --version
docker exec code-review-api qwen-code --version
```

## Поддержка

При возникновении проблем см. раздел "Решение проблем" в соответствующих инструкциях:
- Windows: `INSTALL_WINDOWS.md`
- VPS: `INSTALL_VPS.md`

## Версия пакета

Пакет создан: ${TIMESTAMP}
Версия приложения: см. `README.md`
EOFPACKAGE

# Заменить плейсхолдер в README
sed -i "s/\${TIMESTAMP}/${TIMESTAMP}/g" "${PACKAGE_DIR}/PACKAGE_README.md"

cd "${PROJECT_ROOT}"

echo -e "${YELLOW}📦 Шаг 4: Создание финального архива${NC}"
tar -czf "${PROJECT_ROOT}/${FINAL_ARCHIVE}" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs' \
    --exclude='*.log' \
    -C "${PROJECT_ROOT}" \
    "${PACKAGE_DIR}"

echo -e "${GREEN}✅ Архив создан: ${PROJECT_ROOT}/${FINAL_ARCHIVE}${NC}"
echo ""

# Показать размер и содержимое
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}✅ Подготовка завершена успешно!${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "${YELLOW}📦 Файл для переноса:${NC} ${PROJECT_ROOT}/${FINAL_ARCHIVE}"
echo -e "${YELLOW}📊 Размер архива:${NC} $(du -h "${PROJECT_ROOT}/${FINAL_ARCHIVE}" | cut -f1)"
echo ""
echo -e "${YELLOW}📋 Содержимое пакета:${NC}"
ls -lh "${PACKAGE_DIR}/" | head -20
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${YELLOW}ВАЖНО: Docker образы не включены!${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo "Этот пакет содержит все файлы, кроме Docker образов."
echo "Docker образы нужно собрать на машине с Docker перед развертыванием."
echo ""
echo "См. инструкции в PACKAGE_README.md для получения Docker образов."
echo ""
echo -e "${GREEN}Готово!${NC}"
