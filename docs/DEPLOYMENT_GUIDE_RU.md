# Полное руководство по развертыванию

## Предварительные требования

### Обязательные компоненты

1. **Model API** (OpenAI-compatible)
   - DeepSeek V3.1 Terminus (для Cline)
   - Qwen3-Coder-32B (для Qwen Code)
   - URL endpoint и API key

2. **GitLab**
   - URL GitLab instance
   - Personal Access Token с правами: `api`, `write_repository`

3. **Инфраструктура** (один из вариантов):
   - Docker + Docker Compose
   - Kubernetes cluster (v1.24+)

### Опциональные компоненты

- **Confluence** (для загрузки правил)
- **n8n** (для автоматизации workflows)
- **Prometheus + Grafana** (для мониторинга)

## Вариант 1: Docker Compose (Рекомендуется для начала)

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/your-org/code-review-system.git
cd code-review-system
```

### Шаг 2: Настройка переменных окружения

Создайте `.env` файл:

```bash
cat > .env << 'EOF'
# ==== Model API ====
MODEL_API_URL=https://your-model-api.example.com/v1
MODEL_API_KEY=sk-your-api-key-here

# Model Names
DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
QWEN3_MODEL_NAME=qwen3-coder-32b

# ==== CLI Configuration ====
DEFAULT_CLI_AGENT=CLINE
CLINE_PARALLEL_TASKS=5
QWEN_PARALLEL_TASKS=3
REVIEW_TIMEOUT=300

# ==== GitLab ====
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-your-gitlab-token

# ==== Application ====
VERSION=2.0.0
LOG_LEVEL=INFO
WORK_DIR=/tmp/review
DEFAULT_LANGUAGE=java

# ==== Optional: Confluence ====
CONFLUENCE_RULES_ENABLED=false
# CONFLUENCE_URL=https://confluence.example.com
# CONFLUENCE_API_TOKEN=your-confluence-token

# ==== Optional: MCP RAG ====
MCP_RAG_ENABLED=false
# MCP_SERVER_URL=http://n8n-mcp-server:3000
EOF
```

### Шаг 3: Установка CLI инструментов (если не используете Docker)

**Для локального development**:

```bash
# Установить Node.js 18+ и npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Установить Cline CLI
sudo npm install -g @cline/cli

# Установить Qwen Code CLI
sudo npm install -g @qwen-code/qwen-code

# Проверить установку
cline --version
qwen-code --version
```

**Примечание**: Если CLI пакеты недоступны в npm, см. [docs/CLI_SETUP.md](CLI_SETUP.md) для ручной установки.

### Шаг 4: Запуск с Docker Compose

```bash
# Собрать и запустить
docker-compose up --build -d

# Проверить логи
docker-compose logs -f

# Проверить health
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

### Шаг 5: Тестирование

```bash
# Простой health check
curl http://localhost:8000/health

# Детальный health check
curl http://localhost:8000/api/v1/health | jq

# Пример response:
# {
#   "status": "healthy",
#   "version": "2.0.0",
#   "cline_available": true,
#   "qwen_available": true,
#   "model_api_connected": true,
#   "gitlab_connected": true
# }
```

### Troubleshooting Docker Compose

#### Проблема: CLI not found

```bash
# Зайти в контейнер
docker exec -it code-review-api bash

# Проверить установку
which cline
which qwen-code
node --version
npm --version

# Если не установлено, установить вручную
npm install -g @cline/cli @qwen-code/qwen-code
```

#### Проблема: Model API connection failed

```bash
# Проверить из контейнера
docker exec -it code-review-api bash
curl -H "Authorization: Bearer $MODEL_API_KEY" \
  $MODEL_API_URL/models

# Проверить network
docker-compose exec code-review-api ping your-model-api-host
```

#### Проблема: Out of disk space

```bash
# Проверить использование
docker system df

# Очистить старые образы
docker system prune -a

# Увеличить volume size в docker-compose.yml
volumes:
  review-work:
    driver: local
    driver_opts:
      type: none
      device: /mnt/large-disk/review-work
      o: bind
```

## Вариант 2: Kubernetes

### Шаг 1: Подготовка Docker image

```bash
# Собрать image
docker build -t your-registry.example.com/code-review-api:2.0.0 .

# Push в registry
docker push your-registry.example.com/code-review-api:2.0.0
```

