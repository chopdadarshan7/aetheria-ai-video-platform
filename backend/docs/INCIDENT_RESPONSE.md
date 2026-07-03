# Aetheria Platform — Incident Response Guide

## Severity Definitions

| Severity | Description | Response Time | Examples |
| :--- | :--- | :--- | :--- |
| **P0 — Critical** | Full service down, data loss risk | Immediate (< 5 min) | API returns 500 for all users, DB unreachable |
| **P1 — High** | Major feature broken for all users | 15 min | Renders fail, auth broken |
| **P2 — Medium** | Feature degraded for subset of users | 1 hour | Slow renders, audio jobs failing |
| **P3 — Low** | Minor issue, workaround exists | Next business day | Cosmetic bug, docs typo |

---

## Response Playbook

### Step 1 — Detect & Acknowledge (< 5 min)
- Alert fires in PagerDuty / Slack `#incidents` channel.
- On-call engineer acknowledges within SLA.
- Open a dedicated incident Slack channel: `#inc-YYYYMMDD-brief-description`.
- Assign Incident Commander (IC) and Comms Lead.

### Step 2 — Assess (< 10 min)
Run initial diagnostics:
```bash
curl https://api.yourdomain.com/health
curl https://api.yourdomain.com/healthz
kubectl get pods --all-namespaces
kubectl top nodes
```

Determine:
- Which component is failing?
- How many users are affected?
- Is data at risk?

### Step 3 — Mitigate (< 30 min for P0)
Apply the fastest mitigation that restores service — even if not a permanent fix:
- Restart affected pods
- Roll back to previous deployment
- Enable maintenance page
- Scale up resources

### Step 4 — Communicate
- **Internal**: Post status update every 15 min in incident channel.
- **External**: Update status page (statuspage.io or similar) within 10 min of P0.
- **Template**: `We are aware of an issue affecting [feature]. Our team is investigating. Next update in 15 min.`

### Step 5 — Resolve & Verify
- Implement permanent fix (if different from mitigation).
- Verify all health endpoints return healthy.
- Confirm with affected users / monitoring.
- Close the incident in PagerDuty.

### Step 6 — Post-Mortem (within 48h for P0/P1)
Document in `postmortems/YYYYMMDD-title.md`:
- Timeline of events
- Root cause analysis (5 Whys)
- Impact assessment
- What went well / what didn't
- Action items with owners and due dates

---

## Security Incident Response

### Suspected Breach / Unauthorized Access
1. Immediately rotate `SECRET_KEY` → restart all backend pods (invalidates all existing JWTs).
2. Audit auth logs for anomalous login patterns.
3. Revoke all API keys for affected users.
4. Notify affected users per privacy obligations (GDPR: 72-hour window).

### DDoS Attack
1. Check rate-limit counters: `redis-cli KEYS "rate_limit:*"`.
2. Block attacking IPs at NGINX / WAF level.
3. Enable Cloudflare "Under Attack" mode if applicable.
4. Scale backend replicas to absorb load.

### Malicious File Upload
1. Check `validate_file_signature` logs for bypass attempts.
2. Quarantine affected S3 bucket prefix.
3. Remove malicious assets from DB.
4. Patch validation logic and redeploy.

---

## Escalation Contacts

| Role | Responsibility |
| :--- | :--- |
| On-call Engineer | First responder, initial triage |
| Engineering Lead | P0/P1 escalation, architecture decisions |
| Security Officer | Data breach, compliance violations |
| Legal / Privacy | GDPR notifications, breach disclosure |
