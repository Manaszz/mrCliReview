# Офлайн сборка Docker образа

Инструкция по сборке и запуску системы без доступа к интернету.

## 🎯 Сценарии использования

1. **Air-gapped среда** (полностью изолированная от интернета)
2. **Корпоративная сеть** без прямого доступа к npm/pypi
3. **Ограниченный интернет** (низкая скорость, прокси)

---

## 📋 Предварительные требования

### В среде с интернетом
- Node.js 18+ и npm 9+
- Docker и Docker Compose
- Python 3.11+ (опционально, для подготовки pip пакетов)

### В изолированной среде (целевой сервер)
- Docker и Docker Compose
- 5GB свободного места на диске

---

## 🔧 Часть 1: Подготовка (среда с интернетом)

### Шаг 1: Скачать npm пакеты

**Вариант A: Использовать скрипт (рекомендуется)**

```bash
# Сделать скрипт исполняемым
chmod +x scripts/prepare-offline-build.sh

# Запустить
./scripts/prepare-offline-build.sh
```

**Вариант B: Вручную**

```bash
# Перейти в папку
cd offline-packages

# Скачать пакеты
npm pack @cline/cli
npm pack @qwen-code/qwen-code

# Проверить
ls -lh *.tgz
```

Ожидаемый результат:
```
-rw-r--r-- 1 user user 2.5M Nov  3 15:30 cline-cli-2.1.0.tgz
-rw-r--r-- 1 user user 1.8M Nov  3 15:31 qwen-code-1.5.0.tgz
```

### Шаг 2: Скачать Python пакеты (опционально)

```bash
# Создать папку
mkdir -p offline-packages/pip

# Скачать все зависимости
pip download -r requirements.txt -d offline-packages/pip/

# Проверить
ls offline-packages/pip/ | wc -l
# Должно быть ~30-40 файлов
```

### Шаг 3: Собрать Docker образ

```bash
# В корне проекта
docker-compose build

# Сохранить образ в файл
docker save -o review-api-image.tar code-review-api:latest

# Также сохранить базовый образ Python (если его нет на целевом сервере)
docker pull python:3.11-slim
docker save -o python-3.11-slim.tar python:3.11-slim
```

### Шаг 4: Создать transfer пакет

**Вариант A: Полный пакет (образы + исходники)**

```bash
# Создать архив
tar -czf transfer-package-full.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='logs' \
  review-api-image.tar \
  python-3.11-slim.tar \
  app/ \
  prompts/ \
  rules/ \
  offline-packages/ \
  docker-compose.yml \
  Dockerfile \
  requirements.txt \
  .env.example \
  README.md

# Проверить размер
ls -lh transfer-package-full.tar.gz
```

**Вариант B: Только исходники (для пересборки на сервере)**

```bash
tar -czf transfer-package-sources.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  app/ \
  prompts/ \
  rules/ \
  offline-packages/ \
  docker-compose.yml \
  Dockerfile \
  requirements.txt \
  .env.example \
  README.md \
  scripts/

ls -lh transfer-package-sources.tar.gz
```

---

## 🚀 Часть 2: Развертывание (изолированная среда)

### Вариант A: Использовать готовый образ (быстрее)

```bash
# 1. Скопировать файл на сервер
scp transfer-package-full.tar.gz server:/opt/
ssh server

# 2. Распаковать
cd /opt
tar -xzf transfer-package-full.tar.gz

# 3. Загрузить образы
docker load -i python-3.11-slim.tar
docker load -i review-api-image.tar

# 4. Настроить .env
cp .env.example .env
nano .env

# 5. Запустить
docker-compose up -d

# 6. Проверить
docker-compose logs -f
curl http://localhost:8000/health
```

### Вариант B: Пересобрать на сервере (для кастомизации)

```bash
# 1. Скопировать исходники
scp transfer-package-sources.tar.gz server:/opt/
ssh server

# 2. Распаковать
cd /opt
tar -xzf transfer-package-sources.tar.gz

# 3. Настроить .env
cp .env.example .env
nano .env

# 4. Собрать образ (офлайн, использует offline-packages/)
docker-compose build

# 5. Запустить
docker-compose up -d
```

---

## ✅ Проверка установки

### 1. Проверить статус контейнеров

```bash
docker-compose ps
```

Ожидаемый вывод:
```
NAME                COMMAND               STATUS    PORTS
code-review-api     uvicorn app.main...   Up        0.0.0.0:8000->8000/tcp
```

