# SmartBridge Monitoring & Observability Setup Guide

Comprehensive monitoring, logging, and observability infrastructure for production SmartBridge deployments.

## Table of Contents
1. [Monitoring Architecture](#monitoring-architecture)
2. [Prometheus Setup](#prometheus-setup)
3. [Grafana Dashboards](#grafana-dashboards)
4. [Logging Stack](#logging-stack)
5. [Alerting Configuration](#alerting-configuration)
6. [Distributed Tracing](#distributed-tracing)
7. [Metrics Reference](#metrics-reference)
8. [Troubleshooting](#troubleshooting)

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (SmartBridge API, Frontend, Workers)                       │
└────────────┬────────────────────────────────┬──────────────┘
             │                                │
      ┌──────▼────────┐            ┌──────────▼──────────┐
      │   Prometheus  │            │   Jaeger Tracing   │
      │   Exporter    │            │   (Distributed)    │
      └──────┬────────┘            └──────────┬──────────┘
             │                                │
      ┌──────▼──────────────────────────────▼────────┐
      │         Prometheus Server                    │
      │  (scrape configs, recording rules)           │
      └──────┬──────────────────────────────────────┘
             │
    ┌────────┼────────┐
    │                 │
┌───▼────────┐      ┌─▼──────────┐
│ Grafana    │      │ AlertManager│
│(Dashboards)│      │  (Alerts)   │
└────────────┘      └─┬──────────┘
                      │
              ┌───────┴────────┐
              │                │
        ┌─────▼┐         ┌────▼──┐
        │Slack │         │PagerDuty│
        └──────┘         └────────┘
```

## Prometheus Setup

### 1. Installation & Configuration

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    environment: 'prod'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - 'rules/*.yml'

scrape_configs:
  # SmartBridge API
  - job_name: 'smartbridge-api'
    static_configs:
      - targets: ['smartbridge-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
    
  # PostgreSQL
  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres-exporter:9187']
    
  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    
  # Node Exporter (Infrastructure)
  - job_name: 'node'
    static_configs:
      - targets: 
        - 'node-1:9100'
        - 'node-2:9100'
        - 'node-3:9100'
    
  # Kubernetes
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
```

### 2. Storage Configuration

```yaml
# prometheus/prometheus.yml storage section
storage:
  tsdb:
    path: /prometheus
    retention:
      time: 30d        # 30 days retention
      size: 100GB      # Size-based retention
    
    # Enable compression for long-term storage
    max_block_duration: 2h
    min_block_duration: 2h
    
    # WAL (Write-Ahead Log)
    wal_compression: true
    wal_segment_size: 256MB
```

### 3. Recording Rules

```yaml
# prometheus/rules/recording_rules.yml
groups:
  - name: smartbridge_metrics
    interval: 1m
    rules:
      # HTTP Requests
      - record: http:requests:rate5m
        expr: rate(http_requests_total[5m])
      
      - record: http:errors:rate5m
        expr: rate(http_requests_total{status=~"5.."}[5m])
      
      # Latency (quantiles)
      - record: http:request_duration:p95
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
      
      - record: http:request_duration:p99
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
      
      # Database metrics
      - record: db:connections:used
        expr: pg_stat_activity_count
      
      - record: db:cache:hit_ratio
        expr: rate(pg_stat_database_blks_hit[5m]) / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))
      
      # Business metrics
      - record: business:transactions:rate5m
        expr: rate(transactions_created_total[5m])
      
      - record: business:revenue:rate5m
        expr: rate(total_revenue_cents[5m]) / 100  # Convert cents to dollars
```

### 4. Docker Compose - Prometheus

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    networks:
      - monitoring
    depends_on:
      - smartbridge-api
      - postgres-exporter
      - redis-exporter

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.12.0
    container_name: postgres-exporter
    environment:
      DATA_SOURCE_NAME: "user=${DB_USER} password=${DB_PASSWORD} host=postgres port=5432 dbname=${DB_NAME} sslmode=disable"
    ports:
      - "9187:9187"
    networks:
      - monitoring
    depends_on:
      - postgres

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis-exporter
    environment:
      REDIS_ADDR: redis:6379
    ports:
      - "9121:9121"
    networks:
      - monitoring
    depends_on:
      - redis

volumes:
  prometheus_data:
    driver: local

networks:
  monitoring:
    driver: bridge
```

## Grafana Dashboards

### 1. Installation & Configuration

```yaml
# docker-compose section
services:
  grafana:
    image: grafana/grafana:10.0.0
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=SecurePassword123!
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_AUTH_GITHUB_ENABLED=true
      - GF_AUTH_GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GF_AUTH_GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    networks:
      - monitoring
    depends_on:
      - prometheus

volumes:
  grafana_data:
    driver: local
```

### 2. Dashboard - Application Overview

```json
{
  "dashboard": {
    "title": "SmartBridge - Application Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ method }} {{ path }}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{ status }}"
          }
        ],
        "type": "stat",
        "threshold": { "values": [0, 0.01] }
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "http:request_duration:p95",
            "legendFormat": "{{ handler }}"
          }
        ],
        "type": "graph",
        "yaxes": [{ "format": "ms" }]
      },
      {
        "title": "Active Requests",
        "targets": [
          {
            "expr": "http_requests_in_progress"
          }
        ],
        "type": "gauge"
      },
      {
        "title": "Request Distribution",
        "targets": [
          {
            "expr": "topk(10, sum(rate(http_requests_total[5m])) by (handler))"
          }
        ],
        "type": "piechart"
      }
    ]
  }
}
```

### 3. Dashboard - Database Performance

```json
{
  "dashboard": {
    "title": "SmartBridge - Database Performance",
    "panels": [
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Active"
          },
          {
            "expr": "pg_settings_max_connections",
            "legendFormat": "Max"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Query Latency",
        "targets": [
          {
            "expr": "rate(pg_stat_statements_mean_time[5m])",
            "legendFormat": "{{ query }}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Cache Hit Ratio",
        "targets": [
          {
            "expr": "db:cache:hit_ratio"
          }
        ],
        "type": "stat",
        "unit": "percentunit"
      },
      {
        "title": "Indexes",
        "targets": [
          {
            "expr": "pg_stat_user_indexes_idx_scan",
            "legendFormat": "{{ indexname }}"
          }
        ],
        "type": "table"
      },
      {
        "title": "Disk I/O",
        "targets": [
          {
            "expr": "rate(node_disk_read_bytes_total[5m])",
            "legendFormat": "Read"
          },
          {
            "expr": "rate(node_disk_written_bytes_total[5m])",
            "legendFormat": "Write"
          }
        ],
        "type": "graph",
        "yaxes": [{ "format": "Bps" }]
      }
    ]
  }
}
```

## Logging Stack

### 1. Elasticsearch & Kibana Setup

```yaml
# docker-compose.yml elasticsearch section
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.9.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - logging

  kibana:
    image: docker.elastic.co/kibana/kibana:8.9.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - logging
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:8.9.0
    container_name: logstash
    volumes:
      - ./logstash/pipeline.conf:/usr/share/logstash/pipeline/logstash.conf
    environment:
      - ES_HOST=elasticsearch:9200
    networks:
      - logging
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
    driver: local

networks:
  logging:
    driver: bridge
```

### 2. Logstash Pipeline Configuration

```conf
# logstash/pipeline.conf
input {
  tcp {
    port => 5000
    codec => json
  }
  
  beats {
    port => 5044
  }
}

filter {
  # Parse JSON logs
  if [message] =~ /^\{/ {
    json {
      source => "message"
      target => "json"
    }
  }
  
  # Add metadata
  mutate {
    add_field => {
      "[@metadata][environment]" => "${ENVIRONMENT:production}"
      "[@metadata][service]" => "smartbridge"
    }
  }
  
  # Parse timestamps
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }
  
  # Grok patterns for structured logging
  grok {
    match => {
      "message" => "%{LOGLEVEL:level} \[%{DATA:logger}\] %{GREEDYDATA:message}"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "smartbridge-%{[@metadata][environment]}-%{+YYYY.MM.dd}"
  }
  
  # Also output to stdout for debugging
  stdout {
    codec => rubydebug
  }
}
```

### 3. Filebeat Configuration

```yaml
# filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/smartbridge/*.log
    json.message_key: message
    json.keys_under_root: true
    
  - type: docker
    enabled: true
    containers.ids:
      - "smartbridge-api"
      - "smartbridge-worker"

output.logstash:
  hosts: ["logstash:5044"]

logging.level: info
```

## Alerting Configuration

### 1. AlertManager Rules

```yaml
# prometheus/rules/alerts.yml
groups:
  - name: smartbridge_alerts
    rules:
      # Availability
      - alert: ServiceDown
        expr: up{job="smartbridge-api"} == 0
        for: 1m
        annotations:
          summary: "SmartBridge API is down"
          description: "Service has been down for more than 1 minute"
      
      # Performance
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: SlowResponseTime
        expr: http:request_duration:p95 > 1
        for: 10m
        annotations:
          summary: "Response time is slow"
          description: "P95 response time is {{ $value }}s"
      
      # Database
      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_activity_count / pg_settings_max_connections > 0.8
        for: 5m
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Using {{ $value | humanizePercentage }} of connections"
      
      - alert: DatabaseDiskSpaceLow
        expr: pg_database_size_bytes / node_filesystem_avail_bytes > 0.8
        for: 10m
        annotations:
          summary: "Database disk space running low"
          description: "Using {{ $value | humanizePercentage }} of available space"
      
      # Infrastructure
      - alert: HighCPUUsage
        expr: 100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value }}%"
      
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value }}%"
```

### 2. AlertManager Configuration

```yaml
# alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  
  routes:
    # Critical alerts
    - match:
        severity: critical
      receiver: 'pagerduty'
      group_wait: 0s
      repeat_interval: 1h
    
    # Warning alerts
    - match:
        severity: warning
      receiver: 'slack-warnings'
      repeat_interval: 12h

