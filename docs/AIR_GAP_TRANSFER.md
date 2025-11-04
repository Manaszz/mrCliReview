# Руководство по Air-Gap передаче

## Обзор

Это руководство предоставляет пошаговые инструкции для развёртывания системы code review в air-gapped (изолированной) среде без доступа в интернет.

---

## Предварительные требования

### Требования к подключённой среде
- Доступ в интернет
- Docker и Docker Compose
- Python 3.11+
- Node.js 18+
- npm 9+
- 20GB свободного места на диске для архивов

### Требования к изолированной среде
- Установленные Docker и Docker Compose
- Доступ к внутреннему model API
- Доступ к внутреннему GitLab instance
- 20GB свободного места на диске
- Внутренний container registry (опционально, но рекомендуется)

---

## Фаза 1: Подготовка (Подключённая среда)

### Шаг 1: Экспорт Docker образов

```bash
# Перейдите в директорию проекта
cd code-review-system

# Соберите Docker образ
docker-compose build

# Экспортируйте образ review API
docker save -o review-api.tar review-api:latest

# Экспортируйте базовый Python образ (если недоступен в изолированной среде)
docker pull python:3.11-slim
docker save -o python-3.11-slim.tar python:3.11-slim

# Проверьте архивы
ls -lh *.tar
```

Ожидаемый вывод:
```
-rw-r--r-- 1 user user 1.2G Nov  3 10:00 review-api.tar
-rw-r--r-- 1 user user 150M Nov  3 10:05 python-3.11-slim.tar
```

---

### Шаг 2: Скачать npm пакеты

```bash
# Создайте директорию для пакетов
mkdir -p air-gap-packages/npm

# Скачайте Cline CLI
cd air-gap-packages/npm
npm pack @cline/cli
npm pack @qwen-code/qwen-code

# Скачайте зависимости
mkdir cline-deps qwen-deps

# Зависимости Cline
cd cline-deps
npm install @cline/cli --no-save
tar -czf ../cline-dependencies.tar.gz node_modules/
cd ..

# Зависимости Qwen Code
cd qwen-deps
npm install @qwen-code/qwen-code --no-save
tar -czf ../qwen-dependencies.tar.gz node_modules/
cd ../..

# Проверьте пакеты
ls -lh air-gap-packages/npm/
```

---

### Шаг 3: Создать offline репозиторий Python

```bash
# Создайте директорию для pip пакетов
mkdir -p air-gap-packages/pip

# Скачайте все Python зависимости
pip download \
  -r requirements.txt \
  -d air-gap-packages/pip/

# Проверьте пакеты
ls -lh air-gap-packages/pip/ | wc -l
# Должно показать 20-30 пакетов
```

---

### Шаг 4: Архивировать файлы приложения

```bash
# Создайте архив кода приложения
tar -czf code-review-app.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='venv' \
  --exclude='node_modules' \
  app/ \
  prompts/ \
  rules/ \
  docs/ \
  tests/ \
  docker-compose.yml \
  Dockerfile \
  requirements.txt \
  .env.example \
  README.md
```

---

### Шаг 5: Создать пакет для передачи

```bash
# Создайте финальную директорию передачи
mkdir -p air-gap-transfer

# Переместите все артефакты
mv review-api.tar air-gap-transfer/
mv python-3.11-slim.tar air-gap-transfer/
mv code-review-app.tar.gz air-gap-transfer/
mv air-gap-packages air-gap-transfer/

# Создайте скрипт установки
cat > air-gap-transfer/install.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Установка Code Review System для Air-Gap ==="

# Загрузить Docker образы
echo "Загрузка Docker образов..."
docker load -i review-api.tar
docker load -i python-3.11-slim.tar

# Извлечь приложение
echo "Извлечение файлов приложения..."
tar -xzf code-review-app.tar.gz

# Установить npm пакеты
echo "Установка CLI инструментов..."
npm install -g air-gap-packages/npm/cline-cli-*.tgz
npm install -g air-gap-packages/npm/qwen-code-*.tgz

# Проверить установки
cline --version
qwen-code --version

echo "=== Установка завершена ==="
echo "Следующие шаги:"
echo "1. Настройте .env файл"
echo "2. Запустите: docker-compose up -d"
echo "3. Проверьте логи: docker-compose logs -f"
EOF

chmod +x air-gap-transfer/install.sh

# Создайте README
cat > air-gap-transfer/README.txt << 'EOF'
Code Review System - Пакет для Air-Gap передачи
==============================================

Содержимое:
- review-api.tar: Docker образ для review API
- python-3.11-slim.tar: Базовый Python Docker образ
- code-review-app.tar.gz: Код приложения и конфигурация
- air-gap-packages/: npm и pip пакеты
- install.sh: Скрипт установки

Установка:
1. Перенесите всю эту директорию в изолированную среду
2. Запустите: ./install.sh
3. Следуйте инструкциям после установки

Для детальных инструкций см. docs/AIR_GAP_TRANSFER.md
EOF

# Создайте манифест
cat > air-gap-transfer/MANIFEST.txt << 'EOF'
Манифест пакета - Создан $(date)
====================================

Docker образы:
- review-api:latest
- python:3.11-slim

NPM пакеты:
- @cline/cli@2.1.0
- @qwen-code/qwen-code@1.5.0

Python пакеты:
$(ls -1 air-gap-packages/pip/ | head -20)
...

Общий размер: $(du -sh air-gap-transfer | cut -f1)
EOF

# Создайте финальный архив
cd ..
tar -czf code-review-air-gap-$(date +%Y%m%d).tar.gz air-gap-transfer/

echo "=== Пакет готов ==="
ls -lh code-review-air-gap-*.tar.gz
```

