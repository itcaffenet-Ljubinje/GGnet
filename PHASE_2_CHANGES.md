# PHASE 2 - CHANGES: Image Storage & Conversion

## Summary

This phase implemented background image conversion functionality using qemu-img, enabling automatic VHDX to RAW conversion for iSCSI targets. The implementation includes a robust worker system, comprehensive error handling, and real-time progress tracking.

## What Was Implemented

### 1. qemu-img Wrapper Script
- **File**: `backend/scripts/qemu_convert.py`
- **Purpose**: Python wrapper for qemu-img command-line tool
- **Features**:
  - Async/await support for non-blocking operations
  - Progress monitoring with callbacks
  - Comprehensive error handling
  - Image info retrieval
  - Sparse file creation
  - Image resizing capabilities
  - Command-line interface for manual operations

### 2. Background Worker System
- **File**: `backend/worker/convert.py`
- **Purpose**: Background worker for processing image conversions
- **Features**:
  - Continuous queue processing
  - Database integration with SQLAlchemy
  - Status tracking and updates
  - Error handling and recovery
  - Temp file cleanup
  - Conversion statistics
  - Structured logging

### 3. Enhanced Image Upload
- **File**: `backend/app/routes/images.py` (modified)
- **Changes**:
  - VHDX files automatically trigger conversion
  - Other formats marked as READY immediately
  - Background processing integration
  - New conversion endpoints

### 4. New API Endpoints
- **POST** `/images/{image_id}/convert` - Manually trigger conversion
- **GET** `/images/{image_id}/conversion-status` - Get conversion progress

### 5. Configuration Updates
- **File**: `backend/app/core/config.py` (modified)
- **Added**:
  - `IMAGE_STORAGE_PATH` - Storage for converted images
  - `TEMP_STORAGE_PATH` - Temporary file storage

### 6. System Service
- **File**: `systemd/ggnet-worker.service`
- **Purpose**: Systemd service definition for background worker
- **Features**:
  - Auto-restart on failure
  - Resource limits
  - Security hardening
  - Logging integration

### 7. Comprehensive Testing
- **File**: `backend/tests/test_image_conversion.py`
- **Coverage**:
  - API endpoint testing
  - qemu-img wrapper testing
  - Worker functionality testing
  - Error handling testing
  - Integration testing

## Technical Implementation Details

### qemu-img Integration
```python
# Example conversion command
qemu-img convert -f auto -O raw -p -S 0 input.vhdx output.img
```

**Key Features**:
- Auto-detect input format
- Sparse file creation for efficiency
- Progress reporting
- Comprehensive error handling

### Worker Architecture
```python
# Worker processes images in status PROCESSING
while True:
    pending_images = await get_pending_conversions()
    for image in pending_images:
        await convert_image(image)
```

**Key Features**:
- Continuous queue processing
- Database transaction safety
- Progress tracking
- Error recovery
- Resource cleanup

### Status Flow
1. **UPLOADING** → File being uploaded
2. **PROCESSING** → Checksum calculation, format detection
3. **CONVERTING** → qemu-img conversion in progress
4. **READY** → Conversion complete, ready for use
5. **ERROR** → Conversion failed

## API Examples

### Trigger Conversion
```bash
curl -X POST http://localhost:8000/images/123/convert \
  -H "Authorization: Bearer <token>"
```

### Check Conversion Status
```bash
curl http://localhost:8000/images/123/conversion-status \
  -H "Authorization: Bearer <token>"
```

### Upload VHDX File
```bash
curl -X POST http://localhost:8000/images/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@windows11.vhdx" \
  -F "name=Windows 11" \
  -F "image_type=system"
```

## Error Handling

### qemu-img Errors
- File not found
- Invalid format
- Insufficient disk space
- Permission denied
- Conversion timeout

### Worker Errors
- Database connection issues
- File system errors
- Memory/resource limits
- Process crashes

### Recovery Mechanisms
- Automatic retry with exponential backoff
- Error logging and notification
- Partial file cleanup
- Status rollback

## Performance Considerations

### Memory Usage
- Streaming file operations
- Chunked processing
- Memory limits in systemd service

### Disk Usage
- Sparse file creation
- Temp file cleanup
- Storage path management

### Network Impact
- Background processing
- Progress callbacks
- WebSocket notifications (future)

## Security Features

### File Validation
- Format verification
- Size limits
- Path sanitization

### Process Isolation
- Dedicated user account
- Restricted file system access
- Resource limits

### Error Information
- Sanitized error messages
- Audit logging
- No sensitive data exposure

## Dependencies

### System Requirements
- `qemu-img` binary (qemu-utils package)
- Python 3.11+
- SQLAlchemy 2.0+
- AsyncIO support

### Python Packages
- `asyncio` - Async operations
- `pathlib` - File path handling
- `structlog` - Structured logging
- `sqlalchemy` - Database operations

## Configuration

### Environment Variables
```bash
IMAGE_STORAGE_PATH=/opt/ggnet/storage/images
TEMP_STORAGE_PATH=/opt/ggnet/storage/temp
QEMU_IMG_PATH=/usr/bin/qemu-img
```

### Systemd Service
```bash
sudo systemctl enable ggnet-worker
sudo systemctl start ggnet-worker
sudo systemctl status ggnet-worker
```

## Testing

### Unit Tests
- qemu-img wrapper functionality
- Worker process logic
- API endpoint behavior
- Error handling scenarios

### Integration Tests
- End-to-end conversion workflow
- Database integration
- File system operations
- Service integration

### Manual Testing
```bash
# Test qemu-img wrapper
python backend/scripts/qemu_convert.py --info test.vhdx

# Test conversion
python backend/scripts/qemu_convert.py test.vhdx test.img

# Test worker
python -m backend.worker.convert
```

## Monitoring

### Logs
- Structured JSON logging
- Conversion progress tracking
- Error reporting
- Performance metrics

### Metrics
- Conversion success rate
- Average conversion time
- Queue length
- Resource usage

### Health Checks
- Worker process status
- Queue processing rate
- Error rate monitoring
- Storage space monitoring

## Future Enhancements

### Planned Features
- WebSocket progress updates
- Conversion priority queues
- Multiple format support
- Parallel processing
- Cloud storage integration

### Performance Optimizations
- Conversion caching
- Incremental updates
- Compression options
- Network optimization

## Rollback Instructions

### Disable Worker
```bash
sudo systemctl stop ggnet-worker
sudo systemctl disable ggnet-worker
```

### Revert Code Changes
```bash
git checkout main -- backend/app/routes/images.py
git checkout main -- backend/app/core/config.py
```

### Clean Up Files
```bash
rm -rf backend/worker/
rm -rf backend/scripts/qemu_convert.py
rm -f systemd/ggnet-worker.service
```

## Success Criteria Met

- [x] **Background worker implemented** - Continuous queue processing
- [x] **qemu-img integration** - Full wrapper with error handling
- [x] **VHDX to RAW conversion** - Automatic format conversion
- [x] **Progress tracking** - Real-time conversion status
- [x] **Error handling** - Comprehensive error recovery
- [x] **API endpoints** - Manual trigger and status checking
- [x] **Systemd service** - Production-ready service definition
- [x] **Comprehensive testing** - Unit and integration tests
- [x] **Documentation** - Complete implementation documentation

## Next Steps

Phase 2 is complete and ready for Phase 3: iSCSI Target Wrapper implementation. The image conversion system provides a solid foundation for the diskless boot workflow.
