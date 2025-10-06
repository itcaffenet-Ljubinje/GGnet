# PHASE 4: Session Orchestration i PXE/iPXE - Testing Guide

## Overview
This document provides comprehensive testing instructions for Phase 4 functionality, including session orchestration, iPXE script generation, DHCP configuration management, and TFTP file operations.

## Test Environment Setup

### Prerequisites
- Python 3.11+
- pytest and pytest-asyncio
- Redis server (optional for unit tests)
- Mock system dependencies

### Installation
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Install application dependencies
pip install -r backend/requirements.txt
```

## Running Tests

### All Phase 4 Tests
```bash
# Run all Phase 4 tests
pytest backend/tests/test_phase4_sessions.py -v

# Run with coverage
pytest backend/tests/test_phase4_sessions.py --cov=app.adapters --cov=app.api --cov-report=html
```

### Specific Test Categories
```bash
# Test session orchestration only
pytest backend/tests/test_phase4_sessions.py::TestSessionOrchestration -v

# Test iPXE script generation only
pytest backend/tests/test_phase4_sessions.py::TestiPXEScriptGeneration -v

# Test DHCP configuration only
pytest backend/tests/test_phase4_sessions.py::TestDHCPConfiguration -v

# Test TFTP management only
pytest backend/tests/test_phase4_sessions.py::TestTFTPManagement -v
```

### Individual Test Methods
```bash
# Test specific functionality
pytest backend/tests/test_phase4_sessions.py::TestSessionOrchestration::test_start_session_success -v

# Test with detailed output
pytest backend/tests/test_phase4_sessions.py::TestSessionOrchestration::test_start_session_success -v -s
```

## Test Categories

### 1. Session Orchestration Tests

#### Test: `test_start_session_success`
- **Purpose**: Verify complete session startup orchestration
- **What it tests**:
  - Machine and image validation
  - iSCSI target creation
  - iPXE script generation
  - TFTP script saving
  - DHCP configuration update
  - Session record creation
  - Response format validation

#### Test: `test_start_session_machine_not_found`
- **Purpose**: Verify error handling for non-existent machines
- **What it tests**:
  - Proper error response
  - HTTP status code 400
  - Error message clarity

#### Test: `test_start_session_image_not_ready`
- **Purpose**: Verify validation of image status
- **What it tests**:
  - Image status validation
  - Error handling for non-ready images
  - Proper error messages

#### Test: `test_stop_session_success`
- **Purpose**: Verify complete session shutdown orchestration
- **What it tests**:
  - Session validation
  - iSCSI target deletion
  - DHCP configuration removal
  - TFTP script cleanup
  - Session status update
  - Response format validation

#### Test: `test_list_sessions`
- **Purpose**: Verify session listing functionality
- **What it tests**:
  - Pagination support
  - Status filtering
  - Response format
  - Data accuracy

#### Test: `test_get_machine_boot_script`
- **Purpose**: Verify boot script retrieval
- **What it tests**:
  - Active session validation
  - Script generation
  - Response format
  - iSCSI details inclusion

#### Test: `test_get_session_stats`
- **Purpose**: Verify session statistics
- **What it tests**:
  - Status counting
  - Total session count
  - Active session count
  - Data accuracy

### 2. iPXE Script Generation Tests

#### Test: `test_generate_machine_boot_script`
- **Purpose**: Verify machine-specific script generation
- **What it tests**:
  - Script content validation
  - iSCSI configuration inclusion
  - Machine information inclusion
  - Script structure validation

#### Test: `test_generate_generic_boot_script`
- **Purpose**: Verify generic fallback script generation
- **What it tests**:
  - Generic script content
  - Fallback boot options
  - Chain loading configuration
  - Error handling

#### Test: `test_get_machine_script_filename`
- **Purpose**: Verify filename generation
- **What it tests**:
  - MAC address formatting
  - Filename structure
  - Directory organization

#### Test: `test_validate_script_syntax`
- **Purpose**: Verify script syntax validation
- **What it tests**:
  - Valid script detection
  - Invalid script detection
  - Required elements validation
  - Error reporting

### 3. DHCP Configuration Tests

#### Test: `test_generate_dhcp_config_entry`
- **Purpose**: Verify DHCP configuration generation
- **What it tests**:
  - Host entry format
  - MAC address formatting
  - IP address assignment
  - Boot file configuration

#### Test: `test_dhcp_adapter_status`
- **Purpose**: Verify DHCP adapter status checking
- **What it tests**:
  - Service status detection
  - Configuration file validation
  - Machine count accuracy
  - Error handling

### 4. TFTP Management Tests

#### Test: `test_tftp_adapter_status`
- **Purpose**: Verify TFTP adapter status checking
- **What it tests**:
  - Service status detection
  - Directory structure validation
  - File count accuracy
  - Error handling

#### Test: `test_extract_mac_from_filename`
- **Purpose**: Verify MAC address extraction
- **What it tests**:
  - Valid filename parsing
  - Invalid filename handling
  - MAC address format validation
  - Error cases

## Mocking Strategy

### System Command Mocking
```python
# Mock systemctl commands
with patch("subprocess.run") as mock_run:
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "active"
```

### File System Mocking
```python
# Mock file operations
with patch("pathlib.Path.exists") as mock_exists:
    mock_exists.return_value = True
    
