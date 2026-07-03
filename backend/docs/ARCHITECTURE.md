# Aetheria Platform — Architecture Documentation

## Overview

Aetheria is an enterprise AI Video Generation SaaS built on a microservices-inspired monolith architecture. The core application is split across:

- **FastAPI Backend** — REST API, WebSocket, and background task coordination
- **Next.js Frontend** — TypeScript client with Zustand state management
- **Celery Workers** — Async GPU inference and ML training job orchestration
- **PostgreSQL** — Primary relational datastore
- **Redis** — Celery broker, result backend, rate-limit counters, WebSocket pub/sub
- **MinIO / S3** — Object storage for assets, renders, and model weights

---

## System Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                  │
│         Browser (Next.js)    Mobile    3rd-party API            │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────┐
│           NGINX / Ingress       │  TLS termination, load balance
└────────────────┬────────────────┘
                 │
        ┌────────▼────────┐
        │  FastAPI (x3)   │  Kubernetes Deployment (3 replicas)
        │   :8000         │  JWT auth, CORS, rate limiting
        └──┬──────┬───────┘
           │      │
    ┌──────▼─┐  ┌─▼───────────┐
    │Postgres│  │    Redis     │  ← Celery broker + pub/sub
    │  :5432 │  │    :6379     │
    └────────┘  └──────┬──────┘
                       │
              ┌────────▼────────┐
              │  Celery Workers │  GPU-enabled pods
              │  (GPU nodes)    │  AI inference, MLOps training
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  MinIO / S3     │  Asset + render object storage
              └─────────────────┘
```

---

## Data Flow — Video Render Request

```
Client → POST /api/v1/renders/trigger
       → rate_limiter() — Redis counter check
       → sanitize_prompt() — injection guard
       → RenderJob created in DB (PENDING)
       → Celery task dispatched (Redis broker)
       → Worker loads AI model (ModelManager)
       → Inference runs → video written to S3
       → Job status updated (SUCCESS) in DB
       → Redis pub/sub notification sent
       → WebSocket pushes update to client
```

---

## Security Architecture

| Layer | Control |
| :--- | :--- |
| Transport | TLS 1.3 (NGINX terminates) |
| Authentication | JWT HS256, 60-min expiry |
| Authorization | Per-resource ownership checks on every endpoint |
| Input Validation | Pydantic schemas + prompt sanitizer + file magic-bytes |
| Rate Limiting | Redis sliding window, 60 req/min per IP |
| Secrets | Environment variables only — never committed |
| CORS | Explicit allowlist, no wildcard |

---

## Key Technology Versions

| Component | Version |
| :--- | :--- |
| Python | 3.13 |
| FastAPI | 0.111.0 |
| SQLAlchemy | 2.0.31 |
| Celery | 5.4.0 |
| Redis client | 5.0.7 |
| Next.js | 16.2.10 |
| PostgreSQL | 15+ |
| Redis | 7+ |
