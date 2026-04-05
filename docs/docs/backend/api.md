# Backend API Documentation

The ggnet2 backend provides a REST API via FastAPI and real-time communication via WebSocket/SignalR.

## API Structure

### Base URL

- **Development**: `http://localhost:8000`
- **Production**: Configured via environment variables

### API Versioning

All endpoints are prefixed with `/api/v1/` (or `/api/` for current version).

## Authentication

Currently, authentication is not implemented. Future versions will include:

- JWT token-based authentication
- API key authentication
- Role-based access control (RBAC)

## Endpoints

### Image Management

**Base Path**: `/api/images`

#### List Images
```
GET /api/images
```

**Response:**
```json
{
  "images": [
    {
      "id": "win11",
      "name": "Windows 11",
      "type": "system",
      "size": "100G",
      "snapshots": ["@base", "@2024-01-01"],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Get Image Details
```
GET /api/images/{image_id}
```

#### Create Image
```
POST /api/images
```

**Request Body:**
```json
{
  "name": "win11",
  "type": "system",
  "size": "100G"
}
```

#### Delete Image
```
DELETE /api/images/{image_id}
```

#### Create Snapshot
```
POST /api/images/{image_id}/snapshots
```

**Request Body:**
```json
{
  "name": "2024-01-01",
  "description": "Monthly snapshot"
}
```

#### Apply Writebacks
```
POST /api/images/{image_id}/writebacks
```

### Virtual Machine Management

**Base Path**: `/api/vms`

#### Check VM Status
```
GET /api/vms/enabled
```

**Response:**
```json
{
  "enabled": true,
  "prerequisites": {
    "virtualization": true,
    "libvirt": true,
    "static_ip": true
  }
}
```

#### Enable VMs
```
POST /api/vms/enable
```

**Response:**
```json
{
  "enabled": true,
  "message": "Virtual Machines enabled successfully"
}
```

#### List VMs
```
GET /api/vms
```

**Response:**
```json
{
  "vms": [
    {
      "id": "vm-001",
      "name": "VM-1",
      "status": "running",
      "system_image": "win11",
      "game_image": "games",
      "vcpus": 4,
      "ram": "8G",
      "boot_mode": "uefi",
      "drives_connection": "local"
    }
  ]
}
```

#### Create VM
```
POST /api/vms
```

**Request Body:**
```json
{
  "name": "VM-1",
  "system_image": "win11",
  "game_image": "games",
  "vcpus": 4,
  "ram": "8G",
  "boot_mode": "uefi",
  "drives_connection": "local"
}
```

#### Get VM Details
```
GET /api/vms/{vm_id}
```

#### Update VM
```
PUT /api/vms/{vm_id}
```

**Request Body:**
```json
{
  "name": "VM-1-Updated",
  "vcpus": 8,
  "ram": "16G"
}
```

#### Delete VM
```
DELETE /api/vms/{vm_id}
```

#### Start VM
```
POST /api/vms/{vm_id}/start
```

#### Stop VM (Force)
```
POST /api/vms/{vm_id}/stop
```

#### Shutdown VM (Graceful)
```
POST /api/vms/{vm_id}/shutdown
```

#### Reboot VM
```
POST /api/vms/{vm_id}/reboot
```

#### Reset VM
```
POST /api/vms/{vm_id}/reset
```

#### Get VM Control Data
```
GET /api/vms/{vm_id}/control
```

**Response:**
```json
{
  "vm_id": "vm-001",
  "status": "running",
  "vnc_url": "ws://localhost:6080/vnc.html?host=localhost&port=5900",
  "vnc_password": "generated_password"
}
```

#### Get VNC Connection Details
```
GET /api/vms/{vm_id}/vnc
```

**Response:**
```json
{
  "host": "localhost",
  "port": 5900,
  "password": "generated_password",
  "websocket_url": "ws://localhost:6080/vnc.html"
}
```

#### Apply Writebacks
```
POST /api/vms/{vm_id}/writebacks
```

### Physical Machine Management

**Base Path**: `/api/machines`

#### List Machines
```
GET /api/machines
```

**Query Parameters:**
- `type`: Filter by type (`physical` or `virtual`)
- `status`: Filter by status (`online`, `offline`, `unknown`)

**Response:**
```json
{
  "machines": [
    {
      "id": "machine-001",
      "name": "PC-1",
      "type": "physical",
      "status": "online",
      "ip": "192.168.1.100",
      "mac": "00:11:22:33:44:55",
      "system_image": "win11",
      "game_image": "games",
      "uptime": "02:30:45",
      "sent": "50G",
      "received": "5G",
      "speed": "100Mbps",
      "link_speed": "1Gbps"
    }
  ]
}
```

#### Get Machine Details
```
GET /api/machines/{machine_id}
```

#### Update Machine
```
PUT /api/machines/{machine_id}
```

#### Delete Machine
```
DELETE /api/machines/{machine_id}
```

#### Turn On Machine (Wake-On-LAN)
```
POST /api/machines/{machine_id}/turn-on
```

#### Shutdown Machine
```
POST /api/machines/{machine_id}/shutdown
```

#### Reboot Machine
```
POST /api/machines/{machine_id}/reboot
```

#### Apply Writebacks
```
POST /api/machines/{machine_id}/writebacks
```

#### Bulk Operations
```
POST /api/machines/bulk
```

**Request Body:**
```json
{
  "machine_ids": ["machine-001", "machine-002"],
  "action": "reboot"
}
```

#### Bulk Settings Update
```
PUT /api/machines/bulk
```

**Request Body:**
```json
{
  "machine_ids": ["machine-001", "machine-002"],
  "settings": {
    "system_image": "win11-updated",
    "game_image": "games-updated"
  }
}
```

#### Force Sync with ggLeap
```
POST /api/machines/sync
```

#### Get Real-time Status
```
GET /api/machines/{machine_id}/status
```

**Response (SSE):**
```
data: {"status": "online", "uptime": "02:30:45", "speed": "100Mbps"}

