# Monitoring and Observability

## Overview

The application provides comprehensive monitoring through Prometheus-compatible metrics, enabling production-grade observability for performance tracking, capacity planning, and alerting.

## Metrics Endpoint

**Endpoint**: `GET /metrics`

Exposes metrics in Prometheus text format for scraping by Prometheus server or compatible monitoring systems.

### Example Usage

```bash
# View metrics
curl http://localhost:8000/metrics

# Prometheus scrape configuration
scrape_configs:
  - job_name: 'bricklayers-web'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Available Metrics

### Application Info

**Metric**: `app_info`  
**Type**: Info  
**Description**: Application metadata  
**Labels**: name, version, description

### HTTP Request Metrics

#### `http_requests_total`
**Type**: Counter  
**Description**: Total HTTP requests  
**Labels**:
- `method`: HTTP method (GET, POST, etc.)
- `endpoint`: Request path (/api/v1/upload, etc.)
- `status`: HTTP status code (200, 404, 500, etc.)

**Example**:
```
http_requests_total{method="POST",endpoint="/api/v1/upload",status="201"} 42
http_requests_total{method="GET",endpoint="/api/v1/status/{job_id}",status="200"} 128
```

#### `http_request_duration_seconds`
**Type**: Histogram  
**Description**: HTTP request duration in seconds  
**Labels**:
- `method`: HTTP method
- `endpoint`: Request path

**Buckets**: 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0 seconds

**Example**:
```
http_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/upload",le="0.1"} 35
http_request_duration_seconds_sum{method="POST",endpoint="/api/v1/upload"} 8.3
http_request_duration_seconds_count{method="POST",endpoint="/api/v1/upload"} 42
```

### Upload Metrics

#### `uploads_total`
**Type**: Counter  
**Description**: Total file uploads  
**Labels**:
- `status`: success, failed_size, failed_validation, failed_error

**Example**:
```
uploads_total{status="success"} 156
uploads_total{status="failed_validation"} 8
uploads_total{status="failed_size"} 3
```

#### `upload_file_size_bytes`
**Type**: Histogram  
**Description**: Size of uploaded files in bytes  
**Buckets**: 100KB, 500KB, 1MB, 5MB, 10MB, 25MB, 50MB, 100MB

**Example**:
```
upload_file_size_bytes_bucket{le="1000000"} 45
upload_file_size_bytes_bucket{le="5000000"} 98
upload_file_size_bytes_sum 487392810
upload_file_size_bytes_count 156
```

#### `upload_validation_failures_total`
**Type**: Counter  
**Description**: Upload validation failures by reason  
**Labels**:
- `reason`: validation failure type (e.g., file_too_large, invalid_extension)

### Processing Job Metrics

#### `processing_jobs_total`
**Type**: Counter  
**Description**: Total processing jobs by final status  
**Labels**:
- `status`: completed, error, timeout

**Example**:
```
processing_jobs_total{status="completed"} 142
processing_jobs_total{status="error"} 5
processing_jobs_total{status="timeout"} 1
```

#### `processing_jobs_active`
**Type**: Gauge  
**Description**: Number of jobs currently being processed

**Example**:
```
processing_jobs_active 3
```

#### `processing_jobs_pending`
**Type**: Gauge  
**Description**: Number of jobs waiting in queue

**Example**:
```
processing_jobs_pending 7
```

#### `processing_duration_seconds`
**Type**: Histogram  
**Description**: Time taken to process jobs  
**Buckets**: 1, 5, 10, 30, 60, 120, 300, 600 seconds

**Example**:
```
processing_duration_seconds_bucket{le="30"} 89
processing_duration_seconds_bucket{le="60"} 132
processing_duration_seconds_sum 5832.4
processing_duration_seconds_count 142
```

#### `processing_input_size_bytes`
**Type**: Histogram  
**Description**: Size of input files processed  
**Buckets**: 100KB, 500KB, 1MB, 5MB, 10MB, 25MB, 50MB, 100MB

#### `processing_output_size_bytes`
**Type**: Histogram  
**Description**: Size of output files produced  
**Buckets**: 100KB, 500KB, 1MB, 5MB, 10MB, 25MB, 50MB, 100MB

### Download Metrics

#### `downloads_total`
**Type**: Counter  
**Description**: Total file downloads by status  
**Labels**:
- `status`: success, failed_not_found, failed_not_ready, failed_file_missing

**Example**:
```
downloads_total{status="success"} 128
downloads_total{status="failed_not_ready"} 15
downloads_total{status="failed_not_found"} 3
```

### Cleanup Service Metrics

#### `cleanup_runs_total`
**Type**: Counter  
**Description**: Total cleanup service runs

#### `cleanup_files_deleted_total`
**Type**: Counter  
**Description**: Total files deleted by cleanup service

#### `cleanup_bytes_freed_total`
**Type**: Counter  
**Description**: Total bytes freed by cleanup service

#### `cleanup_errors_total`
**Type**: Counter  
**Description**: Total errors during cleanup operations

**Example**:
```
cleanup_runs_total 48
cleanup_files_deleted_total 234
cleanup_bytes_freed_total 3892745102
cleanup_errors_total 2
```

### System Health Metrics

#### `system_memory_usage_bytes`
**Type**: Gauge  
**Description**: Current memory usage in bytes

#### `system_disk_usage_bytes`
**Type**: Gauge  
**Description**: Current disk usage for temp directories

## Example Prometheus Queries

### Request Rate
```promql
# Requests per second by endpoint
rate(http_requests_total[5m])

