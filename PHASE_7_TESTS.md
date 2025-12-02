# PHASE 7: CI / QA / Monitoring - Testing Guide

## Overview
This document provides comprehensive testing instructions for Phase 7 CI/CD, monitoring, and quality assurance infrastructure.

## Test Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- Git with GitHub Actions access

### Backend Testing Setup
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx
```

### Frontend Testing Setup
```bash
cd frontend
npm install
npm run test:coverage
```

## Running Tests

### 1. Backend Health Endpoints Testing

#### Basic Health Check
```bash
# Test basic health endpoint
curl http://localhost:8000/health/

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "service": "ggnet-backend"
}
```

#### Detailed Health Check
```bash
# Test detailed health endpoint
curl http://localhost:8000/health/detailed

# Expected response with component status:
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "service": "ggnet-backend",
  "components": {
    "database": {"status": "healthy", "details": "Database connection successful"},
    "redis": {"status": "healthy", "details": "Redis connection successful"},
    "system": {"status": "healthy", "cpu_percent": 15.2, "memory_percent": 45.8},
    "storage": {"status": "healthy", "details": "All storage paths accessible"}
  }
}
```

#### Kubernetes Probes
```bash
# Readiness probe
curl http://localhost:8000/health/ready

# Liveness probe
curl http://localhost:8000/health/live

# Startup probe
curl http://localhost:8000/health/startup
```

### 2. Prometheus Metrics Testing

#### Metrics Endpoint
```bash
# Test metrics endpoint
curl http://localhost:8000/metrics/

# Expected Prometheus format:
# HELP ggnet_http_requests_total Total HTTP requests
# TYPE ggnet_http_requests_total counter
# ggnet_http_requests_total 42

# HELP ggnet_active_sessions Active sessions
# TYPE ggnet_active_sessions gauge
# ggnet_active_sessions 3

# HELP ggnet_system_cpu_percent CPU usage percentage
# TYPE ggnet_system_cpu_percent gauge
# ggnet_system_cpu_percent 15.2
```

#### Metrics Validation
```python
# Test metrics collection
import requests

response = requests.get("http://localhost:8000/metrics/")
metrics_text = response.text

# Validate Prometheus format
assert "# HELP" in metrics_text
assert "# TYPE" in metrics_text
assert "ggnet_" in metrics_text

# Check specific metrics
assert "ggnet_http_requests_total" in metrics_text
assert "ggnet_active_sessions" in metrics_text
assert "ggnet_system_cpu_percent" in metrics_text
```

### 3. Logging Infrastructure Testing

#### Log File Creation
```bash
# Check log files are created
ls -la logs/
# Expected files:
# - app.log
# - error.log
# - audit.log
# - security.log
# - performance.log
```

#### Log Rotation Testing
```python
# Test log rotation
import os
import time
from pathlib import Path

log_file = Path("logs/app.log")
initial_size = log_file.stat().st_size

# Generate log entries to trigger rotation
for i in range(1000):
    logger.info(f"Test log entry {i}")

# Check if rotation occurred
time.sleep(1)
new_size = log_file.stat().st_size
assert new_size > initial_size
```

#### Structured Logging Testing
```python
# Test structured logging
import json
import logging

# Configure logger
logger = logging.getLogger("test")
logger.setLevel(logging.INFO)

# Log structured data
logger.info("Test message", extra={
    "user_id": 123,
    "action": "test_action",
    "duration_ms": 45.2
})

# Verify JSON format in log file
with open("logs/app.log", "r") as f:
    log_line = f.readline()
    log_data = json.loads(log_line)
    assert "user_id" in log_data
    assert log_data["user_id"] == 123
```

### 4. CI/CD Pipeline Testing

#### Local Pipeline Simulation
```bash
# Test backend linting
cd backend
flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
black --check app/
isort --check-only app/
mypy app/ --ignore-missing-imports

# Test backend tests
pytest tests/ -v --cov=app --cov-report=xml

# Test frontend linting
cd frontend
npm run lint
npm run type-check

