# Authentication & Authorization - Detaljni Plan Implementacije

**Prioritet:** 🔴 P0 - Kritično za MVP  
**Vreme:** 2-3 nedelje  
**Status:** 📋 Plan

---

## 📋 Pregled

Implementacija kompletnog authentication i authorization sistema sa:
- JWT token-based authentication
- Role-based access control (RBAC)
- User management
- Password management
- Session management

---

## 🎯 Funkcionalni Zahtevi

### 1. User Authentication

**Zahtevi:**
- Login sa username/password
- JWT token generisanje
- Token refresh mehanizam
- Logout funkcionalnost
- Password reset (opciono)

**Endpoint-i:**
- `POST /api/users/authenticate` - Login
- `POST /api/users/logout` - Logout
- `POST /api/users/refresh` - Refresh token (opciono)

### 2. User Management

**Zahtevi:**
- List users
- Get current user
- Create user
- Update user
- Delete user
- Force password change

**Endpoint-i:**
- `GET /api/users` - List users
- `GET /api/users/current` - Get current user
- `GET /api/users/local` - Get local users
- `POST /api/users` - Create user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user
- `POST /api/users/forceChangePassword` - Force password change

### 3. Role-Based Access Control (RBAC)

**Zahtevi:**
- Role definicije (Admin, User, Machine)
- Permission system
- Role assignment
- Permission checking

**Endpoint-i:**
- `GET /api/users/permissions` - Get user permissions
- `GET /api/users/{id}/roles` - Get user roles
- `POST /api/users/{id}/roles` - Assign roles
- `DELETE /api/users/{id}/roles/{roleId}` - Remove role

### 4. Client Authentication

**Zahtevi:**
- Client authentication (za Windows klijente)
- AD joined status check

**Endpoint-i:**
- `POST /api/clients/authenticate` - Authenticate client
- `POST /api/clients/ad-joined` - Check AD joined status

---

## 🗄️ Database Schema

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    force_password_change BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
```

### Roles Table

```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'Administrator - Full access'),
    ('user', 'Regular user - Limited access'),
    ('machine', 'Machine client - Read-only access');
```

### User Roles Table (Many-to-Many)

```sql
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id)
);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
```

### Permissions Table

```sql
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL,  -- 'machines', 'images', 'vms', etc.
    action VARCHAR(50) NOT NULL,     -- 'read', 'write', 'delete', etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_permissions_resource ON permissions(resource);
CREATE INDEX idx_permissions_action ON permissions(action);
```

### Role Permissions Table (Many-to-Many)

```sql
CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);
```

### Refresh Tokens Table (Opciono)

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

---

## 📁 Struktura Fajlova

```
app/backend/
├── auth/
│   ├── __init__.py
│   ├── jwt_handler.py          # JWT token generisanje i validacija
│   ├── password_manager.py     # Password hashing i validacija
│   ├── rbac.py                 # Role-based access control
│   ├── dependencies.py         # FastAPI dependencies za auth
│   └── exceptions.py           # Auth-specific exceptions
├── api/
│   └── users.py                # User management endpoints
└── config/
    └── models.py               # User, Role, Permission models (proširiti)
```

---

## 🔧 Implementacija

### 1. JWT Handler (`app/backend/auth/jwt_handler.py`)

```python
"""
JWT Token Handler
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTHandler:
    """JWT token handler"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Data to encode in token
            expires_delta: Optional expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token
        
        Args:
            data: Data to encode in token
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def get_current_user_id(token: str) -> Optional[int]:
        """
        Get user ID from token
        
        Args:
            token: JWT token
            
        Returns:
            User ID or None
        """
        payload = JWTHandler.verify_token(token)
        if payload:
            return payload.get("sub")  # 'sub' is user ID
        return None
```

### 2. Password Manager (`app/backend/auth/password_manager.py`)

```python
"""
Password Management
"""

from passlib.context import CryptContext
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordManager:
    """Password management utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        return True, None
```

### 3. RBAC System (`app/backend/auth/rbac.py`)

```python
"""
Role-Based Access Control
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.backend.config.models import User, Role, Permission, UserRole, RolePermission


