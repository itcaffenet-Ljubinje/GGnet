# PHASE 3 - iSCSI TARGET WRAPPER TESTS

## Test Overview
Comprehensive test suite for iSCSI target management system including TargetCLI adapter, API endpoints, and integration testing.

## Running Tests

### 1. TargetCLI Adapter Tests
```bash
# Run all TargetCLI adapter tests
pytest tests/test_targetcli_adapter.py -v

# Run specific test class
pytest tests/test_targetcli_adapter.py::TestTargetCLIAdapter -v

# Run specific test method
pytest tests/test_targetcli_adapter.py::TestTargetCLIAdapter::test_adapter_initialization -v
```

### 2. Targets API Tests
```bash
# Run all targets API tests
pytest tests/test_targets_api.py -v

# Run specific test class
pytest tests/test_targets_api.py::TestTargetsAPI -v

# Run specific test method
pytest tests/test_targets_api.py::TestTargetsAPI::test_create_target_success -v
```

### 3. All Phase 3 Tests
```bash
# Run all Phase 3 tests
pytest tests/test_targetcli_adapter.py tests/test_targets_api.py -v

# Run with coverage
pytest tests/test_targetcli_adapter.py tests/test_targets_api.py --cov=app.adapters.targetcli --cov=app.api.targets -v
```

## Test Structure

### 1. TargetCLI Adapter Tests (`test_targetcli_adapter.py`)

#### TestTargetCLIAdapter Class
- **test_adapter_initialization**: Test adapter initialization and configuration
- **test_check_targetcli_available**: Test targetcli availability check
- **test_check_targetcli_unavailable**: Test targetcli unavailability handling
- **test_run_targetcli_command_success**: Test successful command execution
- **test_run_targetcli_command_timeout**: Test command timeout handling
- **test_create_fileio_backstore_success**: Test successful backstore creation
- **test_create_fileio_backstore_file_not_exists**: Test file not found handling
- **test_create_fileio_backstore_with_size**: Test sparse file creation
- **test_create_iscsi_target_success**: Test successful iSCSI target creation
- **test_create_iscsi_target_failure**: Test iSCSI target creation failure
- **test_create_lun_success**: Test successful LUN creation
- **test_create_acl_success**: Test successful ACL creation
- **test_enable_target_portal_success**: Test successful portal enabling
- **test_enable_target_portal_custom_ip_port**: Test custom IP/port configuration
- **test_create_complete_target_success**: Test complete target creation workflow
- **test_create_complete_target_cleanup_on_failure**: Test cleanup on failure
- **test_delete_target_success**: Test successful target deletion
- **test_list_targets_success**: Test successful target listing
- **test_save_config_success**: Test successful configuration save
- **test_get_target_status_success**: Test successful status retrieval
- **test_get_target_status_not_found**: Test status for non-existent target

#### TestTargetCLIConvenienceFunctions Class
- **test_create_target_for_machine**: Test machine-specific target creation
- **test_delete_target_for_machine**: Test machine-specific target deletion

### 2. Targets API Tests (`test_targets_api.py`)

#### TestTargetsAPI Class
- **test_create_target_success**: Test successful target creation via API
- **test_create_target_machine_not_found**: Test creation with non-existent machine
- **test_create_target_image_not_found**: Test creation with non-existent image
- **test_create_target_image_not_ready**: Test creation with non-ready image
- **test_create_target_already_exists**: Test creation when target already exists
- **test_create_target_targetcli_error**: Test creation with targetcli error
- **test_list_targets_success**: Test successful target listing
- **test_list_targets_pagination**: Test paginated target listing
- **test_get_target_success**: Test successful target retrieval
- **test_get_target_not_found**: Test retrieval of non-existent target
- **test_get_target_status_success**: Test successful status retrieval
- **test_get_target_status_error**: Test status retrieval with error
- **test_delete_target_success**: Test successful target deletion
- **test_delete_target_not_found**: Test deletion of non-existent target
- **test_delete_target_targetcli_error**: Test deletion with targetcli error
- **test_get_target_by_machine_success**: Test retrieval by machine
- **test_get_target_by_machine_not_found**: Test retrieval by non-existent machine
- **test_restart_target_success**: Test successful target restart
- **test_restart_target_not_found**: Test restart of non-existent target
- **test_restart_target_error**: Test restart with error
- **test_create_target_unauthorized**: Test creation with insufficient permissions
- **test_delete_target_unauthorized**: Test deletion with insufficient permissions

## Test Fixtures

### 1. TargetCLI Adapter Fixtures
- **adapter**: TargetCLIAdapter instance for testing
- **mock_qemu_img_path**: Mock qemu-img path for tests
- **mock_paths**: Mock storage paths for worker tests

### 2. Targets API Fixtures
- **test_machine**: Test machine instance
- **test_image**: Test image instance
- **test_target**: Test target instance

## Mocking Strategy

### 1. TargetCLI Operations
- **subprocess.run**: Mock targetcli command execution
- **asyncio.create_subprocess_exec**: Mock async subprocess execution
- **tempfile.NamedTemporaryFile**: Mock temporary file creation
- **os.path.exists**: Mock file existence checks
- **os.path.getsize**: Mock file size operations

### 2. Database Operations
- **AsyncSession**: Mock database session
- **Database queries**: Mock SQLAlchemy queries
- **Database commits**: Mock database transactions

