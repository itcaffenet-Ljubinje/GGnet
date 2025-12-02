# PHASE 2 - TESTS: Image Storage & Conversion

## Test Instructions

This document provides comprehensive testing instructions for the image storage and conversion functionality implemented in Phase 2.

## Prerequisites

### System Requirements
- Python 3.11+
- qemu-img binary (qemu-utils package)
- PostgreSQL or SQLite database
- Redis server
- Sufficient disk space for test images

### Dependencies
```bash
# Install system dependencies
sudo apt-get install qemu-utils

# Install Python dependencies
pip install -r backend/requirements.txt
```

## Test Categories

### 1. Unit Tests

#### qemu-img Wrapper Tests
```bash
# Run qemu-img wrapper tests
cd backend
python -m pytest tests/test_image_conversion.py::TestQemuImageConverter -v
```

**Test Coverage**:
- qemu-img availability check
- Image info retrieval
- Successful conversion
- Conversion failure handling
- Progress monitoring

#### Worker Tests
```bash
# Run worker tests
python -m pytest tests/test_image_conversion.py::TestImageConversionWorker -v
```

**Test Coverage**:
- Worker initialization
- Image conversion process
- Error handling
- Database integration
- Status updates

#### API Endpoint Tests
```bash
# Run API endpoint tests
python -m pytest tests/test_image_conversion.py::TestImageConversion -v
```

**Test Coverage**:
- Conversion trigger endpoint
- Status retrieval endpoint
- Error responses
- Authentication/authorization

### 2. Integration Tests

#### End-to-End Workflow
```bash
# Run complete integration tests
python -m pytest tests/test_image_conversion.py::TestImageUploadWithConversion -v
```

**Test Coverage**:
- Upload VHDX file
- Automatic conversion trigger
- Background processing
- Status tracking
- Completion notification

### 3. Manual Testing

#### qemu-img Wrapper Manual Test
```bash
# Test qemu-img wrapper directly
cd backend
python scripts/qemu_convert.py --help

# Test with sample image
python scripts/qemu_convert.py --info /path/to/test.vhdx

# Test conversion
python scripts/qemu_convert.py /path/to/test.vhdx /tmp/output.img
```

#### Worker Process Manual Test
```bash
# Start worker manually
cd backend
python -m worker.convert

# Check logs
tail -f logs/worker.log
```

## Test Data Preparation

### Create Test Images
```bash
# Create a small test VHDX file using qemu-img
qemu-img create -f vhdx test.vhdx 100M

# Create a larger test file
qemu-img create -f vhdx test_large.vhdx 1G

# Create an invalid test file
echo "invalid content" > test_invalid.vhdx
```

### Test File Sizes
- **Small**: 100MB (for quick tests)
- **Medium**: 1GB (for performance tests)
- **Large**: 10GB (for stress tests)
- **Invalid**: Corrupted files (for error tests)

## API Testing

### 1. Upload Test
```bash
# Upload VHDX file
curl -X POST http://localhost:8000/images/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.vhdx" \
  -F "name=Test Image" \
  -F "description=Test VHDX file" \
  -F "image_type=system"
```

**Expected Response**:
```json
{
  "id": 1,
  "name": "Test Image",
  "status": "processing",
  "format": "vhdx",
  "size_bytes": 104857600
}
```

### 2. Conversion Trigger Test
```bash
# Trigger conversion manually
curl -X POST http://localhost:8000/images/1/convert \
  -H "Authorization: Bearer <token>"
```

**Expected Response**:
```json
{
  "message": "Conversion triggered successfully",
  "image_id": 1
}
```

### 3. Status Check Test
```bash
# Check conversion status
curl http://localhost:8000/images/1/conversion-status \
  -H "Authorization: Bearer <token>"
```

**Expected Response**:
```json
{
  "image_id": 1,
  "name": "Test Image",
  "status": "converting",
  "format": "vhdx",
  "processing_info": {
    "progress": 45.2,
    "duration_seconds": 120
  }
}
```