class RBAC:
    """Role-based access control"""
    
    @staticmethod
    def user_has_role(db: Session, user_id: int, role_name: str) -> bool:
        """
        Check if user has specific role
        
        Args:
            db: Database session
            user_id: User ID
            role_name: Role name
            
        Returns:
            True if user has role
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        for user_role in user.roles:
            if user_role.role.name == role_name:
                return True
        return False
    
    @staticmethod
    def user_has_permission(db: Session, user_id: int, resource: str, action: str) -> bool:
        """
        Check if user has permission
        
        Args:
            db: Database session
            user_id: User ID
            resource: Resource name (e.g., 'machines', 'images')
            action: Action name (e.g., 'read', 'write', 'delete')
            
        Returns:
            True if user has permission
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Superuser has all permissions
        if user.is_superuser:
            return True
        
        # Check permissions through roles
        for user_role in user.roles:
            for role_permission in user_role.role.permissions:
                if (role_permission.permission.resource == resource and
                    role_permission.permission.action == action):
                    return True
        
        return False
    
    @staticmethod
    def get_user_permissions(db: Session, user_id: int) -> List[dict]:
        """
        Get all permissions for user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of permissions
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        permissions = set()
        
        # Superuser has all permissions
        if user.is_superuser:
            all_perms = db.query(Permission).all()
            return [{"resource": p.resource, "action": p.action} for p in all_perms]
        
        # Get permissions through roles
        for user_role in user.roles:
            for role_permission in user_role.role.permissions:
                perm = role_permission.permission
                permissions.add((perm.resource, perm.action))
        
        return [{"resource": r, "action": a} for r, a in permissions]
```

### 4. FastAPI Dependencies (`app/backend/auth/dependencies.py`)

```python
"""
FastAPI Dependencies for Authentication
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.backend.config.database import get_db
from app.backend.config.models import User
from app.backend.auth.jwt_handler import JWTHandler
from app.backend.auth.rbac import RBAC

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user
    
    Args:
        credentials: HTTP Bearer token
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = JWTHandler.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(role_name: str):
    """
    Dependency to require specific role
    
    Args:
        role_name: Required role name
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not RBAC.user_has_role(db, current_user.id, role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {role_name} role"
            )
        return current_user
    
    return role_checker


def require_permission(resource: str, action: str):
    """
    Dependency to require specific permission
    
    Args:
        resource: Resource name
        action: Action name
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not RBAC.user_has_permission(db, current_user.id, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {resource}:{action} permission"
            )
        return current_user
    
    return permission_checker


# Common dependencies
RequireAdmin = require_role("admin")
RequireUser = require_role("user")
```

### 5. API Endpoints (`app/backend/api/users.py`)

```python
"""
User Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr

from app.backend.config.database import get_db
from app.backend.config.models import User, Role
from app.backend.auth.jwt_handler import JWTHandler
from app.backend.auth.password_manager import PasswordManager
from app.backend.auth.dependencies import get_current_user, RequireAdmin
from app.backend.auth.rbac import RBAC

router = APIRouter()


# Request Models
class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


class UserCreateRequest(BaseModel):
    """User creation request"""
    username: str
    email: Optional[EmailStr] = None
    password: str
    full_name: Optional[str] = None
    roles: List[str] = []


class UserUpdateRequest(BaseModel):
    """User update request"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str


class ForcePasswordChangeRequest(BaseModel):
    """Force password change request"""
    user_id: int
    new_password: str


# Response Models
class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    """User response"""
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    roles: List[str]
    permissions: List[Dict[str, str]]


# Endpoints
@router.post("/authenticate", response_model=TokenResponse)
async def authenticate(
    request: LoginRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token
    
    Args:
        request: Login credentials
        db: Database session
        
    Returns:
        JWT access token
    """
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not PasswordManager.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = JWTHandler.create_access_token(data={"sub": user.id, "username": user.username})
    
    # Create refresh token (optional)
    refresh_token = JWTHandler.create_refresh_token(data={"sub": user.id})
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/current", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Current user information
    """
    permissions = RBAC.get_user_permissions(db, current_user.id)
    roles = [role.role.name for role in current_user.roles]
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        roles=roles,
        permissions=permissions
    )