### 2. Проверить health endpoint

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:
```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

### 3. Проверить детальный health

```bash
curl http://localhost:8000/api/v1/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "cline_available": true,
  "qwen_available": true,
  "model_api_connected": true,
  "gitlab_connected": true
}
```

### 4. Проверить CLI внутри контейнера

```bash
# Войти в контейнер
docker exec -it code-review-api /bin/bash

# Проверить CLI
cline --version
qwen-code --version

# Проверить Node.js
node --version
npm --version

# Проверить Python пакеты
pip list | grep fastapi
pip list | grep httpx

# Выйти
exit
```

### 5. Проверить логи

```bash
# Посмотреть логи API
docker-compose logs review-api

# Следить за логами в реальном времени
docker-compose logs -f review-api

# Последние 100 строк
docker-compose logs --tail=100 review-api
```

---

## 🔧 Troubleshooting

### Проблема 1: CLI не установлены

**Симптомы:**
```
ERROR: Cline CLI not found!
ERROR: Qwen Code CLI not found!
```

**Решение:**
```bash
# Проверить наличие пакетов
ls -la offline-packages/*.tgz

# Если пакетов нет - скачать их в среде с интернетом
cd offline-packages
npm pack @cline/cli
npm pack @qwen-code/qwen-code

# Пересобрать образ
docker-compose build --no-cache
```

### Проблема 2: Python пакеты не установились

**Симптомы:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Решение - Вариант A: Использовать pip cache**
```bash
# В Dockerfile добавить перед pip install:
RUN pip install --no-cache-dir --no-index --find-links=offline-packages/pip/ -r requirements.txt
```

**Решение - Вариант B: Установить вручную**
```bash
docker cp offline-packages/pip code-review-api:/tmp/pip-packages
docker exec code-review-api pip install --no-index --find-links=/tmp/pip-packages -r requirements.txt
```

### Проблема 3: Node.js не установился

**Симптомы:**
```
/bin/sh: 1: npm: not found
```

**Решение:**

Проверить, что в Dockerfile строки 6-16 выполняются успешно. Если у вас нет доступа к deb.nodesource.com, нужно:

1. Скачать Node.js .deb пакет отдельно
2. Добавить в offline-packages/
3. Модифицировать Dockerfile для локальной установки

### Проблема 4: Сборка падает на COPY offline-packages

**Симптомы:**
```
COPY failed: no source files were specified
```

**Решение:**
```bash
# Создать папку с хотя бы одним файлом
mkdir -p offline-packages
touch offline-packages/.gitkeep

# Или закомментировать строку в Dockerfile, если CLI не нужны
```

---

## 📊 Размеры файлов

Примерные размеры для переноса:

| Компонент | Размер |
|-----------|--------|
| review-api-image.tar | 1.5 - 2.0 GB |
| python-3.11-slim.tar | 150 MB |
| npm пакеты (*.tgz) | 4 - 5 MB |
| pip пакеты | 50 - 80 MB |
| Исходный код | 5 - 10 MB |
| **ИТОГО (полный пакет)** | **~2.2 GB** |
| **ИТОГО (только исходники)** | **~60 MB** |

---

## 🔐 Безопасность

### Проверка целостности

**При подготовке (среда с интернетом):**
```bash
# Создать checksums
sha256sum transfer-package-full.tar.gz > checksums.txt
```

**При развертывании (изолированная среда):**
```bash
# Проверить checksum
sha256sum -c checksums.txt
```

### GPG подпись (опционально)

```bash
# Подписать пакет
gpg --detach-sign transfer-package-full.tar.gz

# Проверить подпись
gpg --verify transfer-package-full.tar.gz.sig
```

---

## 🆕 Обновления

### Обновление образа

```bash
# В среде с интернетом
docker-compose build
docker save -o review-api-update.tar code-review-api:latest

# Перенести на сервер
scp review-api-update.tar server:/opt/

# На сервере
docker load -i review-api-update.tar
docker-compose down
docker-compose up -d
```

### Обновление только кода (без пересборки)

```bash
# Создать патч
tar -czf update-patch.tar.gz app/ prompts/ rules/

# На сервере
docker cp app/ code-review-api:/app/
docker-compose restart
```

---

## 📚 Связанные документы

- [DEPLOYMENT_GUIDE_RU.md](DEPLOYMENT_GUIDE_RU.md) - Полное руководство по развертыванию
- [AIR_GAP_TRANSFER.md](AIR_GAP_TRANSFER.md) - Детальная инструкция для air-gap среды
- [CLI_SETUP.md](CLI_SETUP.md) - Настройка CLI инструментов

---

**Обновлено:** 2025-11-03  
**Версия:** 1.0.0