## Performance Testing

### 1. Conversion Speed Test
```bash
# Test with different file sizes
time python scripts/qemu_convert.py test_100m.vhdx test_100m.img
time python scripts/qemu_convert.py test_1g.vhdx test_1g.img
time python scripts/qemu_convert.py test_10g.vhdx test_10g.img
```

### 2. Memory Usage Test
```bash
# Monitor memory usage during conversion
python -c "
import psutil
import time
import subprocess

process = subprocess.Popen(['python', 'scripts/qemu_convert.py', 'test.vhdx', 'test.img'])
pid = process.pid

while process.poll() is None:
    try:
        proc = psutil.Process(pid)
        print(f'Memory: {proc.memory_info().rss / 1024 / 1024:.2f} MB')
        time.sleep(5)
    except psutil.NoSuchProcess:
        break
"
```

### 3. Concurrent Processing Test
```bash
# Test multiple conversions simultaneously
python scripts/qemu_convert.py test1.vhdx test1.img &
python scripts/qemu_convert.py test2.vhdx test2.img &
python scripts/qemu_convert.py test3.vhdx test3.img &
wait
```

## Error Testing

### 1. Invalid File Test
```bash
# Test with corrupted file
python scripts/qemu_convert.py test_invalid.vhdx test_invalid.img
```

**Expected**: Error message and proper cleanup

### 2. Insufficient Space Test
```bash
# Test with insufficient disk space
# Fill disk to 95% capacity, then try conversion
python scripts/qemu_convert.py test_large.vhdx test_large.img
```

**Expected**: Error handling and cleanup

### 3. Permission Test
```bash
# Test with read-only output directory
chmod 444 /tmp/readonly/
python scripts/qemu_convert.py test.vhdx /tmp/readonly/test.img
```

**Expected**: Permission error handling

## Service Testing

### 1. Systemd Service Test
```bash
# Install and start service
sudo cp systemd/ggnet-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ggnet-worker
sudo systemctl start ggnet-worker

# Check status
sudo systemctl status ggnet-worker

# Check logs
sudo journalctl -u ggnet-worker -f
```

### 2. Service Restart Test
```bash
# Test service restart
sudo systemctl restart ggnet-worker
sudo systemctl status ggnet-worker

# Test service stop/start
sudo systemctl stop ggnet-worker
sudo systemctl start ggnet-worker
```

### 3. Service Failure Test
```bash
# Simulate service failure
sudo kill -9 $(pgrep -f "worker.convert")
sudo systemctl status ggnet-worker

# Should auto-restart within 10 seconds
```

## Database Testing

### 1. Status Update Test
```sql
-- Check image status updates
SELECT id, name, status, updated_at 
FROM images 
WHERE status IN ('processing', 'converting', 'ready', 'error')
ORDER BY updated_at DESC;
```

### 2. Processing Log Test
```sql
-- Check processing logs
SELECT id, name, processing_log, error_message
FROM images 
WHERE processing_log IS NOT NULL OR error_message IS NOT NULL;
```

### 3. Transaction Test
```bash
# Test database transaction safety
# Kill worker during conversion and check database consistency
sudo kill -9 $(pgrep -f "worker.convert")
# Check that no partial data was committed
```

## Monitoring Testing

### 1. Log Analysis
```bash
# Check structured logs
tail -f logs/worker.log | jq .

# Check for errors
grep -i error logs/worker.log

# Check conversion statistics
grep "conversion completed" logs/worker.log | wc -l
```

### 2. Metrics Collection
```bash
# Check conversion success rate
grep "conversion completed" logs/worker.log | wc -l
grep "conversion failed" logs/worker.log | wc -l

# Check average conversion time
grep "duration_seconds" logs/worker.log | jq '.duration_seconds' | awk '{sum+=$1; count++} END {print sum/count}'
```

