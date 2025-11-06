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

Пакет создан: 20251106-095214
Версия приложения: см. `README.md`
