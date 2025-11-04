# AI Code Review System v2.0

**Мультиагентная система автоматического ревью кода на базе Cline и Qwen Code CLI**

## 🎯 Обзор

Система автоматического code review, использующая CLI инструменты (Cline, Qwen Code) с поддержкой LLM моделей DeepSeek V3.1 Terminus и Qwen3-Coder через OpenAI-совместимый API. Предназначена для интеграции с GitLab и n8n для полной автоматизации процесса ревью merge requests.

### Ключевые особенности

- 🤖 **Два CLI агента**: Cline (DeepSeek V3.1) и Qwen Code (Qwen3-Coder) с гибким переключением
- 🔍 **11 типов проверок**: От обнаружения ошибок до оптимизации БД
- 🚀 **Параллельное выполнение**: Множественные инстансы CLI для разных типов ревью
- 📝 **Автоматическая документация**: Javadoc и комментарии коммитятся в исходную ветку
- 🔧 **Умный рефакторинг**: Классификация на significant/minor с созданием отдельных MR
- 🎯 **JIRA интеграция**: Проверка соответствия задачам (TODO agent)
- 📋 **Changelog генерация**: Автоматическое обновление CHANGELOG.md (TODO agent)
- 🔒 **Minimal GitLab API**: Основная работа через Git CLI, API только для MR
- 🌐 **Confluence rules**: Загрузка правил из Confluence (опционально)
- 🐳 **Docker + K8s**: Готовые конфигурации для развертывания

## 📐 Архитектура развертывания

### Вопрос: Должны ли API и CLI быть на одном сервере?

**Ответ**: Зависит от требований к безопасности и масштабируемости.

#### Вариант 1: Совместное размещение (Рекомендуется для начала)

```
┌─────────────────────────────────────┐
│      Docker Container / K8s Pod     │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  FastAPI     │  │  Cline CLI  │ │
│  │  Review API  │──│  Qwen CLI   │ │
│  └──────────────┘  └─────────────┘ │
│         │                           │
│         │                           │
│  ┌──────▼──────┐                   │
│  │   Git CLI   │                   │
│  └─────────────┘                   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│   Model API     │     │   GitLab     │
│  (DeepSeek/     │     │  (Minimal    │
│   Qwen3)        │     │   API usage) │
└─────────────────┘     └──────────────┘
```

**Преимущества**:
- ✅ Простое развертывание (один контейнер/pod)
- ✅ Низкая латентность (локальное взаимодействие)
- ✅ Проще отладка
- ✅ Нет сетевых задержек между API и CLI

**Недостатки**:
- ❌ Больше ресурсов на один контейнер (Node.js + Python + Git)
- ❌ Сложнее масштабировать отдельно

**Использование**:
- Малые/средние команды (до 100 MR/день)
- Простая инфраструктура
- Быстрый старт

#### Вариант 2: Раздельное размещение (Для Enterprise)

```
┌──────────────────┐      ┌───────────────────────┐
│   Review API     │      │   CLI Workers Pool    │
│   (FastAPI)      │◄────►│  ┌─────────────────┐  │
│                  │      │  │ Worker 1: Cline │  │
│  - API endpoints │      │  └─────────────────┘  │
│  - GitLab API    │      │  ┌─────────────────┐  │
│  - Orchestration │      │  │ Worker 2: Qwen  │  │
└──────────────────┘      │  └─────────────────┘  │
                          │  ┌─────────────────┐  │
                          │  │ Worker 3: Cline │  │
                          │  └─────────────────┘  │
                          └───────────────────────┘
```

**Преимущества**:
- ✅ Независимое масштабирование (больше CLI workers)
- ✅ Изоляция ресурсов
- ✅ Возможность разных версий CLI
- ✅ Graceful degradation (если один worker падает)

**Недостатки**:
- ❌ Сложность архитектуры (нужен message broker: RabbitMQ/Redis)
- ❌ Увеличенная латентность (сетевое взаимодействие)
- ❌ Больше инфраструктурных затрат

**Использование**:
- Крупные команды (>100 MR/день)
- Требуется высокая доступность
- Разные типы review на разных workers

