# Архитектура AI Code Review System

## Обзор компонентов

```
┌───────────────────────────────────────────────────────────────┐
│                         n8n Workflow                          │
│  (Trigger на GitLab webhooks, валидация MR, запуск review)   │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│                    FastAPI Review Service                     │
│                                                               │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │   Routes    │──►│   Services   │──►│  CLI Managers   │  │
│  │  /review    │   │  - Review    │   │  - Cline        │  │
│  │  /validate  │   │  - GitLab    │   │  - QwenCode     │  │
│  │  /health    │   │  - Git       │   └─────────────────┘  │
│  └─────────────┘   │  - MR Creator│                         │
│                    │  - Rules     │                         │
│                    └──────────────┘                         │
└────────────┬──────────────────────────────────────┬──────────┘
             │                                       │
             ▼                                       ▼
┌─────────────────────┐                  ┌──────────────────────┐
│    GitLab API       │                  │   Model API          │
│  - Get MR data      │                  │  (OpenAI-compatible) │
│  - Create MR        │                  │  - DeepSeek V3.1     │
│  - Add comments     │                  │  - Qwen3-Coder       │
│  - Commit changes   │                  └──────────────────────┘
└─────────────────────┘
             │
             ▼
┌─────────────────────┐
│   Git Repository    │
│  - Clone locally    │
│  - CLI analysis     │
│  - Commit docs      │
└─────────────────────┘
```

## Детальная архитектура слоев

### 1. API Layer (FastAPI)

```python
app/
├── main.py              # FastAPI app, CORS, lifespan
├── api/
│   ├── routes.py        # REST endpoints
│   └── schemas.py       # Request/Response models (deprecated)
├── models.py            # Pydantic models для всех сущностей
├── config.py            # Settings из env vars
└── dependencies.py      # DI для сервисов
```

**Endpoints**:
- `POST /api/v1/review` - Главный endpoint для review MR
- `POST /api/v1/validate-mr` - Валидация MR перед review (для n8n)
- `GET /api/v1/health` - Health check с проверкой всех зависимостей

### 2. Service Layer

```python
app/services/
├── review_service.py              # Оркестратор review процесса
├── cline_cli_manager.py           # Менеджер Cline CLI
├── qwen_code_cli_manager.py       # Менеджер Qwen Code CLI
├── base_cli_manager.py            # Базовый класс для CLI менеджеров
├── custom_rules_loader.py         # Загрузка правил (default/project/Confluence)
├── gitlab_service.py              # Минимальное взаимодействие с GitLab API
├── git_repository_manager.py     # Локальные Git операции (clone, commit, push)
├── refactoring_classifier.py     # Классификация рефакторинга (SIGNIFICANT/MINOR)
├── mr_creator.py                  # Создание MR для fixes/refactoring
├── jira_task_matcher_agent.py    # TODO: JIRA task validation
├── changelog_generator_agent.py  # TODO: Changelog generation
├── library_updater_agent.py      # TODO: Library updates checker
└── mcp_rag_client.py             # TODO: MCP RAG integration
```

### 3. Data Flow

#### Review Process Flow

```
1. n8n Webhook Trigger
   │
   ▼
2. n8n: Validate MR
   │ POST /api/v1/validate-mr
   │ - Check JIRA ticket
   │ - Check description
   ▼
3. n8n: Trigger Review
   │ POST /api/v1/review
   │ {
   │   "project_id": 123,
   │   "merge_request_iid": 456,
   │   "agent": "CLINE",
   │   "review_types": ["ALL"]
   │ }
   ▼
4. ReviewService
   │ - Select CLI manager (Cline/Qwen)
   │ - Load rules & prompts
   │ - Clone repository
   ▼
5. CLI Manager (parallel execution)
   │
   ├─► Cline CLI Instance 1 → ERROR_DETECTION
   ├─► Cline CLI Instance 2 → BEST_PRACTICES  
   ├─► Cline CLI Instance 3 → SECURITY_AUDIT
   ├─► Cline CLI Instance 4 → REFACTORING
   └─► Cline CLI Instance 5 → DOCUMENTATION
   │
   │ Each CLI:
   │ 1. Reads git diff automatically
   │ 2. Calls Model API with prompt
   │ 3. Returns JSON results
   ▼
6. Aggregate Results
   │ - Merge all findings
   │ - Classify issues by severity
   │ - Classify refactoring (SIGNIFICANT/MINOR)
   ▼
7. Background Tasks (async)
   │
   ├─► Commit documentation → source branch
   ├─► Create Fix MR (+ minor refactoring)
   ├─► Create Refactoring MR (if significant)
   ├─► Post comment to original MR
   └─► Cleanup repository
   ▼
8. Return Review Result to n8n
```

