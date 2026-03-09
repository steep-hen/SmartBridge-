# SmartBridge Production Setup - Complete Guide

Welcome! This is the **complete production-ready infrastructure setup** for SmartBridge. Everything you need to run SmartBridge at enterprise scale is documented here.

## 📋 Quick Start (5 Minutes)

### First Time Setup?

Start here: **[Infrastructure Checklist](../docs/INFRASTRUCTURE.md#pre-deployment-checklist)**

### Deploying to Production?

Follow this path:
1. [Deployment Guide](../docs/DEPLOYMENT.md) - Step-by-step deployment
2. [Monitoring Setup](../docs/MONITORING.md) - Configure observability
3. [Incident Response](../docs/INCIDENT_RESPONSE.md) - Handle issues

### Something Broken?

Emergency resources:
- **Service Down?** → [Incident Runbooks](../docs/INCIDENT_RESPONSE.md#common-incident-runbooks)
- **Database Issue?** → [Database Troubleshooting](../infrastructure/database/troubleshooting.md)
- **Slow Performance?** → [Performance Tuning](../docs/MONITORING.md#troubleshooting)

## 📁 Directory Structure Overview

```
smartbridge/
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md           # System architecture & design
│   ├── DEPLOYMENT.md             # Deployment procedures
│   ├── MONITORING.md             # Monitoring & observability
│   ├── INCIDENT_RESPONSE.md      # Incident management
│   └── SECURITY.md               # Security guidelines
│
├── infrastructure/                # Infrastructure as Code
│   ├── terraform/                # Terraform configs
│   ├── kubernetes/               # K8s manifests
│   ├── helm/                     # Helm charts
│   ├── docker/                   # Docker configs
│   ├── database/                 # PostgreSQL setup
│   ├── cache/                    # Redis setup
│   └── networking/               # Network configs
│
├── scripts/                       # Operational scripts
│   ├── deploy.sh                 # Deployment automation
│   ├── backup.sh                 # Backup procedures
│   ├── restore.sh                # Restore procedures
│   ├── health_check.sh           # Health verification
│   ├── prune_audit.py            # Audit log retention
│   ├── package_release.sh        # Release packaging
│   └── smoke_test.sh             # Acceptance testing
│
├── ci-cd/                         # CI/CD Configuration
│   ├── .github/workflows/        # GitHub Actions
│   ├── .gitlab-ci.yml            # GitLab CI
│   └── terraform/                # Infrastructure CI/CD
│
├── monitoring/                    # Monitoring Configuration
│   ├── prometheus/               # Prometheus rules & config
│   ├── grafana/                  # Grafana dashboards
│   ├── alertmanager/             # Alert routing
│   ├── elasticsearch/            # Log storage
│   └── jaeger/                   # Distributed tracing
│
└── README.md                      # This file
```

## 🎯 Core Components

### Infrastructure
- **Cloud**: AWS, Azure, or On-Premises
- **Orchestration**: Kubernetes (with Helm charts)
- **Database**: PostgreSQL 15+ with replication
- **Cache**: Redis 7+ with clustering
- **Message Queue**: RabbitMQ or Kafka (optional)

### Application
- **API Server**: FastAPI/Python or Node.js/TypeScript
- **Frontend**: React + webpack with nginx
- **Workers**: Celery, Bull, or native async
- **Load Balancer**: NGINX/HAProxy or cloud native

### Observability
- **Metrics**: Prometheus + Grafana
- **Logging**: Elasticsearch + Kibana + Filebeat
- **Tracing**: Jaeger distributed tracing
- **Alerts**: AlertManager with multiple channels

### Security
- **Authentication**: OAuth2/OpenID Connect
- **Authorization**: Role-Based Access Control (RBAC)
- **Encryption**: TLS 1.3, AES-256, HMAC-SHA256
- **Secrets**: HashiCorp Vault or cloud KMS

## 🚀 Common Tasks

### Deploy New Version

```bash
# 1. Prepare
git pull origin main
./scripts/package_release.sh --version 1.2.0 --all

# 2. Deploy
./scripts/deploy.sh --version 1.2.0 --environment production

# 3. Verify
./scripts/smoke_test.sh --environment production

# Time: 15-45 minutes (depending on deployment strategy)
```

### Handle Incident

```bash
# 1. Detect & respond
# - Monitoring alert fires
# - On-call notified

# 2. Investigate
kubectl logs -f deployment/smartbridge -n production
curl http://api.example.com/health

# 3. Resolve
./scripts/deploy.sh --hotfix --rollback

# 4. Document
# - Create postmortem
# - Add action items
# - Update runbooks

# Reference: Incident Response Guide
```

### Scale for Traffic

```bash
# Horizontal scaling (more pods/nodes)
kubectl scale deployment smartbridge --replicas=10 -n production

# Vertical scaling (more CPU/memory)
kubectl patch deployment smartbridge -p '{"spec":{"template":{"spec":{"resources":{"limits":{"memory":"4Gi","cpu":"2"}}}}}}'

# Database connection pool
kubectl set env deployment/smartbridge DB_POOL_SIZE=100

# Cache warm-up
./scripts/warmup_cache.sh
```

### Backup & Restore

```bash
# Automated daily backup
./scripts/backup.sh --full --encrypt --to-s3

# Point-in-time restore
./scripts/restore.sh --from 2024-01-15T14:30:00Z

# Verify backup
./scripts/verify_backup.sh --backup-date 2024-01-15
```

### Update Configuration

```bash
# Update environment variables
kubectl set env deployment/smartbridge \
  LOG_LEVEL=DEBUG \
  API_TIMEOUT=60 \
  -n production

# Update secrets
kubectl create secret generic smartbridge-secrets \
  --from-file=.env \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply Helm values
helm upgrade smartbridge ./helm/smartbridge \
  -f helm/values-production.yaml \
  -n production
```

## 📊 Monitoring & Observability

### Key Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Overview | `http://grafana:3000/d/overview` | System health & metrics |
| API Performance | `http://grafana:3000/d/api-perf` | Request rates & latency |
| Database | `http://grafana:3000/d/database` | DB connections, queries |
| Infrastructure | `http://grafana:3000/d/infra` | CPU, memory, disk, network |
| Business | `http://grafana:3000/d/business` | Transactions, revenue, users |

### Key Alerts

| Alert | Threshold | Action |
|-------|-----------|--------|
| Service Down | All replicas failed | Page on-call immediately |
| High Error Rate | >5% errors/min | Investigate & deploy fix |
| Database Lag | >30 seconds | Check replication, scale readers |
| Disk Full | >90% used | Cleanup or expand storage |
| High Latency | P95 > 1s | Profile, optimize queries |

## 🔒 Security Checklist

- [ ] All secrets stored in Vault/KMS (not in config)
- [ ] HTTPS/TLS 1.3 enabled for all endpoints
- [ ] OAuth2/OIDC configured for authentication
- [ ] RBAC policies implemented for authorization
- [ ] Network policies restrict pod-to-pod communication
- [ ] Database encryption at rest enabled
- [ ] Audit logging enabled for all data access
- [ ] Regular security scans (SAST, DAST, dependency)
- [ ] Incident response procedures documented
- [ ] On-call team trained

## 📈 Performance Metrics

**Target Performance Baselines:**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Response Time (P95) | < 200ms | > 1000ms |
| Error Rate | < 0.1% | > 5% |
| Availability | > 99.95% | < 99.9% |
| Database Query Time (P95) | < 50ms | > 500ms |
| Cache Hit Ratio | > 90% | < 80% |
| CPU Usage | < 60% | > 80% |
| Memory Usage | < 70% | > 85% |
| Disk Usage | < 80% | > 90% |

## 📚 Documentation Map

### Getting Started
- [System Architecture](../docs/ARCHITECTURE.md) - Design & components
- [Infrastructure Setup](../docs/INFRASTRUCTURE.md) - Network, compute, storage
- [Security Architecture](../docs/SECURITY.md) - OAuth2, RBAC, encryption

### Operations
- [Deployment Guide](../docs/DEPLOYMENT.md) - Deploy & rollback procedures
- [Monitoring Setup](../docs/MONITORING.md) - Prometheus, Grafana, logs
- [Incident Response](../docs/INCIDENT_RESPONSE.md) - Detection & resolution
- [Runbooks](../runbooks/) - Step-by-step incident guides

### Development/Customization
- [Backend API](../api/README.md) - API development & testing
- [Frontend UI](../frontend/README.md) - UI customization
- [CI/CD Pipeline](../ci-cd/README.md) - Continuous integration setup

### Infrastructure as Code
- [Terraform](../infrastructure/terraform/README.md) - Cloud resources
- [Kubernetes](../infrastructure/kubernetes/README.md) - K8s manifests
- [Helm Charts](../infrastructure/helm/README.md) - Templated deployments
- [Docker](../infrastructure/docker/README.md) - Container builds

## 🛠️ Useful Commands

```bash
# System Status
kubectl get all -n production
kubectl top nodes
kubectl top pods -n production

# Deployment Management
kubectl rollout status deployment/smartbridge -n production
kubectl rollout undo deployment/smartbridge -n production
kubernetes scale deployment/smartbridge --replicas=5 -n production

# Logs & Debugging
kubectl logs -f deployment/smartbridge -n production
kubectl exec -it deployment/smartbridge -n production -- /bin/bash
kubectl describe pod smartbridge-xxx -n production

# Database
psql -U $DB_USER -h $DB_HOST -d $DB_NAME
SELECT * FROM pg_stat_activity;  # Active connections
SELECT * FROM pg_stat_statements;  # Slow queries

# Redis
redis-cli -h redis.example.com
INFO stats; DBSIZE; KEYS *;

# Monitoring
curl http://prometheus:9090/api/v1/targets
curl http://prometheus:9090/api/v1/query?query=up

# Networking
curl -v https://api.example.com/health
openssl s_client -connect api.example.com:443

# Health Checks
./scripts/smoke_test.sh --environment production
./scripts/health_check.sh --comprehensive
```

## 📞 Support & Escalation

### Getting Help

1. **Documentation**: Check relevant docs in `/docs/`
2. **Runbooks**: Follow procedures in `/runbooks/`
3. **Team**: Reach out in #smartbridge-ops
4. **On-Call**: Page through PagerDuty for urgent issues
5. **Leadership**: Escalate to engineering manager if needed

### When to Escalate

| Situation | Escalate To |
|-----------|-------------|
| Service unavailable | On-call + Engineering Lead |
| Data loss / corruption | CTO + Database Expert |
| Security incident | Security Officer + Legal |
| Sustained high latency | Architecture Lead |
| Customer impacting issue | Product Manager |

## 🎓 Learning Resources

### Architecture & Design
- [System Architecture](../docs/ARCHITECTURE.md)
- [Database Design](../infrastructure/database/design.md)
- [Networking](../infrastructure/networking/architecture.md)

### Operations
- [Operational Procedures](../docs/)
- [Incident Runbooks](../runbooks/)
- [Monitoring Dashboards](./MONITORING.md#grafana-dashboards)

### Development
- API Documentation: [OpenAPI/Swagger](../api/openapi.yaml)
- Frontend: [React Components](../frontend/src/components/README.md)
- Database Migrations: [Alembic](../migrations/)

## 🔄 Continuous Improvement

### Regular Reviews (Monthly)
- [ ] Review incident reports
- [ ] Update runbooks based on learnings
- [ ] Performance metric analysis
- [ ] Security assessment
- [ ] Capacity planning review

### Quarterly Tasks
- [ ] Disaster recovery drill
- [ ] Load testing simulation
- [ ] Architecture review
- [ ] Dependency updates
- [ ] Security scanning

### Annual Tasks
- [ ] Complete system audit
- [ ] Infrastructure refresh planning
- [ ] Team training refresh
- [ ] Vendor assessments
- [ ] Budget planning

## 📝 License & Credits

This production setup guide is part of the SmartBridge project. For license information, see [LICENSE](../LICENSE).

---

## Quick Links

- **Status Page**: https://status.smartbridge.example.com
- **Monitoring**: https://grafana.example.com
- **Documentation Wiki**: https://wiki.smartbridge.example.com
- **Slack**: #smartbridge-ops
- **PagerDuty**: https://smartbridge.pagerduty.com
- **GitHub**: https://github.com/your-org/smartbridge

---

**Last Updated**: January 2024
**Version**: 1.0.0
**Maintainers**: DevOps Team, SRE Team