# Success rate (2xx, 3xx responses)
sum(rate(http_requests_total{status=~"2..|3.."}[5m])) / sum(rate(http_requests_total[5m]))
```

### Latency
```promql
# 95th percentile request duration
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Average processing time
rate(processing_duration_seconds_sum[5m]) / rate(processing_duration_seconds_count[5m])
```

### Upload Success Rate
```promql
# Upload success rate
sum(rate(uploads_total{status="success"}[5m])) / sum(rate(uploads_total[5m]))

# Validation failure rate by reason
sum by (reason) (rate(upload_validation_failures_total[5m]))
```

### Processing Throughput
```promql
# Jobs completed per minute
rate(processing_jobs_total{status="completed"}[1m]) * 60

# Average job queue depth
avg_over_time(processing_jobs_pending[5m])

# Processing failure rate
sum(rate(processing_jobs_total{status=~"error|timeout"}[5m])) / sum(rate(processing_jobs_total[5m]))
```

### Storage Management
```promql
# Cleanup efficiency (bytes freed per run)
rate(cleanup_bytes_freed_total[1h]) / rate(cleanup_runs_total[1h])

# Files deleted per hour
increase(cleanup_files_deleted_total[1h])
```

## Grafana Dashboard Setup

### Recommended Panels

1. **Overview**
   - Total requests (counter)
   - Success rate (gauge)
   - Active jobs (gauge)
   - Queue depth (graph)

2. **Performance**
   - Request duration (heatmap)
   - Processing duration (heatmap)
   - 95th percentile latency (graph)

3. **Uploads**
   - Upload rate (graph)
   - Upload success rate (gauge)
   - File size distribution (histogram)
   - Validation failures by reason (pie chart)

4. **Processing**
   - Jobs completed/failed (graph)
   - Processing duration trends (graph)
   - Active vs. pending jobs (graph)
   - Input/output size trends (graph)

5. **Downloads**
   - Download rate (graph)
   - Download failures by reason (pie chart)

6. **System Health**
   - Cleanup metrics (graph)
   - Memory usage (graph)
   - Disk usage (graph)

### Sample Grafana Panel JSON

```json
{
  "title": "Upload Success Rate",
  "targets": [
    {
      "expr": "sum(rate(uploads_total{status=\"success\"}[5m])) / sum(rate(uploads_total[5m]))",
      "legendFormat": "Success Rate"
    }
  ],
  "type": "stat",
  "options": {
    "unit": "percentunit"
  }
}
```

## Alerting Rules

### Example Prometheus Alert Rules

```yaml
groups:
  - name: bricklayers_alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) 
          / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # High processing failure rate
      - alert: HighProcessingFailureRate
        expr: |
          sum(rate(processing_jobs_total{status=~"error|timeout"}[10m])) 
          / sum(rate(processing_jobs_total[10m])) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High processing failure rate"
          description: "Processing failure rate is {{ $value | humanizePercentage }}"

      # Job queue backing up
      - alert: JobQueueBacklog
        expr: processing_jobs_pending > 50
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Job queue backing up"
          description: "{{ $value }} jobs pending for over 15 minutes"

      # Slow request response
      - alert: SlowRequests
        expr: |
          histogram_quantile(0.95, 
            rate(http_request_duration_seconds_bucket[5m])
          ) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow request response times"
          description: "95th percentile latency is {{ $value }}s"

      # Cleanup failures
      - alert: CleanupFailures
        expr: increase(cleanup_errors_total[1h]) > 5
        labels:
          severity: warning
        annotations:
          summary: "Multiple cleanup failures"
          description: "{{ $value }} cleanup errors in the past hour"
```

## Integration with Monitoring Tools

### Prometheus Server

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'bricklayers-web'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Grafana

1. Add Prometheus as data source
2. Import dashboard using queries above
3. Configure alerts based on your SLOs

### Cloud Services

The metrics endpoint is compatible with:
- **AWS CloudWatch**: Use Prometheus exporter
- **Google Cloud Monitoring**: Use Prometheus integration
- **Azure Monitor**: Use Prometheus metrics collection
- **Datadog**: Native Prometheus integration
- **New Relic**: Prometheus integration

## Performance Impact

- **Memory**: ~10MB for metric storage (scales with cardinality)
- **CPU**: <1% overhead for metric collection
- **Scrape Time**: <100ms for full metric export

## Best Practices

1. **Scrape Interval**: 15-30 seconds for most use cases
2. **Retention**: 15 days minimum for Prometheus data
3. **Alerting**: Set up alerts for SLO violations
4. **Dashboards**: Create role-specific dashboards (ops, dev, business)
5. **Cardinality**: Avoid high-cardinality labels (user IDs, job IDs)

## Troubleshooting

### Metrics Not Appearing

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Verify Prometheus can reach the app
curl http://prometheus:9090/api/v1/targets
```

### High Memory Usage

If metric memory usage is high:
1. Check label cardinality
2. Reduce histogram buckets
3. Decrease Prometheus retention period

### Missing Data Points

- Verify scrape interval configuration
- Check for network issues
- Review Prometheus logs for scrape errors

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [prometheus_client Python Library](https://github.com/prometheus/client_python)