receivers:
  - name: 'default'
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_URL}
        channel: '#alerts'
        title: 'Alert'
        text: '{{ .CommonAnnotations.description }}'
  
  - name: 'slack-warnings'
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_URL}
        channel: '#alerts-warnings'
  
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: ${PAGERDUTY_SERVICE_KEY}
        description: '{{ .GroupLabels.alertname }}'
```

## Distributed Tracing

### 1. Jaeger Setup

```yaml
# docker-compose section
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    ports:
      - "6831:6831/udp"  # Jaeger agent
      - "16686:16686"    # UI
    environment:
      COLLECTOR_ZIPKIN_HTTP_PORT: 9411
    networks:
      - tracing

networks:
  tracing:
    driver: bridge
```

### 2. Application Instrumentation

```python
# Python/FastAPI instrumentation
from jaeger_client import Config as JaegerConfig
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
    service_name="smartbridge-api",
)

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Use in FastAPI middleware
@app.middleware("http")
async def trace_middleware(request, call_next):
    with tracer.start_as_current_span("http_request"):
        response = await call_next(request)
        return response
```

## Metrics Reference

### HTTP Metrics
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current in-flight requests

### Business Metrics
- `transactions_created_total` - Total transactions
- `total_revenue_cents` - Revenue in cents
- `active_users_count` - Active user count

### Database Metrics
- `pg_stat_activity_count` - Active connections
- `pg_stat_database_blks_hit` - Cache hits
- `pg_stat_database_blks_read` - Cache misses

### Infrastructure Metrics
- `node_cpu_seconds_total` - CPU time
- `node_memory_MemAvailable_bytes` - Available memory
- `node_disk_read_bytes_total` - Disk read bytes
- `node_filesystem_avail_bytes` - Available disk space

## Troubleshooting

### Prometheus Issues

```bash
# Check if Prometheus is scraping correctly
curl http://localhost:9090/api/v1/targets

# Query metrics manually
curl 'http://localhost:9090/api/v1/query?query=up'

# Check alert rules
curl http://localhost:9090/api/v1/rules

# Validate configuration
promtool check config prometheus.yml
```

### Elasticsearch Issues

```bash
# Check cluster health
curl http://localhost:9200/_cluster/health

# List indices
curl http://localhost:9200/_cat/indices

# Check disk usage
curl http://localhost:9200/_cat/allocation
```

### High Cardinality Issues

```bash
# Find high cardinality metrics in Prometheus
curl 'http://localhost:9090/api/v1/series?match[]={__name__!=""}'| \
  jq -r '.data[]["__name__"]' | sort | uniq -c | sort -rn
```

## Related Documentation

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Jaeger Tracing](https://www.jaegertracing.io/docs/)