### Шаг 2: Настройка Secrets

```bash
cd deployment/kubernetes

# Создать namespace
kubectl apply -f namespace.yaml

# Создать secrets (отредактируйте secret.yaml с реальными значениями)
kubectl create secret generic code-review-secrets \
  --from-literal=MODEL_API_KEY=sk-your-api-key \
  --from-literal=GITLAB_TOKEN=glpat-your-gitlab-token \
  --namespace=code-review

# Или через файл
kubectl apply -f secret.yaml
```

### Шаг 3: Настройка ConfigMap

```bash
# Отредактируйте configmap.yaml под вашу среду
vim configmap.yaml

# Примените
kubectl apply -f configmap.yaml
```

### Шаг 4: Создание ConfigMaps для prompts и rules

```bash
# Из корня проекта
kubectl create configmap code-review-prompts \
  --from-file=prompts/ \
  --namespace=code-review

kubectl create configmap code-review-rules \
  --from-file=rules/ \
  --namespace=code-review
```

### Шаг 5: Deployment

```bash
# Deploy приложения
kubectl apply -f deployment.yaml

# Service
kubectl apply -f service.yaml

# Ingress (если есть)
kubectl apply -f ingress.yaml

# Проверить статус
kubectl get pods -n code-review
kubectl logs -f deployment/code-review-api -n code-review
```

### Шаг 6: Проверка

```bash
# Port-forward для тестирования
kubectl port-forward -n code-review svc/code-review-api 8000:80

# Health check
curl http://localhost:8000/health

# Или через Ingress
curl https://code-review.example.com/health
```

### Масштабирование K8s

#### Горизонтальное автомасштабирование

```bash
# Создать HPA
kubectl autoscale deployment code-review-api \
  --min=3 --max=10 \
  --cpu-percent=70 \
  --namespace=code-review

# Проверить
kubectl get hpa -n code-review
```

#### Вертикальное масштабирование

```yaml
# Отредактировать deployment.yaml
resources:
  requests:
    memory: "1Gi"   # Вместо 512Mi
    cpu: "1000m"    # Вместо 500m
  limits:
    memory: "4Gi"   # Вместо 2Gi
    cpu: "4000m"    # Вместо 2000m

# Применить
kubectl apply -f deployment.yaml
```

### Обновление приложения в K8s

```bash
# Собрать новый image
docker build -t your-registry.example.com/code-review-api:2.1.0 .
docker push your-registry.example.com/code-review-api:2.1.0

# Обновить deployment
kubectl set image deployment/code-review-api \
  api=your-registry.example.com/code-review-api:2.1.0 \
  --namespace=code-review

# Или rolling update
kubectl rollout restart deployment/code-review-api -n code-review

# Следить за процессом
kubectl rollout status deployment/code-review-api -n code-review
```

### Обновление prompts/rules в K8s

```bash
# Обновить ConfigMap
kubectl create configmap code-review-prompts \
  --from-file=prompts/ \
  --namespace=code-review \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap code-review-rules \
  --from-file=rules/ \
  --namespace=code-review \
  --dry-run=client -o yaml | kubectl apply -f -

# Перезапустить pods для применения
kubectl rollout restart deployment/code-review-api -n code-review
```

## Вариант 3: Air-Gap Installation

См. [docs/AIR_GAP_TRANSFER.md](AIR_GAP_TRANSFER.md)

## Настройка n8n интеграции

### Шаг 1: Создать n8n workflow

См. [docs/N8N_WORKFLOW.md](N8N_WORKFLOW.md) для детального руководства.

Краткая схема:
```
GitLab Webhook (MR created/updated)
  ↓
LangChain Code Node: Validate MR
  ↓
HTTP Node: POST /api/v1/validate-mr
  ↓
If valid:
  HTTP Node: POST /api/v1/review
    ↓
  Wait for completion
    ↓
  Parse results
    ↓
  Send Slack notification
```

### Шаг 2: Настроить GitLab Webhook

```bash
# В GitLab проекте: Settings → Webhooks

URL: https://n8n.example.com/webhook/code-review-trigger
Secret Token: your-webhook-secret
Trigger: Merge request events

Events:
  ☑ Merge request created
  ☑ Merge request updated
  ☑ Merge request merged
```

### Шаг 3: Тестировать

