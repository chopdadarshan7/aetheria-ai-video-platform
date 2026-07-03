# Aetheria Platform — Operations Runbook

This runbook is for on-call engineers responding to live incidents.

---

## Daily Health Checks

| Check | Command / URL |
| :--- | :--- |
| API health | `curl https://api.yourdomain.com/health` |
| DB + Redis probe | `curl https://api.yourdomain.com/healthz` |
| Celery queue depth | `redis-cli LLEN celery` |
| Pod status | `kubectl get pods -l app=aetheria-backend` |
| Worker pod status | `kubectl get pods -l app=aetheria-worker` |

---

## Restarting Services

### Restart backend pods (rolling, zero downtime)
```bash
kubectl rollout restart deployment/aetheria-backend
kubectl rollout status deployment/aetheria-backend
```

### Restart Celery workers
```bash
kubectl rollout restart deployment/aetheria-worker
```

### Flush stuck Celery queue
```bash
redis-cli DEL celery          # clears default queue
celery -A app.celery_app purge -f
```

---

## Scaling

### Scale backend replicas
```bash
kubectl scale deployment aetheria-backend --replicas=5
```

### Scale GPU workers
```bash
kubectl scale deployment aetheria-worker --replicas=3
```

---

## Common Alerts & Remediation

### Alert: `HighAPILatency` (p95 > 2s)
1. Check `kubectl top pods` for CPU/memory pressure.
2. Check Postgres slow query log (`pg_stat_activity`).
3. Scale backend replicas if CPU-bound.
4. Check Redis latency: `redis-cli --latency`.

### Alert: `CeleryQueueDepth > 100`
1. Check worker pod count: `kubectl get pods -l app=aetheria-worker`.
2. Scale workers: `kubectl scale deployment aetheria-worker --replicas=5`.
3. Check for stuck/failing tasks: `celery -A app.celery_app inspect active`.

### Alert: `DatabaseConnectionError`
1. Check RDS/PostgreSQL health in cloud console.
2. Check `DATABASE_URL` env var is set correctly.
3. Verify security group allows backend → DB on port 5432.

### Alert: `RedisConnectionError`
1. Check Redis cluster health.
2. Verify `REDIS_HOST` and `REDIS_PORT` env vars.
3. Test connectivity: `redis-cli -h $REDIS_HOST ping`.

### Alert: `WorkerGPUOOM` (CUDA out of memory)
1. Check VRAM usage on GPU nodes.
2. Reduce batch size or increase worker pod memory limits.
3. Restart affected worker: `kubectl delete pod <pod-name>`.

---

## Logs

### Backend API logs
```bash
kubectl logs -l app=aetheria-backend --tail=200 -f
```

### Celery worker logs
```bash
kubectl logs -l app=aetheria-worker --tail=200 -f
```

### Grep for errors
```bash
kubectl logs -l app=aetheria-backend | grep -i "error\|exception\|traceback"
```

---

## Deploying a New Version

```bash
# Build and push new image
docker build -t your-registry/aetheria-backend:v1.x.x backend/
docker push your-registry/aetheria-backend:v1.x.x

# Rolling update
kubectl set image deployment/aetheria-backend backend=your-registry/aetheria-backend:v1.x.x
kubectl rollout status deployment/aetheria-backend

# Rollback if needed
kubectl rollout undo deployment/aetheria-backend
```
