# GGnet Diskless Server - API Documentation

## Overview

The GGnet Diskless Server provides a comprehensive REST API for managing diskless boot infrastructure. This document covers all available endpoints, authentication, and usage examples.

## Base URL

```
http://your-server/api
```

## Authentication

The API uses JWT (JSON Web Token) authentication with access and refresh tokens.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Tokens

Include the access token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Endpoints

### Authentication

#### POST /auth/login
Authenticate user and receive tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

#### POST /auth/logout
Logout user (invalidate tokens).

#### GET /auth/me
Get current user information.

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@ggnet.local",
  "full_name": "System Administrator",
  "role": "admin",
  "status": "active",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-01-01T12:00:00Z"
}
```

### Images

#### GET /images
List all disk images.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100)
- `image_type` (string): Filter by image type (system, game, data, template)
- `status` (string): Filter by status (uploading, processing, ready, error)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Windows 11 Pro",
    "description": "Windows 11 Professional Edition",
    "filename": "win11pro.vhdx",
    "format": "vhdx",
    "size_bytes": 10737418240,
    "virtual_size_bytes": 53687091200,
    "status": "ready",
    "image_type": "system",
    "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "created_at": "2025-01-01T00:00:00Z",
    "created_by_username": "admin"
  }
]
```

#### POST /images/upload
Upload a new disk image.

**Request:** Multipart form data
- `file`: Image file (VHD, VHDX, RAW, QCOW2, etc.)
- `name`: Image name
- `description`: Optional description
- `image_type`: Image type (system, game, data, template)

#### GET /images/{id}
Get specific image details.

#### PUT /images/{id}
Update image metadata.

**Request Body:**
```json
{
  "name": "Updated Image Name",
  "description": "Updated description",
  "image_type": "system"
}
```

#### DELETE /images/{id}
Delete an image.

### Machines

#### GET /machines
List all client machines.

**Query Parameters:**
- `skip`, `limit`: Pagination
- `status`: Filter by status (active, inactive, maintenance, retired)
- `location`: Filter by location
- `room`: Filter by room

**Response:**
```json
[
  {
    "id": 1,
    "name": "LAB-PC-01",
    "description": "Laboratory Computer 01",
    "mac_address": "00:11:22:33:44:55",
    "ip_address": "192.168.1.101",
    "hostname": "lab-pc-01",
    "boot_mode": "uefi",
    "secure_boot_enabled": true,
    "status": "active",
    "is_online": false,
    "location": "Computer Lab",
    "room": "Room 101",
    "asset_tag": "LAB001",
    "created_at": "2025-01-01T00:00:00Z",
    "last_seen": null,
    "last_boot": null,
    "boot_count": 0
  }
]
```

#### POST /machines
Create a new machine.

**Request Body:**
```json
{
  "name": "LAB-PC-02",
  "description": "Laboratory Computer 02",
  "mac_address": "00:11:22:33:44:56",
  "ip_address": "192.168.1.102",
  "hostname": "lab-pc-02",
  "boot_mode": "uefi",
  "secure_boot_enabled": true,
  "location": "Computer Lab",
  "room": "Room 101",
  "asset_tag": "LAB002"
}
```

#### GET /machines/{id}
Get specific machine details.

#### PUT /machines/{id}
Update machine information.

#### DELETE /machines/{id}
Delete a machine.

### Targets

#### GET /targets
List all iSCSI targets.

**Query Parameters:**
- `skip`, `limit`: Pagination
- `machine_id`: Filter by machine
- `status`: Filter by status