### Как взаимодействуют компоненты?

#### В совместном размещении (текущая реализация):

```python
# FastAPI endpoint
@app.post("/api/v1/review")
async def review(request: ReviewRequest):
    # 1. Клонируем репозиторий через Git CLI
    repo_path = await git_manager.clone_repository(...)
    
    # 2. Вызываем CLI напрямую через subprocess
    # CLI сам определяет changed files через git diff
    process = await asyncio.create_subprocess_exec(
        "cline", "review",
        "--model", "deepseek-v3.1-terminus",
        "--api-base", settings.MODEL_API_URL,
        "--api-key", settings.MODEL_API_KEY,
        cwd=repo_path  # CLI работает внутри репозитория
    )
    
    # 3. Читаем результаты от CLI
    stdout, stderr = await process.communicate()
    result = parse_cli_output(stdout)
    
    # 4. Создаем MR через GitLab API
    await gitlab_service.create_merge_request(...)
    
    # 5. Cleanup
    await git_manager.cleanup_repository(repo_path)
```

**Взаимодействие**:
1. **FastAPI ↔ CLI**: Прямые subprocess вызовы, JSON через stdout/stderr
2. **CLI ↔ Git**: CLI использует локальный `.git` репозиторий
3. **CLI ↔ Model API**: HTTP запросы к OpenAI-compatible endpoint
4. **FastAPI ↔ GitLab**: Минимальные HTTP запросы (create MR, add comment)

#### В раздельном размещении (будущее расширение):

```python
# FastAPI endpoint
@app.post("/api/v1/review")
async def review(request: ReviewRequest):
    # 1. Публикуем задачу в очередь
    task_id = await queue.publish({
        "project_id": request.project_id,
        "mr_iid": request.merge_request_iid,
        "review_types": request.review_types
    })
    
    # 2. Возвращаем task_id клиенту
    return {"task_id": task_id, "status": "queued"}

# CLI Worker
async def worker():
    async for task in queue.consume():
        # Клонирует, выполняет review, возвращает результат
        result = await execute_review(task)
        await queue.publish_result(task.id, result)
```

## 🚨 Обработка ошибок, логирование и дебаг

### Типы возможных ошибок

#### 1. CLI Execution Errors

**Возможные проблемы**:
- CLI не установлен или не доступен в PATH
- Неверные параметры командной строки
- Timeout выполнения (слишком большой MR)
- Out of memory (большие файлы)
- CLI crash/segfault

**Логирование**:
```python
# В ClineCLIManager
logger.info(f"Executing CLI command: {' '.join(command)}")
logger.debug(f"Working directory: {repo_path}")

try:
    process = await asyncio.create_subprocess_exec(...)
    stdout, stderr = await asyncio.wait_for(
        process.communicate(),
        timeout=settings.REVIEW_TIMEOUT
    )
except asyncio.TimeoutError:
    logger.error(f"CLI timeout after {settings.REVIEW_TIMEOUT}s", extra={
        "project_id": project_id,
        "mr_iid": mr_iid,
        "command": command
    })
    # Записываем в Prometheus metric
    cli_timeout_counter.inc()
    raise
except Exception as e:
    logger.exception("CLI execution failed", extra={
        "command": command,
        "stderr": stderr.decode() if stderr else None
    })
    raise
```

**Восстановление**:
- Retry с экспоненциальным backoff (3 попытки)
- Fallback на другой CLI agent (Cline → Qwen)
- Graceful degradation (пропуск некритичных review types)

#### 2. Model API Errors

**Возможные проблемы**:
- API недоступен (сетевые проблемы)
- Rate limiting (429)
- Invalid API key (401)
- Model overloaded (503)
- Malformed response

**Логирование**:
```python
logger.info(f"Calling Model API: {api_url}", extra={
    "model": model_name,
    "request_tokens": estimate_tokens(prompt)
})

try:
    response = await httpx.post(api_url, ...)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    logger.error(f"Model API error: {e.response.status_code}", extra={
        "response_body": e.response.text,
        "headers": dict(e.response.headers)
    })
    # Alerting
    if e.response.status_code >= 500:
        await send_alert("Model API is down", severity="high")
    raise
```