## CLI Agents Architecture

### Cline CLI Manager

**Model**: DeepSeek V3.1 Terminus  
**Parallel Tasks**: 5  
**Review Types**: Все 11 типов

```python
class ClineCLIManager(BaseCLIManager):
    async def execute_parallel_reviews(
        self,
        review_types: List[ReviewType],
        repo_path: str,
        prompts: Dict[str, str],
        custom_rules: Dict[str, str]
    ) -> List[ReviewRawResult]:
        # Создать семафор для ограничения параллельности
        semaphore = asyncio.Semaphore(self.parallel_tasks)
        
        tasks = []
        for review_type in review_types:
            task = self._execute_single_review(
                review_type, repo_path, prompts, custom_rules, semaphore
            )
            tasks.append(task)
        
        # Запустить все параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

### Qwen Code CLI Manager

**Model**: Qwen3-Coder-32B  
**Parallel Tasks**: 3  
**Review Types**: ERROR_DETECTION, BEST_PRACTICES, REFACTORING (основные)

```python
class QwenCodeCLIManager(BaseCLIManager):
    # Аналогично Cline, но с меньшей параллельностью
    # и оптимизирован для быстрого ревью базовых проверок
```

## Prompts System

```
prompts/
├── cline/                    # Для DeepSeek через Cline
│   ├── error_detection.md
│   ├── best_practices.md
│   ├── refactoring.md
│   ├── security_audit.md
│   └── documentation.md
├── qwen/                     # Для Qwen3-Coder
│   ├── error_detection.md
│   ├── best_practices.md
│   └── refactoring.md
├── additional/               # Общие промты для обоих
│   ├── performance.md
│   ├── architecture.md
│   ├── transaction_management.md
│   ├── concurrency.md
│   └── database_optimization.md
└── todo/                     # Промты для TODO agents
    ├── jira_task_matcher.md
    └── changelog_generator.md
```

**Переменные в промтах**:
- `{{CODE}}` - Измененный код (from git diff)
- `{{LANGUAGE}}` - Язык программирования
- `{{RULES}}` - Загруженные правила
- `{{CONTEXT}}` - Дополнительный контекст (JIRA, description)
- `{{REVIEW_TYPE}}` - Тип проверки
- `{{MR_TITLE}}` - Заголовок MR
- `{{MR_DESCRIPTION}}` - Описание MR

## Rules System

```
rules/
├── java-spring-boot/         # Default rules для Java
│   ├── README.md
│   ├── error_detection.md
│   ├── best_practices.md
│   ├── security.md
│   ├── refactoring_criteria.md
│   ├── documentation_style.md
│   └── performance.md
├── python/                   # TODO: Python rules
└── javascript/               # TODO: JS rules
```

**Приоритет загрузки правил**:
1. **Project-specific rules** (из параметра `project_rules_path` в API request)
2. **Confluence rules** (если `CONFLUENCE_RULES_ENABLED=true`)
3. **Default rules** (из `rules/<language>/`)

## GitLab Integration

### Минимальное использование API

**Почему минимальное?**
- GitLab API имеет rate limits
- Медленнее чем Git CLI
- Больше точек отказа

**Что делается через API**:
- ✅ Получение данных MR (`get_merge_request`)
- ✅ Получение project data (`get_project`)
- ✅ Создание MR (`create_merge_request`)
- ✅ Добавление комментариев (`post_mr_comment`)

**Что делается через Git CLI**:
- ✅ Клонирование репозитория
- ✅ Определение измененных файлов (`git diff`)
- ✅ Анализ истории (`git log`)
- ✅ Коммиты документации
- ✅ Push в ветки

```python
# GitLabService - только для API
class GitLabService:
    async def get_merge_request(self, project_id, mr_iid):
        return await self.client.get(f"/projects/{project_id}/merge_requests/{mr_iid}")
    
    async def create_merge_request(self, project_id, source, target, title):
        return await self.client.post(f"/projects/{project_id}/merge_requests", ...)

# GitRepositoryManager - для Git CLI
class GitRepositoryManager:
    async def clone_repository(self, clone_url, branch):
        await self._execute_git(["clone", "-b", branch, clone_url, repo_path])
    
    async def commit_and_push(self, repo_path, branch, message):
        await self._execute_git(["add", "."], cwd=repo_path)
        await self._execute_git(["commit", "-m", message], cwd=repo_path)
        await self._execute_git(["push", "origin", branch], cwd=repo_path)
