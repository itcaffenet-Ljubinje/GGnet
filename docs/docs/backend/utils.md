# Utilities Module

The Utilities module provides shared utilities and helpers used across all backend modules.

## Overview

The Utils module provides:

- **ZFS Parser**: Parsing ZFS command outputs
- **Command Executor**: Shell command execution wrapper
- **Logger**: Logging utilities

## Components

### ZFS Parser (`zfs_parser.py`)

Parses ZFS command outputs into structured data.

**Key Functions:**
- `parse_zfs_list(output)`: Parse `zfs list` output
- `parse_zpool_status(output)`: Parse `zpool status` output
- `parse_zpool_get(output)`: Parse `zpool get` output
- `parse_zfs_get(output)`: Parse `zfs get` output
- `parse_zpool_iostat(output)`: Parse `zpool iostat` output
- `parse_arcstats(content)`: Parse ARC statistics from `/proc/spl/kstat/zfs/arcstats`

**ZFS List Output:**
```
NAME                              USED  AVAIL     REFER  MOUNTPOINT
pool0/ggnet2/images/win11         50G   950G     50G    -
pool0/ggnet2/images/games         100G  900G     100G   -
```

**Parsed Output:**
```python
[
    {
        "name": "pool0/ggnet2/images/win11",
        "used": "50G",
        "avail": "950G",
        "refer": "50G",
        "mountpoint": "-",
        "type": "volume"
    },
    {
        "name": "pool0/ggnet2/images/games",
        "used": "100G",
        "avail": "900G",
        "refer": "100G",
        "mountpoint": "-",
        "type": "volume"
    }
]
```

**Example:**
```python
from utils.zfs_parser import ZFSParser
from utils.command_executor import CommandExecutor

parser = ZFSParser()
executor = CommandExecutor()

# Execute zfs list
output = executor.execute(["zfs", "list", "-t", "volume", "-r", "pool0/ggnet2/images"])

# Parse output
volumes = parser.parse_zfs_list(output)
```

### Command Executor (`command_executor.py`)

Wrapper for shell command execution with error handling.

**Key Functions:**
- `execute(command, timeout=None)`: Execute shell command
- `execute_safe(command, timeout=None)`: Execute command with error handling
- `execute_background(command)`: Execute command in background

**Command Execution:**
```python
from utils.command_executor import CommandExecutor

executor = CommandExecutor()

# Execute command
result = executor.execute(["zfs", "list", "-t", "volume"])

# Result structure
{
    "success": True,
    "returncode": 0,
    "stdout": "NAME                              USED  AVAIL...",
    "stderr": "",
    "command": ["zfs", "list", "-t", "volume"]
}
```

**Error Handling:**
```python
try:
    result = executor.execute(["zfs", "list", "nonexistent"])
except CommandExecutionError as e:
    logger.error(f"Command failed: {e}")
    # result = {
    #     "success": False,
    #     "returncode": 1,
    #     "stdout": "",
    #     "stderr": "dataset does not exist",
    #     "command": ["zfs", "list", "nonexistent"]
    # }
```

### Logger (`logger.py`)

Logging utilities for consistent logging across modules.

**Key Functions:**
- `setup_logging(level, log_file)`: Setup logging configuration
- `get_logger(name)`: Get logger instance for module

**Logging Configuration:**
```python
from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(
    level="INFO",
    log_file="/var/log/ggnet2/ggnet2.log"
)

# Get logger
logger = get_logger(__name__)
logger.info("Module initialized")
logger.error("Error occurred")
logger.debug("Debug information")
```

**Log Format:**
```
2024-01-01 12:00:00,123 - INFO - images.image_manager - Image created: win11
2024-01-01 12:00:01,456 - ERROR - machines.vm_manager - VM creation failed: Insufficient resources
2024-01-01 12:00:02,789 - DEBUG - storage.zfs_pool_manager - Pool status: online
```

## Usage Examples

### ZFS Parser

**Parse ZFS List:**
```python
from utils.zfs_parser import ZFSParser

parser = ZFSParser()
output = """
NAME                              USED  AVAIL     REFER  MOUNTPOINT
pool0/ggnet2/images/win11         50G   950G     50G    -
"""
volumes = parser.parse_zfs_list(output)
```

**Parse ZPool Status:**
```python
output = """
  pool: pool0
 state: ONLINE
  scan: scrub in progress since Mon Jan 1 12:00:00 2024
config:

        NAME        STATE     READ WRITE CKSUM
        pool0       ONLINE       0     0     0
          sda       ONLINE       0     0     0

errors: No known data errors
"""
status = parser.parse_zpool_status(output)
```

### Command Executor

**Execute Command:**
```python
from utils.command_executor import CommandExecutor

executor = CommandExecutor()
result = executor.execute(["zfs", "snapshot", "pool0/ggnet2/images/win11@base"])

if result["success"]:
    print("Snapshot created")
else:
    print(f"Error: {result['stderr']}")
```

**Execute with Timeout:**
```python
result = executor.execute(
    ["zpool", "scrub", "pool0"],
    timeout=3600  # 1 hour timeout
)
```

**Execute Background:**
```python
process = executor.execute_background(["long_running_command"])
# Process runs in background
```

### Logger

**Setup Logging:**
```python
from utils.logger import setup_logging, get_logger

setup_logging(
    level="INFO",
    log_file="/var/log/ggnet2/ggnet2.log"
)

logger = get_logger("images.image_manager")
logger.info("Image manager initialized")
```

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical error messages

## Integration

All modules use utilities:

```python
# Images module
from utils.command_executor import CommandExecutor
from utils.zfs_parser import ZFSParser
from utils.logger import get_logger

executor = CommandExecutor()
parser = ZFSParser()
logger = get_logger(__name__)

# Execute ZFS command
result = executor.execute(["zfs", "list", "-t", "volume"])
volumes = parser.parse_zfs_list(result["stdout"])
logger.info(f"Found {len(volumes)} volumes")
```

## Error Handling

**Command Execution Errors:**
```python
from utils.command_executor import CommandExecutionError

try:
    result = executor.execute(["invalid", "command"])
except CommandExecutionError as e:
    logger.error(f"Command execution failed: {e}")
```

**Parsing Errors:**
```python
from utils.zfs_parser import ZFSParseError

try:
    volumes = parser.parse_zfs_list(invalid_output)
except ZFSParseError as e:
    logger.error(f"ZFS parsing failed: {e}")
```

## Development Notes

- All ZFS operations use command executor for consistency
- Command outputs are parsed using ZFS parser
- Logging is centralized for easy debugging
- Command execution includes timeout handling
- Background execution supports long-running processes

## To-Do

- [ ] Add command caching for frequently executed commands
- [ ] Implement command retry logic
- [ ] Add command execution metrics
- [ ] Implement structured logging (JSON)
- [ ] Add log rotation support
- [ ] Implement log aggregation