**Восстановление**:
- Retry с jitter для rate limiting
- Переключение на резервный model endpoint
- Кэширование для одинаковых фрагментов кода

#### 3. GitLab API Errors

**Возможные проблемы**:
- Недостаточные permissions для создания MR
- MR уже существует
- Branch не существует
- API rate limit

**Логирование**:
```python
logger.info(f"Creating MR in project {project_id}", extra={
    "source_branch": source_branch,
    "target_branch": target_branch
})

try:
    mr = await gitlab_service.create_merge_request(...)
    logger.info(f"MR created: !{mr['iid']}")
except gitlab.exceptions.GitlabCreateError as e:
    if "already exists" in str(e):
        logger.warning(f"MR already exists, updating instead")
        mr = await gitlab_service.update_merge_request(...)
    else:
        logger.error(f"Failed to create MR: {e}")
        raise
```

#### 4. Git Repository Errors

**Возможные проблемы**:
- Clone failure (authentication, network)
- Merge conflicts при коммите
- Disk space full
- Permission denied для /tmp/review

**Логирование**:
```python
try:
    repo_path = await git_manager.clone_repository(clone_url, branch)
    logger.info(f"Repository cloned to {repo_path}", extra={
        "disk_usage_mb": get_dir_size_mb(repo_path)
    })
except Exception as e:
    logger.error(f"Git clone failed: {e}", extra={
        "clone_url": mask_credentials(clone_url),
        "branch": branch,
        "disk_free_gb": get_disk_free_space_gb("/tmp")
    })
    raise
finally:
    # ВСЕГДА cleanup, даже при ошибках
    await git_manager.cleanup_repository(repo_path)
```

### Структура логирования

```python
# app/utils/logger.py
from loguru import logger
import sys

def setup_logger():
    logger.remove()  # Удалить default handler
    
    # Console output (structured JSON для production)
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="INFO",
        serialize=True if settings.LOG_FORMAT == "json" else False
    )
    
    # File output (ротация)
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # Новый файл каждый день
        retention="30 days",
        compression="zip",
        level="DEBUG",
        format="{time} | {level} | {name}:{function}:{line} | {extra} | {message}"
    )
    
    # Error-only file
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        rotation="100 MB",
        level="ERROR",
        format="{time} | {level} | {name}:{function}:{line} | {extra} | {message} | {exception}"
    )
```

### Алертинг

#### Prometheus Metrics

```python
# app/monitoring.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics
review_duration = Histogram(
    'code_review_duration_seconds',
    'Time spent on code review',
    ['agent', 'review_type', 'status']
)

review_total = Counter(
    'code_review_total',
    'Total number of reviews',
    ['agent', 'review_type', 'status']
)

cli_timeouts = Counter(
    'cli_timeouts_total',
    'Number of CLI timeouts',
    ['agent']
)

model_api_errors = Counter(
    'model_api_errors_total',
    'Model API errors',
    ['status_code']
)

active_reviews = Gauge(
    'active_reviews',
    'Number of currently running reviews'
)
```

#### Алерты в n8n

```javascript
// n8n workflow: Monitor Code Review Health
// Trigger: Every 5 minutes
// Check /api/v1/health endpoint
// If unhealthy → Send Slack/Email alert

if (response.status !== 'healthy') {
  await sendAlert({
    title: '🚨 Code Review System Unhealthy',
    details: {
      cline_available: response.cline_available,
      qwen_available: response.qwen_available,
      model_api_connected: response.model_api_connected,
      gitlab_connected: response.gitlab_connected
    },
    severity: 'high',
    channels: ['slack://ops-alerts', 'email://team@example.com']
  });
}
```

### Дебаг и диагностика

#### 1. Подключение к терминальной сессии CLI

**Вопрос: Есть ли возможность подключаться к терминальной сессии агента?**