**Response:**
```json
[
  {
    "id": 1,
    "name": "LAB-PC-01-Target",
    "description": "Target for LAB-PC-01",
    "iqn": "iqn.2025.ggnet:lab-pc-01",
    "portal_ip": "192.168.1.100",
    "portal_port": 3260,
    "target_type": "system_game",
    "status": "active",
    "machine_id": 1,
    "machine_name": "LAB-PC-01",
    "system_image_id": 1,
    "system_image_name": "Windows 11 Pro",
    "extra_disk_image_id": 2,
    "extra_disk_image_name": "Games Disk",
    "extra_disk_mountpoint": "D:",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

#### POST /targets
Create a new iSCSI target.

**Request Body:**
```json
{
  "name": "LAB-PC-02-Target",
  "description": "Target for LAB-PC-02",
  "machine_id": 2,
  "system_image_id": 1,
  "extra_disk_image_id": 2,
  "extra_disk_mountpoint": "D:",
  "target_type": "system_game"
}
```

#### GET /targets/{id}
Get specific target details.

#### DELETE /targets/{id}
Delete a target.

### Sessions

#### GET /sessions
List all boot sessions.

**Query Parameters:**
- `skip`, `limit`: Pagination
- `status`: Filter by status (starting, active, stopping, stopped, error)
- `machine_id`: Filter by machine

**Response:**
```json
[
  {
    "id": 1,
    "session_id": "session_a1b2c3d4",
    "session_type": "diskless_boot",
    "status": "active",
    "machine_id": 1,
    "machine_name": "LAB-PC-01",
    "target_id": 1,
    "target_name": "LAB-PC-01-Target",
    "client_ip": "192.168.1.101",
    "server_ip": "192.168.1.100",
    "boot_method": "uefi",
    "started_at": "2025-01-01T12:00:00Z",
    "ended_at": null,
    "duration_seconds": 3600,
    "iscsi_info": {
      "portal": "192.168.1.100:3260",
      "iqn": "iqn.2025.ggnet:lab-pc-01",
      "lun_mapping": {
        "0": {
          "image_id": 1,
          "mountpoint": "C:",
          "type": "system"
        },
        "1": {
          "image_id": 2,
          "mountpoint": "D:",
          "type": "data"
        }
      }
    }
  }
]
```

#### POST /sessions/start
Start a new boot session.

**Request Body:**
```json
{
  "target_id": 1,
  "session_type": "diskless_boot",
  "boot_method": "uefi"
}
```

#### GET /sessions/{session_id}/status
Get session status.

#### POST /sessions/{session_id}/stop
Stop a running session.

### Storage

#### GET /storage/info
Get storage usage information.

**Response:**
```json
{
  "upload_storage": {
    "path": "/var/lib/ggnet/uploads",
    "total_bytes": 107374182400,
    "used_bytes": 21474836480,
    "free_bytes": 85899345920,
    "total_gb": 100.0,
    "used_gb": 20.0,
    "free_gb": 80.0,
    "usage_percent": 20.0
  },
  "images_storage": {
    "path": "/var/lib/ggnet/images",
    "total_bytes": 1073741824000,
    "used_bytes": 214748364800,
    "free_bytes": 858993459200,
    "total_gb": 1000.0,
    "used_gb": 200.0,
    "free_gb": 800.0,
    "usage_percent": 20.0
  },
  "system_storage": {
    "path": "/",
    "total_bytes": 214748364800,
    "used_bytes": 107374182400,
    "free_bytes": 107374182400,
    "total_gb": 200.0,
    "used_gb": 100.0,
    "free_gb": 100.0,
    "usage_percent": 50.0
  }
}
```

#### GET /storage/health
Check storage health status.

#### POST /storage/cleanup
Clean up temporary and orphaned files.

### Health

#### GET /health
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "service": "ggnet-diskless-server",
  "version": "1.0.0"
}
```

#### GET /health/detailed
Detailed health check with system information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "service": "ggnet-diskless-server",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "error": null
    },
    "directories": {
      "/var/lib/ggnet/uploads": {
        "exists": true,
        "writable": true,
        "status": "healthy"
      },
      "/var/lib/ggnet/images": {
        "exists": true,
        "writable": true,
        "status": "healthy"
      }
    },
    "system": {
      "cpu_percent": 15.2,
      "memory": {
        "total_mb": 16384,
        "available_mb": 12288,
        "percent_used": 25.0
      },
      "disk": {
        "total_gb": 1000,
        "free_gb": 800,
        "percent_used": 20
      }
    }
  }
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "error_code",
  "detail": "Human readable error message",
  "timestamp": 1704067200
}
```

### Common Error Codes

- `authentication_error`: Invalid credentials or expired token
- `authorization_error`: Insufficient permissions
- `validation_error`: Invalid request data
- `not_found`: Resource not found
- `conflict_error`: Resource conflict (e.g., duplicate name)
- `rate_limit_exceeded`: Too many requests
- `internal_server_error`: Server error

### HTTP Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict
- `422`: Validation Error
- `429`: Too Many Requests
- `500`: Internal Server Error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **General API**: 100 requests per minute
- **Authentication**: 5 requests per 5 minutes
- **File Upload**: 3 requests per minute

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067260
X-RateLimit-Window: 60
```

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 1000)

**Response Headers:**
```http
X-Total-Count: 250
X-Page-Count: 3
```

## Filtering and Sorting

Many list endpoints support filtering and sorting:

**Query Parameters:**
- `search`: Text search across relevant fields
- `sort`: Sort field (e.g., `created_at`, `name`)
- `order`: Sort order (`asc` or `desc`)

Example:
```http
GET /images?search=windows&sort=created_at&order=desc&limit=50
```

## WebSocket Events (Future)

Real-time updates will be available via WebSocket:

```javascript
const ws = new WebSocket('ws://your-server/api/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

Event types:
- `session_started`
- `session_stopped`
- `image_uploaded`
- `machine_online`
- `machine_offline`
- `system_alert`

## SDK and Client Libraries

Official client libraries are available:

- **Python**: `pip install ggnet-client`
- **JavaScript/Node.js**: `npm install @ggnet/client`
- **Go**: `go get github.com/ggnet/go-client`

Example usage (Python):

```python
from ggnet_client import GGnetClient

client = GGnetClient('http://your-server/api')
client.login('admin', 'password')

# List images
images = client.images.list()

# Upload image
with open('windows11.vhdx', 'rb') as f:
    image = client.images.upload(f, name='Windows 11', image_type='system')

# Create machine
machine = client.machines.create(
    name='LAB-PC-01',
    mac_address='00:11:22:33:44:55',
    boot_mode='uefi'
)
```

## Testing

Use the interactive API documentation at `/api/docs` for testing endpoints.

You can also use curl:

```bash
# Login
TOKEN=$(curl -X POST "http://your-server/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# List images
curl -H "Authorization: Bearer $TOKEN" \
  "http://your-server/api/images"

# Upload image
curl -X POST "http://your-server/api/images/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@windows11.vhdx" \
  -F "name=Windows 11" \
  -F "image_type=system"
```

## Support

For API support:
- GitHub Issues: https://github.com/ggnet/diskless-server/issues
- API Documentation: http://your-server/api/docs
- Community Forum: https://community.ggnet.local

