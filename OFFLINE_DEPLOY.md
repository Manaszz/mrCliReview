# Подготовка офлайн Docker пакета

## Быстрый старт

Для создания полностью автономного пакета для развертывания на изолированных системах:

```bash
# Запустить скрипт подготовки
./scripts/prepare-offline-deploy-package.sh
```

## Что создается

Скрипт создает архив `offline-deploy-package-YYYYMMDD-HHMMSS.tar.gz` содержащий:

- ✅ Docker образы (base-python-nodejs.tar, review-api.tar)
- ✅ npm пакеты (Cline CLI, Qwen Code CLI)
- ✅ Исходный код приложения
- ✅ Конфигурационные файлы
- ✅ Подробные инструкции для Windows и VPS

## Использование

### На Windows PC:
1. Распакуйте архив
2. Следуйте инструкциям в `INSTALL_WINDOWS.md`

### На VPS сервере:
1. Распакуйте архив
2. Следуйте инструкциям в `INSTALL_VPS.md`

## Подробная документация

См. [docs/OFFLINE_DEPLOY_PACKAGE.md](docs/OFFLINE_DEPLOY_PACKAGE.md) для детальной информации.
