# Обработка ошибок и восстановление

## Категории ошибок

### 1. CLI Execution Errors

#### 1.1. CLI Not Found

**Симптомы**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'cline'
```

**Причины**:
- CLI не установлен
- CLI не в PATH
- Неправильная конфигурация Dockerfile

**Диагностика**:
```bash
# Проверка установки
docker exec code-review-api which cline
docker exec code-review-api cline --version

# Проверка PATH
docker exec code-review-api env | grep PATH
```

**Решение**:
```dockerfile
# Dockerfile - установка CLI глобально
RUN npm install -g @cline/cli
RUN npm install -g @qwen-code/qwen-code

# Альтернатива: локальная установка
WORKDIR /app
RUN npm install @cline/cli
ENV PATH="/app/node_modules/.bin:${PATH}"
```

#### 1.2. CLI Timeout

**Симптомы**:
```
asyncio.TimeoutError: CLI execution exceeded 300 seconds
```

**Причины**:
- Слишком большой MR (>10k lines)
- Model API медленно отвечает
- Сложный код требует больше времени

**Диагностика**:
```python
# Логи покажут
logger.error(f"CLI timeout after {settings.REVIEW_TIMEOUT}s", extra={
    "project_id": 123,
    "mr_iid": 456,
    "mr_size_lines": 15000,  # Большой MR
    "review_type": "architecture"  # Сложный тип
})
```

**Решение**:

**A. Увеличить timeout**:
```python
# .env
REVIEW_TIMEOUT=600  # 10 минут для больших MR
```

**B. Разбить review на части**:
```python
# ReviewService - chunking для больших MR
async def execute_review(self, request, repo_path):
    changed_files = await self.get_changed_files(repo_path)
    
    if len(changed_files) > 50:  # Слишком много файлов
        logger.info(f"Large MR detected: {len(changed_files)} files. Splitting into chunks.")
        chunks = self._split_into_chunks(changed_files, chunk_size=20)
        
        results = []
        for chunk in chunks:
            result = await self._review_chunk(chunk, request)
            results.append(result)
        
        return self._merge_results(results)
```

**C. Graceful degradation**:
```python
# Fallback на быстрые review types при timeout
try:
    result = await cli_manager.execute_review(
        review_types=[ReviewType.ALL],
        timeout=300
    )
except asyncio.TimeoutError:
    logger.warning("Full review timed out, falling back to quick checks")
    result = await cli_manager.execute_review(
        review_types=[ReviewType.ERROR_DETECTION, ReviewType.SECURITY_AUDIT],
        timeout=120
    )
```

#### 1.3. CLI Out of Memory

**Симптомы**:
```
Process was killed (OOM)
CLI stderr: "JavaScript heap out of memory"
```

**Причины**:
- Node.js heap size по умолчанию (512MB)
- Большие файлы в MR

**Решение**:
```bash
# Увеличить Node.js heap
export NODE_OPTIONS="--max-old-space-size=4096"  # 4GB

# В Dockerfile
ENV NODE_OPTIONS="--max-old-space-size=4096"
```

```yaml
# K8s - увеличить memory limits
resources:
  limits:
    memory: "4Gi"  # Вместо 2Gi
```

#### 1.4. CLI Invalid Output

**Симптомы**:
```
json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Причины**:
- CLI вернул non-JSON output
- CLI напечатал warnings/errors в stdout
- CLI crash

**Диагностика**:
```python
logger.error("Failed to parse CLI output", extra={
    "raw_output": stdout.decode()[:1000],  # Первые 1000 символов
    "stderr": stderr.decode()
})
```

**Решение**:
```python
# Robust parsing в ClineCLIManager
async def _parse_cli_output(self, stdout, stderr):
    output = stdout.decode('utf-8').strip()
    
    # Попытка 1: Чистый JSON
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass
    
    # Попытка 2: JSON внутри текста
    json_start = output.find('{')
    json_end = output.rfind('}')
    if json_start != -1 and json_end != -1:
        json_str = output[json_start:json_end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Попытка 3: Fallback на пустой результат
    logger.warning(f"Could not parse CLI output, using fallback")
    return {
        "issues": [],
        "summary": "Review completed but output parsing failed",
        "raw_output": output[:500]
    }
```

### 2. Model API Errors

#### 2.1. API Unavailable (503, Connection Error)

**Симптомы**:
```
httpx.ConnectError: Connection refused
or
httpx.HTTPStatusError: 503 Service Unavailable
```

**Причины**:
- Model API server down
- Network issues
- API overloaded

**Решение**:

**A. Retry с exponential backoff**:
```python
# В BaseCLIManager
async def _call_model_api_with_retry(self, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await self._call_model_api(prompt)
            return response
        except (httpx.ConnectError, httpx.HTTPStatusError) as e:
            if e.response.status_code == 503:
                wait_time = 2 ** attempt + random.uniform(0, 1)  # Exponential backoff с jitter
                logger.warning(f"Model API unavailable, retry {attempt+1}/{max_retries} after {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            else:
                raise
    
    raise Exception(f"Model API unavailable after {max_retries} retries")
```

**B. Fallback на резервный endpoint**:
```python
# config.py
MODEL_API_URL_PRIMARY = "https://primary-api.example.com/v1"
MODEL_API_URL_SECONDARY = "https://backup-api.example.com/v1"

# В ClineCLIManager
async def _call_model_api(self, prompt):
    try:
        return await self._call_api(self.primary_url, prompt)
    except Exception as e:
        logger.warning(f"Primary API failed: {e}, trying secondary")
        return await self._call_api(self.secondary_url, prompt)
```

**C. Circuit breaker pattern**:
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_model_api(self, prompt):
    # После 5 failed attempts, открыть circuit на 60 секунд
    # Все запросы будут немедленно rejected без попытки вызова
    return await self._call_api(self.api_url, prompt)
