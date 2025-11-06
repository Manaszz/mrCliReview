# Установка на изолированном VPS сервере (Linux)

Руководство по установке AI Code Review System на изолированный Linux VPS сервер без доступа в интернет.

---

## 📋 Требования

### Минимальные требования системы
- Linux: Ubuntu 20.04+, Debian 11+, CentOS 8+, или RHEL 8+
- 4GB RAM (рекомендуется 8GB+)
- 20GB свободного места на диске
- Docker 20.10+ и Docker Compose 2.0+

### Предустановленное ПО (ОБЯЗАТЕЛЬНО)
⚠️ **Установите ДО отключения от интернета:**

1. **Docker Engine**
2. **Docker Compose**
3. **Git** (опционально, для работы системы)

Инструкции по установке см. в разделе "Подготовка сервера".

---

## 🚀 Быстрая установка (5 минут)

### Шаг 1: Перенос файлов на сервер

Скопируйте файл `code-review-offline-YYYYMMDD.tar.gz` на изолированный сервер:

**Вариант A: scp через внутреннюю сеть**
```bash
scp code-review-offline-20251106.tar.gz user@server-ip:/opt/
```

**Вариант B: USB/физический носитель**
```bash
# На USB носителе
mount /dev/sdb1 /mnt/usb
cp /mnt/usb/code-review-offline-20251106.tar.gz /opt/
```

**Вариант C: Внутренняя система передачи файлов**
```
Используйте корпоративную систему передачи файлов
```

### Шаг 2: Распаковка архива

```bash
# Перейти в целевую директорию
cd /opt

# Распаковать архив
tar -xzf code-review-offline-20251106.tar.gz

# Перейти в распакованную папку
cd code-review-offline-20251106

# Проверить содержимое
ls -la
```

### Шаг 3: Запуск скрипта установки

```bash
# Сделать скрипт исполняемым
chmod +x install-linux.sh

# Запустить установку
sudo bash install-linux.sh
```

**Что делает скрипт:**
- ✅ Проверяет наличие Docker
- ✅ Загружает Docker образы в систему
- ✅ Создает файл конфигурации .env

### Шаг 4: Настройка конфигурации

Отредактируйте файл `.env`:

```bash
# Создать .env если не существует
cp .env.example .env

# Отредактировать конфигурацию
nano .env
```

**Обязательные параметры:**

```env
# URL внутреннего Model API (DeepSeek/Qwen)
MODEL_API_URL=http://internal-model-api.company.local:8000/v1

# API ключ для Model API
MODEL_API_KEY=your-internal-api-key-here

# URL внутреннего GitLab
GITLAB_URL=https://gitlab.company.local

# GitLab Personal Access Token
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx

# Имена моделей (должны быть доступны в вашем Model API)
DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
QWEN3_MODEL_NAME=qwen3-coder-32b

# Выбор CLI агента (CLINE или QWEN_CODE)
DEFAULT_CLI_AGENT=CLINE

# Настройки логирования
LOG_LEVEL=INFO
```

Сохраните файл: `Ctrl+X`, `Y`, `Enter`

### Шаг 5: Запуск системы

```bash
# Запустить Docker Compose
docker-compose -f docker-compose.offline.yml up -d

# Проверить статус
docker-compose ps

# Посмотреть логи
docker-compose logs -f
```

### Шаг 6: Проверка работы

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Детальная проверка
curl http://localhost:8000/api/v1/health | jq
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

---

## 📝 Ручная установка (альтернативный метод)

Если автоматический скрипт не работает:

### 1. Проверить Docker

```bash
# Проверить версию Docker
docker --version

# Проверить версию Docker Compose
docker-compose --version

# Проверить, что Docker daemon запущен
sudo systemctl status docker
```

Если Docker не запущен:
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Загрузить Docker образы вручную

```bash
# Загрузить базовый образ
docker load -i base-python-nodejs.tar

# Загрузить образ API
docker load -i code-review-api.tar

# Проверить загруженные образы
docker images
```

Вы должны увидеть:
```
REPOSITORY                    TAG       IMAGE ID       SIZE
code-review-api               latest    xxxxxxxxxxxx   2.5GB
nikolaik/python-nodejs        python... xxxxxxxxxxxx   450MB
```

### 3. Создать конфигурацию

```bash
# Скопировать пример
cp .env.example .env

# Отредактировать
nano .env
```

### 4. Запустить систему

```bash
# Запустить в фоновом режиме
docker-compose -f docker-compose.offline.yml up -d

# Или в интерактивном режиме (для отладки)
docker-compose -f docker-compose.offline.yml up
```

---

## 🔧 Troubleshooting

### Проблема 1: Docker daemon не запущен