**Ответ**: Прямого подключения к уже запущенной сессии нет (CLI agents запускаются как subprocess и завершаются). Но есть несколько способов дебага:

##### Вариант A: Debug Mode с сохранением вывода

```bash
# В .env
DEBUG_MODE=true
SAVE_CLI_OUTPUT=true
CLI_OUTPUT_DIR=/app/logs/cli_debug

# Результат: все stdout/stderr CLI сохраняются в файлы
# /app/logs/cli_debug/2025-01-15_14-30-45_cline_error_detection_MR123.log
```

```python
# В ClineCLIManager
if settings.DEBUG_MODE:
    debug_file = f"{settings.CLI_OUTPUT_DIR}/{timestamp}_{agent}_{review_type}_MR{mr_iid}.log"
    with open(debug_file, 'w') as f:
        f.write(f"Command: {' '.join(command)}\n")
        f.write(f"Working Dir: {repo_path}\n")
        f.write(f"Stdout:\n{stdout.decode()}\n")
        f.write(f"Stderr:\n{stderr.decode()}\n")
```

##### Вариант B: Interactive Debug Shell (для разработки)

```bash
# Запустить контейнер в интерактивном режиме
docker exec -it code-review-api /bin/bash

# Внутри контейнера
cd /tmp/review/project-123-mr-456

# Запустить CLI вручную с теми же параметрами
cline review \
  --model deepseek-v3.1-terminus \
  --api-base https://api.example.com/v1 \
  --api-key $MODEL_API_KEY \
  --language java \
  --type error_detection \
  --rules /app/rules/java-spring-boot/error_detection.md \
  --prompt /app/prompts/cline/error_detection.md \
  --verbose \
  --debug

# Анализировать вывод в реальном времени
```

##### Вариант C: Long-running Debug Session

Для глубокого дебага можно запустить CLI в tmux/screen сессии:

```bash
# В Dockerfile добавить
RUN apt-get install -y tmux

# Запустить debug session
docker exec -it code-review-api tmux new -s debug

# Внутри tmux
cd /tmp/review/cloned-repo
export DEBUG=cline:*  # Включить verbose logging CLI
cline review --config debug.json

# Отсоединиться: Ctrl+B, D
# Переподключиться: docker exec -it code-review-api tmux attach -t debug
```

#### 2. Trace Request через весь pipeline

```python
# Добавить correlation_id для трейсинга
@router.post("/api/v1/review")
async def review(request: ReviewRequest):
    correlation_id = str(uuid.uuid4())
    logger.info(f"Review started", extra={"correlation_id": correlation_id, "mr_iid": request.merge_request_iid})
    
    # Передать correlation_id во все вызовы
    repo_path = await git_manager.clone_repository(..., correlation_id=correlation_id)
    result = await review_service.execute_review(..., correlation_id=correlation_id)
    
    # В логах можно найти все записи по grep correlation_id
    # grep "abc-123-def" logs/app_2025-01-15.log
```

#### 3. Health Check Endpoint с детальной диагностикой

```python
@router.get("/api/v1/health")
async def health():
    # Проверить все зависимости
    diagnostics = {
        "cli": await check_cli_availability(),
        "model_api": await check_model_api(),
        "gitlab": await check_gitlab(),
        "disk": get_disk_usage(),
        "memory": get_memory_usage()
    }
    return diagnostics

async def check_cli_availability():
    return {
        "cline": {
            "installed": await run_command("which cline"),
            "version": await run_command("cline --version"),
            "can_call_api": await test_cline_api_call()
        },
        "qwen": {
            "installed": await run_command("which qwen-code"),
            "version": await run_command("qwen-code --version")
        }
    }
```

## 🔧 Перезапуск и продолжение процесса

### Idempotency

Все операции спроектированы как идемпотентные:

```python
# Если MR уже создан - обновляем, не создаем заново
try:
    mr = await gitlab_service.create_merge_request(...)
except gitlab.exceptions.GitlabCreateError as e:
    if "already exists" in str(e):
        mr = await gitlab_service.update_merge_request(...)
```

### Graceful Shutdown

