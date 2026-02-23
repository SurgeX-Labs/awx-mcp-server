# Logging and Monitoring Guide

## Overview

The AWX MCP Server includes comprehensive logging and monitoring capabilities for production deployments.

---

## 📝 Logging Architecture

### Structured Logging

All logs are emitted in **structured JSON format** using `structlog`:

```json
{
  "timestamp": "2026-02-23T01:45:30.123456Z",
  "level": "info",
  "event": "tool_call",
  "environment": "https://awx-prod.example.com",
  "tenant_id": "user_12345",
  "tool_name": "awx_templates_list",
  "duration_ms": 245,
  "status": "success"
}
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages (non-critical)
- **ERROR**: Error messages (operation failed)

### Configuration

```bash
# Set log level via environment variable
export LOG_LEVEL=info  # debug, info, warning, error
```

---

## 🔍 Log Events

### MCP Protocol Events

#### tools/call - Tool Execution
```json
{
  "event": "tool_call",
  "tool_name": "awx_job_launch",
  "arguments": {"template_id": 5},
  "environment": "https://awx-prod.example.com",
  "tenant_id": "user_12345",
  "duration_ms": 1234,
  "status": "success"
}
```

#### tools/list - Tool Discovery
```json
{
  "event": "tools_list",
  "tenant_id": "user_12345",
  "tools_count": 49
}
```

#### initialize - Client Connection
```json
{
  "event": "mcp_initialize",
  "tenant_id": "user_12345",
  "protocol_version": "2024-11-05",
  "client_info": {"name": "vscode", "version": "1.95.0"}
}
```

### HTTP Server Events

#### Request Received
```json
{
  "event": "mcp_message_received",
  "tenant_id": "default",
  "method": "tools/call",
  "environment": "https://awx-dev.example.com"
}
```

#### Request Completed
```json
{
  "event": "request_completed",
  "tenant_id": "default",
  "endpoint": "/mcp",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 345
}
```

### Error Events

#### Tool Execution Error
```json
{
  "event": "tool_error",
  "level": "error",
  "tool_name": "awx_job_launch",
  "error": "Authentication failed",
  "environment": "https://awx-prod.example.com",
  "tenant_id": "user_12345"
}
```

#### MCP Protocol Error
```json
{
  "event": "mcp_error",
  "level": "error",
  "error": "Internal error: Connection timeout",
  "method": "tools/call",
  "tenant_id": "default"
}
```

---

## 📊 Prometheus Metrics

### Endpoint

```
GET /prometheus-metrics
```

Returns metrics in Prometheus exposition format.

### Available Metrics

#### Request Counters

```prometheus
# Total requests by tenant and endpoint
mcp_requests_total{tenant_id="default",endpoint="/mcp",method="POST"} 1523

# Tool calls by tenant and tool name
mcp_tool_calls_total{tenant_id="default",tool_name="awx_templates_list"} 245
mcp_tool_calls_total{tenant_id="default",tool_name="awx_job_launch"} 89

# Chat interactions by source
mcp_chat_interactions_total{tenant_id="default",source="vscode"} 432

# Errors by tenant and endpoint
mcp_errors_total{tenant_id="default",endpoint="/mcp"} 12
```

#### Request Duration Histograms

```prometheus
# Request duration in seconds
mcp_request_duration_seconds_bucket{tenant_id="default",endpoint="/mcp",le="0.1"} 1234
mcp_request_duration_seconds_bucket{tenant_id="default",endpoint="/mcp",le="0.5"} 1456
mcp_request_duration_seconds_bucket{tenant_id="default",endpoint="/mcp",le="1.0"} 1500
mcp_request_duration_seconds_sum{tenant_id="default",endpoint="/mcp"} 345.67
mcp_request_duration_seconds_count{tenant_id="default",endpoint="/mcp"} 1523
```

---

## 🎯 Monitoring Setup

### Prometheus Configuration

**prometheus.yml**:
```yaml
scrape_configs:
  - job_name: 'awx-mcp-server'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/prometheus-metrics'