# Test frontend tests
npm test -- --coverage --watchAll=false

# Test frontend build
npm run build
```

#### Docker Build Testing
```bash
# Test backend Docker build
cd backend
docker build -t ggnet-backend:test .

# Test frontend Docker build
cd frontend
docker build -t ggnet-frontend:test .

# Test docker-compose
cd infra
docker compose config
docker compose build
```

#### Security Scanning Testing
```bash
# Test Python security scanning
cd backend
bandit -r app/ -f json -o bandit-report.json
safety check --json --output safety-report.json

# Check for vulnerabilities
python -c "
import json
with open('bandit-report.json') as f:
    report = json.load(f)
    assert len(report['results']) == 0, 'Security issues found'
"
```

### 5. Frontend Testing

#### Unit Tests
```bash
cd frontend
npm test

# Test specific components
npm test -- SessionManager
npm test -- TargetManager
npm test -- NetworkBootMonitor
```

#### Integration Tests
```bash
# Test API integration
npm test -- --testNamePattern="API integration"

# Test real-time updates
npm test -- --testNamePattern="real-time updates"
```

#### Coverage Testing
```bash
# Run coverage tests
npm run test:coverage

# Check coverage thresholds
npm run test:coverage -- --coverage.thresholds.global.branches=80
npm run test:coverage -- --coverage.thresholds.global.functions=80
npm run test:coverage -- --coverage.thresholds.global.lines=80
```

### 6. Performance Testing

#### Load Testing
```bash
# Test health endpoint performance
for i in {1..100}; do
  curl -s http://localhost:8000/health/ > /dev/null
done

# Test metrics endpoint performance
for i in {1..100}; do
  curl -s http://localhost:8000/metrics/ > /dev/null
done
```

#### Memory Usage Testing
```python
# Test memory usage
import psutil
import time

process = psutil.Process()
initial_memory = process.memory_info().rss

# Perform operations
for i in range(1000):
    response = requests.get("http://localhost:8000/health/")

final_memory = process.memory_info().rss
memory_increase = final_memory - initial_memory

# Check for memory leaks
assert memory_increase < 10 * 1024 * 1024  # Less than 10MB increase
```

### 7. Integration Testing

#### End-to-End Health Check
```python
# Test complete health check workflow
import requests
import time