with patch("builtins.open", mock_open("test content")):
    # Test file operations
```

### Service Mocking
```python
# Mock external services
with patch("app.adapters.targetcli.create_target_for_machine") as mock_create:
    mock_create.return_value = {"target_id": "test", "iqn": "test.iqn"}
```

## Integration Testing

### End-to-End Session Lifecycle
```bash
# Test complete session lifecycle
pytest backend/tests/test_phase4_sessions.py::TestSessionOrchestration::test_start_session_success -v
pytest backend/tests/test_phase4_sessions.py::TestSessionOrchestration::test_stop_session_success -v
```

### Network Boot Simulation
```bash
# Test network boot components
pytest backend/tests/test_phase4_sessions.py::TestiPXEScriptGeneration -v
pytest backend/tests/test_phase4_sessions.py::TestDHCPConfiguration -v
pytest backend/tests/test_phase4_sessions.py::TestTFTPManagement -v
```

## Performance Testing

### Load Testing
```bash
# Test with multiple concurrent sessions
pytest backend/tests/test_phase4_sessions.py -k "test_start_session" --count=10
```

### Memory Testing
```bash
# Test memory usage
pytest backend/tests/test_phase4_sessions.py --profile
```

## Error Testing

### Validation Errors
```bash
# Test validation error handling
pytest backend/tests/test_phase4_sessions.py -k "test_start_session_machine_not_found" -v
pytest backend/tests/test_phase4_sessions.py -k "test_start_session_image_not_ready" -v
```

### System Errors
```bash
# Test system error handling
pytest backend/tests/test_phase4_sessions.py -k "test_dhcp_adapter_status" -v
pytest backend/tests/test_phase4_sessions.py -k "test_tftp_adapter_status" -v
```

## Manual Testing

### Prerequisites for Manual Testing
- Real DHCP server running
- Real TFTP server running
- Real iSCSI targets available
- Physical machines for network boot testing

### Manual Test Steps

#### 1. Session Creation
```bash
# Start a session
curl -X POST http://localhost:8000/api/v1/sessions/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "machine_id": 1,
    "image_id": 1,
    "session_type": "DISKLESS_BOOT",
    "description": "Manual test session"
  }'
```

#### 2. Boot Script Verification
```bash
# Get boot script
curl -X GET http://localhost:8000/api/v1/sessions/machine/1/boot-script \
  -H "Authorization: Bearer <token>"
