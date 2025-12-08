# API Authentication Documentation

## Overview

ggNET2 uses JWT (JSON Web Tokens) for API authentication. All API endpoints except `/api/users/login` require authentication.

## Authentication Flow

1. **Login**: POST to `/api/users/login` with username and password
2. **Receive Token**: Response includes `access_token` and `refresh_token`
3. **Use Token**: Include token in `Authorization` header for all subsequent requests
4. **Refresh Token**: Use `refresh_token` to get a new `access_token` when it expires

## Login Endpoint

### POST /api/users/login

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `422 Unprocessable Entity`: Missing or invalid request body

## Using the Token

Include the token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Expiration

- **Access Token**: Expires after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh Token**: Expires after 7 days (configurable)

## Refresh Token Endpoint

### POST /api/users/refresh

Get a new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Current User Endpoint

### GET /api/users/me

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@ggnet2.local",
  "full_name": "Administrator",
  "is_active": true,
  "is_superuser": true,
  "roles": [
    {
      "id": 1,
      "name": "admin",
      "description": "Administrator - Full access to all resources"
    }
  ],
  "permissions": [
    {
      "id": 1,
      "name": "machines:read",
      "resource": "machines",
      "action": "read"
    },
    ...
  ]
}
```

## Role-Based Access Control (RBAC)

### Roles

- **admin**: Full access to all resources
- **user**: Limited access (read/write, no delete, no user management)
- **machine**: Read-only access for machine clients

### Permissions

Permissions follow the format: `<resource>:<action>`

**Resources:**
- `machines`
- `images`
- `vms`
- `storage`
- `settings`
- `users`

**Actions:**
- `read`: View/list resources
- `write`: Create/update resources
- `delete`: Delete resources

### Permission Checks

API endpoints automatically check user permissions based on:
1. User roles
2. Role permissions
3. Resource and action required

**Example:**
- Endpoint: `DELETE /api/machines/{id}` requires `machines:delete` permission
- User with `admin` role: ✅ Allowed (admin has all permissions)
- User with `user` role: ❌ Forbidden (user role doesn't have delete permission)

## Error Responses

### 401 Unauthorized

Token is missing, invalid, or expired.

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

User doesn't have required permissions.

```json
{
  "detail": "Insufficient permissions"
}
```

## Security Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** (httpOnly cookies or secure storage)
3. **Never expose tokens** in URLs or logs
4. **Rotate tokens regularly** using refresh tokens
5. **Use strong passwords** (minimum 8 characters, mixed case, numbers)
6. **Change default admin password** after first login

## Example: Complete Authentication Flow

### 1. Login

```bash
curl -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 2. Use Token

```bash
curl -X GET http://localhost:8000/api/machines \
  -H "Authorization: Bearer <access_token>"
```

### 3. Refresh Token

```bash
curl -X POST http://localhost:8000/api/users/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

## Frontend Integration

### Storing Tokens

```javascript
// After login
localStorage.setItem('access_token', response.data.access_token);
localStorage.setItem('refresh_token', response.data.refresh_token);
```

### Using Tokens

```javascript
// Axios interceptor
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Handling Token Expiration

```javascript
// Axios response interceptor
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('/api/users/refresh', {
            refresh_token: refreshToken
          });
          localStorage.setItem('access_token', response.data.access_token);
          // Retry original request
          return axios.request(error.config);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
```

## Default Credentials

**⚠️ IMPORTANT**: Change default admin password after first login!

- Username: `admin`
- Password: `admin123` (or value from `ADMIN_PASSWORD` environment variable)

## Environment Variables

- `SECRET_KEY`: JWT secret key (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration (default: 30)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ADMIN_PASSWORD`: Default admin password (default: admin123)