```

## MR Creation Strategy

### 1. Documentation Commit (Always)

```
source_branch
└── Commit: "[Code Review] Add Javadoc and comments"
    - Updated Java files with javadoc
    - Added inline comments
```

### 2. Fixes MR (If issues found)

```
source_branch → fixes_branch → target_branch
                    │
                    └── MR: "Code Review: Fixes for MR !123"
                        - Fix critical bugs
                        - Fix security issues
                        - Minor refactoring (if any)
```

### 3. Refactoring MR (If significant refactoring)

```
source_branch → refactoring_branch → target_branch
                    │
                    └── MR: "Code Review: Refactoring for MR !123"
                        - Architectural improvements
                        - Major refactoring
                        - Performance optimizations
```

**Критерии SIGNIFICANT refactoring**:
- Затрагивает >3 файлов
- Изменяет архитектуру
- Требует >4 часов работы
- Содержит ключевые слова: "architecture", "design pattern", "restructure"

## Scalability

### Horizontal Scaling (K8s)

```yaml
# Автомасштабирование по CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: code-review-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: code-review-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Resource Requirements

**Minimum (1 pod)**:
- CPU: 500m (0.5 core)
- Memory: 512Mi
- Disk: 10Gi (для `/tmp/review`)

**Recommended (production)**:
- CPU: 2000m (2 cores) - для параллельных CLI вызовов
- Memory: 2Gi - CLI + Git + Node.js
- Disk: 50Gi - множественные репозитории

**Limits**:
- Одновременно: до 10 active reviews на pod
- Max MR size: 10,000 lines of code
- Timeout: 5 минут на review

## Security

### Secrets Management

```yaml
# Kubernetes Secrets
apiVersion: v1
kind: Secret
metadata:
  name: code-review-secrets
type: Opaque
data:
  MODEL_API_KEY: <base64>
  GITLAB_TOKEN: <base64>
  CONFLUENCE_API_TOKEN: <base64>
```

### Network Security

```yaml
# NetworkPolicy: Разрешить только необходимые соединения
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: code-review-api
spec:
  podSelector:
    matchLabels:
      app: code-review-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector: {}  # Model API
    ports:
    - protocol: TCP
      port: 443
  - to:
    - namespaceSelector: {}  # GitLab
    ports:
    - protocol: TCP
      port: 443
```

### RBAC (K8s)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: code-review-pod-reader
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: code-review-pod-reader-binding
subjects:
- kind: ServiceAccount
  name: code-review-sa
roleRef:
  kind: Role
  name: code-review-pod-reader
  apiGroup: rbac.authorization.k8s.io
```

## Monitoring & Observability

### Prometheus Metrics

```
code_review_duration_seconds{agent="cline", review_type="error_detection", status="success"}
code_review_total{agent="cline", review_type="all", status="success"}
cli_timeouts_total{agent="cline"}
model_api_errors_total{status_code="503"}
active_reviews
gitlab_api_calls_total{method="create_mr", status="201"}
```

### Grafana Dashboards

1. **Review Performance**
   - Review duration (p50, p95, p99)
   - Success rate
   - CLI timeouts

2. **System Health**
   - Active reviews
   - Memory usage
   - Disk usage (/tmp/review)

3. **Model API**
   - Request rate
   - Error rate
   - Latency

### Logging

```
# Structured JSON logs
{
  "timestamp": "2025-01-15T14:30:45Z",
  "level": "INFO",
  "correlation_id": "abc-123-def",
  "project_id": 123,
  "mr_iid": 456,
  "agent": "cline",
  "review_type": "error_detection",
  "duration_ms": 12450,
  "status": "success",
  "issues_found": 3
}
```

## Future Enhancements

### Phase 2: TODO Agents

1. **JIRA Task Matcher**
   - Проверка соответствия кода описанию задачи
   - Автокомментарии с расхождениями

2. **Changelog Generator**
   - Автоматическое обновление CHANGELOG.md
   - Semantic versioning

3. **Library Updater**
   - Проверка устаревших зависимостей
   - Предложение обновлений

### Phase 3: MCP RAG Integration

- Remote RAG через n8n MCP server
- Контекст из базы знаний компании
- Поиск похожих решений в прошлых MR

### Phase 4: Advanced Features

- Multi-language support (Python, JS, Go)
- Custom review types через API
- ML-based priority scoring
- Review suggestions learning