---

## Фаза 2: Передача

### Варианты физической передачи

#### Вариант 1: Внешний диск
```bash
# Скопируйте на USB диск
cp code-review-air-gap-*.tar.gz /media/usb-drive/

# Безопасно извлеките
sync
umount /media/usb-drive
```

#### Вариант 2: Внутренняя система передачи файлов
```bash
# Загрузите во внутреннюю систему передачи
# (Специфично для процесса вашей организации)
```

#### Вариант 3: CD/DVD
```bash
# Для меньших пакетов
brasero code-review-air-gap-*.tar.gz
```

---

## Фаза 3: Установка (Изолированная среда)

### Шаг 1: Извлечь пакет передачи

```bash
# Перенесите файл на изолированный сервер
scp code-review-air-gap-20251103.tar.gz isolated-server:/opt/

# SSH на изолированный сервер
ssh isolated-server

# Извлеките пакет
cd /opt
tar -xzf code-review-air-gap-20251103.tar.gz
cd air-gap-transfer
```

---

### Шаг 2: Запустить скрипт установки

```bash
# Сделайте скрипт исполняемым (если нужно)
chmod +x install.sh

# Запустите установку
sudo ./install.sh
```

Ожидаемый вывод:
```
=== Установка Code Review System для Air-Gap ===
Загрузка Docker образов...
Loaded image: review-api:latest
Loaded image: python:3.11-slim
Извлечение файлов приложения...
Установка CLI инструментов...
/usr/local/bin/cline -> ...
/usr/local/bin/qwen-code -> ...
cline version 2.1.0
qwen-code version 1.5.0
=== Установка завершена ===
```

---

### Шаг 3: Настроить окружение

```bash
# Скопируйте example env файл
cp .env.example .env

# Редактируйте конфигурацию
nano .env
```

Требуемая конфигурация для изолированной среды:

```env
# Model API (внутренний endpoint)
MODEL_API_URL=https://internal-model-api.company.local/v1
MODEL_API_KEY=your-internal-api-key

# Имена моделей (должны быть доступны во внутреннем развёртывании)
DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
QWEN3_MODEL_NAME=qwen3-coder-32b

# GitLab (внутренний instance)
GITLAB_URL=https://gitlab.company.local
GITLAB_TOKEN=your-gitlab-token

# Конфигурация CLI
DEFAULT_CLI_AGENT=CLINE
CLINE_PARALLEL_TASKS=5
QWEN_PARALLEL_TASKS=3

# Приложение
LOG_LEVEL=INFO
REVIEW_TIMEOUT=300
```

---

### Шаг 4: Настроить CLI

```bash
# Настройте Cline CLI
mkdir -p ~/.config/cline
cat > ~/.config/cline/config.json << EOF
{
  "model": {
    "provider": "openai-compatible",
    "baseURL": "https://internal-model-api.company.local/v1",
    "apiKey": "\${MODEL_API_KEY}",
    "model": "deepseek-v3.1-terminus"
  },
  "parallelTasks": 5,
  "timeout": 300000
}
EOF

# Настройте Qwen Code CLI
mkdir -p ~/.config/qwen-code
cat > ~/.config/qwen-code/config.json << EOF
{
  "model": {
    "provider": "openai-compatible",
    "baseURL": "https://internal-model-api.company.local/v1",
    "apiKey": "\${MODEL_API_KEY}",
    "model": "qwen3-coder-32b"
  },
  "parallelTasks": 3,
  "timeout": 180000
}
EOF
```

---

### Шаг 5: Запустить сервисы

```bash
# Запустите с docker-compose
docker-compose up -d

# Проверьте статус
docker-compose ps

# Просмотрите логи
docker-compose logs -f review-api
```

Ожидаемый вывод:
```
review-api_1  | INFO:     Started server process
review-api_1  | INFO:     Waiting for application startup.
review-api_1  | INFO:     Application startup complete.
review-api_1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Шаг 6: Проверить установку

```bash
# Протестируйте health endpoint
curl http://localhost:8000/api/v1/health

# Ожидаемый ответ
{
  "status": "healthy",
  "version": "2.0.0",
  "cline_available": true,
  "qwen_available": true,
  "model_api_connected": true
}

