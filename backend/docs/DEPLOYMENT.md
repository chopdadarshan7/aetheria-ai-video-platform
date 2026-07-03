# Aetheria Platform — Production Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- Kubernetes 1.28+ (for K8s deployment)
- `kubectl` configured for your cluster
- A PostgreSQL 15 instance (managed RDS / Cloud SQL recommended)
- A Redis 7 instance (managed ElastiCache / Memorystore recommended)
- An S3-compatible object store (AWS S3 / MinIO)
- A domain with TLS certificate (Let's Encrypt / ACM)

---

## Step 1 — Environment Variables

Create a `.env` file (never commit this):

```env
# Security — REQUIRED, generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_randomly_generated_64_char_hex_key_here

# CORS — comma-separated list of allowed frontend origins
ALLOWED_ORIGINS=["https://app.yourdomain.com"]

# Database
DATABASE_URL=postgresql://user:password@your-db-host:5432/aetheria

# Redis
REDIS_HOST=your-redis-host
REDIS_PORT=6379

# S3 / MinIO
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=aetheria-assets

# Static directory (container path)
STATIC_DIR=/app/static
```

---

## Step 2 — Docker Compose (Local / Staging)

```bash
cd "image to vieo"
docker compose up --build -d
```

Services started:
- `backend` — FastAPI on :8000
- `worker` — Celery GPU worker
- `frontend` — Next.js on :3000
- `postgres` — PostgreSQL
- `redis` — Redis
- `minio` — Object storage

---

## Step 3 — Database Migration

On first deploy, tables are auto-created via SQLAlchemy `create_all`. For schema changes, use Alembic:

```bash
# Install Alembic in backend venv
pip install alembic

# Initialise (first time only)
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "describe_change"

# Apply migration
alembic upgrade head
```

---

## Step 4 — Kubernetes Deploy

```bash
# Apply manifests
kubectl apply -f k8s/k8s-deployment.yaml

# Verify pods
kubectl get pods -l app=aetheria-backend

# Check logs
kubectl logs -l app=aetheria-backend --tail=100 -f
```

---

## Step 5 — Health Checks

Kubernetes liveness and readiness probes should point to:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## Step 6 — SSL / TLS

Use cert-manager with Let's Encrypt, or terminate TLS at your cloud load balancer. The NGINX ingress is pre-configured in `k8s/k8s-deployment.yaml`.

---

## Step 7 — Monitoring

Apply Prometheus config:
```bash
kubectl apply -f k8s/prometheus.yml
```

Access Prometheus at port 9090 and set up Grafana dashboards importing the standard FastAPI dashboard (ID: 14930).