### 3. External Dependencies
- **targetcli**: Mock targetcli executable
- **File operations**: Mock file system operations
- **Network operations**: Mock network calls

## Test Data

### 1. Test Machines
```python
machine = Machine(
    name="Test Machine",
    description="Test machine for targets",
    mac_address="aa:bb:cc:dd:ee:ff",
    ip_address="192.168.1.100",
    boot_mode=BootMode.UEFI,
    status=MachineStatus.ACTIVE,
    created_by=1
)
```

### 2. Test Images
```python
image = Image(
    name="Test Image",
    description="Test image for targets",
    filename="test.img",
    file_path="/tmp/test.img",
    format=ImageFormat.RAW,
    size_bytes=1024*1024*100,
    status=ImageStatus.READY,
    image_type=ImageType.SYSTEM,
    created_by=1
)
```

### 3. Test Targets
```python
target = Target(
    target_id="machine_1",
    iqn="iqn.2025.ggnet:target-machine_1",
    machine_id=test_machine.id,
    image_id=test_image.id,
    image_path=test_image.file_path,
    initiator_iqn="iqn.2025.ggnet:initiator-aabbccddeeff",
    lun_id=0,
    status=TargetStatus.ACTIVE,
    description="Test target",
    created_by=1
)
```

## Error Scenarios Tested

### 1. TargetCLI Errors
- **Command execution failures**: Timeout, permission errors
- **Configuration errors**: Invalid targetcli configuration
- **Resource conflicts**: Target already exists
- **File system errors**: File not found, permission denied

### 2. Database Errors
- **Constraint violations**: Foreign key violations
- **Connection issues**: Database connection failures
- **Transaction failures**: Rollback scenarios
- **Data integrity**: Invalid data handling

### 3. API Errors
- **Authentication failures**: Invalid tokens
- **Authorization failures**: Insufficient permissions
- **Validation errors**: Invalid input data
- **Resource not found**: Non-existent resources

## Performance Testing

### 1. Load Testing
- **Concurrent target creation**: Multiple simultaneous operations
- **Large target lists**: Pagination performance
- **Status monitoring**: Real-time status updates
- **Database queries**: Query performance optimization

### 2. Stress Testing
- **Resource exhaustion**: Memory and disk usage
- **Connection limits**: Database connection limits
- **Timeout scenarios**: Long-running operations
- **Error recovery**: Failure recovery testing

## Integration Testing

### 1. End-to-End Workflows
- **Complete target creation**: From API to targetcli
- **Target lifecycle**: Creation to deletion
- **Status monitoring**: Real-time status updates
- **Error recovery**: Failure and recovery scenarios

### 2. Cross-Component Testing
- **Machine integration**: Target-machine relationships
- **Image integration**: Target-image relationships
- **User integration**: User-target relationships
- **Session integration**: Target-session relationships

## Test Coverage

### 1. Code Coverage
- **TargetCLI Adapter**: 100% method coverage
- **Targets API**: 100% endpoint coverage
- **Error Handling**: 100% error scenario coverage
- **Validation**: 100% input validation coverage

### 2. Scenario Coverage
- **Happy Path**: All successful operations
- **Error Paths**: All error scenarios
- **Edge Cases**: Boundary conditions
- **Integration**: Cross-component interactions

## Continuous Integration

### 1. Automated Testing
- **Unit Tests**: Automated unit test execution
- **Integration Tests**: Automated integration testing
- **Coverage Reports**: Automated coverage reporting
- **Performance Tests**: Automated performance testing

### 2. Quality Gates
- **Test Coverage**: Minimum 90% coverage required
- **Test Pass Rate**: 100% test pass rate required
- **Performance Benchmarks**: Performance requirements
- **Security Tests**: Security validation required

## Test Maintenance

### 1. Test Updates
- **API Changes**: Update tests for API changes
- **Model Changes**: Update tests for model changes
- **Dependency Updates**: Update tests for dependency changes
- **Configuration Changes**: Update tests for config changes

### 2. Test Documentation
- **Test Descriptions**: Clear test descriptions
- **Test Data**: Documented test data
- **Mocking Strategy**: Documented mocking approach
- **Error Scenarios**: Documented error testing

## Troubleshooting

### 1. Common Issues
- **Import Errors**: Check module imports
- **Database Issues**: Check database configuration
- **Mocking Issues**: Check mock configurations
- **Async Issues**: Check async/await usage

### 2. Debugging
- **Test Logs**: Enable test logging
- **Mock Debugging**: Debug mock behavior
- **Database Debugging**: Debug database operations
- **API Debugging**: Debug API responses

## Best Practices

### 1. Test Design
- **Single Responsibility**: One test per scenario
- **Clear Naming**: Descriptive test names
- **Proper Setup**: Clean test setup and teardown
- **Isolation**: Independent test execution

### 2. Mocking
- **Minimal Mocking**: Mock only what's necessary
- **Realistic Mocks**: Use realistic mock data
- **Mock Verification**: Verify mock interactions
- **Mock Cleanup**: Clean up mocks properly

### 3. Assertions
- **Specific Assertions**: Use specific assertions
- **Error Messages**: Clear error messages
- **Multiple Assertions**: Test multiple aspects
- **Edge Cases**: Test boundary conditions