data: {"status": "online", "uptime": "02:30:46", "speed": "100Mbps"}

...
```

### Storage/Array Management

**Base Path**: `/api/array`

#### Create Pool
```
POST /api/array/pool
```

**Request Body:**
```json
{
  "pool_name": "pool0",
  "devices": ["/dev/sda", "/dev/sdb"],
  "topology": "stripe"  // or "mirror", "raidz", "raidz2", "raidz3"
}
```

**Response:**
```json
{
  "pool_name": "pool0",
  "status": "online",
  "size": "10T",
  "allocated": "0",
  "free": "10T",
  "health": "healthy",
  "topology": {
    "type": "stripe",
    "vdevs": [
      {
        "name": "sda",
        "size": "5T",
        "status": "online"
      },
      {
        "name": "sdb",
        "size": "5T",
        "status": "online"
      }
    ]
  }
}
```

**Note:** Pool can be created either during installation (via setup script) or later via this web interface endpoint. The web interface provides more control over pool configuration.

#### Import Pool
```
POST /api/array/pool/import
```

**Request Body:**
```json
{
  "pool_name": "pool0"
}
```

**Response:**
```json
{
  "pool_name": "pool0",
  "status": "imported",
  "message": "Pool imported successfully"
}
```

#### Get Pool Status
```
GET /api/array/pool
```

**Response:**
```json
{
  "pool_name": "pool0",
  "status": "online",
  "size": "10T",
  "allocated": "5T",
  "free": "5T",
  "health": "healthy",
  "topology": {
    "type": "stripe",
    "vdevs": [
      {
        "name": "sda",
        "size": "10T",
        "status": "online"
      }
    ]
  }
}
```

#### Get Pool Stats
```
GET /api/array/pool/stats
```

#### Start Scrub
```
POST /api/array/pool/scrub
```

#### Get ARC Stats
```
GET /api/array/arc/stats
```

**Response:**
```json
{
  "available": true,
  "method": "procfs",
  "hits": 1000000,
  "misses": 50000,
  "hit_rate": 0.95,
  "size": "2G",
  "max_size": "4G"
}
```

#### Enable Autotrim
```
POST /api/array/trim/enable
```

#### Manual TRIM
```
POST /api/array/trim/manual
```

### Client Management

**Base Path**: `/api/clients`

#### List Clients
```
GET /api/clients
```

#### Register Client
```
POST /api/clients
```

**Request Body:**
```json
{
  "name": "PC-1",
  "mac": "00:11:22:33:44:55",
  "ip": "192.168.1.100"
}
```

#### Get Client Details
```
GET /api/clients/{client_id}
```

#### Update Client
```
PUT /api/clients/{client_id}
```

#### Delete Client
```
DELETE /api/clients/{client_id}
```

#### Generate Registry Script
```
POST /api/clients/{client_id}/registry-script
```

**Request Body:**
```json
{
  "script_type": "install",
  "computer_name": "PC-1",
  "server_url": "http://server:8000",
  "client_id": "client-uuid"
}
```

**Response:**
```
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\ggnet2]
"ServerURL"="http://server:8000"
"ClientID"="client-uuid"
...
```

### Settings

**Base Path**: `/api/settings`

#### Get Settings
```
GET /api/settings
```

#### Update Settings
```
PUT /api/settings
```

**Request Body:**
```json
{
  "pool_name": "pool0",
  "default_volume_size": "100G",
  "autotrim": true,
  "max_vm_ram": "32G",
  "pxe_enabled": true
}
```

## WebSocket/SignalR Hub

### Connection

**Endpoint**: `/hubs/clients`

**Connection URL:**
```
ws://localhost:8000/hubs/clients
```

### Client Events

#### Register Client
```json
{
  "event": "register",
  "data": {
    "name": "PC-1",
    "mac": "00:11:22:33:44:55",
    "ip": "192.168.1.100",
    "client_id": "client-uuid"
  }
}
```

#### Send Status
```json
{
  "event": "status",
  "data": {
    "client_id": "client-uuid",
    "status": "online",
    "uptime": "02:30:45",
    "speed": "100Mbps"
  }
}
```

#### Heartbeat
```json
{
  "event": "heartbeat",
  "data": {
    "client_id": "client-uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Server Events

#### Command
```json
{
  "event": "command",
  "data": {
    "client_id": "client-uuid",
    "command": "rename_pc",
    "params": {
      "new_name": "PC-1-Updated"
    }
  }
}
```

#### Broadcast
```json
{
  "event": "broadcast",
  "data": {
    "message": "System maintenance in 5 minutes"
  }
}
```

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

**Common Error Codes:**
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `409`: Conflict
- `500`: Internal Server Error

## Rate Limiting

Rate limiting is not currently implemented. Future versions will include:

- Per-IP rate limiting
- Per-endpoint rate limiting
- Token-based rate limiting

## Development Notes

- All endpoints use Pydantic models for request/response validation
- Error handling is centralized in exception handlers
- Logging is implemented for all API requests
- CORS is configured for frontend access

## To-Do

- [ ] Implement JWT authentication
- [ ] Add API versioning
- [ ] Implement rate limiting
- [ ] Add request/response compression
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Implement request caching
- [ ] Add metrics collection