# Протестируйте CLI соединения
cline --test-connection
qwen-code --test-connection
```

---

## Фаза 4: Внутренний Container Registry (Опционально)

Для более простого управления, загрузите образы во внутренний registry:

### Настройка

```bash
# Пометьте образы для внутреннего registry
docker tag review-api:latest registry.company.local/code-review/review-api:2.0.0
docker tag review-api:latest registry.company.local/code-review/review-api:latest

# Загрузите в registry
docker push registry.company.local/code-review/review-api:2.0.0
docker push registry.company.local/code-review/review-api:latest
```

### Обновите docker-compose.yml

```yaml
services:
  review-api:
    image: registry.company.local/code-review/review-api:latest
    # Удалите директиву 'build'
    environment:
      - MODEL_API_KEY=${MODEL_API_KEY}
      # ... другие env переменные
```

---

## Устранение неполадок

### Проблема: Не удалось загрузить Docker

**Симптомы**:
```
Error loading image: unexpected EOF
```

**Решения**:
1. **Проверьте целостность архива**:
```bash
tar -tzf review-api.tar | head
```

2. **Переэкспортируйте образ**:
```bash
# В подключённой среде
docker save review-api:latest | gzip > review-api.tar.gz
```

3. **Проверьте место на диске**:
```bash
df -h /var/lib/docker
```

---

### Проблема: Не удалось установить npm

**Симптомы**:
```
npm ERR! network request failed
```

**Решения**:
1. **Установите из локального tarball**:
```bash
npm install -g /path/to/cline-cli-2.1.0.tgz
```

2. **Извлеките зависимости вручную**:
```bash
cd /usr/local/lib/node_modules
tar -xzf /path/to/cline-dependencies.tar.gz
```

---

### Проблема: Отсутствуют Python пакеты

**Симптомы**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**Решения**:
1. **Установите из offline репозитория**:
```bash
pip install --no-index --find-links=/path/to/air-gap-packages/pip/ -r requirements.txt
```

2. **Проверьте скачанные пакеты**:
```bash
ls -1 air-gap-packages/pip/*.whl | wc -l
```

---

### Проблема: Не удалось подключиться к Model API

**Симптомы**:
```
Error: Failed to connect to model API
```

**Решения**:
1. **Протестируйте внутренний API**:
```bash
curl -H "Authorization: Bearer $MODEL_API_KEY" \
  https://internal-model-api.company.local/v1/models
```

2. **Проверьте доступ к сети**:
```bash
telnet internal-model-api.company.local 443
```

3. **Проверьте сертификаты** (если HTTPS):
```bash
openssl s_client -connect internal-model-api.company.local:443
```

---

## Обновления и патчи

### Обновление в Air-Gap среде

1. **В подключённой среде**:
```bash
# Получите последние изменения
git pull

# Пересоберите образ
docker-compose build

# Создайте пакет обновления
docker save -o review-api-update.tar review-api:latest
tar -czf update-$(date +%Y%m%d).tar.gz \
  review-api-update.tar \
  app/ \
  prompts/ \
  rules/ \
  requirements.txt
```

2. **Перенесите пакет обновления**

3. **В изолированной среде**:
```bash
# Извлеките обновление
tar -xzf update-20251103.tar.gz

# Загрузите новый образ
docker load -i review-api-update.tar

# Остановите текущие сервисы
docker-compose down

# Запустите с новым образом
docker-compose up -d
```

---

## Соображения безопасности

### Проверка

1. **Проверка контрольной суммы**:
```bash
# В подключённой среде
sha256sum code-review-air-gap-*.tar.gz > checksums.txt

# В изолированной среде
sha256sum -c checksums.txt
```

2. **GPG подпись** (если применимо):
```bash
# Подпишите пакет
gpg --detach-sign code-review-air-gap-*.tar.gz

# Проверьте подпись
gpg --verify code-review-air-gap-*.tar.gz.sig
```

---

### Контроль доступа

- Ограничьте доступ к директории установки
- Используйте безопасные credentials для GitLab и model API
- Реализуйте принципы наименьших привилегий

```bash
# Защитите директорию установки
chmod 750 /opt/code-review
chown root:code-review /opt/code-review

# Защитите env файл
chmod 600 .env
```

---

## Резервное копирование и восстановление

### Резервное копирование

```bash
# Резервная копия конфигурации
tar -czf backup-config-$(date +%Y%m%d).tar.gz \
  .env \
  docker-compose.yml \
  ~/.config/cline/ \
  ~/.config/qwen-code/

# Резервная копия данных
docker-compose exec review-api tar -czf - /app/logs > backup-logs-$(date +%Y%m%d).tar.gz
```

### Восстановление

```bash
# Восстановите конфигурацию
tar -xzf backup-config-20251103.tar.gz

# Перезапустите сервисы
docker-compose restart
```

---

## Ссылки

- [Docker Save/Load Documentation](https://docs.docker.com/engine/reference/commandline/save/)
- [npm Offline Installation](https://docs.npmjs.com/cli/v9/commands/npm-install)
- [pip Offline Installation](https://pip.pypa.io/en/stable/cli/pip_download/)

---

**Последнее обновление**: 2025-11-03  
**Версия**: 2.0.0