```bash
# Создать test MR в GitLab
git checkout -b test-review
echo "test" >> test.txt
git add test.txt
git commit -m "[TEST-123] Test code review"
git push origin test-review

# Создать MR через GitLab UI
# Проверить n8n logs для trigger
# Проверить code-review-api logs для review execution
```

## Мониторинг и Observability

### Prometheus

#### Шаг 1: Установить Prometheus в K8s

```bash
# Использовать Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring --create-namespace

# Или kube-prometheus-stack (с Grafana)
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

#### Шаг 2: Добавить ServiceMonitor для code-review-api

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: code-review-api
  namespace: code-review
spec:
  selector:
    matchLabels:
      app: code-review-api
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

```bash
kubectl apply -f servicemonitor.yaml
```

#### Шаг 3: Добавить /metrics endpoint в FastAPI

```python
# app/main.py
from prometheus_client import make_asgi_app

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### Grafana Dashboards

Импортировать dashboards из `deployment/grafana/`:

1. **Code Review Performance**
   - Review duration (p50, p95, p99)
   - Success/failure rate
   - CLI timeouts

2. **System Health**
   - CPU/Memory usage
   - Active reviews
   - Disk usage

3. **Model API**
   - Request rate
   - Error rate by status code
   - Latency

4. **GitLab API**
   - MR creation success rate
   - API rate limit usage

### Logging (ELK Stack)

```yaml
# filebeat-configmap.yaml для сбора логов
apiVersion: v1
kind: ConfigMap
metadata:
  name: filebeat-config
  namespace: code-review
data:
  filebeat.yml: |
    filebeat.inputs:
    - type: container
      paths:
        - /var/log/containers/*code-review*.log
      json.keys_under_root: true
      json.add_error_key: true
    
    output.elasticsearch:
      hosts: ['elasticsearch.monitoring:9200']
      index: "code-review-%{+yyyy.MM.dd}"
```

## Backup и Disaster Recovery

### Backup strategie

**Что нужно бэкапить**:
1. **Secrets** (MODEL_API_KEY, GITLAB_TOKEN)
2. **ConfigMaps** (prompts, rules, config)
3. **Logs** (для audit trail)

**Что НЕ нужно бэкапить**:
- `/tmp/review` (временные репозитории)
- Docker volumes (ephemeral data)

### Backup script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR=/backup/code-review-$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# Backup K8s resources
kubectl get secret code-review-secrets -n code-review -o yaml > $BACKUP_DIR/secrets.yaml
kubectl get configmap code-review-config -n code-review -o yaml > $BACKUP_DIR/config.yaml
kubectl get configmap code-review-prompts -n code-review -o yaml > $BACKUP_DIR/prompts.yaml
kubectl get configmap code-review-rules -n code-review -o yaml > $BACKUP_DIR/rules.yaml

# Backup deployment configs
kubectl get deployment code-review-api -n code-review -o yaml > $BACKUP_DIR/deployment.yaml

# Compress
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

### Disaster Recovery procedure

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

# Extract
tar -xzf $BACKUP_FILE
BACKUP_DIR=${BACKUP_FILE%.tar.gz}

# Restore secrets (remove resourceVersion first)
yq eval 'del(.metadata.resourceVersion)' $BACKUP_DIR/secrets.yaml | kubectl apply -f -

# Restore configmaps
yq eval 'del(.metadata.resourceVersion)' $BACKUP_DIR/config.yaml | kubectl apply -f -
yq eval 'del(.metadata.resourceVersion)' $BACKUP_DIR/prompts.yaml | kubectl apply -f -
yq eval 'del(.metadata.resourceVersion)' $BACKUP_DIR/rules.yaml | kubectl apply -f -

# Restore deployment
kubectl apply -f $BACKUP_DIR/deployment.yaml

