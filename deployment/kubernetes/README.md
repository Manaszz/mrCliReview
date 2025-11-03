# Kubernetes Deployment для AI Code Review System

## Быстрый старт

### 1. Создать namespace
```bash
kubectl apply -f namespace.yaml
```

### 2. Настроить secrets
Отредактируйте `secret.yaml` и добавьте реальные значения:
```bash
kubectl apply -f secret.yaml
```

### 3. Настроить ConfigMap
Отредактируйте `configmap.yaml` под свою среду:
```bash
kubectl apply -f configmap.yaml
```

### 4. Создать ConfigMaps для prompts и rules
```bash
# Из корня проекта
kubectl create configmap code-review-prompts \
  --from-file=prompts/ \
  --namespace=code-review

kubectl create configmap code-review-rules \
  --from-file=rules/ \
  --namespace=code-review
```

### 5. Deploy приложения
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

### 6. Проверить статус
```bash
kubectl get pods -n code-review
kubectl logs -f deployment/code-review-api -n code-review
```

## Обновление prompts/rules

```bash
# Обновить prompts
kubectl create configmap code-review-prompts \
  --from-file=prompts/ \
  --namespace=code-review \
  --dry-run=client -o yaml | kubectl apply -f -

# Обновить rules
kubectl create configmap code-review-rules \
  --from-file=rules/ \
  --namespace=code-review \
  --dry-run=client -o yaml | kubectl apply -f -

# Перезапустить pods для применения изменений
kubectl rollout restart deployment/code-review-api -n code-review
```

## Масштабирование

```bash
# Увеличить количество реплик
kubectl scale deployment/code-review-api --replicas=5 -n code-review

# Автомасштабирование (HPA)
kubectl autoscale deployment/code-review-api \
  --min=3 --max=10 \
  --cpu-percent=70 \
  -n code-review
```

## Мониторинг

```bash
# Логи
kubectl logs -f deployment/code-review-api -n code-review

# Метрики
kubectl top pods -n code-review

# Health check
kubectl exec -it deployment/code-review-api -n code-review -- \
  curl http://localhost:8000/health
```

## Удаление

```bash
kubectl delete namespace code-review
```