```python
# В main.py
@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down, waiting for active reviews...")
    await review_service.wait_for_completion(timeout=60)
    await git_manager.cleanup_all()
```

### Restart Strategy

```yaml
# docker-compose.yml
services:
  review-api:
    restart: unless-stopped
    deploy:
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

## 📚 Глоссарий документации

### Основная документация

| Документ | Описание | Язык |
|----------|----------|------|
| [README.md](README.md) | Основное описание проекта, быстрый старт | 🇷🇺 RU |
| [PRD_RU.md](docs/PRD_RU.md) | Полный документ требований к продукту | 🇷🇺 RU |
| [PRD.md](docs/PRD.md) | Product Requirements Document | 🇬🇧 EN |
| [SUMMARY.md](SUMMARY.md) | Краткая сводка проекта | 🇷🇺 RU |

### Архитектура и развёртывание

| Документ | Описание | Язык |
|----------|----------|------|
| [ARCHITECTURE_RU.md](docs/ARCHITECTURE_RU.md) | Архитектура системы | 🇷🇺 RU |
| [DEPLOYMENT_GUIDE_RU.md](docs/DEPLOYMENT_GUIDE_RU.md) | Полное руководство по развёртыванию | 🇷🇺 RU |
| [AIR_GAP_TRANSFER.md](docs/AIR_GAP_TRANSFER.md) | Руководство по air-gap передаче для изолированных сред | 🇷🇺 RU |
| [OFFLINE_BUILD.md](docs/OFFLINE_BUILD.md) | Сборка и развёртывание в offline режиме | 🇷🇺 RU |
| [OFFLINE_QUICK_START.md](OFFLINE_QUICK_START.md) | Быстрый старт для offline установки | 🇷🇺 RU |
| [DOCKER_OFFLINE_PROBLEM.md](docs/DOCKER_OFFLINE_PROBLEM.md) | Решение проблем Docker в offline режиме | 🇷🇺 RU |

### Настройка и конфигурация

| Документ | Описание | Язык |
|----------|----------|------|
| [CLI_SETUP.md](docs/CLI_SETUP.md) | Настройка CLI инструментов (Cline, Qwen) | 🇬🇧 EN |
| [RULES_CUSTOMIZATION.md](docs/RULES_CUSTOMIZATION.md) | Кастомизация правил ревью | 🇷🇺 RU |
| [PROMPTS_GUIDE.md](docs/PROMPTS_GUIDE.md) | Руководство по системе промптов | 🇷🇺 RU |
| [SYSTEM_PROMPT_GUIDE.md](docs/SYSTEM_PROMPT_GUIDE.md) | Руководство по системному промпту | 🇬🇧 EN |
| [NEW_REVIEW_TYPES.md](docs/NEW_REVIEW_TYPES.md) | Документация новых типов ревью (UNIT_TEST_COVERAGE, MEMORY_BANK) | 🇷🇺 RU |

### CLI агенты и ответственность

| Документ | Описание | Язык |
|----------|----------|------|
| [CLI_RESPONSIBILITY_QUICK.md](CLI_RESPONSIBILITY_QUICK.md) | Быстрая справка по разделению ответственности | ru RU |
| [CLI_RESPONSIBILITY_SEPARATION.md](docs/CLI_RESPONSIBILITY_SEPARATION.md) | Разделение ответственностей CLI и FastAPI | ru RU |
| [CLI_ACCESS_QUICK.md](CLI_ACCESS_QUICK.md) | Быстрая справка по CLI доступу | ru RU |

### Интеграции и workflow

| Документ | Описание | Язык |
|----------|----------|------|
| [N8N_WORKFLOW.md](docs/N8N_WORKFLOW.md) | Интеграция с n8n workflow | 🇬🇧 EN |
| [ERROR_HANDLING_RU.md](docs/ERROR_HANDLING_RU.md) | Обработка ошибок и мониторинг | 🇷🇺 RU |

### Примеры и шаблоны

| Файл | Описание |
|------|----------|
| [env.example.annotated](env.example.annotated) | Аннотированный пример .env файла |
| [docker-compose.yml](docker-compose.yml) | Docker Compose конфигурация для стандартного развёртывания |
| [docker-compose.offline.yml](docker-compose.offline.yml) | Docker Compose конфигурация для offline режима |
| [deployment/kubernetes/](deployment/kubernetes/) | Kubernetes манифесты для продакшн развёртывания |

### Правила и промпты

| Директория | Описание |
|------------|----------|
| [rules/java-spring-boot/](rules/java-spring-boot/) | Правила ревью по умолчанию для Java Spring Boot |
| [prompts/cline/](prompts/cline/) | Промпты для Cline CLI агента |
| [prompts/qwen/](prompts/qwen/) | Промпты для Qwen Code CLI агента |
| [prompts/additional/](prompts/additional/) | Дополнительные специализированные промпты |
| [prompts/todo/](prompts/todo/) | Промпты для будущих TODO функций |

### Исследования

| Документ | Описание |
|----------|----------|
| [research/Qwen Code для ревью merge requests_ полный анализ.md](research/Qwen%20Code%20для%20ревью%20merge%20requests_%20полный%20анализ.md) | Анализ Qwen Code для MR ревью |
| [research/Возможно ли реализовать, чтоб self-hosted n8n на сервере управлял CLI агентом.md](research/Возможно%20ли%20реализовать,%20чтоб%20self-hoted%20n8n%20%20на%20с.md) | Исследование self-hosted n8n |

---

## 📖 Быстрые ссылки

### Для начала работы
1. 🚀 [README.md](README.md) - Старт здесь
2. 📦 [OFFLINE_QUICK_START.md](OFFLINE_QUICK_START.md) - Offline установка
3. 🐳 [DEPLOYMENT_GUIDE_RU.md](docs/DEPLOYMENT_GUIDE_RU.md) - Полное развёртывание

### Для настройки
1. ⚙️ [CLI_SETUP.md](docs/CLI_SETUP.md) - Настройка CLI
2. 📝 [RULES_CUSTOMIZATION.md](docs/RULES_CUSTOMIZATION.md) - Свои правила
3. 💬 [PROMPTS_GUIDE.md](docs/PROMPTS_GUIDE.md) - Настройка промптов

### Для понимания системы
1. 🏗️ [ARCHITECTURE_RU.md](docs/ARCHITECTURE_RU.md) - Архитектура
2. 📋 [PRD_RU.md](docs/PRD_RU.md) - Полное описание продукта
3. 🤖 [NEW_REVIEW_TYPES.md](docs/NEW_REVIEW_TYPES.md) - Новые возможности

### Для production
1. ☸️ [deployment/kubernetes/](deployment/kubernetes/) - Kubernetes манифесты
2. 🔒 [AIR_GAP_TRANSFER.md](docs/AIR_GAP_TRANSFER.md) - Изолированные среды
3. 🚨 [ERROR_HANDLING_RU.md](docs/ERROR_HANDLING_RU.md) - Обработка ошибок

## 🚀 Быстрый старт

### Docker Compose (Рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd mrCliReview

# 2. Создать .env файл (скопировать содержимое из README ниже)
cat > .env << 'EOF'
MODEL_API_URL=https://your-api.example.com/v1
MODEL_API_KEY=your-api-key
DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
QWEN3_MODEL_NAME=qwen3-coder-32b
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your-gitlab-token
DEFAULT_CLI_AGENT=CLINE
LOG_LEVEL=INFO
EOF

# 3. Запустить
docker-compose up -d

# 4. Проверить
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

### Kubernetes

```bash
cd deployment/kubernetes

# 1. Настроить secrets
kubectl apply -f secret.yaml

# 2. Настроить config
kubectl apply -f configmap.yaml

# 3. Deploy
kubectl apply -f namespace.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

## 📊 API Endpoints

```
GET  /                     - Service info
GET  /health               - Simple health check
GET  /api/v1/health        - Detailed health check
POST /api/v1/review        - Execute code review
POST /api/v1/validate-mr   - Validate MR (n8n integration)
```

## 🤝 Contributing

См. [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License