```

#### 2.2. Rate Limiting (429)

**Симптомы**:
```
httpx.HTTPStatusError: 429 Too Many Requests
Headers: {'Retry-After': '60'}
```

**Решение**:
```python
async def _handle_rate_limit(self, response):
    retry_after = int(response.headers.get('Retry-After', 60))
    logger.warning(f"Rate limited, waiting {retry_after}s")
    
    # Exponentially decrease parallel tasks
    self.parallel_tasks = max(1, self.parallel_tasks // 2)
    logger.info(f"Reduced parallel tasks to {self.parallel_tasks}")
    
    await asyncio.sleep(retry_after)
    
    # Retry request
    return await self._call_model_api(prompt)
```

#### 2.3. Invalid API Key (401)

**Симптомы**:
```
httpx.HTTPStatusError: 401 Unauthorized
```

**Решение**:
```python
# Health check при старте
@app.on_event("startup")
async def verify_api_key():
    try:
        response = await httpx.get(
            f"{settings.MODEL_API_URL}/models",
            headers={"Authorization": f"Bearer {settings.MODEL_API_KEY}"}
        )
        response.raise_for_status()
        logger.info("Model API key valid")
    except httpx.HTTPStatusError as e:
        logger.error(f"Invalid Model API key: {e}")
        # Alert DevOps
        await send_alert("Invalid Model API key", severity="critical")
        # Не падать, но помечать service as unhealthy
        app.state.model_api_available = False
```

### 3. GitLab API Errors

#### 3.1. Insufficient Permissions (403)

**Симптомы**:
```
gitlab.exceptions.GitlabCreateError: 403 Forbidden
```

**Причины**:
- GitLab token не имеет прав на создание MR
- Token не имеет доступа к проекту

**Решение**:
```python
# При старте проверить permissions
async def verify_gitlab_permissions(self):
    try:
        # Проверить доступ к тестовому проекту
        project = await self.client.get("/projects/test-project-id")
        
        # Проверить scope токена
        user = await self.client.get("/user")
        scopes = user.headers.get("X-Oauth-Scopes", "")
        
        required_scopes = ["api", "write_repository"]
        missing_scopes = [s for s in required_scopes if s not in scopes]
        
        if missing_scopes:
            logger.error(f"GitLab token missing scopes: {missing_scopes}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"GitLab permission check failed: {e}")
        return False
```

#### 3.2. MR Already Exists

**Симптомы**:
```
gitlab.exceptions.GitlabCreateError: Branch already has merge request
```

**Решение**:
```python
# Idempotent MR creation
async def create_or_update_mr(self, project_id, source, target, title, description):
    try:
        # Попытка создать
        mr = await self.client.post(f"/projects/{project_id}/merge_requests", {
            "source_branch": source,
            "target_branch": target,
            "title": title,
            "description": description
        })
        logger.info(f"MR created: !{mr['iid']}")
        return mr
    except gitlab.exceptions.GitlabCreateError as e:
        if "already has merge request" in str(e).lower():
            # MR уже существует, найти и обновить
            logger.info(f"MR already exists for {source} → {target}, updating")
            mrs = await self.client.get(f"/projects/{project_id}/merge_requests", params={
                "source_branch": source,
                "target_branch": target,
                "state": "opened"
            })
            if mrs:
                mr = mrs[0]
                updated_mr = await self.client.put(
                    f"/projects/{project_id}/merge_requests/{mr['iid']}",
                    {"description": description}
                )
                logger.info(f"MR updated: !{updated_mr['iid']}")
                return updated_mr
        raise
```

### 4. Git Repository Errors

#### 4.1. Clone Failure (Authentication)

**Симптомы**:
```
git clone failed: Authentication failed for 'https://gitlab.example.com/project.git'
```

**Решение**:
```python
# Использовать token в clone URL
def get_authenticated_clone_url(self, project_data):
    clone_url = project_data['http_url_to_repo']
    
    # Вставить token в URL
    parsed = urllib.parse.urlparse(clone_url)
    authenticated_url = parsed._replace(
        netloc=f"oauth2:{self.token}@{parsed.netloc}"
    )
    
    return urllib.parse.urlunparse(authenticated_url)
```

#### 4.2. Disk Space Full

**Симптомы**:
```
OSError: [Errno 28] No space left on device
```

**Диагностика**:
```python
import shutil

def get_disk_usage(path="/tmp/review"):
    total, used, free = shutil.disk_usage(path)
    return {
        "total_gb": total // (2**30),
        "used_gb": used // (2**30),
        "free_gb": free // (2**30),
        "percent_used": (used / total) * 100
    }

logger.info("Disk usage", extra=get_disk_usage())
```

**Решение**:
```python
# Cleanup старых репозиториев
async def cleanup_old_repositories(self, max_age_hours=2):
    import time
    now = time.time()
    
    for repo_dir in os.listdir(self.work_dir):
        repo_path = os.path.join(self.work_dir, repo_dir)
        mtime = os.path.getmtime(repo_path)
        age_hours = (now - mtime) / 3600
        
        if age_hours > max_age_hours:
            logger.info(f"Removing old repository: {repo_dir} (age: {age_hours:.1f}h)")
            shutil.rmtree(repo_path)

# Вызывать periodically
@app.on_event("startup")
async def start_cleanup_task():
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    while True:
        await asyncio.sleep(3600)  # Каждый час
        await git_manager.cleanup_old_repositories(max_age_hours=2)
```

## Logging Best Practices

### Structured Logging

```python
from loguru import logger

# Всегда использовать extra для structured fields
logger.info("Review started", extra={
    "correlation_id": correlation_id,
    "project_id": project_id,
    "mr_iid": mr_iid,
    "agent": agent.value,
    "review_types": [rt.value for rt in review_types]
})

# При ошибках - включать context
logger.error("CLI execution failed", extra={
    "command": command,
    "exit_code": process.returncode,
    "stderr": stderr.decode()[:500],  # Limit size
    "repo_path": repo_path
})
```

### Log Levels

- **DEBUG**: Детальная информация для отладки (каждый шаг CLI, raw outputs)
- **INFO**: Нормальный flow (review started, MR created, completion)
- **WARNING**: Потенциальные проблемы (timeout retry, rate limit, fallback)
- **ERROR**: Ошибки с partial recovery (CLI failed но review продолжился)
- **CRITICAL**: Фатальные ошибки (service cannot start, invalid config)

### Correlation ID

```python
import uuid

# При каждом request создавать correlation_id
@router.post("/api/v1/review")
async def review(request: ReviewRequest):
    correlation_id = str(uuid.uuid4())
    
    # Передавать везде
    result = await review_service.execute_review(
        request, correlation_id=correlation_id
    )
    
    # Логи будут с correlation_id
    # grep "abc-123-def-456" logs/*.log покажет весь flow
```

## Alerting

### Critical Alerts (PagerDuty/Slack)

```python
# Когда отправлять critical alert:
- Model API down (>5 минут)
- GitLab API unreachable
- Disk space <10%
- Memory >90%
- CLI не установлен при старте

async def send_critical_alert(message, details):
    await slack.post_message(
        channel="#code-review-alerts",
        text=f"🚨 CRITICAL: {message}",
        attachments=[{
            "color": "danger",
            "fields": [{"title": k, "value": v} for k, v in details.items()]
        }]
    )
    
    # Также отправить в PagerDuty если production
    if settings.ENV == "production":
        await pagerduty.trigger_incident(
            title=message,
            severity="critical",
            details=details
        )
```

### Warning Alerts (Slack only)

```python
# Когда отправлять warning:
- Rate limiting activated
- Fallback на secondary API
- CLI timeout (но review продолжился)
- High review duration (>3 min)

async def send_warning_alert(message, details):
    await slack.post_message(
        channel="#code-review-warnings",
        text=f"⚠️ WARNING: {message}",
        attachments=[{
            "color": "warning",
            "fields": [{"title": k, "value": v} for k, v in details.items()]
        }]
    )
```

## Metrics & Monitoring

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Errors
cli_errors = Counter(
    'cli_errors_total',
    'Total CLI errors',
    ['agent', 'error_type']  # error_type: timeout, oom, parse_error
)

model_api_errors = Counter(
    'model_api_errors_total',
    'Model API errors',
    ['status_code', 'endpoint']
)

gitlab_api_errors = Counter(
    'gitlab_api_errors_total',
    'GitLab API errors',
    ['method', 'status_code']
)

# Recovery
retries_total = Counter(
    'retries_total',
    'Total retries',
    ['operation', 'success']  # operation: cli, model_api, gitlab_api
)

fallbacks_total = Counter(
    'fallbacks_total',
    'Total fallbacks to secondary system',
    ['from', 'to']  # from: cline, to: qwen
)

# Disk usage
disk_usage_percent = Gauge(
    'disk_usage_percent',
    'Disk usage percentage',
    ['mount_point']
)
```

### Grafana Alerts

```yaml
# Alert: High Error Rate
- alert: HighCLIErrorRate
  expr: rate(cli_errors_total[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High CLI error rate ({{ $value }} errors/sec)"

# Alert: Model API Down
- alert: ModelAPIDown
  expr: model_api_errors_total{status_code="503"} > 10
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Model API appears to be down"

# Alert: Disk Space Low
- alert: DiskSpaceLow
  expr: disk_usage_percent{mount_point="/tmp/review"} > 90
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Disk space critically low ({{ $value }}%)"
```

## Recovery Procedures

### Manual Recovery

#### 1. CLI Crash - Restart review
```bash
# Найти failed review
kubectl logs -n code-review deployment/code-review-api | grep "ERROR.*CLI execution failed"

# Перезапустить через API
curl -X POST http://code-review.example.com/api/v1/review \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 123,
    "merge_request_iid": 456,
    "agent": "QWEN_CODE",  # Fallback на другой agent
    "review_types": ["ERROR_DETECTION", "SECURITY_AUDIT"]  # Только критичные
  }'
```

#### 2. Disk Space Full - Cleanup
```bash
# Вручную удалить старые repos
kubectl exec -n code-review deployment/code-review-api -- \
  find /tmp/review -type d -mtime +1 -exec rm -rf {} \;

# Или через API (если добавить endpoint)
curl -X POST http://code-review.example.com/api/v1/admin/cleanup
```

#### 3. Model API Down - Wait and retry
```bash
# Проверить статус Model API
curl -H "Authorization: Bearer $MODEL_API_KEY" \
  https://model-api.example.com/v1/models

# Если down, подождать recovery или переключить на backup
# В .env изменить MODEL_API_URL на backup endpoint
kubectl set env deployment/code-review-api -n code-review \
  MODEL_API_URL=https://backup-model-api.example.com/v1

# Rollout restart
kubectl rollout restart deployment/code-review-api -n code-review
```

### Automatic Recovery

```python
# Graceful degradation при partial failures
async def execute_review_with_graceful_degradation(self, request, repo_path):
    results = {}
    failed_review_types = []
    
    for review_type in request.review_types:
        try:
            result = await self._execute_single_review(review_type, repo_path)
            results[review_type] = result
        except Exception as e:
            logger.error(f"Review type {review_type} failed: {e}")
            failed_review_types.append(review_type)
            # Продолжить с остальными типами
            continue
    
    if not results:
        # Все failed, raise error
        raise Exception(f"All review types failed: {failed_review_types}")
    
    # Partial success
    logger.warning(f"Partial review completed. Failed types: {failed_review_types}")
    return self._aggregate_results(results, failed_types=failed_review_types)
```

## Тестирование обработки ошибок

```python
# tests/test_error_handling.py

@pytest.mark.asyncio
async def test_cli_timeout_recovery():
    """Test CLI timeout triggers retry"""
    manager = ClineCLIManager(timeout=1)  # 1 second timeout
    
    with pytest.raises(asyncio.TimeoutError):
        await manager.execute_review(
            review_types=[ReviewType.ALL],
            repo_path="/large-repo"
        )
    
    # Verify retry was attempted
    assert manager.retry_count == 3

@pytest.mark.asyncio
async def test_model_api_fallback():
    """Test fallback to secondary API"""
    manager = ClineCLIManager(
        primary_api="http://down-api.com",
        secondary_api="http://working-api.com"
    )
    
    result = await manager.execute_review(...)
    
    # Should use secondary API
    assert manager.api_calls["secondary"] > 0
    assert result is not None

@pytest.mark.asyncio
async def test_graceful_degradation():
    """Test partial review completion"""
    # Mock one review type to fail
    with mock.patch.object(ClineCLIManager, '_execute_single_review') as mock_execute:
        mock_execute.side_effect = [
            ReviewRawResult(...),  # ERROR_DETECTION success
            Exception("CLI crashed"),  # SECURITY fail
            ReviewRawResult(...)  # REFACTORING success
        ]
        
        result = await review_service.execute_review(...)
        
        # Should have partial results
        assert len(result.issues) > 0
        assert "SECURITY_AUDIT" in result.failed_review_types
```


