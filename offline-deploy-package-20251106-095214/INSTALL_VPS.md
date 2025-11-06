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
