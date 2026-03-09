# SmartBridge Incident Response & Management

Enterprise-grade incident management procedures for production SmartBridge environments.

## Table of Contents
1. [Incident Classification](#incident-classification)
2. [Incident Response Process](#incident-response-process)
3. [Communication Protocols](#communication-protocols)
4. [Common Incident Runbooks](#common-incident-runbooks)
5. [Post-Incident Review](#post-incident-review)
6. [On-Call Procedures](#on-call-procedures)

## Incident Classification

### Severity Levels

| Severity | Definition | Response Time | Impact |
|----------|-----------|---|---|
| **P1 - Critical** | Complete service unavailability or major data loss | 15 min | All users affected |
| **P2 - High** | Service significantly degraded, major feature down | 1 hour | Large user segment |
| **P3 - Medium** | Service partially degraded, non-critical feature down | 4 hours | Small user segment |
| **P4 - Low** | Minor issue, workaround available | Next business day | Minimal user impact |

### Incident Types

- **Availability**: Service down or unreachable
- **Performance**: Slow response times, high latency
- **Data Integrity**: Corruption, loss, or inconsistency
- **Security**: Unauthorized access, data breach, vulnerability exploitation
- **Functionality**: Feature not working as expected
- **Infrastructure**: Hardware failure, resource exhaustion
- **External**: Third-party service dependency failure

## Incident Response Process

### Phase 1: Detection & Alerting

```
Detection Methods:
├── Monitoring alerts (Prometheus/Grafana)
├── User reports
├── Uptime monitoring (external)
├── Log analysis
├── APM dashboards
└── Manual observation

Alert Workflow:
1. Alert triggered
2. Parse alert details
3. Check alert context in Grafana
4. Determine incident severity
5. Notify incident commander & team
```

### Phase 2: Initial Response (First 15 minutes)

```bash
#!/bin/bash
# incident_response_init.sh - Initial incident response script

# 1. Acknowledge incident
echo "[$(date)] INCIDENT START: $INCIDENT_TYPE" | tee incident.log

# 2. Notify stakeholders
./scripts/alert_team.sh "$INCIDENT_TYPE" "$SEVERITY"

# 3. Establish war room
# - Create Slack channel: #incident-YYYY-MM-DD-HHMM
# - Create Google Meet: incident-bridge
# - Establish incident commander role

# 4. Gather initial metrics
echo "=== System Status ===" >> incident.log
curl http://localhost:9090/api/v1/targets >> incident.log
kubectl get nodes >> incident.log
kubectl get pods -n production >> incident.log
docker stats --no-stream >> incident.log

# 5. Take snapshots
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p incident_reports/$TIMESTAMP
kubectl describe nodes > incident_reports/$TIMESTAMP/nodes.txt
kubectl get events -n production > incident_reports/$TIMESTAMP/events.txt
kubectl logs -n production -l app=smartbridge --tail=100 > incident_reports/$TIMESTAMP/logs.txt
```

### Phase 3: Investigation & Diagnosis

```bash
#!/bin/bash
# incident_diagnosis.sh - Systematic diagnosis

investigate_service() {
    echo "=== Service Health ===" 
    
    # Health endpoints
    curl -f http://api.smartbridge.example.com/health || echo "UNHEALTHY"
    curl -f http://api.smartbridge.example.com/api/v1/status || echo "UNAVAILABLE"
    
    # Check running instances
    kubectl get deployment smartbridge -n production -o jsonpath='{.status}'
    
    # Check recent logs
    kubectl logs -f deployment/smartbridge -n production --tail=50 --all-containers=true
}

investigate_database() {
    echo "=== Database Health ==="
    
    # Connection status
    psql -U $DB_USER -h $DB_HOST -c "SELECT count(*) FROM pg_stat_activity;"
    
    # Long-running queries
    psql -U $DB_USER -h $DB_HOST -c "SELECT pid, usename, query, state, query_start FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"
    
    # Table bloat
    psql -U $DB_USER -h $DB_HOST -c "SELECT schemaname, tablename, (pg_total_relation_size(schemaname||'.'||tablename)/1024/1024) as sizeMB FROM pg_tables ORDER BY sizeMB DESC LIMIT 10;"
    
    # Replication status (if applicable)
    psql -U $DB_USER -h $DB_HOST -c "SELECT slot_name, slot_type, active FROM pg_replication_slots;"
}

investigate_cache() {
    echo "=== Cache Health ==="
    
    # Redis
    redis-cli -h redis.example.com PING
    redis-cli -h redis.example.com INFO stats
    redis-cli -h redis.example.com --latency
}

investigate_infrastructure() {
    echo "=== Infrastructure ==="
    
    # CPU & Memory
    top -bn1 | head -n 20
    free -h
    df -h
    
    # Network
    netstat -an | grep ESTABLISHED | wc -l
    iftop -n
    
    # Disk I/O
    iostat -x 1 5
}

# Run systematic investigation
investigate_service
investigate_database
investigate_cache
investigate_infrastructure
```

### Phase 4: Mitigation

**Mitigation strategies by incident type:**

#### Availability Issues

```bash
# 1. Service restart
kubectl rollout restart deployment/smartbridge -n production
kubectl rollout status deployment/smartbridge -n production --timeout=5m

# 2. Scale up instances
kubectl scale deployment smartbridge --replicas=5 -n production

# 3. Check/drain node
kubectl cordon $NODE_NAME
kubectl drain $NODE_NAME --ignore-daemonsets

# 4. Failover to backup region
./scripts/failover_region.sh --target secondary

# 5. Emergency contact list
PagerDuty: incident_commander@pagerduty.oncall
Management: @engineering-leads
```

#### Performance Issues

```bash
# 1. Find slow queries
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -c \
  "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# 2. Kill long-running queries
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '1 hour';"

# 3. Clear cache if safe
redis-cli -h redis.example.com FLUSHDB  # Careful - use sparingly!

# 4. Enable read replicas
kubectl patch deployment smartbridge \
  -p '{"spec":{"replicas":10}}' -n production

# 5. Reduce logging verbosity
kubectl set env deployment/smartbridge LOG_LEVEL=WARN -n production
```

#### Data Integrity Issues

```bash
# 1. STOP all write operations
kubectl set env deployment/smartbridge DB_READ_ONLY=true -n production

# 2. Snapshot current state
pg_dump -U $DB_USER -h $DB_HOST $DB_NAME | gzip > backup_incident_$(date +%Y%m%d_%H%M%S).sql.gz

# 3. Validate data
./scripts/validate_data_integrity.sh --comprehensive

# 4. Run consistency checks
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST << 'EOF'
SELECT * FROM pg_constraints WHERE conisvalid = false;
SELECT * FROM audit_logs WHERE data IS NULL OR data = '';
PRAGMA integrity_check;
EOF

# 5. Restore from backup if necessary
```

#### Security Issues

```bash
# 1. Isolate affected systems
kubectl delete service smartbridge-external -n production
# OR
iptables -I INPUT 1 -j DROP  # Emergency: block all

# 2. Revoke credentials
./scripts/revoke_credentials.sh --scope all
aws eks update-kubeconfig --name smartbridge-prod --generate-cli-auth

# 3. Apply security patches
kubectl patch deployment smartbridge \
  --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value":"smartbridge:v1.0.1-security-patch"}]' \
  -n production

# 4. Audit affected data
./scripts/audit_data_access.sh --start-time "$INCIDENT_TIME" --suspicious

# 5. Notify security team & customers
./scripts/notify_security_incident.sh
```

### Phase 5: Resolution & Testing

```bash
# 1. Implement fix
git branch incident-$INCIDENT_ID
# ... apply fix ...
git commit -m "Fix: incident-$INCIDENT_ID"
git push origin incident-$INCIDENT_ID
# Create PR -> merge -> deploy

# 2. Deploy fix
helm upgrade smartbridge ./helm/smartbridge \
  --set image.tag=v1.0.1 \
  -n production

# 3. Validate resolution
./scripts/smoke_test.sh --environment production --verbose

# 4. Monitor closely
watch -n 1 'curl -s http://api.example.com/health | jq .'

# 5. Gradually roll back workarounds
kubectl set env deployment/smartbridge DB_READ_ONLY=false -n production
kubectl scale deployment smartbridge --replicas=3 -n production
```

## Communication Protocols

### Incident Communications

```
Timeline: 0:15 (15 minutes from incident start)

0:00   - Alert fired, on-call notified
       - Incident #2024-001 opened
       - Incident channel created: #incident-2024-001

0:05   - War room established
       - Incident commander: @alice
       - Technical lead: @bob
       - Product: @charlie

0:15   - Initial assessment: Database replication lag
       - Severity: P2
       - Estimated resolution: 30 minutes
       
1:00   - Root cause identified: Disk fill up
       - Workaround implemented
       - Resolution in progress

2:00   - Issue resolved
       - Services stabilized
       - Monitoring closely
       
T+30min - Post-incident review scheduled
        - Postmortem meeting: Tomorrow 10 AM
        - RCA document: In progress
```

### Status Page Updates

```bash
#!/bin/bash
# update_status_page.sh

# Public status
curl -X POST https://status.smartbridge.example.com/api/v1/incidents \
  -H "Authorization: Bearer $STATUS_PAGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Database Connectivity Issues",
    "status": "investigating",
    "impact": "major",
    "body": "We are investigating increased latency on API endpoints"
  }'

# Internal notification
./scripts/notify_slack.sh \
  "#engineering" \
  "🚨 INCIDENT P1: Database issue detected - investigating | https://status.example.com/incidents/123"

# Customer notification (if critical)
./scripts/send_customer_notification.sh \
  "Incident: SmartBridge Service Disruption" \
  "We are actively investigating a service issue and will update you every 15 minutes"
```

## Common Incident Runbooks

### Runbook: High Database Load

```yaml
Title: High Database Load
Severity: P2
Prerequisites: 
  - Database access
  - Kubectl access

Steps:

1. Identify Root Cause
   - Check long-running queries:
     $ SELECT pid, query, query_start FROM pg_stat_activity 
       WHERE state = 'active' ORDER BY query_start;
   - Check query statistics:
     $ SELECT query, mean_time, calls FROM pg_stat_statements 
       ORDER BY mean_time DESC LIMIT 10;

2. Immediate Actions
   - Kill problematic queries:
     $ SELECT pg_terminate_backend({{PID}});
   
   - Increase connection pool:
     $ kubectl set env deployment/smartbridge \
         DB_POOL_SIZE=50 -n production

3. Investigation
   - If specific query slow: Check execution plan
     $ EXPLAIN ANALYZE {{QUERY}};
   
   - Check index usage:
     $ SELECT schemaname, tablename, indexname, idx_scan 
       FROM pg_stat_user_indexes ORDER BY idx_scan;

4. Remediation
   - Add missing indexes if needed:
     $ CREATE INDEX idx_{{column}} ON {{table}}({{column}});
   
   - Scale read replicas:
     $ kubectl scale deployment smartbridge-reader --replicas=10
   
   - Adjust query timeout:
     $ kubectl set env deployment/smartbridge \
         DB_STATEMENT_TIMEOUT=30s

5. Post-Incident
   - Monitor for 30 minutes:
     $ watch 'psql -c "SELECT count(*) FROM pg_stat_activity;"'
   
   - Document in runbook:
     - Root cause
     - Steps taken
     - Prevention measures
```

### Runbook: Memory Leak

```yaml
Title: Application Memory Leak
Severity: P2

Steps:

1. Detect Leak
   kubectl top pods -n production | grep smartbridge
   kubectl get resourcequota -n production

2. Confirm Leak
   # Monitor memory over time
   for i in {1..10}; do
     kubectl top pods -n production -l app=smartbridge
     sleep 60
   done

3. Immediate Mitigation
   # Restart affected pods
   kubectl delete pods -l app=smartbridge -n production

4. Investigation
   # Capture heap dump
   kubectl exec deployment/smartbridge -n production -- \
     jmap -heap {{PID}} > heap_dump.txt
   
   # Check logs for errors
   kubectl logs deployment/smartbridge -n production \
     --tail=100 | grep -i "error\|exception\|oom"

5. Deploy Fix
   # Cherry-pick fix from development
   git cherry-pick {{FIX_COMMIT}}
   # Build and push
   docker build -t smartbridge:v1.0.1 .
   docker push $REGISTRY/smartbridge:v1.0.1
   # Update deployment
   kubectl set image deployment/smartbridge \
     smartbridge=$REGISTRY/smartbridge:v1.0.1 -n production

6. Verify
   # Wait for new pods to stabilize
   kubectl rollout status deployment/smartbridge -n production
   # Monitor memory
   for i in {1..30}; do
     kubectl top pods -n production -l app=smartbridge
     sleep 60
   done
```

## Post-Incident Review (Postmortem)

### Postmortem Template

```markdown
# Incident Postmortem: [INCIDENT_ID]

## Summary
**Date**: 2024-01-15
**Duration**: 2 hours
**Severity**: P2
**Impact**: 500 users affected, $15K estimated loss

## Timeline

| Time | Event |
|------|-------|
| 14:30 | Alert fired: Database lag > 5min |
| 14:35 | Team notified, war room opened |
| 14:45 | Root cause identified: Disk full |
| 15:15 | Disk space freed, replication recovered |
| 16:30 | All services normalized |
| 17:00 | Incident closed |

## Root Cause Analysis

**Primary Cause**: 
Backup job did not clean up old WAL files, causing disk to fill up to 100%.

**Contributing Factors**:
- No alert for disk usage > 80%
- Backup cleanup script executed but failed silently
- No monitoring of backup job execution

## Resolution

1. Freed 200GB by deleting old WAL files
2. Restarted replication subsystem
3. Verified data consistency

## Action Items

| Item | Owner | Due Date | Priority |
|------|-------|----------|----------|
| Add disk usage alert (>80%) | @alice | 2024-01-17 | P1 |
| Fix backup cleanup script error handling | @bob | 2024-01-19 | P2 |
| Increase disk capacity by 50% | @ops | 2024-01-20 | P2 |
| Document disk management procedures | @charlie | 2024-01-22 | P3 |

## Prevention

- Automated disk cleanup every 24 hours
- Alert on disk usage > 80% and > 90%
- Weekly disk capacity review
- Backup job monitoring and alerting

## Lessons Learned

1. **What went well**: 
   - Fast detection by monitoring system
   - Excellent coordination between teams
   - Quick root cause identification

2. **What could be improved**:
   - Backup cleanup needs better error handling
   - Disk monitoring could have prevented this
   - Could have had automated recovery

## Metrics

- **Detection Time**: 5 min
- **Response Time**: 10 min (acceptable)
- **MTTR**: 2 hours (too high - target: 30 min)
- **Users Affected**: 500
- **Estimated Revenue Impact**: $15K
```

## On-Call Procedures

### On-Call Escalation

```
L1: Backend Engineer (primary)
    ↓ (no response > 5 min)
L2: SRE Team Lead
    ↓ (no response > 15 min)
L3: Engineering Manager
    ↓ (critical, no response > 30 min)
L4: VP Engineering
```

### On-Call Handoff Checklist

Starting on-call shift:
```bash
# 1. Update Slack status
/status on-call for smartbridge

# 2. Get briefing
* Check ongoing incidents
* Review previous week's incidents
* Check deployment calendar
* Review known issues log

# 3. Verify tools access
* VPN connected
* kubectl working
* AWS console accessible
* Slack/PagerDuty responsive

# 4. Review escalation
* Verify phone number in PagerDuty
* Confirm fallback contact
* Update emergency contact list

# 5. Load context
* Review RUNBOOKS
* Check monitoring dashboards
* Review architecture docs
```

Ending on-call shift:
```bash
# 1. Brief next on-call
* Any ongoing issues
* Any known problems
* Recent deployments
* Infrastructure changes

# 2. Close open items
* Document any workarounds
* Update runbooks with lessons
* File follow-up tickets

# 3. Update status
/status clear

# 4. Handoff contact info
* Update emergency list
* Confirm new on-call in escalation
```

## Incident Response Tools

### Slack Integration
```bash
# Set status
@incident set status "Investigating database issue"

# List recent incidents
@incident list --limit 10

# Create incident
@incident create --title "Service Down" --severity P1

# Send update
@incident update --message "Issue resolved, monitoring"
```

### Useful Commands

```bash
# Get system status
kubectl get all -n production

# Real-time logs
kubectl logs -f deployment/smartbridge -n production --all-containers=true

# Metrics query
curl 'http://prometheus:9090/api/v1/query?query=rate(errors_total[5m])'

# Database status
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -c \
  "SELECT now(), datname, usename, state FROM pg_stat_activity;"

# Execute fix
git tag -a incident-$INCIDENT_ID -m "Hotfix for incident-$INCIDENT_ID"
```

## Related Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Monitoring Setup](MONITORING.md)
- [Architecture](ARCHITECTURE.md)
- Incident Runbooks: `/runbooks/`
- On-Call Schedule: PagerDuty
- Status Page: https://status.smartbridge.example.com
