# SmartBridge Production Deployment Guide

## Overview

This guide covers deploying SmartBridge to production using Docker Compose with integrated monitoring (Prometheus + Grafana) and audit logging.

## Prerequisites

- Docker and Docker Compose (v1.29+)
- Linux server with 4GB RAM minimum (8GB recommended)
- Python 3.10+ (for CLI tools)
- Git

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/yourorg/smartbridge.git
cd smartbridge

# Copy environment template
cp .env.example .env.prod
```

### 2. Set Production Environment Variables

Edit `.env.prod` with production secrets:

```bash
# Database
DB_USER=smartbridge_prod
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=smartbridge_prod
DB_PORT=5432

# Security
SECRET_KEY=$(openssl rand -base64 32)
API_KEY=$(openssl rand -base64 32)
ADMIN_API_KEY=$(openssl rand -base64 32)

# AI
GEMINI_API_KEY=your_actual_gemini_key

# Monitoring
ENVIRONMENT=production
LOG_LEVEL=INFO

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=$(openssl rand -base64 32)

# pgAdmin
PGADMIN_EMAIL=admin@smartbridge.local
PGADMIN_PASSWORD=$(openssl rand -base64 32)
```

**⚠️ Security Note**: Store `.env.prod` securely, never commit to git. Use AWS Secrets Manager, HashiCorp Vault, or similar for production.

### 3. Start Services

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up --build -d

# Verify services are running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 4. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Check metrics endpoint (should return Prometheus format)
curl http://localhost:8000/metrics | head -20

# Access Prometheus
# Navigate to: http://localhost:9090
# Go to Status > Targets to see if backend is being scraped

# Access Grafana
# Navigate to: http://localhost:3000
# Login with credentials from .env.prod
# Import dashboard from infra/grafana/dashboard.json
```

### 5. Run Smoke Tests

```bash
# Make smoke_test.sh executable
chmod +x smoke_test.sh

# Run tests
./smoke_test.sh

# Expected output:
# ✅ Health check passed
# ✅ Database connectivity verified
# ✅ Sample report generated successfully
# ✅ AI advice endpoint functional
# ✅ Metrics endpoint exposed
```

## Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  BACKEND     │  │  POSTGRES    │  │  PROMETHEUS  │           │
│  │  :8000       │  │  :5432       │  │  :9090       │           │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤           │
│  │ /health      │  │ Financial    │  │ Scrapes      │           │
│  │ /metrics     │  │ User Data    │  │ /metrics     │           │
│  │ /reports/    │  │ Audit Logs   │  │ every 10s    │           │
│  │ /advice      │  │ Consent Logs │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│         │                 │                  │                   │
│         └─────────────────┴──────────────────┘                   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   GRAFANA    │  │   PGADMIN    │  │   LOGS       │           │
│  │  :3000       │  │  :5050       │  │  (mounted)   │           │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤           │
│  │ Dashboards   │  │ DB Admin UI  │  │ Audit logs   │           │
│  │ Alerting     │  │ Query Tool   │  │ App logs     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Port Mapping

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Backend | 8000 | http://localhost:8000 | API server |
| PostgreSQL | 5432 | localhost:5432 | Database |
| Prometheus | 9090 | http://localhost:9090 | Metrics storage |
| Grafana | 3000 | http://localhost:3000 | Dashboards & alerts |
| pgAdmin | 5050 | http://localhost:5050 | Database admin |

## Monitoring & Alerting

### Prometheus

Prometheus scrapes metrics from the backend every 10 seconds.

**Key Metrics to Monitor**:
- `request_latency_seconds` - API response times
- `request_count_total` - Request volume
- `ai_calls_total` - AI model call frequency
- `ai_failures_total` - AI failures/fallbacks
- `ai_latency_seconds` - AI response times

Access Prometheus at: http://localhost:9090

### Grafana Dashboards

The `infra/grafana/dashboard.json` includes:
- **Request Latency Panel** - P50, P95, P99 latencies
- **Request Rate Panel** - Requests per second by endpoint
- **AI Call Rate Panel** - Model call frequency
- **AI Latency Panel** - Model response latencies
- **AI Failures Panel** - Error rates by model
- **Consent Records Panel** - Privacy compliance tracking

Access Grafana at: http://localhost:3000

**Default credentials** (from `.env.prod`):
- Username: `admin`
- Password: [value from GRAFANA_PASSWORD]

### Setting Up Alerts (Optional)

Create alert rules in `/infra/prometheus/alert_rules.yml`:

```yaml
groups:
  - name: smartbridge
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.99, request_latency_seconds) > 5
        for: 5m
        annotations:
          summary: "API latency > 5 seconds"

      - alert: HighAIFailureRate
        expr: rate(ai_failures_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "AI failure rate > 10%"
```

## Data Persistence

All data is persisted in Docker volumes:

```bash
# List persistent volumes
docker volume ls | grep smartbridge

# Data locations:
# postgres_data_prod       - PostgreSQL data
# prometheus_data_prod     - Metrics history (30-day retention)
# grafana_data_prod        - Dashboards & settings
# pgadmin_data_prod        - pgAdmin preferences
```

## Backup & Restore

### Backup Database

```bash
docker-compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U smartbridge_prod smartbridge_prod \
  > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
docker-compose -f docker-compose.prod.yml exec -T postgres psql \
  -U smartbridge_prod smartbridge_prod < backup_20240315_120000.sql
```

### Backup Audit Logs

```bash
# Audit logs are also in PostgreSQL, included in above backup
# For file-based audit logs:
docker cp smartbridge_backend_prod:/app/audit_logs ./audit_logs_backup_$(date +%Y%m%d)
```