echo "Restore completed"
```

## Production Checklist

### Security

- [ ] Secrets хранятся в Vault/AWS Secrets Manager (не в Git)
- [ ] GitLab token с минимальными правами (только нужные projects)
- [ ] Model API key ротируется регулярно
- [ ] TLS/HTTPS для всех endpoints (Ingress с cert-manager)
- [ ] NetworkPolicy ограничивает egress/ingress
- [ ] RBAC для K8s service account
- [ ] Container runs as non-root (uid 1000)

### Performance

- [ ] HPA настроен (min 3, max 10)
- [ ] Resource requests/limits установлены
- [ ] Health checks configured (liveness, readiness)
- [ ] Review timeout настроен адекватно (300s для средних MR)
- [ ] Parallel tasks настроены под load (Cline: 5, Qwen: 3)
- [ ] Disk space monitoring настроен (alert at 90%)

### Monitoring

- [ ] Prometheus metrics exposed (/metrics)
- [ ] Grafana dashboards настроены
- [ ] Alerts настроены (PagerDuty/Slack)
- [ ] Logs shipping в ELK/Loki
- [ ] Distributed tracing (Jaeger) если нужно
- [ ] Uptime monitoring (uptimerobot.com)

### Reliability

- [ ] Multi-replica deployment (3+ pods)
- [ ] PodDisruptionBudget настроен (maxUnavailable: 1)
- [ ] Rolling update strategy (maxSurge: 1, maxUnavailable: 0)
- [ ] Graceful shutdown implemented
- [ ] Retry logic с exponential backoff
- [ ] Circuit breaker для Model API
- [ ] Fallback на secondary Model API
- [ ] Idempotent operations (MR creation)

### Documentation

- [ ] README обновлен
- [ ] Runbooks для common issues
- [ ] On-call playbook
- [ ] Architecture diagram актуален
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Change log maintained

### Testing

- [ ] Unit tests pass (pytest)
- [ ] Integration tests pass
- [ ] Load testing done (k6, locust)
- [ ] Chaos engineering (optional: litmus)
- [ ] DR drill проведен

## Настройка разных сред

### Development

```yaml
# .env.dev
LOG_LEVEL=DEBUG
REVIEW_TIMEOUT=600  # Больше для отладки
CLINE_PARALLEL_TASKS=2  # Меньше для экономии ресурсов
DEBUG_MODE=true
SAVE_CLI_OUTPUT=true
```

### Staging

```yaml
# .env.staging
LOG_LEVEL=INFO
REVIEW_TIMEOUT=300
CLINE_PARALLEL_TASKS=3
MODEL_API_URL=https://staging-model-api.example.com/v1
GITLAB_URL=https://gitlab-staging.example.com
```

### Production

```yaml
# .env.prod
LOG_LEVEL=WARNING  # Меньше noise
REVIEW_TIMEOUT=300
CLINE_PARALLEL_TASKS=5
MODEL_API_URL=https://prod-model-api.example.com/v1
GITLAB_URL=https://gitlab.example.com

# Production-specific
SENTRY_DSN=https://...@sentry.io/...
PROMETHEUS_ENABLED=true
DISTRIBUTED_TRACING=true
```

## Поддержка и обслуживание

### Регулярные задачи

**Ежедневно**:
- Проверить Grafana dashboards
- Проверить alerts в Slack
- Проверить error rate

**Еженедельно**:
- Review logs для unusual patterns
- Очистить старые logs (>30 days)
- Проверить disk usage
- Update prompts/rules если нужно

**Ежемесячно**:
- Ротация API keys
- Backup verification (restore test)
- Review и обновление dependencies
- Performance tuning

### Обновление зависимостей

```bash
# Python packages
pip list --outdated
pip install -U package-name

# Обновить requirements.txt
pip freeze > requirements.txt

# Node.js packages (CLI)
npm outdated -g
npm update -g @cline/cli @qwen-code/qwen-code

# Docker base image
# Обновить в Dockerfile: FROM python:3.11-slim → python:3.12-slim
```

## Troubleshooting Common Issues

См. [docs/ERROR_HANDLING_RU.md](ERROR_HANDLING_RU.md) для детального руководства.

### Quick Fixes

**Service не запускается**:
```bash
kubectl describe pod -n code-review
kubectl logs -f deployment/code-review-api -n code-review
```

**High memory usage**:
```bash
# Увеличить limits
kubectl set resources deployment code-review-api --limits=memory=4Gi -n code-review
```

**Slow reviews**:
```bash
# Увеличить timeout
kubectl set env deployment/code-review-api REVIEW_TIMEOUT=600 -n code-review
```

## Support

- **Documentation**: `/docs`
- **Issues**: GitHub Issues
- **Slack**: #code-review-support
- **On-call**: PagerDuty

---

**Готово к production!** 🚀


