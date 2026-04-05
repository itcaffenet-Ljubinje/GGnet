# CLI Tool

The CLI (Command-Line Interface) tool provides administrative commands for managing ggnet2 from the command line.

## Overview

The CLI tool provides:

- **Image Management**: Create, list, delete images
- **VM Management**: Create, start, stop VMs
- **Machine Management**: Register, list machines
- **Storage Operations**: Pool status, scrub, TRIM
- **System Administration**: Settings, configuration

## Installation

Install CLI tool:

```bash
pip install -e .
```

Or install in development mode:

```bash
pip install -e .[dev]
```

## Usage

### Basic Commands

**Help:**
```bash
ggnet2 --help
ggnet2 images --help
ggnet2 vms --help
```

**Version:**
```bash
ggnet2 --version
```

## Commands

### Image Commands

**List Images:**
```bash
ggnet2 images list
```

**Create Image:**
```bash
ggnet2 images create --name win11 --type system --size 100G
```

**Delete Image:**
```bash
ggnet2 images delete win11
```

**Create Snapshot:**
```bash
ggnet2 images snapshot win11 --name 2024-01-01
```

**List Snapshots:**
```bash
ggnet2 images snapshots win11
```

**Apply Writebacks:**
```bash
ggnet2 images writebacks win11 --apply
```

### VM Commands

**List VMs:**
```bash
ggnet2 vms list
```

**Create VM:**
```bash
ggnet2 vms create \
  --name VM-1 \
  --system-image win11 \
  --game-image games \
  --vcpus 4 \
  --ram 8G \
  --boot-mode uefi \
  --drives-connection local
```

**Start VM:**
```bash
ggnet2 vms start VM-1
```

**Stop VM:**
```bash
ggnet2 vms stop VM-1
```

**Shutdown VM:**
```bash
ggnet2 vms shutdown VM-1
```

**Reboot VM:**
```bash
ggnet2 vms reboot VM-1
```

**Delete VM:**
```bash
ggnet2 vms delete VM-1
```

**Enable VMs:**
```bash
ggnet2 vms enable
```

**Check VMs Status:**
```bash
ggnet2 vms status
```

### Machine Commands

**List Machines:**
```bash
ggnet2 machines list
```

**Register Machine:**
```bash
ggnet2 machines register \
  --mac 00:11:22:33:44:55 \
  --name PC-1 \
  --ip 192.168.1.100
```

**Wake-On-LAN:**
```bash
ggnet2 machines wol PC-1
```

**Shutdown Machine:**
```bash
ggnet2 machines shutdown PC-1
```

**Reboot Machine:**
```bash
ggnet2 machines reboot PC-1
```

**Delete Machine:**
```bash
ggnet2 machines delete PC-1
```

### Storage Commands

**Pool Status:**
```bash
ggnet2 storage pool status
```

**Pool Stats:**
```bash
ggnet2 storage pool stats
```

**Start Scrub:**
```bash
ggnet2 storage pool scrub --start
```

**Scrub Status:**
```bash
ggnet2 storage pool scrub --status
```

**ARC Stats:**
```bash
ggnet2 storage arc stats
```

**Enable Autotrim:**
```bash
ggnet2 storage trim enable
```

**Manual TRIM:**
```bash
ggnet2 storage trim manual
```

### Settings Commands

**Get Settings:**
```bash
ggnet2 settings get
```

**Set Setting:**
```bash
ggnet2 settings set --key max_vm_ram --value 64G
```

**Update Settings:**
```bash
ggnet2 settings update --file settings.json
```

## Command Structure

### Click Framework

CLI uses Click framework:

```python
import click

@click.group()
def cli():
    """ggnet2 CLI tool"""
    pass

@cli.group()
def images():
    """Image management commands"""
    pass

@images.command()
@click.option('--name', required=True, help='Image name')
@click.option('--type', required=True, type=click.Choice(['system', 'game']))
@click.option('--size', default='100G', help='Image size')
def create(name, type, size):
    """Create a new image"""
    from images.image_manager import ImageManager
    manager = ImageManager()
    image = manager.create_image(name, type, size)
    click.echo(f"Image created: {image['id']}")
```

## Examples

### Create Image and Snapshot

```bash
# Create image
ggnet2 images create --name win11 --type system --size 100G

# Create snapshot
ggnet2 images snapshot win11 --name base

# List images
ggnet2 images list
```

### Create and Manage VM

```bash
# Enable VMs
ggnet2 vms enable

# Create VM
ggnet2 vms create \
  --name VM-1 \
  --system-image win11 \
  --game-image games \
  --vcpus 4 \
  --ram 8G

# Start VM
ggnet2 vms start VM-1

# Get VM status
ggnet2 vms list
```

### Register and Manage Machine

```bash
# Register machine
ggnet2 machines register \
  --mac 00:11:22:33:44:55 \
  --name PC-1 \
  --ip 192.168.1.100

# Wake-On-LAN
ggnet2 machines wol PC-1

# Shutdown machine
ggnet2 machines shutdown PC-1
```

### Storage Operations

```bash
# Check pool status
ggnet2 storage pool status

# Start scrub
ggnet2 storage pool scrub --start

# Check ARC stats
ggnet2 storage arc stats

# Enable autotrim
ggnet2 storage trim enable
```

## Error Handling

**Common Errors:**
- **Command Not Found**: Invalid command
- **Invalid Options**: Invalid command options
- **Operation Failed**: Backend operation failed

**Error Messages:**
```bash
$ ggnet2 images create --name win11
Error: Missing option '--type'

$ ggnet2 vms start nonexistent
Error: VM 'nonexistent' not found
```

## Development Notes

- CLI uses Click framework for command parsing
- Commands map to backend API functions
- Error handling is consistent across commands
- Output formatting supports JSON and human-readable formats

## To-Do

- [ ] Add command completion (bash/zsh)
- [ ] Implement command aliases
- [ ] Add command history
- [ ] Implement command chaining
- [ ] Add command output formatting (JSON, YAML, table)
- [ ] Implement command logging

