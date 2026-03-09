# SmartBridge Operational Runbook

Quick reference guide for common operational tasks and incident response.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Incident Response](#incident-response)
3. [User Issues](#user-issues)
4. [Database Operations](#database-operations)
5. [Security Operations](#security-operations)

---

## Daily Operations

### Health Check

```bash
# Quick system health check
./health_check.sh

# Or manually:
curl http://localhost:8000/health
curl http://localhost:9090/-/healthy  # Prometheus
curl -s http://localhost:3000/api/health | grep ok  # Grafana
```

### Monitor Key Metrics

1. **Access Grafana**: http://localhost:3000
2. **Check dashboard panels**:
   - Request Latency: Monitor P99 latency (should be < 2s)
   - Error Rate: Should be < 1%
   - AI Failure Rate: Should be < 5%
   - Active Users: Monitor growth trends

### Backup Database

```bash
# Automated daily - verify it ran
ls -lh backup_*.sql | tail -1

# Manual backup if needed
docker-compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U smartbridge_prod smartbridge_prod | gzip > backup_manual_$(date +%s).sql.gz
```

### Log Rotation

```bash
# Logs rotate automatically when they hit 50MB
# Verify recent log files
docker-compose -f docker-compose.prod.yml logs backend --tail 100

# Export logs for analysis
docker-compose -f docker-compose.prod.yml logs > logs_$(date +%Y%m%d).txt
```

---

## Incident Response

### Incident: High API Latency

**Symptoms**: `/metrics` shows `request_latency_seconds_99` > 5 seconds

**Response Steps**:

```bash
# 1. Check backend resource usage
docker stats smartbridge_backend_prod

# 2. Check database query performance
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U smartbridge_prod -d smartbridge_prod -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# 3. Check current connections
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U smartbridge_prod -d smartbridge_prod -c \
  "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# 4. If latency due to slow queries, check for:
#    - Missing indexes
#    - Large table scans
#    - N+1 queries in reports endpoint

# 5. Restart backend service if needed (graceful)
docker-compose -f docker-compose.prod.yml restart backend
```

**Resolution**:
- Increase backend memory if resource-constrained
- Optimize slow queries (usually in report generation)
- Add database indexes on frequently filtered columns
- Scale to multiple backend instances behind load balancer

### Incident: High AI Failure Rate

**Symptoms**: Prometheus `ai_failures_total` increasing, Grafana shows red trend

**Response Steps**:

```bash
# 1. Check AI failure logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i "ai\|gemini\|fallback"

# 2. Query audit logs for blocked/failed advice
ADMIN_KEY="your-admin-key"
curl -H "X-API-Key: $ADMIN_KEY" \
  http://localhost:8000/audit/ai-calls?limit=50

# 3. Check if Gemini API is accessible
python -c "import google.generativeai; google.generativeai.configure(api_key='test')"

# 4. Verify fallback model is functioning
curl http://localhost:8000/health | grep ai_fallback

# 5. If Gemini rate limited (429), wait or upgrade API quota
# If auth failed (401), verify GEMINI_API_KEY in .env.prod

# 6. Monitor recovery
curl http://localhost:8000/metrics | grep ai_calls_total
```

**Resolution**:
- If Gemini issues: Contact Google Cloud Support, upgrade quota, or extend fallback usage
- If fallback issues: Check logs for specific errors, may need model retraining
- Increase timeout values if APIs are slow
- Set up automatic retries with exponential backoff

### Incident: Database Connection Failures

**Symptoms**: Backend logs show "connection refused" or "too many connections"

**Response Steps**:

```bash
# 1. Check database is running
docker-compose -f docker-compose.prod.yml ps postgres

# 2. Check connection count
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U smartbridge_prod -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Kill idle connections if over limit (200)
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U smartbridge_prod -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE state = 'idle' AND query_start < now() - interval '30 minutes';"

# 4. Increase max connections in postgres config
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -c "ALTER SYSTEM SET max_connections = 300;"

# 5. Restart postgres to apply change
docker-compose -f docker-compose.prod.yml restart postgres
```

**Prevention**:
- Monitor connection pool usage in application
- Set connection timeouts to release idle connections
- Use PgBouncer for connection pooling
- Scale database horizontally with read replicas

### Incident: Out of Disk Space

**Symptoms**: Logs show "no space left on device"

**Response Steps**:

```bash
# 1. Check disk usage
df -h

# 2. Identify large files/volumes
du -sh /var/lib/docker/volumes/*/data

# 3. Clean old logs
docker-compose -f docker-compose.prod.yml logs --tail 0 backend
docker system prune -af --volumes

# 4. Reduce Prometheus retention (default 30 days)
# Edit docker-compose.prod.yml:
# command:
#   - '--storage.tsdb.retention.time=7d'  # Reduce from 30d
docker-compose -f docker-compose.prod.yml restart prometheus

# 5. Archive and remove old logs
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/
rm -rf logs/

# 6. Archive audit logs to external storage
python scripts/prune_audit.py --days 30 --archive-path /backups/
```

**Prevention**:
- Monitor disk space daily
- Set up alerts when disk > 80% full
- Archive old logs to S3/GCS weekly
- Use external database (RDS/Cloud SQL) instead of container

---

## User Issues

### Issue: "Consent Required" Error

**User Reports**: Cannot view dashboard, says missing consent

**Solution**:

```bash
# 1. Check user's consent records
ADMIN_KEY="your-admin-key"
USER_ID="user-uuid"

curl -H "X-API-Key: $ADMIN_KEY" \
  http://localhost:8000/consent/user/$USER_ID

# 2. If no records, ask user to check consent checkbox in UI
# 3. If trying to re-grant consent, use consent endpoint

# Frontend workaround: Clear browser localStorage and reconnect
```

### Issue: "Export Failed" - Cannot Download JSON/PDF

**User Reports**: Export button shows error or file is empty

**Solution**:

```bash
# 1. Check backend logs for export errors
docker-compose -f docker-compose.prod.yml logs backend | grep -i export

# 2. Verify reportlab is installed (for PDF)
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "import reportlab; print('reportlab OK')"

# 3. If reportlab missing, it falls back to JSON - that's expected
# 4. Test JSON export endpoint
curl "http://localhost:8000/reports/$USER_ID" | python -m json.tool > /tmp/test.json

# 5. If JSON is empty, check report generation
# See "Database Operations" -> "Generate Report for User"
```

### Issue: "AI Advice Unavailable" or Shows Only Fallback

**User Reports**: Advice section is empty or shows generic advice

**Solution**:

```bash
# 1. Check if Gemini API key is configured
docker-compose -f docker-compose.prod.yml exec backend \
  grep -i gemini_api_key .env

# 2. Test Gemini connectivity
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "
import google.generativeai
google.generativeai.configure(api_key='$GEMINI_API_KEY')
model = google.generativeai.GenerativeModel('gemini-pro')
response = model.generate_content('test')
print('Gemini works' if response.text else 'Gemini failed')
"

# 3. If Gemini unavailable, fallback is used (normal behavior)
# 4. Check audit logs to see which model was used
curl -H "X-API-Key: $ADMIN_KEY" \
  http://localhost:8000/audit/ai-calls?blocked_only=true | grep -i "$USER_ID"

# 5. If blocked: Review reason in audit log details
#    (Likely contains forbidden phrase like "guarantee")
```

---

## Database Operations

### Backup & Restore

```bash
# **Full Backup** (recommended daily)
docker-compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U smartbridge_prod smartbridge_prod \
  | gzip -9 > backup_full_$(date +%Y%m%d_%H%M%S).sql.gz

# **Restore from Backup**
gunszip < backup_full_20240315_120000.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U smartbridge_prod smartbridge_prod

# **Backup Size** (typically 10-50 MB for demo with test data)
du -h backup_full_*.sql.gz

# **Test Restore** (in separate database first)
docker-compose exec postgres psql -U smartbridge_prod -c \
  "CREATE DATABASE smartbridge_test;"
# Restore to smartbridge_test, verify, then drop
```

### Generate Report for User

```bash
# 1. Get list of users
curl http://localhost:8000/users?limit=10

# 2. Generate report for specific user
USER_ID="550e8400-e29b-41d4-a716-446655440001"
curl "http://localhost:8000/reports/$USER_ID" | python -m json.tool

# 3. Generate with custom assumptions
curl "http://localhost:8000/reports/$USER_ID?expected_equity_return=0.10&inflation_rate=0.04" \
  | python -m json.tool
```

### Query Database Directly

```bash
# Interactive SQL shell
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U smartbridge_prod -d smartbridge_prod

# Common queries:
# Users with most reports
SELECT user_id, count(*) as report_count FROM audit_logs 
WHERE event_type = 'report_generated' GROUP BY user_id ORDER BY report_count DESC;

# Audit events in last 24 hours
SELECT event_type, count(*) FROM audit_logs 
WHERE created_at > now() - interval '24 hours' GROUP BY event_type;

# Consent records by scope
SELECT consent_scope, count(*) as consent_count FROM consent_logs 
GROUP BY consent_scope;
```

### Cleanup Old Audit Logs

```bash
# Run pruning script (keeps 90 days, archives older)
cd scripts/
python prune_audit.py --days 90 --archive-path /backups/audit_archive

# Or direct SQL
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U smartbridge_prod -d smartbridge_prod -c \
  "DELETE FROM audit_logs WHERE created_at < now() - interval '6 months';"
```

---

## Security Operations

### Rotate API Keys

```bash
# 1. Generate new key
NEW_KEY=$(openssl rand -base64 32)
echo $NEW_KEY

# 2. Update .env.prod
sed -i "s/API_KEY=.*/API_KEY=$NEW_KEY/" .env.prod

# 3. Notify all API consumers of new key
# (They should receive new key via secure channel)

# 4. Restart backend gracefully
docker-compose -f docker-compose.prod.yml restart backend

# 5. Monitor for failed auth attempts (old key)
docker-compose -f docker-compose.prod.yml logs backend | grep "Invalid API"

# 6. After 24 hours, disable old key completely
# (Remove from anywhere still accepting it)
```

### Enforce HTTPS/TLS

For production:

```bash
# 1. Obtain certificate (Let's Encrypt example)
sudo certbot certonly --standalone -d api.smartbridge.com

# 2. Configure reverse proxy (nginx) with certificate
# Copy certs to docker volume
sudo cp /etc/letsencrypt/live/api.smartbridge.com/fullchain.pem /secure/
sudo cp /etc/letsencrypt/live/api.smartbridge.com/privkey.pem /secure/

# 3. Add nginx service to docker-compose.prod.yml
# 4. Configure HSTS headers
# 5. Restart services

# 6. Test HTTPS
curl -I https://api.smartbridge.com/health
```

### Audit User Data Access

```bash
# Find all data accessed by a specific user
ADMIN_KEY="admin-key"
USER_ID="user-uuid"

curl -H "X-API-Key: $ADMIN_KEY" \
  "http://localhost:8000/audit/user/$USER_ID/history?limit=1000" | \
  python -m json.tool | grep -E "event_type|created_at"

# Check what fields were accessed (in audit log details)
# Verify no unauthorized access
```

### Investigate Suspicious Activity

```bash
# 1. Check for failed login/auth attempts
docker-compose -f docker-compose.prod.yml logs backend | grep -i "unauthorized\|forbidden\|denied"

# 2. Check audit logs for unusual patterns
curl -H "X-API-Key: $ADMIN_KEY" \
  http://localhost:8000/audit/stats?hours=24

# 3. Monitor IP addresses of requests
docker-compose -f docker-compose.prod.yml logs backend | grep "POST\|GET" | \
  awk '{print $NF}' | sort | uniq -c | sort -rn

# 4. If attack detected:
#    a. Block IP at firewall level
#    b. Rotate API keys
#    c. Review and archive audit logs
#    d. Notify security team
```

### Data Deletion (GDPR/Privacy)

```bash
# 1. Verify consent withdrawal
ADMIN_KEY="admin-key"
USER_ID="user-uuid"

curl -X POST -H "X-API-Key: $ADMIN_KEY" \
  "http://localhost:8000/consent/withdraw/$USER_ID"

# 2. Export user data (for data portability request)
curl "http://localhost:8000/user/$USER_ID/data-export" > user_data_export.json

# 3. Archive audit logs related to user
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U smartbridge_prod smartbridge_prod \
  --table=audit_logs -f audit_backup_$USER_ID.sql

# 4. Delete user from system
#    NOTE: Mark as deleted, don't actually remove audit records
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U smartbridge_prod -d smartbridge_prod -c \
  "UPDATE users SET deleted_at = now() WHERE id = '$USER_ID';"

# 5. Verify user data is no longer accessible
curl "http://localhost:8000/reports/$USER_ID"
# Should return 404 or "User not found"

# 6. Store user data export in secure archive for retention period
tar -czf user_data_archive_$USER_ID.tar.gz user_data_export.json audit_backup_$USER_ID.sql
# Keep for retention period (e.g., 7 years for financial records)
```

---

## Troubleshooting Checklist

When things go wrong, work through this checklist:

- [ ] Check service health: `docker-compose ps`
- [ ] Check logs for errors: `docker-compose -f docker-compose.prod.yml logs backend`
- [ ] Verify database connectivity: `curl http://localhost:8000/health`
- [ ] Check disk space: `df -h`, `docker system df`
- [ ] Check resource usage: `docker stats`
- [ ] Review Prometheus/Grafana for anomalies
- [ ] Check recent audit logs for suspicious activity
- [ ] Verify API keys in .env.prod are correct
- [ ] Ensure environment is set to "production" (not development)
- [ ] Check firewall rules (if on cloud provider)

## Emergency Procedures

### Emergency Shutdown

```bash
# Graceful shutdown (waits for requests to complete)
docker-compose -f docker-compose.prod.yml down --timeout 30

# Force immediate shutdown (risky, may lose data)
docker-compose -f docker-compose.prod.yml kill

# Remove all containers and volumes (WARNING: data loss)
docker-compose -f docker-compose.prod.yml down -v
```

### Recovery from Catastrophic Failure

```bash
# 1. Preserve audit logs (if possible)
docker cp smartbridge_backend_prod:/app/audit_logs ./backup_audit_emergency

# 2. Stop all services
docker-compose -f docker-compose.prod.yml down

# 3. Restore from latest backup
gunzip < backup_full_latest.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U smartbridge_prod smartbridge_prod

# 4. Restart services
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify health
./health_check.sh

# 6. Review loss: Compare timestamps of backed-up audit logs with current
```

---

**Last Updated**: 2024-03-15
**Runbook Maintainer**: [DevOps Team]
**Escalation Contact**: [On-call contact info]
