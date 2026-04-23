# Перепроектирование MR review на Hermes

## Цель

Перевести проект с модели:

- FastAPI API + два прямых CLI-адаптера (`cline`, `qwen-code`)
- внутренняя оркестрация Python-кодом
- отдельная логика подготовки prompt и публикации результата

на модель:

- **GitLab webhook → Hermes webhook adapter**
- **Hermes skill как оркестратор сценария**
- **OpenCode как исполнитель code review задач**
- **GitLab API для публикации итогового комментария в MR**

Предусловие: **Hermes Agent уже развёрнут и работает**.

---

## Почему это лучше текущей схемы

### Что было

Текущий проект заточен под два конкретных CLI-агента:

- `CLINE`
- `QWEN_CODE`

Это приводит к жёсткой привязке orchestration-слоя к деталям запуска конкретных бинарников, их аргументам, форматам вывода и способам параллелизма.

### Что становится

Hermes уже умеет:

- принимать события через webhook
- запускать агентные сценарии по template prompt
- работать в изолированном worktree
- подключать skills
- использовать встроенный skill для **OpenCode**
- хранить состояние, память и конфигурацию отдельно по профилям

В результате Python-сервис больше не обязан быть главным оркестратором ревью.

---

## Целевая архитектура

```text
GitLab MR webhook
        │
        ▼
Hermes webhook route
        │
        ▼
Prompt template маршрута
        │
        ▼
Custom skill: gitlab-mr-opencode-review
        │
        ├─ читает payload webhook
        ├─ проверяет action MR
        ├─ тянет MR metadata из GitLab API
        ├─ клонирует / обновляет repo
        ├─ строит diff source vs target
        ├─ делегирует анализ в OpenCode
        ├─ собирает markdown-отчёт
        └─ публикует note в GitLab MR
```

---

## Новые роли компонентов

### Hermes webhook

Отвечает за:

- HTTP endpoint
- валидацию `X-Gitlab-Token`
- фильтрацию по событию `merge_request`
- преобразование payload в стартовый prompt

### Hermes skill `gitlab-mr-opencode-review`

Отвечает за бизнес-логику:

1. игнорирует неподходящие actions (`close`, `merge`, `approved`, если не нужен повторный review)
2. достаёт полные данные MR
3. подготавливает рабочую директорию
4. получает diff между `target_branch` и `source_branch`
5. вызывает OpenCode на review
6. нормализует результат
7. публикует итоговый комментарий в GitLab

### OpenCode

Отвечает за фактический анализ изменений:

- ошибки
- security smells
- best practices
- архитектурные замечания
- точечные рекомендации по исправлению

---

## Что в этом репозитории добавлено

### 1. `deployment/hermes/config.hermes.example.yaml`

Готовый шаблон `config.yaml` для Hermes-профиля, где:

- включён webhook platform
- добавлен route `gitlab-mr-review`
- подключена директория skills из этого репозитория через `skills.external_dirs`

### 2. `.hermes/skills/gitlab-mr-opencode-review/`

Кастомный skill для Hermes с:

- сценарием MR review
- шаблоном prompt для OpenCode
- скриптом публикации комментария в GitLab

### 3. `docs/HERMES_SETUP_STUPID_AGENT_RU.md`

Пошаговая инструкция для «тупого агента» по развертыванию и настройке.

---

## Ожидаемый runtime flow

1. GitLab отправляет `merge_request` webhook на Hermes.
2. Hermes route `gitlab-mr-review` принимает payload.
3. В prompt route передаются `project.id`, `project.path_with_namespace`, `object_attributes.iid`, `source_branch`, `target_branch`, `action`, `url`.
4. Hermes загружает skill `gitlab-mr-opencode-review`.
5. Skill:
   - создаёт рабочую папку
   - получает проект через GitLab API
   - клонирует repo
   - fetch target/source
   - строит diff
   - формирует prompt для OpenCode
6. OpenCode возвращает review summary.
7. Hermes публикует markdown comment в исходный MR.

---

## Что сознательно НЕ делается в этой версии

Чтобы не устроить очередной корпоративный культ YAML и хрупких абстракций, в первой версии **не переносим**:

- автоматическое создание fix MR
- автоматическое создание refactoring MR
- auto-commit документации в source branch
- параллельный fan-out по множеству review types внутри Python API

Сначала надо стабильно получить **один надёжный review pipeline**:

**GitLab event → Hermes → OpenCode → comment in MR**

После стабилизации можно добавлять:

- отдельные review modes
- фоновые сессии Hermes
- multi-pass review
- автофиксы в отдельную ветку
- повторный review после push в тот же MR

---

## Рекомендуемая стратегия миграции

### Этап 1

Оставить текущий Python/FastAPI код как legacy-реализацию, но новый поток запускать только через Hermes.

### Этап 2

Когда Hermes-поток будет обкатан:

- пометить `ClineCLIManager` и `QwenCodeCLIManager` как deprecated
- убрать прямую зависимость от этих бинарников из production deployment
- оставить Python-код только как reference / архивный implementation path

### Этап 3

Если Hermes полностью закрывает use case:

- перенести проект в формат skill-pack + deployment docs
- свести Python backend к вспомогательным утилитам или убрать целиком

---

## Практические замечания

### 1. GitLab комментарий

У Hermes из коробки есть documented delivery для GitHub comment, но для GitLab удобнее и надёжнее публиковать note напрямую через GitLab API из skill/script.

### 2. Worktree и sandbox

Для webhook-triggered сценариев лучше использовать:

- отдельный Hermes profile под automation
- отдельную рабочую директорию
- при возможности Docker backend или изолированный Linux user

### 3. Skills из репозитория

Рекомендуемый режим для этого проекта:

- skill хранится в git-репозитории
- Hermes подключает его через `skills.external_dirs`

Так skill versioned вместе с проектом, а не расползается по машине в стиле «кто-то когда-то что-то правил руками на сервере». Люди это обожают, пока не надо воспроизводить окружение.

---

## Минимальный definition of done

Решение считается внедрённым, если выполняется всё ниже:

- Hermes принимает `merge_request` webhook от GitLab
- skill запускается только на нужных actions
- repo клонируется и diff строится корректно
- OpenCode получает prompt с контекстом MR
- результат публикуется комментарием в исходный MR
- настройка воспроизводима по инструкции из `docs/HERMES_SETUP_STUPID_AGENT_RU.md`

---

## Следующие улучшения

1. Добавить режимы review:
   - `full`
   - `security`
   - `architecture`
   - `quick`

2. Добавить label-based routing:
   - `ai-review`
   - `ai-review-security`
   - `ai-review-arch`

3. Добавить автофиксы в отдельную ветку через OpenCode.

4. Добавить сохранение review artifacts:
   - raw diff
   - raw OpenCode output
   - final markdown comment

5. Добавить re-review на каждый новый push в тот же MR.