## Logging

### Application Logs

Logs are stored in JSON format for easy parsing:

```bash
# View backend logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View with filtering
docker-compose -f docker-compose.prod.yml logs backend | grep "ERROR"

# Export logs
docker-compose -f docker-compose.prod.yml logs backend > backend_logs.txt
```

### Log Rotation

Logs are configured with automatic rotation (50MB max, keep 5 files). Configure in `docker-compose.prod.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "5"
```

### Audit Log Retention

Run the retention policy script regularly (e.g., daily cron):

```bash
# Keep audit logs for 90 days, archive older ones
python scripts/prune_audit.py --days 90 --archive-path /backups/audit_archive
```

## Scaling Considerations

For production scale-up:

1. **Horizontal Scaling**: Run multiple backend instances behind a load balancer
2. **Database**: Migrate to managed PostgreSQL (AWS RDS, Cloud SQL)
3. **Cache**: Add Redis for session caching and report caching
4. **Cloud Storage**: Move audit logs to S3/GCS for long-term retention
5. **Observability**: Integrate with ELK Stack or Datadog for advanced monitoring

## Security Hardening

### HTTPS Configuration

To enable HTTPS in production:

1. Obtain SSL certificate (Let's Encrypt, AWS Certificate Manager, etc.)
2. Configure reverse proxy (nginx, HAProxy, or AWS ALB)
3. Update `docker-compose.prod.yml` to reference certs
4. Set `ENVIRONMENT=production` to enable HTTPS redirects in backend

Example nginx reverse proxy:

```nginx
server {
    listen 443 ssl http2;
    server_name api.smartbridge.com;
    
    ssl_certificate /etc/letsencrypt/live/api.smartbridge.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.smartbridge.com/privkey.pem;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Security

- Use strong passwords (auto-generated via openssl)
- Restrict postgres port (5432) to internal network only
- Enable PostgreSQL SSL connections
- Regular security updates: `docker-compose pull && docker-compose up -d`

### API Key Rotation

Keys should be rotated regularly:

```bash
# Generate new keys
NEW_KEY=$(openssl rand -base64 32)

# Update .env.prod
sed -i "s/API_KEY=.*/API_KEY=$NEW_KEY/" .env.prod

# Restart services (one per few minutes to avoid downtime)
docker-compose -f docker-compose.prod.yml restart backend
```

### Secret Management (Production)

For production, use HashiCorp Vault or cloud provider secrets manager:

```bash
# Example: AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id smartbridge/prod > secrets.json

# Example: HashiCorp Vault
vault login
vault kv get secret/smartbridge/prod
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common issues:
# 1. Database not ready: Wait 30 seconds, try again
# 2. Missing env vars: Verify .env.prod exists and is readable
# 3. Port already in use: Check "docker ps" and kill conflicting container
```

### Database Connection Errors

```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from backend.db import SessionLocal; SessionLocal()"

# If that fails, check postgres container:
docker-compose -f docker-compose.prod.yml logs postgres
```

### Metrics Not Showing in Prometheus

```bash
# 1. Verify backend /metrics endpoint is working
curl http://localhost:8000/metrics

# 2. Check Prometheus targets
# Navigate to: http://localhost:9090/targets
# Backend should show "UP"

# 3. If DOWN, check prometheus logs:
docker-compose -f docker-compose.prod.yml logs prometheus
```

### Grafana Won't Connect to Prometheus

```bash
# 1. Verify Prometheus is accessible from Grafana container
docker-compose -f docker-compose.prod.yml exec grafana \
  curl http://prometheus:9090

# 2. In Grafana UI:
#    Configuration > Data Sources > Edit Prometheus
#    URL should be: http://prometheus:9090
```

## Compliance & Legal

⚠️ **Important Disclaimers**:

All users must see and accept the disclaimer before using the system:

> "This financial planning tool provides educational analysis only. It is NOT financial advice. We are not registered financial advisors or investment professionals. Past performance does not guarantee future results. All projections are hypothetical. Consult a qualified financial advisor before making investment decisions. For production deployment, register with relevant financial regulators in your jurisdiction."

This disclaimer is displayed in:
- Streamlit dashboard (top + footer)
- PDF exports
- API documentation (/docs)
- Email notifications
- Terms of service (link in UI)

### Audit Log Compliance

The system maintains immutable audit logs of:
- All AI advice generation (model used, template, timestamp)
- User consent records (scope, timestamp, IP)
- Report access logs
- Data export requests

Audit logs are **never deleted** - archived per retention policy but kept indefinitely for compliance.

Requests for data deletion must:
1. Preserve all associated audit logs
2. Cancel future services/agreements
3. Archive deleted user data to secure backup

See `docs/runbook.md` for data deletion procedures.

## Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Security updates | Weekly | `docker-compose pull && docker-compose up -d` |
| Database backup | Daily | See backup procedure above |
| Log rotation | Daily | Automatic (Docker driver) |
| Audit log archival | Monthly | `python scripts/prune_audit.py` |
| Free disk space check | Weekly | `docker system df` |

## Support & Escalation

For issues:

1. Check logs: `docker-compose logs -f backend`
2. Check Prometheus/Grafana for anomalies
3. Run smoke tests: `./smoke_test.sh`
4. Review runbook: `docs/runbook.md`
5. Contact support with logs and error messages

---

**Deployment Date**: [Deployment Date]
**Deployed By**: [Name/Team]
**Version**: SmartBridge v1.0.0
**Last Updated**: 2024-03-15
