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