**Симптомы:**
```
Cannot connect to the Docker daemon
```

**Решение:**
```bash
# Запустить Docker
sudo systemctl start docker

# Включить автозапуск
sudo systemctl enable docker

# Проверить статус
sudo systemctl status docker
```

### Проблема 2: Недостаточно прав

**Симптомы:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Решение:**
```bash
# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Применить изменения (выйти и войти заново)
newgrp docker

# Или использовать sudo
sudo docker-compose up -d
```

### Проблема 3: Порт 8000 уже занят

**Симптомы:**
```
Error: Port 8000 is already allocated
```

**Решение:**

Вариант A: Найти и остановить процесс
```bash
# Найти процесс на порту 8000
sudo lsof -i :8000

# Остановить процесс (замените PID)
sudo kill -9 PID
```

Вариант B: Изменить порт в docker-compose.offline.yml
```yaml
ports:
  - "8001:8000"  # Изменить 8000 на 8001
```

### Проблема 4: CLI не найден в контейнере

**Симптомы:**
```json
{
  "cline_available": false,
  "qwen_available": false
}
```

**Решение:**
```bash
# Войти в контейнер
docker exec -it code-review-api bash

# Проверить установку CLI
which cline
which qwen-code

# Проверить версии
cline --version
qwen-code --version

# Если не установлены, проверить offline-packages
ls -la /tmp/npm-packages/

# Установить вручную (если нужно)
npm install -g /tmp/npm-packages/cline-*.tgz
npm install -g /tmp/npm-packages/qwen-code-*.tgz
```

### Проблема 5: Недостаточно памяти

**Симптомы:**
```
Container killed (out of memory)
```

**Решение:**
```bash
# Проверить доступную память
free -h

# Увеличить лимиты в docker-compose.offline.yml
# Добавить в секцию services.review-api:
deploy:
  resources:
    limits:
      memory: 8G
    reservations:
      memory: 4G
```

### Проблема 6: Ошибка при загрузке образа

**Симптомы:**
```
Error loading image: unexpected EOF
```

**Решение:**
```bash
# Проверить целостность архива
tar -tzf code-review-api.tar | head

# Проверить MD5 (если есть checksum файл)
md5sum code-review-api.tar
md5sum base-python-nodejs.tar

# Переэкспортировать образ на машине с интернетом
docker save code-review-api:latest | gzip > code-review-api.tar.gz
```

### Проблема 7: Не удается подключиться к Model API

**Симптомы:**
```json
{
  "model_api_connected": false
}
```

**Решение:**
```bash
# Проверить доступность из контейнера
docker exec -it code-review-api curl MODEL_API_URL/v1/models

# Проверить доступность с хоста
curl MODEL_API_URL/v1/models

# Проверить DNS разрешение
docker exec -it code-review-api nslookup model-api.company.local

# Если используется localhost, замените на IP хоста
# В .env: MODEL_API_URL=http://172.17.0.1:8000/v1
```

### Проблема 8: Firewall блокирует соединения

**Симптомы:**
```
Connection timed out
Connection refused
```

**Решение:**
```bash
# Ubuntu/Debian - ufw
sudo ufw allow 8000/tcp
sudo ufw status

# CentOS/RHEL - firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# Проверить правила iptables
sudo iptables -L -n
```

---

## 🔄 Обновление системы

### Обновление до новой версии

```bash
# Остановить текущую версию
docker-compose down

# Загрузить новый образ
docker load -i code-review-api-new.tar

# Запустить новую версию
docker-compose -f docker-compose.offline.yml up -d

# Проверить логи
docker-compose logs -f
```

### Обновление конфигурации

```bash
# Остановить систему
docker-compose down

# Отредактировать .env
nano .env

# Перезапустить
docker-compose -f docker-compose.offline.yml up -d
```

### Обновление промптов и правил

```bash
# Промпты и правила монтируются как volumes
# Можно обновлять без перезапуска контейнера

# Обновить файлы
cp new-prompts/* prompts/
cp new-rules/* rules/

# Перезагрузить конфигурацию (если требуется)
docker-compose restart
```

---

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Все логи
docker-compose logs

# Последние 100 строк
docker-compose logs --tail=100

# В реальном времени
docker-compose logs -f

# Только определенный сервис
docker-compose logs review-api

# Сохранить логи в файл
docker-compose logs > review-api.log
```

### Проверка ресурсов

```bash
# Использование ресурсов всех контейнеров
docker stats

# Информация о конкретном контейнере
docker inspect code-review-api

# Использование диска
docker system df
```

### Проверка работы API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Service info
curl http://localhost:8000/

# Детальная проверка (с форматированием)
curl -s http://localhost:8000/api/v1/health | jq

# Тестовый review
curl -X POST http://localhost:8000/api/v1/review \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 123,
    "merge_request_iid": 456,
    "review_types": ["ERROR_DETECTION"]
  }'
```

