# 🚀 Быстрый старт: Офлайн сборка

## ⚠️ Проблемы в текущем Dockerfile

### Проблема 1: npm пакеты (строки 22-23)
```dockerfile
RUN npm install -g @cline/cli || echo "Warning: Cline CLI not available"
```
→ Сборка успешна, но CLI не установлены → система не работает!

### Проблема 2: Node.js репозиторий (строки 12-13)
```dockerfile
curl -fsSL https://deb.nodesource.com/gpgkey/...
echo "deb [signed-by=...] https://deb.nodesource.com/node_18.x"
```
→ **Требуется доступ в интернет** для скачивания GPG ключа и установки Node.js!

## ✅ Решения

У вас есть **2 варианта** в зависимости от ваших требований:

---

## 🎯 Вариант 1: Модифицированный Dockerfile (частично офлайн)

**Используйте если:** У вас есть доступ к базовому образу `python:3.11-slim` с Node.js

### Шаг 1: Подготовка npm пакетов (нужен интернет)

```bash
# Скачать npm пакеты
cd offline-packages
npm pack @cline/cli
npm pack @qwen-code/qwen-code
cd ..

# ИЛИ использовать готовый скрипт
chmod +x scripts/prepare-offline-build.sh
./scripts/prepare-offline-build.sh
```

**Результат:** Папка `offline-packages/` будет содержать:
- `cline-cli-2.1.0.tgz` (~2.5 MB)
- `qwen-code-1.5.0.tgz` (~1.8 MB)

### Шаг 2: Сборка (требует доступ к Node.js репозиторию)

```bash
# Собрать образ (использует offline-packages/)
docker-compose build

# Проверить, что CLI установлены
docker-compose up -d
docker exec code-review-api cline --version
docker exec code-review-api qwen-code --version
```

### Шаг 3: Перенос на другой сервер

**Вариант A: Готовый образ (рекомендуется)**
```bash
# Сохранить образ
docker save -o review-api.tar code-review-api:latest

# Скопировать на целевой сервер
scp review-api.tar docker-compose.yml .env.example server:/opt/

# На сервере
docker load -i review-api.tar
docker-compose up -d
```

**Вариант B: Исходники для пересборки**
```bash
# Архивировать проект с offline-packages
tar -czf project.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  app/ prompts/ rules/ offline-packages/ \
  docker-compose.yml Dockerfile requirements.txt .env.example

# На целевом сервере
tar -xzf project.tar.gz
docker-compose build
docker-compose up -d
```

---

## 🚀 Вариант 2: Полностью офлайн (РЕКОМЕНДУЕТСЯ)

**Используйте если:** Нет доступа в интернет при сборке вообще

Использует готовый образ `nikolaik/python-nodejs:python3.11-nodejs18-slim`, который уже содержит Python 3.11 + Node.js 18.

### Шаг 1: Подготовка (в среде с интернетом)

```bash
# Автоматический скрипт (делает всё за вас)
chmod +x scripts/prepare-full-offline.sh
./scripts/prepare-full-offline.sh
```

**Что делает скрипт:**
1. Скачивает npm пакеты (cline, qwen-code)
2. Скачивает pip пакеты (опционально)
3. Скачивает базовый Docker образ с Python + Node.js
4. Собирает review-api образ
5. Сохраняет всё в `transfer-full-offline.tar.gz`

**Результат:**
- `transfer-full-offline.tar.gz` (~2-3 GB) - готов к переносу

### Шаг 2: Перенос

```bash
# Скопировать на целевой сервер
scp transfer-full-offline.tar.gz server:/opt/

# На сервере: распаковать
tar -xzf transfer-full-offline.tar.gz
```

### Шаг 3: Развертывание (полностью офлайн)

```bash
# Загрузить образы
docker load -i base-python-nodejs.tar
docker load -i review-api.tar

# Настроить .env
cp .env.example .env
nano .env

# Запустить
docker-compose -f docker-compose.offline.yml up -d
```

**✅ Никаких интернет-запросов при сборке!**

---

## 📊 Сравнение вариантов

| Критерий | Вариант 1 (Dockerfile) | Вариант 2 (Dockerfile.offline) |
|----------|----------------------|-------------------------------|
| **Требует интернет для Node.js** | ✅ Да (deb.nodesource.com) | ❌ Нет |
| **Требует интернет для npm** | ❌ Нет (offline-packages) | ❌ Нет (offline-packages) |
| **Размер базового образа** | ~150 MB | ~300 MB |
| **Простота настройки** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Полностью офлайн** | ❌ Нет | ✅ Да |

---

## ✅ Проверка (для обоих вариантов)

```bash
# Health check
curl http://localhost:8000/health

# Детальная проверка
curl http://localhost:8000/api/v1/health

# Проверка CLI внутри контейнера
docker exec code-review-api cline --version
docker exec code-review-api qwen-code --version
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "cline_available": true,
  "qwen_available": true
}
```

---

## 🔧 Что изменилось в Dockerfile?

### ❌ Старая версия (опасно!)
```dockerfile
RUN npm install -g @cline/cli || echo "Warning: Cline CLI not available"
```
→ Сборка успешна, но CLI не работают!

### ✅ Новая версия (безопасно)
```dockerfile
COPY offline-packages/*.tgz /tmp/npm-packages/
RUN npm install -g /tmp/npm-packages/cline-*.tgz
RUN which cline && cline --version || echo "ERROR: Cline CLI not found!"
```
→ Явная проверка установки + офлайн поддержка

---

## 📚 Полная документация

См. [docs/OFFLINE_BUILD.md](docs/OFFLINE_BUILD.md) для детальной инструкции.

