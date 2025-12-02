# Admin Login Guide

## Default Credentials

After starting the application, you can log in with:

```
Username: admin
Password: admin123
```

## How It Works

The admin user is automatically created when the Docker container starts:

1. **Docker Startup**: When you run `docker-compose up`, the backend container starts
2. **Database Migration**: Alembic runs all migrations to create tables
3. **Admin Initialization**: The `init_admin.py` script automatically creates the admin user
4. **Application Start**: Uvicorn starts and the API is ready

## Manual Admin Creation (if needed)

### For Docker (PostgreSQL):

```bash
cd backend
python create_admin_postgres.py
```

This will:
- Connect to PostgreSQL database at `localhost:5432`
- Create or update the admin user
- Set password to `admin123`

### For Local Development (SQLite):

```bash
cd backend
python create_admin.py
```

This will:
- Connect to SQLite database `ggnet.db`
- Create admin user with password `admin123`

## Troubleshooting

### Login Fails with "Invalid credentials"

**Check 1: Is the backend running?**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

**Check 2: Is PostgreSQL running?**
```bash
docker-compose ps
# Should show postgres, redis, backend, and frontend all "Up"
```

**Check 3: Recreate admin user**
```bash
# Stop containers
docker-compose down

# Start just the database
docker-compose up -d postgres

# Wait 5 seconds for DB to be ready
sleep 5

# Create admin user
cd backend
python create_admin_postgres.py

# Start all services
cd ..
docker-compose up
```

### Backend Logs Show Errors

Check the backend logs:
```bash
docker-compose logs backend
```

Look for:
- `✓ Admin user created successfully` - Good!
- `✓ Database is ready!` - Good!
- Any error messages about database connection or migrations

### Frontend Can't Connect

**Check nginx proxy configuration:**
```bash
docker-compose logs frontend
```

The frontend should proxy `/api` to the backend service.

### Test Login Directly

You can test the login API directly:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Should return:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "..."
}
```

## Changing Admin Password

### Option 1: Via API (when logged in)

```bash
# 1. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r .access_token)

# 2. Change password
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "admin123",
    "new_password": "YourNewSecurePassword123!"
  }'
```

### Option 2: Via Database Script

Create a script `backend/change_admin_password.py`:

```python
import asyncio
from sqlalchemy import select
from app.core.database import get_async_engine, AsyncSession
from app.models.user import User
from app.core.security import get_password_hash

async def change_password():
    async_engine = get_async_engine()
    
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            result = await session.execute(
                select(User).where(User.username == 'admin')
            )
            user = result.scalar_one_or_none()
            
            if user:
                new_password = input("Enter new password: ")
                user.hashed_password = get_password_hash(new_password)
                await session.flush()
                print("Password changed successfully!")
            else:
                print("Admin user not found!")

if __name__ == "__main__":
    asyncio.run(change_password())
```

Then run:
```bash
cd backend
python change_admin_password.py
```

## Security Recommendations

1. **Change Default Password Immediately** in production
2. **Use Strong Passwords**: At least 12 characters, mix of letters, numbers, symbols
3. **Enable 2FA** (if implemented)
4. **Rotate Passwords Regularly**: Every 90 days
5. **Monitor Failed Login Attempts**: Check audit logs
6. **Use HTTPS**: Always in production
7. **Limit Admin Accounts**: Create separate accounts for each administrator

## Production Deployment

For production, **CHANGE** these in `docker-compose.yml`:

```yaml
environment:
  - SECRET_KEY=<generate-random-256-bit-key>
  - POSTGRES_PASSWORD=<strong-random-password>
  - REDIS_PASSWORD=<strong-random-password>
```

Then recreate the admin user with a strong password using `change_admin_password.py`.

## Summary

✅ **Default Login**: `admin` / `admin123`  
✅ **Auto-Created**: On every Docker startup  
✅ **Can be Reset**: Using provided scripts  
✅ **Should be Changed**: Immediately in production

**Happy networking! 🚀**