@router.get("/permissions", response_model=List[Dict[str, str]])
async def get_user_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user permissions
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of user permissions
    """
    return RBAC.get_user_permissions(db, current_user.id)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(RequireAdmin),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only)
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user (must be admin)
        db: Database session
        
    Returns:
        List of users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        permissions = RBAC.get_user_permissions(db, user.id)
        roles = [role.role.name for role in user.roles]
        
        result.append(UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=roles,
            permissions=permissions
        ))
    
    return result


@router.post("/", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest = Body(...),
    current_user: User = Depends(RequireAdmin),
    db: Session = Depends(get_db)
):
    """
    Create new user (Admin only)
    
    Args:
        request: User creation request
        current_user: Current authenticated user (must be admin)
        db: Database session
        
    Returns:
        Created user
    """
    # Validate password strength
    is_valid, error_msg = PasswordManager.validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if username exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create user
    user = User(
        username=request.username,
        email=request.email,
        password_hash=PasswordManager.hash_password(request.password),
        full_name=request.full_name,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Assign roles
    for role_name in request.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            db.add(user_role)
    
    db.commit()
    db.refresh(user)
    
    permissions = RBAC.get_user_permissions(db, user.id)
    roles = [role.role.name for role in user.roles]
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=roles,
        permissions=permissions
    )


@router.post("/forceChangePassword")
async def force_password_change(
    request: ForcePasswordChangeRequest = Body(...),
    current_user: User = Depends(RequireAdmin),
    db: Session = Depends(get_db)
):
    """
    Force password change for user (Admin only)
    
    Args:
        request: Force password change request
        current_user: Current authenticated user (must be admin)
        db: Database session
        
    Returns:
        Success message
    """
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate password strength
    is_valid, error_msg = PasswordManager.validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    user.password_hash = PasswordManager.hash_password(request.new_password)
    user.force_password_change = True
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/local", response_model=List[UserResponse])
async def get_local_users(
    current_user: User = Depends(RequireAdmin),
    db: Session = Depends(get_db)
):
    """
    Get local users (Admin only)
    
    Args:
        current_user: Current authenticated user (must be admin)
        db: Database session
        
    Returns:
        List of local users
    """
    # This could filter by some criteria (e.g., not AD users)
    # For now, return all users
    return await list_users(0, 100, current_user, db)
```

---

## 🧪 Test Plan

### Unit Tests

1. **JWT Handler Tests**
   - Test token creation
   - Test token verification
   - Test token expiration
   - Test invalid token handling

2. **Password Manager Tests**
   - Test password hashing
   - Test password verification
   - Test password strength validation

3. **RBAC Tests**
   - Test role checking
   - Test permission checking
   - Test superuser permissions

### Integration Tests

1. **Authentication Flow**
   - Test successful login
   - Test failed login
   - Test inactive user login
   - Test token refresh

2. **User Management**
   - Test user creation
   - Test user update
   - Test user deletion
   - Test role assignment

3. **Authorization**
   - Test admin-only endpoints
   - Test permission-based access
   - Test unauthorized access

### Security Tests

1. **SQL Injection**
   - Test all user inputs
   - Test database queries

2. **XSS**
   - Test user input sanitization

3. **Token Security**
   - Test token expiration
   - Test token tampering
   - Test token replay attacks

---

## 📦 Dependencies

### Python Packages

```txt
python-jose[cryptography]>=3.3.0  # JWT handling
passlib[bcrypt]>=1.7.4            # Password hashing
bcrypt>=4.0.1                     # Bcrypt algorithm
python-multipart>=0.0.6           # Form data parsing
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add authentication tables"

# Apply migration
alembic upgrade head
```

---

## 🔐 Security Considerations

1. **Password Storage**
   - Use bcrypt with appropriate cost factor (12+)
   - Never store plain text passwords
   - Implement password strength requirements

2. **Token Security**
   - Use strong secret key (32+ characters)
   - Set appropriate expiration times
   - Implement token refresh mechanism
   - Store refresh tokens securely

3. **Rate Limiting**
   - Implement rate limiting for login attempts
   - Prevent brute force attacks
   - Lock accounts after failed attempts

4. **HTTPS**
   - Always use HTTPS in production
   - Never send tokens over HTTP

---

## 📝 Environment Variables

```bash
# .env
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
```

---

## ✅ Checklist

### Setup
- [ ] Install dependencies
- [ ] Create database migrations
- [ ] Setup environment variables
- [ ] Create default roles and permissions

### Implementation
- [ ] JWT Handler
- [ ] Password Manager
- [ ] RBAC System
- [ ] FastAPI Dependencies
- [ ] User API Endpoints
- [ ] Client Authentication

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Security tests
- [ ] Performance tests

### Documentation
- [ ] API documentation
- [ ] Security documentation
- [ ] Deployment guide

---

*Plan kreiran za Authentication & Authorization implementaciju.*