```

### Grafana Dashboard

**Key Panels**:

1. **Request Rate**
   - Query: `rate(mcp_requests_total[5m])`
   - Type: Graph
   - Description: Requests per second

2. **Tool Call Distribution**
   - Query: `sum by (tool_name) (mcp_tool_calls_total)`
   - Type: Pie chart
   - Description: Most popular tools

3. **Error Rate**
   - Query: `rate(mcp_errors_total[5m])`
   - Type: Graph
   - Description: Errors per second

4. **Request Latency (p95)**
   - Query: `histogram_quantile(0.95, rate(mcp_request_duration_seconds_bucket[5m]))`
   - Type: Graph
   - Description: 95th percentile latency

5. **Tenant Activity**
   - Query: `sum by (tenant_id) (rate(mcp_requests_total[5m]))`
   - Type: Bar chart
   - Description: Activity by tenant

---

## 🚨 Alerting

### Prometheus Alert Rules

**alerts.yml**:
```yaml
groups:
  - name: awx_mcp_server
    interval: 30s
    rules:
      # Server is down
      - alert: MCPServerDown
        expr: up{job="awx-mcp-server"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MCP Server is down"
          description: "The AWX MCP Server has been down for more than 1 minute"

      # High error rate
      - alert: MCPHighErrorRate
        expr: rate(mcp_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High MCP error rate"
          description: "Error rate is {{ $value }} errors/sec (threshold: 0.05)"

      # High latency
      - alert: MCPHighLatency
        expr: histogram_quantile(0.95, rate(mcp_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High MCP request latency"
          description: "P95 latency is {{ $value }} seconds (threshold: 5s)"

      # Authentication failures
      - alert: MCPAuthFailures
        expr: increase(mcp_errors_total{error=~".*[Aa]uth.*"}[5m]) > 10
        labels:
          severity: critical
        annotations:
          summary: "Multiple authentication failures"
          description: "{{ $value }} authentication failures in the last 5 minutes"
```

---

## 📁 Log Aggregation

### ELK Stack (Elasticsearch, Logstash, Kibana)

**Logstash Configuration**:
```ruby
input {
  file {
    path => "/var/log/awx-mcp-server/*.log"
    codec => json
  }
}

filter {
  # Parse structured JSON logs
  json {
    source => "message"
  }
  
  # Add timestamp
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "awx-mcp-server-%{+YYYY.MM.dd}"
  }
}
```

**Kibana Visualizations**:
1. Tool usage over time
2. Error rates by environment
3. Top users by request count
4. Failed authentication attempts
5. Request latency heatmap

---

### Splunk

**inputs.conf**:
```ini
[monitor:///var/log/awx-mcp-server/*.log]
sourcetype = awx_mcp_json
index = awx_mcp
```

**props.conf**:
```ini
[awx_mcp_json]
INDEXED_EXTRACTIONS = json
KV_MODE = json
TIME_PREFIX = \"timestamp\":\s*\"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%6N%Z
MAX_TIMESTAMP_LOOKAHEAD = 32
```

**Sample Splunk Queries**:
```spl
# Top tools used
index=awx_mcp event=tool_call
| stats count by tool_name
| sort -count

# Error rate by environment
index=awx_mcp level=error
| timechart count by environment

# Slow requests (>5s)
index=awx_mcp duration_ms>5000
| table timestamp, environment, tool_name, duration_ms
| sort -duration_ms
```

---

## 🔎 Log Queries

### Find all tool calls for a specific environment
```bash
grep '"environment": "https://awx-prod.example.com"' /var/log/awx-mcp-server/*.log | grep '"event": "tool_call"'
```

### Count errors in the last hour
```bash
journalctl -u awx-mcp-server --since "1 hour ago" | grep '"level": "error"' | wc -l
```

### Find authentication failures
```bash
grep -i 'authentication failed' /var/log/awx-mcp-server/*.log
```

### Get request latency statistics
```bash
grep '"duration_ms"' /var/log/awx-mcp-server/*.log | awk -F'"duration_ms": ' '{print $2}' | awk -F',' '{print $1}' | sort -n
```

---

## 🛠️ Troubleshooting with Logs

### Issue: Slow Performance

**Check request latencies**:
```bash
grep '"tool_call"' /var/log/awx-mcp-server/*.log | grep duration_ms | awk -F'"duration_ms": ' '{print $2}' | awk '{print $1}' | sort -rn | head -20
```

### Issue: Authentication Failures

**Find auth failures**:
```bash
grep -i 'auth' /var/log/awx-mcp-server/*.log | grep error
```

### Issue: Missing Events

**Check if environment is being logged**:
```bash
grep '"environment"' /var/log/awx-mcp-server/*.log | tail -100
```

---

## 📋 Log Retention

### Recommended Retention Policies

- **Development**: 7 days
- **Staging**: 30 days
- **Production**: 90 days (or per compliance requirements)

### Log Rotation

**logrotate.conf**:
```
/var/log/awx-mcp-server/*.log {
    daily
    rotate 90
    compress
    delaycompress
    notifempty
    create 0640 awx-mcp awx-mcp
    sharedscripts
    postrotate
        systemctl reload awx-mcp-server > /dev/null 2>&1 || true
    endscript
}
```

---

## ✅ Monitoring Checklist

Production monitoring should include:

- [ ] Prometheus scraping configured
- [ ] Grafana dashboards created
- [ ] Alert rules defined
- [ ] PagerDuty/Slack integration configured
- [ ] Log aggregation setup (ELK/Splunk)
- [ ] Log retention policy defined
- [ ] Log rotation configured
- [ ] Health check monitoring
- [ ] SSL certificate expiration monitoring
- [ ] Disk space monitoring
- [ ] Memory usage monitoring
