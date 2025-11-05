# Инструкции по установке и настройке для Windows

## Оглавление

1. [Требования](#требования)
2. [Установка зависимостей](#установка-зависимостей)
3. [Локальная разработка](#локальная-разработка)
4. [Docker сборка](#docker-сборка)
5. [Offline установка](#offline-установка)
6. [Troubleshooting](#troubleshooting)

## Требования

### Системные требования

- **ОС**: Windows 10/11 (64-bit)
- **RAM**: Минимум 8 GB, рекомендуется 16 GB
- **Disk**: Минимум 10 GB свободного места
- **PowerShell**: 5.1 или выше

### Необходимое ПО

1. **Python 3.11+**
   - Скачать: https://www.python.org/downloads/
   - При установке отметить "Add Python to PATH"

2. **Node.js 18+**
   - Скачать: https://nodejs.org/
   - LTS версия рекомендуется

3. **Git для Windows**
   - Скачать: https://git-scm.com/download/win
   - При установке выбрать "Use Git from Windows Command Prompt"

4. **Docker Desktop** (для Docker сборки)
   - Скачать: https://www.docker.com/products/docker-desktop/
   - Требуется WSL 2

## Установка зависимостей

### 1. Проверка установки

Откройте PowerShell и проверьте версии:

```powershell
# Проверка Python
python --version
# Должно быть: Python 3.11.x или выше

# Проверка Node.js
node --version
# Должно быть: v18.x.x или выше

# Проверка npm
npm --version

# Проверка Git
git --version
```

### 2. Установка Python зависимостей

```powershell
# Переход в директорию проекта
cd D:\path\to\mrCliReview

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
.\venv\Scripts\Activate.ps1

# Если получите ошибку ExecutionPolicy, выполните:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Обновление pip
python -m pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Установка CLI инструментов

**Примечание**: Cline и Qwen Code CLI - это гипотетические инструменты для примера. В реальной системе используйте реальные CLI агенты.

```powershell
# Глобальная установка CLI инструментов
npm install -g @cline/cli
npm install -g @qwen-code/qwen-code

# Проверка установки
cline --version
qwen-code --version
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```powershell
# Копирование примера
Copy-Item env.example.annotated .env

# Или создайте вручную
New-Item -Path .env -ItemType File
```

Содержимое `.env`:

```env
# Model API Configuration
MODEL_API_URL=https://your-model-api.com/v1
MODEL_API_KEY=your-api-key-here

# Model Names
DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
QWEN3_MODEL_NAME=qwen3-coder-32b

# CLI Configuration
DEFAULT_CLI_AGENT=CLINE
CLINE_PARALLEL_TASKS=5
QWEN_PARALLEL_TASKS=3
REVIEW_TIMEOUT=300

# GitLab Configuration
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your-gitlab-token

# Application Configuration
LOG_LEVEL=INFO
WORK_DIR=C:\Temp\review
PROMPTS_PATH=prompts
DEFAULT_RULES_PATH=rules/java-spring-boot
DEFAULT_LANGUAGE=java

# Optional: Confluence Rules
CONFLUENCE_RULES_ENABLED=false
CONFLUENCE_URL=
CONFLUENCE_API_TOKEN=

# Optional: MCP RAG
MCP_RAG_ENABLED=false
MCP_SERVER_URL=
```

**Важно для Windows**: Используйте `C:\Temp\review` вместо `/tmp/review` для WORK_DIR.

## Локальная разработка

### Запуск приложения

```powershell
# Активация виртуального окружения
.\venv\Scripts\Activate.ps1

# Создание рабочей директории
New-Item -Path "C:\Temp\review" -ItemType Directory -Force

# Создание директории для логов
New-Item -Path "logs" -ItemType Directory -Force

# Запуск FastAPI приложения
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Приложение будет доступно по адресу: http://localhost:8000

API документация: http://localhost:8000/docs

### Запуск тестов

```powershell
# Активация виртуального окружения
.\venv\Scripts\Activate.ps1

# Запуск всех тестов
python -m pytest tests/ -v

# Запуск с покрытием
python -m pytest tests/ --cov=app --cov-report=html

# Запуск конкретного теста
python -m pytest tests/test_review_service.py -v

# Запуск с подробным выводом
python -m pytest tests/ -vv --tb=long
```

### Отладка

Для отладки в VS Code создайте `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000"
            ],
            "jinja": true,
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

## Docker сборка

### Предварительные требования

1. **Установите Docker Desktop**
   - Скачать: https://www.docker.com/products/docker-desktop/
   - После установки перезагрузите компьютер

2. **Включите WSL 2**
   ```powershell
   # Выполните в PowerShell от администратора
   wsl --install
   wsl --set-default-version 2
   ```

3. **Настройте Docker Desktop**
   - Откройте Docker Desktop
   - Settings → General → Use the WSL 2 based engine (должно быть включено)
   - Settings → Resources → WSL Integration → Enable integration with your WSL distro

### Сборка Docker образа

```powershell
# Переход в директорию проекта
cd D:\path\to\mrCliReview

# Сборка образа (online режим)
docker build -t code-review-api:latest .

# Сборка с указанием платформы
docker build --platform linux/amd64 -t code-review-api:latest .
```

**Примечание**: Сборка может занять 10-15 минут при первом запуске.

### Запуск через Docker Compose

```powershell
# Создайте .env файл (см. раздел выше)

# Запуск контейнера
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Проверка статуса
docker-compose ps

# Остановка
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

### Проверка работы

```powershell
# Health check
Invoke-WebRequest -Uri http://localhost:8000/health -Method GET

# Или через curl (если установлен)
curl http://localhost:8000/health

# Через PowerShell
(Invoke-WebRequest -Uri http://localhost:8000/health).Content | ConvertFrom-Json
```

## Offline установка

### Подготовка offline пакетов

На машине с интернетом:

```powershell
# Создание директорий
New-Item -Path "offline-packages" -ItemType Directory -Force
New-Item -Path "offline-python" -ItemType Directory -Force

# Скачивание Python зависимостей
pip download -r requirements.txt -d offline-python

# Скачивание npm пакетов
npm pack @cline/cli
npm pack @qwen-code/qwen-code

# Перемещение в offline-packages
Move-Item -Path "*.tgz" -Destination "offline-packages/"

# Создание архива для переноса
Compress-Archive -Path offline-packages,offline-python,requirements.txt -DestinationPath review-system-offline.zip
```

### Установка на offline машине

```powershell
# Распаковка архива
Expand-Archive -Path review-system-offline.zip -DestinationPath .

# Установка Python зависимостей
pip install --no-index --find-links=offline-python -r requirements.txt

# Установка npm пакетов
cd offline-packages
npm install -g cline-*.tgz
npm install -g qwen-code-*.tgz
cd ..
```

### Docker offline сборка

```powershell
# Сохранение Docker образа
docker save code-review-api:latest | gzip > code-review-api-latest.tar.gz

# На целевой машине - загрузка образа
docker load -i code-review-api-latest.tar.gz

# Проверка
docker images | Select-String "code-review-api"
```

## Troubleshooting

### Проблема: "Execution Policy" ошибка при активации venv

**Решение**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Проблема: "pip" не найден

**Решение**:
```powershell
# Используйте python -m pip вместо pip
python -m pip install -r requirements.txt
```

### Проблема: Ошибка компиляции pydantic-core

**Решение**:
```powershell
# Установите более новую версию с pre-built wheels
pip install --upgrade pydantic pydantic-settings
```

### Проблема: Docker не может найти WSL

**Решение**:
1. Откройте PowerShell от администратора
2. Выполните:
   ```powershell
   wsl --install
   wsl --set-default-version 2
   wsl --update
   ```
3. Перезагрузите компьютер
4. Запустите Docker Desktop

### Проблема: "Module not found" при импорте app

**Решение**:
```powershell
# Убедитесь что находитесь в корне проекта
cd D:\path\to\mrCliReview

# Добавьте текущую директорию в PYTHONPATH
$env:PYTHONPATH = (Get-Location).Path

# Или активируйте виртуальное окружение
.\venv\Scripts\Activate.ps1
```

### Проблема: Тесты падают с UnicodeDecodeError

**Решение**:
```powershell
# Установите переменную окружения для кодировки
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Запустите тесты снова
python -m pytest tests/ -v
```

### Проблема: GitLab clone failed - SSL certificate problem

**Решение**:
```powershell
# Временное решение (только для тестирования!)
$env:GIT_SSL_NO_VERIFY = "true"

# Лучшее решение - добавить сертификат
git config --global http.sslVerify true
git config --global http.sslCAInfo "C:\path\to\ca-bundle.crt"
```

### Проблема: Docker Desktop не стартует

**Решение**:
1. Проверьте Hyper-V:
   ```powershell
   # Выполните от администратора
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   ```

2. Проверьте WSL 2:
   ```powershell
   wsl --status
   wsl --list --verbose
   ```

3. Переустановите Docker Desktop

### Проблема: Высокое потребление памяти Docker

**Решение**:
Создайте или отредактируйте `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
```

Перезапустите WSL:
```powershell
wsl --shutdown
```

## Полезные команды Windows

### Управление процессами

```powershell
# Найти процесс на порту 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object -Property OwningProcess

# Убить процесс
Stop-Process -Id <PID> -Force

# Или одной командой
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Просмотр логов

```powershell
# Tail логов
Get-Content -Path "logs\app_*.log" -Wait -Tail 50

# Поиск ошибок
Select-String -Path "logs\app_*.log" -Pattern "ERROR"
```

### Очистка

```powershell
# Удаление временных файлов
Remove-Item -Path "C:\Temp\review\*" -Recurse -Force

# Удаление Python cache
Get-ChildItem -Path . -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Filter "*.pyc" -Recurse | Remove-Item -Force

# Очистка Docker
docker system prune -a --volumes
```

## Дополнительные ресурсы

- [Основной README](../README.md)
- [Руководство по развертыванию](DEPLOYMENT_GUIDE_RU.md)
- [Архитектура](ARCHITECTURE_RU.md)
- [Документация API](http://localhost:8000/docs) (после запуска)

## Контрольный чеклист установки

- [ ] Python 3.11+ установлен и добавлен в PATH
- [ ] Node.js 18+ установлен
- [ ] Git для Windows установлен
- [ ] Docker Desktop установлен и настроен (если нужен)
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены (`pip install -r requirements.txt`)
- [ ] CLI инструменты установлены (`npm install -g`)
- [ ] Файл `.env` настроен
- [ ] Рабочая директория создана (`C:\Temp\review`)
- [ ] Приложение запускается (`uvicorn app.main:app`)
- [ ] Тесты проходят (`pytest tests/`)
- [ ] Health check отвечает (http://localhost:8000/health)

