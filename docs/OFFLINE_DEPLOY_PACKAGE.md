# Инструкция по подготовке офлайн Docker пакета

## Быстрый старт

Этот скрипт создает полностью автономный пакет для развертывания Code Review System на изолированных системах (без интернета).

### Требования

- Среда **С ИНТЕРНЕТОМ** для подготовки пакета
- Docker и Docker Compose
- Node.js и npm
- ~5-10 GB свободного места

### Запуск

```bash
# Сделать скрипт исполняемым (если еще не сделано)
chmod +x scripts/prepare-offline-deploy-package.sh

# Запустить скрипт
./scripts/prepare-offline-deploy-package.sh
```

### Что делает скрипт

1. ✅ Скачивает npm пакеты (@cline/cli, @qwen-code/qwen-code)
2. ✅ Скачивает базовый Docker образ (Python 3.11 + Node.js 18)
3. ✅ Собирает Docker образ с установленными CLI инструментами
4. ✅ Проверяет установку CLI в образе
5. ✅ Сохраняет Docker образы в файлы (.tar)
6. ✅ Создает инструкции для Windows и VPS
7. ✅ Упаковывает все в архив

### Результат

После выполнения скрипта вы получите:

- `offline-deploy-package-YYYYMMDD-HHMMSS.tar.gz` - готовый архив для переноса

### Размер архива

Примерно 2-3 GB (включая Docker образы)

### Использование архива

#### На Windows PC:
1. Распакуйте архив
2. Следуйте инструкциям в `INSTALL_WINDOWS.md`

#### На VPS сервере:
1. Распакуйте архив
2. Следуйте инструкциям в `INSTALL_VPS.md`

## Детальная информация

См. документацию в созданном пакете:
- `PACKAGE_README.md` - общая информация о пакете
- `INSTALL_WINDOWS.md` - инструкции для Windows
- `INSTALL_VPS.md` - инструкции для VPS/Linux

## Troubleshooting

### Ошибка: npm пакеты не скачиваются

**Решение:**
- Проверьте подключение к интернету
- Проверьте доступность npm registry: `npm ping`

### Ошибка: Docker образ не собирается

**Решение:**
- Убедитесь, что Docker запущен: `docker ps`
- Проверьте наличие `offline-packages/*.tgz` файлов
- Проверьте логи: `docker-compose -f docker-compose.offline.yml build --progress=plain`

### Ошибка: CLI не найдены в образе

**Решение:**
- Проверьте, что npm пакеты скачаны: `ls -lh offline-packages/*.tgz`
- Пересоберите образ: `docker-compose -f docker-compose.offline.yml build --no-cache`

## Альтернативный метод

Если скрипт не работает, можно использовать существующий скрипт:

```bash
./scripts/prepare-full-offline.sh
```

Он создаст похожий пакет, но без детальных инструкций для Windows/VPS.
