# System Prompt Guide: Статическая фиксация правил кодстайла

## Обзор

Система поддерживает статическую фиксацию правил кодстайла через **системный промпт**, который загружается один раз при старте и автоматически добавляется ко всем запросам ревью.

## Архитектура

```
┌─────────────────────────────────────────────┐
│  FastAPI Startup                            │
│  └─> BaseCLIManager.__init__()             │
│      └─> _load_system_prompt()             │
│           └─> _system_prompt_cache (ONE TIME)│
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  Every Review Request                       │
│  └─> execute_review()                       │
│      └─> _substitute_prompt_variables()    │
│           └─> Prepend cached system prompt │
└─────────────────────────────────────────────┘
```

## Использование

### 1. Системный промпт (Основной способ)

**Файл:** `prompts/system_prompt.md`

**Загрузка:** Один раз при инициализации CLI менеджера (singleton pattern)

**Применение:** Автоматически добавляется ко всем промптам

**Преимущества:**
- ✅ Загружается один раз — нет overhead на каждый запрос
- ✅ Единая точка управления правилами кодстайла
- ✅ Нет необходимости передавать с каждым запросом
- ✅ Кэширование на уровне класса (shared между всеми инстансами)

**Пример структуры:**

```markdown
# System Prompt: Java Spring Boot Code Review Standards

## General Code Style Standards

### Java Formatting
- **Indentation**: 4 spaces (no tabs)
- **Line Length**: Maximum 120 characters
- **Braces**: Always use braces

### Spring Boot Conventions
- **Dependency Injection**: Constructor injection only
- **Layer Separation**: Controllers → Services → Repositories
...
```

### 2. Кастомизация per-project (Custom Rules)

**Файл:** `.project-rules/` в корне репозитория

**Загрузка:** Динамически при каждом ревью

**Применение:** Переопределяет дефолтные правила

**Преимущества:**
- ✅ Специфичные правила для конкретного проекта
- ✅ Версионируются вместе с кодом
- ✅ Команда может управлять своими правилами

**Пример:**
```
project-repo/
├── .project-rules/
│   ├── error_detection.md
│   ├── best_practices.md
│   └── security.md
└── src/
    └── ...
```

### 3. Confluence Rules (Enterprise)

**Источник:** Confluence Wiki API

**Загрузка:** Через n8n workflow

**Применение:** Для правил, общих для нескольких проектов

**Преимущества:**
- ✅ Централизованное управление
- ✅ Один источник истины для нескольких команд
- ✅ Легко обновлять без изменения кода

## Приоритет правил

```
1. Project Rules (.project-rules/)     ← Highest priority
2. Confluence Rules (via n8n)
3. Default Rules (rules/java-spring-boot/)
4. System Prompt (prompts/system_prompt.md) ← Always applied
```

## Как изменить системный промпт

### Вариант A: Редактировать файл (По умолчанию)

```bash
# Отредактировать файл
vi prompts/system_prompt.md

# Перезапустить сервис
docker-compose restart review-api
```

### Вариант B: Кастомный путь

```python
# В app/dependencies.py
cline_manager = ClineCLIManager(
    ...
    system_prompt_path="prompts/custom_system_prompt.md"  # Кастомный путь
)
```

### Вариант C: Отключить системный промпт

```python
# В app/dependencies.py
cline_manager = ClineCLIManager(
    ...
    system_prompt_path=""  # Пустая строка = отключить
)
```

## Environment Variables

Можно вынести путь в переменные окружения:

```bash
# В .env
SYSTEM_PROMPT_PATH=prompts/system_prompt.md

# В app/config.py
class Settings(BaseSettings):
    SYSTEM_PROMPT_PATH: str = "prompts/system_prompt.md"
```

## Производительность

### Кэширование

- **Уровень:** Class-level (singleton)
- **Загрузка:** Один раз при первом вызове `BaseCLIManager.__init__()`
- **Переиспользование:** Все инстансы CLI менеджеров используют один кэш
- **Overhead:** ~0ms на каждый запрос (только prepend строки)

### Метрики

```python
# Загрузка системного промпта (один раз)
Loaded system prompt from prompts/system_prompt.md

# Каждый запрос (нет повторной загрузки)
Using CLINE for review
Prepending system prompt (cached) → 0.001ms
```

## Troubleshooting

### Системный промпт не применяется

**Проблема:** Правила из системного промпта игнорируются

**Решения:**
```bash
# 1. Проверить, что файл существует
ls -la prompts/system_prompt.md

# 2. Проверить логи
docker-compose logs review-api | grep "system prompt"

# 3. Перезапустить сервис
docker-compose restart review-api
```

### Изменения не применяются

**Проблема:** Обновил system_prompt.md, но изменения не видны

**Причина:** Кэш загружается один раз при старте

**Решение:**
```bash
# Перезапустить контейнер
docker-compose restart review-api
```

### Как проверить, что системный промпт применён?

**Способ 1:** Проверить логи при старте
```bash
docker-compose logs review-api | grep "system prompt"
# Должно быть: "Loaded system prompt from prompts/system_prompt.md"
```

**Способ 2:** Debug mode (добавить в код временно)
```python
# В base_cli_manager.py → _substitute_prompt_variables()
logger.debug(f"Final prompt length: {len(result)} chars")
logger.debug(f"System prompt prepended: {bool(BaseCLIManager._system_prompt_cache)}")
```

## Рекомендации

### ✅ DO

- Используйте системный промпт для **общих** правил кодстайла
- Используйте project rules для **специфичных** требований проекта
- Перезапускайте сервис после изменения system_prompt.md
- Версионируйте system_prompt.md в Git

### ❌ DON'T

- Не дублируйте правила между system prompt и custom rules
- Не делайте системный промпт слишком большим (>10KB)
- Не забывайте перезапускать сервис после изменений
- Не храните чувствительную информацию в системном промпте

## Примеры

### Пример 1: Lombok правила (РЕАЛИЗОВАНО)

Правила по использованию Lombok уже добавлены в системный промпт:

- **@Data** - для простых POJO/DTO
- **@Builder** - для сложных объектов
- **@Slf4j** - для логирования
- **@RequiredArgsConstructor** - для constructor injection
- **@Value** - для immutable классов
- **@NoArgsConstructor/@AllArgsConstructor** - для JPA entities

См. `prompts/system_prompt.md` секцию "Lombok Usage Guidelines"

### Пример 2: Изменить severity уровни

```markdown
# В prompts/system_prompt.md

## Custom Severity Guidelines

- **CRITICAL**: Security vulnerabilities, SQL injection, XSS
- **HIGH**: N+1 queries, business logic in controllers
- **MEDIUM**: Missing null checks, hardcoded values
- **LOW**: Style violations, naming
```

## FAQ

**Q: Можно ли использовать несколько системных промптов?**

A: Нет, система поддерживает один системный промпт. Но можно комбинировать:
- System prompt: Общие правила для всех проектов
- Custom rules: Специфичные правила для конкретного проекта

**Q: Как часто перезагружать системный промпт?**

A: При каждом изменении файла. Кэш обновляется только при рестарте сервиса.

**Q: Влияет ли размер системного промпта на производительность?**

A: Minimal. Промпт загружается один раз и кэшируется. Overhead только на prepend строки (~0.001ms).

**Q: Можно ли динамически менять системный промпт?**

A: Да, но потребуется:
1. Очистить кэш: `BaseCLIManager._system_prompt_cache = None`
2. Перезагрузить промпт: `cli_manager._load_system_prompt()`
3. Лучше просто перезапустить сервис.