def test_health_check_workflow():
    # Test basic health
    response = requests.get("http://localhost:8000/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Test detailed health
    response = requests.get("http://localhost:8000/health/detailed")
    assert response.status_code == 200
    health_data = response.json()
    assert health_data["status"] in ["healthy", "degraded"]
    
    # Test metrics
    response = requests.get("http://localhost:8000/metrics/")
    assert response.status_code == 200
    assert "ggnet_" in response.text
    
    # Test Kubernetes probes
    for endpoint in ["/health/ready", "/health/live", "/health/startup"]:
        response = requests.get(f"http://localhost:8000/health{endpoint}")
        assert response.status_code == 200
```

#### Database Integration Testing
```python
# Test database metrics collection
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.routes.metrics import _update_database_metrics

async def test_database_metrics():
    async with get_db() as db:
        await _update_database_metrics(db)
        
        # Verify metrics were updated
        from app.routes.metrics import _metrics
        assert _metrics["total_machines"] >= 0
        assert _metrics["total_images"] >= 0
        assert _metrics["total_targets"] >= 0
        assert _metrics["total_users"] >= 0
```

### 8. Monitoring Integration Testing

#### Prometheus Scraping
```bash
# Test Prometheus scraping
curl -H "Accept: application/openmetrics-text" http://localhost:8000/metrics/

# Validate metrics format
curl http://localhost:8000/metrics/ | grep -E "^# (HELP|TYPE)"
```

#### Grafana Dashboard Testing
```yaml
# Test Grafana dashboard queries
# CPU Usage
ggnet_system_cpu_percent

# Memory Usage
ggnet_system_memory_percent

# Active Sessions
ggnet_active_sessions

# HTTP Requests
rate(ggnet_http_requests_total[5m])
```

### 9. Error Handling Testing

#### Health Check Failure Testing
```python
# Test health check with database failure
import requests
from unittest.mock import patch

def test_health_check_database_failure():
    with patch('app.routes.health.db.execute') as mock_execute:
        mock_execute.side_effect = Exception("Database connection failed")
        
        response = requests.get("http://localhost:8000/health/detailed")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "unhealthy"
        assert health_data["components"]["database"]["status"] == "unhealthy"
```

#### Metrics Collection Failure Testing
```python
# Test metrics collection with Redis failure
import requests
from unittest.mock import patch

def test_metrics_redis_failure():
    with patch('app.core.cache.cache_manager.set') as mock_set:
        mock_set.side_effect = Exception("Redis connection failed")
        
        response = requests.get("http://localhost:8000/metrics/")
        assert response.status_code == 200
        
        # Metrics should still be collected from database
        assert "ggnet_" in response.text
```

### 10. Security Testing

#### Health Endpoint Security
```bash
# Test health endpoint security
curl -X POST http://localhost:8000/health/
# Should return 405 Method Not Allowed

curl http://localhost:8000/health/ -H "X-Forwarded-For: 192.168.1.1"
# Should work normally
```

#### Metrics Endpoint Security
```bash
# Test metrics endpoint security
curl -X POST http://localhost:8000/metrics/
# Should return 405 Method Not Allowed

curl http://localhost:8000/metrics/ -H "Authorization: Bearer invalid-token"
# Should work (metrics are public)
```

## Continuous Integration Testing

### GitHub Actions Testing
```bash
# Test CI pipeline locally
act push

# Test specific jobs
act -j backend-tests
act -j frontend-tests
act -j integration-tests
act -j security-scan
```

### Code Quality Testing
```bash
# Test all quality checks
cd backend
black --check app/
isort --check-only app/
flake8 app/
mypy app/ --ignore-missing-imports
bandit -r app/
safety check

cd frontend
npm run lint
npm run type-check
npm run format:check
```

## Performance Benchmarks

### Health Check Performance
- Basic health check: < 50ms
- Detailed health check: < 200ms
- Kubernetes probes: < 100ms

### Metrics Collection Performance
- Metrics endpoint: < 100ms
- Database metrics update: < 50ms
- System metrics collection: < 20ms

### Logging Performance
- Structured log entry: < 1ms
- Log rotation: < 100ms
- Audit log entry: < 2ms

## Troubleshooting

### Common Issues

#### Health Check Failures
```bash
# Check database connectivity
psql -h localhost -U postgres -d ggnet -c "SELECT 1"

# Check Redis connectivity
redis-cli ping

# Check system resources
top
df -h
```

#### Metrics Collection Issues
```bash
# Check metrics endpoint
curl -v http://localhost:8000/metrics/

# Check Prometheus format
curl http://localhost:8000/metrics/ | head -20
```

#### Logging Issues
```bash
# Check log files
ls -la logs/
tail -f logs/app.log
tail -f logs/error.log

# Check log rotation
logrotate -d /etc/logrotate.d/ggnet
```

### Debug Commands
```bash
# Debug health checks
curl -v http://localhost:8000/health/detailed

# Debug metrics
curl -v http://localhost:8000/metrics/

# Debug logging
journalctl -u ggnet-backend -f

# Debug CI pipeline
act -v push
```

## Best Practices

### Testing Strategy
- Test health checks regularly
- Monitor metrics collection
- Verify log rotation
- Test CI pipeline changes
- Validate security scans

### Performance Monitoring
- Set up alerts for slow health checks
- Monitor metrics collection performance
- Track log file sizes
- Monitor CI pipeline duration

### Security Testing
- Regular security scans
- Dependency vulnerability checks
- Health endpoint security
- Metrics endpoint security

### Maintenance
- Regular log cleanup
- Metrics retention policies
- CI pipeline optimization
- Test coverage monitoring
