# Aetheria Platform — Disaster Recovery Guide

## Recovery Time Objectives

| Tier | Scenario | RTO Target | RPO Target |
| :--- | :--- | :--- | :--- |
| P0 | Full service outage | 30 min | 1 hour |
| P1 | Database failure | 15 min | 15 min |
| P2 | Worker unavailability | 5 min | n/a (stateless) |
| P3 | Single pod crash | < 1 min | n/a (auto-restart) |

---

## Backup Strategy

### Database (PostgreSQL)
- **Frequency**: Continuous WAL archiving + daily full snapshots.
- **Retention**: 7-day daily snapshots, 4-week weekly snapshots.
- **Storage**: Encrypted S3 bucket in a separate AWS region.
- **Tooling**: `pg_dump` / managed RDS automated backups.

```bash
# Manual snapshot
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
aws s3 cp backup_*.sql.gz s3://aetheria-backups/postgres/
```

### Redis
- RDB snapshots every 15 minutes.
- AOF persistence enabled for crash recovery.
- Celery task state is ephemeral — in-flight tasks are re-queued on restart.

### Object Storage (S3/MinIO)
- Cross-region replication enabled.
- Versioning enabled on the assets bucket.
- Rendered videos stored with 90-day retention policy.

---

## Recovery Procedures

### Scenario 1: Database Total Loss

```bash
# 1. Provision a new PostgreSQL instance
# 2. Restore from latest snapshot
aws s3 cp s3://aetheria-backups/postgres/latest.sql.gz .
gunzip latest.sql.gz
psql $NEW_DATABASE_URL < latest.sql

# 3. Update DATABASE_URL secret in Kubernetes
kubectl create secret generic aetheria-secrets \
  --from-literal=DATABASE_URL=$NEW_DATABASE_URL \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Rolling restart backend
kubectl rollout restart deployment/aetheria-backend
```

### Scenario 2: Redis Total Loss

Redis holds Celery queue state and rate-limit counters only. Loss causes:
- In-flight render jobs fail (will need retry).
- Rate-limit counters reset (brief open window).
- WebSocket pub/sub drops (clients reconnect automatically).

```bash
# 1. Start a new Redis instance
# 2. Update REDIS_HOST env var
kubectl set env deployment/aetheria-backend REDIS_HOST=new-redis-host
kubectl set env deployment/aetheria-worker REDIS_HOST=new-redis-host
kubectl rollout restart deployment/aetheria-backend
kubectl rollout restart deployment/aetheria-worker
```

### Scenario 3: Worker Pod Failures (GPU crash)

Workers are stateless. Kubernetes will auto-restart crashed pods.
```bash
# Check pod restart count
kubectl get pods -l app=aetheria-worker
# Force restart if stuck
kubectl delete pod -l app=aetheria-worker
```

### Scenario 4: Full Region Outage

1. Activate standby region deployment (if configured).
2. Update DNS CNAME to point to standby region load balancer.
3. Restore DB from cross-region replica.
4. TTL change propagation typically takes 1–5 minutes with low TTL.

---

## Testing Disaster Recovery

Run quarterly DR drills:

1. **DB Failover Test**: Stop primary DB → verify standby promotion → measure RTO.
2. **Redis Restart Test**: Terminate Redis → verify API degrades gracefully → measure recovery time.
3. **Worker Kill Test**: Delete all worker pods → verify jobs re-queue → verify workers restart.
4. **Restore Test**: Restore a DB backup to a test environment → verify application boots correctly.

Record results in the DR drill log.
