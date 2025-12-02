# Alertmanager Configuration for GGnet

Alertmanager handles alert notifications from Prometheus.

## Setup

### 1. Add Alertmanager to docker-compose.yml

```yaml
alertmanager:
  image: prom/alertmanager:latest
  container_name: ggnet-alertmanager
  volumes:
    - ./docker/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
  ports:
    - "9093:9093"
  restart: unless-stopped
```

### 2. Update Prometheus Configuration

Uncomment Alertmanager configuration in `docker/prometheus/prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### 3. Configure Notification Channels

Edit `docker/alertmanager/alertmanager.yml` and configure:

- **Email:** Set SMTP settings
- **Slack:** Add webhook URL
- **Other:** Add PagerDuty, OpsGenie, etc.

## Testing

### Test Alert Rules

```bash
# Check if alerts are firing
curl http://localhost:9090/api/v1/alerts
```

### Test Notification

1. Trigger a test alert
2. Check Alertmanager UI: http://localhost:9093
3. Verify notification received

## Configuration

See `alertmanager.yml` for:
- Route configuration
- Receiver setup
- Notification templates
- Inhibition rules