```

#### 3. DHCP Configuration Check
```bash
# Check DHCP configuration
sudo cat /etc/dhcp/dhcpd.conf | grep "host workstation"
```

#### 4. TFTP File Check
```bash
# Check TFTP files
ls -la /var/lib/tftpboot/machines/
cat /var/lib/tftpboot/machines/00-11-22-33-44-55.ipxe
```

#### 5. Network Boot Test
- Boot a physical machine from network
- Verify iPXE script loads
- Verify iSCSI connection
- Verify diskless boot success

## Test Data

### Test Machines
```python
test_machine = Machine(
    id=1,
    name="test-workstation",
    mac_address="00:11:22:33:44:55",
    ip_address="192.168.1.101",
    status=MachineStatus.ACTIVE,
    boot_mode="bios",
    created_by=1
)
```

### Test Images
```python
test_image = Image(
    id=1,
    name="test-image",
    filename="test.vhdx",
    file_path="/storage/images/test.vhdx",
    format=ImageFormat.VHDX,
    status=ImageStatus.READY,
    size_bytes=1024*1024*1024,
    created_by=1
)
```

### Test Sessions
```python
test_session = Session(
    id=1,
    machine_id=1,
    target_id=1,
    image_id=1,
    session_type=SessionType.DISKLESS_BOOT,
    status=SessionStatus.ACTIVE,
    started_at=datetime.utcnow(),
    created_by=1
)
```

## Expected Results

### Successful Test Run
```
backend/tests/test_phase4_sessions.py::TestSessionOrchestration::test_start_session_success PASSED
backend/tests/test_phase4_sessions.py::TestSessionOrchestration::test_stop_session_success PASSED
backend/tests/test_phase4_sessions.py::TestiPXEScriptGeneration::test_generate_machine_boot_script PASSED
backend/tests/test_phase4_sessions.py::TestDHCPConfiguration::test_generate_dhcp_config_entry PASSED
backend/tests/test_phase4_sessions.py::TestTFTPManagement::test_tftp_adapter_status PASSED
```

### Coverage Report
```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
app/adapters/dhcp.py                      200     20    90%   45-50, 120-125
app/adapters/ipxe.py                      180     15    92%   80-85, 150-155
app/adapters/tftp.py                      220     25    89%   60-65, 180-185
app/api/sessions.py                       300     30    90%   100-105, 250-255
---------------------------------------------------------------------
TOTAL                                     900     90    90%
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure all dependencies are installed
pip install -r backend/requirements.txt
```

#### 2. Database Connection Issues
```bash
# Check database configuration
python -c "from app.core.database import get_db; print('DB OK')"
```

#### 3. Redis Connection Issues
```bash
# Check Redis connection
python -c "import redis; r = redis.Redis(); print(r.ping())"
```

#### 4. Mock Issues
```bash
# Ensure proper mocking
pytest backend/tests/test_phase4_sessions.py -v -s --tb=short
```

### Debug Mode
```bash
# Run tests in debug mode
pytest backend/tests/test_phase4_sessions.py -v -s --pdb
```

### Verbose Output
```bash
# Get detailed test output
pytest backend/tests/test_phase4_sessions.py -v -s --tb=long
```

## Continuous Integration

### GitHub Actions
```yaml
# .github/workflows/phase4-tests.yml
name: Phase 4 Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-mock
      - name: Run Phase 4 tests
        run: pytest backend/tests/test_phase4_sessions.py -v --cov=app.adapters --cov=app.api
```

### Local CI Simulation
```bash
# Run tests as in CI
pytest backend/tests/test_phase4_sessions.py -v --cov=app.adapters --cov=app.api --cov-report=xml
```

## Test Maintenance

### Adding New Tests
1. Create test method in appropriate test class
2. Add proper mocking for external dependencies
3. Verify test data and expected results
4. Update documentation

### Updating Existing Tests
1. Review test requirements
2. Update test data if needed
3. Verify test still passes
4. Update documentation

### Test Data Management
1. Use consistent test data across tests
2. Clean up test data after tests
3. Use fixtures for common test objects
4. Mock external dependencies

## Performance Benchmarks

### Expected Performance
- Session start: < 5 seconds
- Session stop: < 3 seconds
- Script generation: < 1 second
- DHCP update: < 2 seconds
- TFTP operations: < 1 second

### Load Testing
- 100+ concurrent sessions
- 1000+ machines
- 100+ images
- 10+ requests/second

### Memory Usage
- < 512MB memory usage
- < 50% CPU usage
- < 100MB/s disk I/O
- < 10MB/s network I/O