### 3. Health Check Test
```bash
# Test worker health
curl http://localhost:8000/health

# Check worker process
ps aux | grep worker.convert

# Check queue status
curl http://localhost:8000/images?status=processing
```

## Stress Testing

### 1. Large File Test
```bash
# Create and test with 50GB file
qemu-img create -f vhdx test_50g.vhdx 50G
python scripts/qemu_convert.py test_50g.vhdx test_50g.img
```

### 2. Multiple Files Test
```bash
# Test with 10 concurrent conversions
for i in {1..10}; do
    python scripts/qemu_convert.py test_${i}.vhdx test_${i}.img &
done
wait
```

### 3. Long Running Test
```bash
# Run conversions for 24 hours
timeout 86400 python -m worker.convert
```

## Security Testing

### 1. File Validation Test
```bash
# Test with malicious file names
python scripts/qemu_convert.py "../../etc/passwd" test.img
python scripts/qemu_convert.py "test; rm -rf /" test.img
```

### 2. Permission Test
```bash
# Test with restricted permissions
chmod 000 test.vhdx
python scripts/qemu_convert.py test.vhdx test.img
```

### 3. Resource Limit Test
```bash
# Test with resource limits
ulimit -f 1000  # Limit file size to 1MB
python scripts/qemu_convert.py test.vhdx test.img
```

## Test Results Validation

### 1. Success Criteria
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Manual tests complete successfully
- [ ] Performance meets requirements
- [ ] Error handling works correctly
- [ ] Service runs reliably
- [ ] Database consistency maintained
- [ ] Logs are properly structured
- [ ] Security tests pass

### 2. Performance Benchmarks
- [ ] 100MB file converts in < 30 seconds
- [ ] 1GB file converts in < 5 minutes
- [ ] 10GB file converts in < 1 hour
- [ ] Memory usage < 2GB per conversion
- [ ] CPU usage < 200% per conversion
- [ ] Service restart time < 10 seconds

### 3. Error Handling Validation
- [ ] Invalid files handled gracefully
- [ ] Insufficient space handled properly
- [ ] Permission errors handled correctly
- [ ] Network failures handled appropriately
- [ ] Database errors handled safely
- [ ] Service crashes auto-recover

## Troubleshooting

### Common Issues

#### qemu-img Not Found
```bash
# Install qemu-utils
sudo apt-get install qemu-utils

# Check installation
which qemu-img
qemu-img --version
```

#### Permission Denied
```bash
# Check file permissions
ls -la test.vhdx
ls -la /tmp/

# Fix permissions
chmod 644 test.vhdx
chmod 755 /tmp/
```

#### Database Connection Error
```bash
# Check database status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U ggnet -d ggnet
```

#### Worker Not Starting
```bash
# Check service status
sudo systemctl status ggnet-worker

# Check logs
sudo journalctl -u ggnet-worker -n 50

# Check configuration
cat /etc/systemd/system/ggnet-worker.service
```

### Debug Commands
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m worker.convert

# Check process status
ps aux | grep worker
netstat -tlnp | grep 8000

# Check file system
df -h
ls -la /opt/ggnet/storage/
```

## Test Report Template

### Test Execution Summary
- **Date**: [Date]
- **Tester**: [Name]
- **Environment**: [OS, Python version, etc.]
- **Test Duration**: [Hours]

### Results Summary
- **Total Tests**: [Number]
- **Passed**: [Number]
- **Failed**: [Number]
- **Skipped**: [Number]
- **Success Rate**: [Percentage]

### Performance Results
- **Average Conversion Time**: [Seconds]
- **Memory Usage**: [MB]
- **CPU Usage**: [Percentage]
- **Disk I/O**: [MB/s]

### Issues Found
- **Critical**: [Number]
- **High**: [Number]
- **Medium**: [Number]
- **Low**: [Number]

### Recommendations
- [List of recommendations for improvements]

## Conclusion

This comprehensive test suite ensures the image storage and conversion functionality is robust, performant, and production-ready. All tests should pass before proceeding to Phase 3.
