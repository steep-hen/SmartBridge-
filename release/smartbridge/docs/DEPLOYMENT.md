# SmartBridge Production Deployment Guide

This guide covers deploying SmartBridge to production environments following enterprise best practices.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Preparation](#environment-preparation)
3. [Database Migration](#database-migration)
4. [Application Deployment](#application-deployment)
5. [Verification & Testing](#verification--testing)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Deployment](#post-deployment)

## Pre-Deployment Checklist

### Code Readiness
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code review completed and approved
- [ ] Security scan passed (SAST)
- [ ] Dependency vulnerabilities resolved
- [ ] Semantic versioning updated (MAJOR.MINOR.PATCH)
- [ ] CHANGELOG updated with all changes
- [ ] API documentation updated if applicable

### Infrastructure Readiness
- [ ] All nodes healthy (CPU, memory, disk)
- [ ] Network connectivity verified
- [ ] SSL/TLS certificates valid and installed
- [ ] Secret management configured (env vars encrypted)
- [ ] Database backups current
- [ ] Cache systems operational
- [ ] Load balancers configured
- [ ] DNS records pointing to correct endpoints

### Documentation
- [ ] Deployment runbook reviewed
- [ ] Rollback procedure documented
- [ ] Known issues documented
- [ ] Architecture changes documented
- [ ] Team notified of deployment schedule
- [ ] Stakeholders (business, ops) informed

### Operational Readiness
- [ ] Incident response team available
- [ ] Monitoring alerts configured
- [ ] Log aggregation tested
- [ ] Runbooks accessible
- [ ] On-call schedule confirmed
- [ ] Communication channels established

## Environment Preparation

### 1. Database Preparation

```bash
# Run pre-deployment checks
./scripts/db_healthcheck.sh --environment production

# Create backup
pg_dump -U $DB_USER -h $DB_HOST $DB_NAME | gzip > backups/pre-deploy-$(date +%Y%m%d_%H%M%S).sql.gz

# Test migrations (on replica first)
alembic upgrade head --sql > migration_plan.sql
```

### 2. Configuration Updates

```bash
# Update environment configuration
export ENVIRONMENT=production
export APP_VERSION=1.0.0

# Load secrets from secure storage
source ./scripts/load_secrets.sh

# Validate configuration
./scripts/validate_config.sh --environment production
```

### 3. Service Dependencies

```bash
# Ensure all dependencies are ready
docker-compose -f docker-compose.production.yml up -d redis postgresql

# Wait for dependencies
./scripts/wait_for_services.sh --services redis,postgresql --timeout 60

# Run health checks
curl http://localhost:5432 --connect-timeout 5
redis-cli ping
```

## Database Migration

### Pre-Migration Steps

```bash
# 1. Notify all users
echo "Database maintenance scheduled for 2024-01-15 02:00-03:00 UTC"

# 2. Stop application gracefully
docker-compose -f docker-compose.production.yml exec api \
  curl -X POST http://localhost:8000/shutdown/graceful

# 3. Wait for in-flight requests to complete (max 5 minutes)
sleep 300

# 4. Verify no active connections
psql -U $DB_USER -h $DB_HOST -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME';"
```

### Run Migrations

```bash
# 1. Run pre-migration validation
alembic upgrade head --sql --validate

# 2. Execute migration
alembic upgrade head

# 3. Verify migration success
./scripts/validate_schema.sh --expected-version 2024.01

# 4. Run post-migration tests
./scripts/test_data_integrity.sh
```

### Post-Migration Verification

```bash
# Verify data consistency
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM audit_logs;
SELECT COUNT(*) FROM transactions;

# Check for constraint violations
SELECT * FROM pg_constraints WHERE contype = 'c' AND conisvalid = false;
```

## Application Deployment

### Kubernetes Deployment

```bash
# 1. Update deployment manifests
sed -i "s/smartbridge:.*/smartbridge:${APP_VERSION}/g" k8s/deployment.yaml

# 2. Apply manifests (rolling update)
kubectl apply -f k8s/ --record

# 3. Monitor rollout
kubectl rollout status deployment/smartbridge -n production --timeout=5m

# 4. Check pod status
kubectl get pods -n production -l app=smartbridge
kubectl logs -f deployment/smartbridge -n production --all-containers=true
```

### Docker Compose Deployment

```bash
# 1. Pull new images
docker-compose -f docker-compose.production.yml pull

# 2. Stop current containers
docker-compose -f docker-compose.production.yml down

# 3. Start new version
docker-compose -f docker-compose.production.yml up -d

# 4. Wait for health checks
docker-compose -f docker-compose.production.yml exec api \
  curl --retry 5 --retry-delay 2 -f http://localhost:8000/health
```

### Helm Deployment

```bash
# 1. Validate chart
helm lint ./helm/smartbridge

# 2. Dry-run deployment
helm upgrade smartbridge ./helm/smartbridge \
  --install \
  --namespace production \
  --values helm/values-production.yaml \
  --dry-run \
  --debug

# 3. Execute upgrade
helm upgrade smartbridge ./helm/smartbridge \
  --install \
  --namespace production \
  --values helm/values-production.yaml \
  --wait \
  --timeout 10m

# 4. Verify release
helm status smartbridge -n production
helm get values smartbridge -n production
```

## Verification & Testing

### 1. Service Health Checks

```bash
# Basic health checks
./scripts/smoke_test.sh --environment production --verbose

# Detailed endpoint testing
curl -f http://api.smartbridge.example.com/health
curl -f http://api.smartbridge.example.com/api/v1/status
curl -f http://api.smartbridge.example.com/api/v1/version
```

### 2. Functional Testing

```bash
# Run post-deployment test suite
pytest tests/integration/post_deployment_tests.py -v

# Key test scenarios:
# - User authentication
# - Core business logic
# - Data consistency
# - External integrations
# - Rate limiting
# - Error handling
```

### 3. Performance Baselines

```bash
# Compare metrics to baseline
curl http://metrics.example.com/api/compare \
  --data '{"version": "'${APP_VERSION}'", "metric": "response_time"}'

# Expected results:
# - Response time: ±5% of baseline
# - Error rate: <0.1%
# - CPU/Memory: normal ranges
# - Database connections: stable
```

### 4. Data Verification

```bash
# Verify critical data sections
./scripts/verify_deployment.sh \
  --check users \
  --check transactions \
  --check audit_logs

# Run consistency checks
./scripts/test_data_integrity.sh --full-check
```

## Rollback Procedures

### Immediate Rollback (Critical Issues)

```bash
# 1. Alert team
./scripts/alert_incident_team.sh "CRITICAL: Initiating rollback"

# 2. Rollback to previous version
VERSION_PREVIOUS=$(git describe --tags $(git rev-list --tags --max-count=2 | tail -1))

# Kubernetes
kubectl rollout undo deployment/smartbridge -n production
kubectl rollout status deployment/smartbridge -n production --timeout=5m

# Or Helm
helm rollback smartbridge 0 -n production
kubectl rollout status deployment/smartbridge -n production --timeout=5m

# Docker Compose
docker-compose -f docker-compose.production.yml \
  pull smartbridge:${VERSION_PREVIOUS}
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

### Database Rollback

```bash
# If migration failed or caused issues:

# 1. Restore from backup
pg_restore -U $DB_USER -h $DB_HOST -d $DB_NAME \
  backups/pre-deploy-*.sql.gz

# 2. Downgrade schema (if using alembic)
alembic downgrade -1

# 3. Verify data restored
SELECT COUNT(*) FROM users;
```

### Partial Rollback (Canary)

```bash
# For canary deployment issues:

# 1. Scale down new version
kubectl scale deployment smartbridge-new --replicas=0 -n production

# 2. Scale up previous version
kubectl scale deployment smartbridge-stable --replicas=5 -n production

# 3. Update load balancer
kubectl patch service smartbridge \
  -p '{"spec":{"selector":{"version":"stable"}}}' -n production
```

## Post-Deployment

### 1. Monitoring Validation

```bash
# Verify monitoring is working
curl http://prometheus.example.com/api/v1/query \
  '?query=up{instance="smartbridge"}'

# Check alert rules loaded
amtool config routes
amtool alert
```

### 2. Security Verification

```bash
# Verify SSL/TLS
echo | openssl s_client -servername api.smartbridge.example.com \
  -connect api.smartbridge.example.com:443

# Check security headers
curl -I https://api.smartbridge.example.com | grep -i "x-\|strict"

# Verify CORS configuration
curl -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS https://api.smartbridge.example.com/api/v1/test -v
```

### 3. Documentation & Communication

```bash
# Update status page
./scripts/update_status_page.sh \
  --status "operational" \
  --message "Successfully deployed v${APP_VERSION}"

# Post deployment summary
cat > DEPLOYMENT_SUMMARY.md << 'EOF'
# Deployment Summary - v1.0.0
- **Date**: 2024-01-15
- **Duration**: 45 minutes
- **Status**: ✓ Successful
- **Tests Passed**: 250/250
- **Issues**: None
- **Rollback**: Not required
EOF

# Notify stakeholders
./scripts/notify_stakeholders.sh \
  --version "${APP_VERSION}" \
  --status "success" \
  --summary "DEPLOYMENT_SUMMARY.md"
```

### 4. Metrics Snapshot

```bash
# Capture post-deployment metrics
metrics=$(curl http://prometheus.example.com/api/v1/query_range \
  '?query=smartbridge_http_requests_total' \
  '&start=now()-30m&end=now()&step=1m')

echo "Post-deployment metrics captured: $metrics"
echo "Baseline comparison completed"
```

## Deployment Strategies

### Blue-Green Deployment

```bash
# 1. Deploy to "green" environment
kubectl create deployment smartbridge-green \
  --image=smartbridge:${APP_VERSION} \
  -n production

# 2. Run validation tests against green
./scripts/smoke_test.sh --environment staging

# 3. Switch traffic
kubectl patch service smartbridge \
  -p '{"spec":{"selector":{"version":"green"}}}' \
  -n production

# 4. Keep blue running for quick rollback
```

### Canary Deployment

```bash
# 1. Deploy new version to 10% of traffic
kubectl set image deployment/smartbridge \
  smartbridge=smartbridge:${APP_VERSION} \
  --record \
  -n production

kubectl patch deployment smartbridge \
  -p '{"spec":{"strategy":{"canary":{"steps":[{"weight":10}]}}}}' \
  -n production

# 2. Monitor metrics
for i in {1..60}; do
  CANARY_ERROR_RATE=$(curl http://prometheus.example.com/api/v1/query \
    '?query=rate(errors_total[5m]){version="canary"}')
  echo "Canary error rate: $CANARY_ERROR_RATE"
  sleep 10
done

# 3. Gradually increase traffic
kubectl patch deployment smartbridge \
  -p '{"spec":{"strategy":{"canary":{"steps":[{"weight":50}]}}}}' \
  -n production

# 4. Full rollout
kubectl patch deployment smartbridge \
  -p '{"spec":{"strategy":{"canary":{"steps":[{"weight":100}]}}}}' \
  -n production
```

## Troubleshooting Common Issues

### Service Not Starting

```bash
# 1. Check logs
kubectl logs -f deployment/smartbridge -n production --all-containers=true

# 2. Check events
kubectl describe deployment smartbridge -n production

# 3. Check resource constraints
kubectl top nodes
kubectl top pods -n production

# 4. Check probe failures
kubectl get events -n production --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# 1. Verify connection parameters
echo "SELECT version();" | \
  psql -U $DB_USER -h $DB_HOST -d $DB_NAME

# 2. Check active connections
psql -U $DB_USER -h $DB_HOST -c \
  "SELECT pid, usename, state FROM pg_stat_activity;"

# 3. Check connection limits
psql -U $DB_USER -h $DB_HOST -c \
  "SELECT name, setting FROM pg_settings WHERE name = 'max_connections';"
```

### High Error Rates

```bash
# 1. Check application logs
kubectl logs -f deployment/smartbridge -n production --tail=100

# 2. Check metrics
curl 'http://prometheus.example.com/api/v1/query?query=rate(http_requests_total{status="5xx"}[5m])'

# 3. Check resource usage
kubectl top pods -n production

# 4. Check slow queries (if database)
psql -U $DB_USER -h $DB_HOST -c \
  "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md)
- [Infrastructure Setup](infrastructure/README.md)
- [Monitoring Setup](MONITORING.md)
- [Incident Response](INCIDENT_RESPONSE.md)
- [Rollback Procedures](ROLLBACK.md)

## Support & Escalation

- **Primary On-Call**: Check rotation in Opsgenie
- **Incident Channel**: #smartbridge-incidents (Slack)
- **Emergency**: +1-XXX-XXX-XXXX (PagerDuty)