---

## 🛡️ Безопасность

### Настройка файрвола

```bash
# Ubuntu/Debian - ufw
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw enable

# CentOS/RHEL - firewalld
sudo firewall-cmd --permanent --add-rich-rule='
  rule family="ipv4" 
  source address="10.0.0.0/8" 
  port port="8000" protocol="tcp" accept'
sudo firewall-cmd --reload
```

### Защита .env файла

```bash
# Установить правильные права доступа
chmod 600 .env
chown root:root .env

# Проверить
ls -la .env
# Должно быть: -rw------- 1 root root
```

### Настройка SSL/TLS

Для production рекомендуется использовать reverse proxy:

```bash
# Установить nginx
sudo apt install nginx

# Настроить SSL (пример конфигурации)
cat > /etc/nginx/sites-available/code-review << 'EOF'
server {
    listen 443 ssl;
    server_name code-review.company.local;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Включить конфигурацию
sudo ln -s /etc/nginx/sites-available/code-review /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔄 Резервное копирование

### Backup конфигурации

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p ${BACKUP_DIR}

# Backup конфигурации
tar -czf ${BACKUP_DIR}/config-${TIMESTAMP}.tar.gz \
    .env \
    docker-compose.offline.yml \
    prompts/ \
    rules/

# Backup логов
docker-compose logs > ${BACKUP_DIR}/logs-${TIMESTAMP}.txt

# Очистка старых backup (старше 30 дней)
find ${BACKUP_DIR} -type f -mtime +30 -delete

echo "Backup создан: ${BACKUP_DIR}/config-${TIMESTAMP}.tar.gz"
```

### Восстановление из backup

```bash
# Остановить систему
docker-compose down

# Восстановить конфигурацию
tar -xzf config-20251106_120000.tar.gz

# Запустить систему
docker-compose -f docker-compose.offline.yml up -d
```

### Автоматический backup (cron)

```bash
# Добавить задачу в crontab
crontab -e

# Backup каждый день в 2:00
0 2 * * * /opt/code-review-offline-20251106/backup.sh
```

---

## 🛑 Остановка и удаление

### Остановка системы

```bash
# Остановить контейнеры
docker-compose down

# Остановить и удалить volumes
docker-compose down -v

# Остановить и удалить образы
docker-compose down --rmi all
```

### Полное удаление

```bash
# Остановить всё
docker-compose down -v --rmi all

# Удалить директорию
cd /opt
sudo rm -rf code-review-offline-20251106

# Очистить неиспользуемые Docker ресурсы
docker system prune -a --volumes
```

---

## 📚 Systemd Service (автозапуск)

Создать systemd service для автозапуска:

```bash
# Создать service файл
sudo nano /etc/systemd/system/code-review.service
```

```ini
[Unit]
Description=AI Code Review System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/code-review-offline-20251106
ExecStart=/usr/local/bin/docker-compose -f docker-compose.offline.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.offline.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Включить service
sudo systemctl daemon-reload
sudo systemctl enable code-review
sudo systemctl start code-review

# Проверить статус
sudo systemctl status code-review
```

---

## 📈 Мониторинг с Prometheus (опционально)

Если требуется детальный мониторинг:

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  prometheus-data:
  grafana-data:
```

---

## 💡 Производственные рекомендации

### 1. Ресурсы

```yaml
# Добавить в docker-compose.offline.yml
services:
  review-api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### 2. Логирование

```yaml
# Ограничить размер логов
services:
  review-api:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
```

### 3. Health checks

```yaml
services:
  review-api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 4. Restart policy

```yaml
services:
  review-api:
    restart: unless-stopped
```

---

## 📞 Поддержка

### Полезные команды

```bash
# Проверка всей системы
docker-compose ps
docker-compose logs --tail=50
curl http://localhost:8000/api/v1/health

# Перезапуск
docker-compose restart

# Просмотр использования ресурсов
docker stats --no-stream

# Очистка логов
docker-compose logs --no-log-prefix > /dev/null
```

### Сбор диагностической информации

```bash
#!/bin/bash
# diagnostic.sh

echo "=== System Info ==="
uname -a
free -h
df -h

echo "=== Docker Info ==="
docker --version
docker-compose --version
docker ps
docker images

echo "=== Service Status ==="
docker-compose ps

echo "=== Recent Logs ==="
docker-compose logs --tail=100

echo "=== Health Check ==="
curl -s http://localhost:8000/api/v1/health | jq
```

---

**Версия документа:** 1.0  
**Дата обновления:** 2025-11-06  
**Совместимость:** Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+
