# Troubleshooting Guide

Common issues and solutions for ggNET2.

## Authentication Issues

### Cannot Login

**Symptoms:**
- Login returns 401 Unauthorized
- "Invalid credentials" error

**Solutions:**
1. Verify username and password are correct
2. Check if user account is active: `is_active = true`
3. Verify database has default admin user:
   ```bash
   python -m app.backend.auth.init_default_data
   ```
4. Check backend logs for authentication errors

### Token Expired

**Symptoms:**
- API requests return 401 Unauthorized
- "Not authenticated" error

**Solutions:**
1. Refresh token using `/api/users/refresh` endpoint
2. Re-login to get new tokens
3. Check token expiration settings in backend config

### Permission Denied

**Symptoms:**
- API requests return 403 Forbidden
- "Insufficient permissions" error

**Solutions:**
1. Verify user has required role and permissions
2. Check RBAC configuration
3. Ensure user roles are assigned correctly

## Database Issues

### Migration Errors

**Symptoms:**
- Alembic migration fails
- Database schema errors

**Solutions:**
1. Backup database before migration:
   ```bash
   pg_dump -U ggnet2 ggnet2 > backup.sql
   ```
2. Check migration file for errors
3. Verify database connection settings
4. Run migration manually:
   ```bash
   alembic upgrade head
   ```

### Connection Errors

**Symptoms:**
- "Connection refused" errors
- Database connection timeout

**Solutions:**
1. Verify PostgreSQL is running:
   ```bash
   systemctl status postgresql
   ```
2. Check database credentials in `.env` file
3. Verify database exists:
   ```bash
   psql -U ggnet2 -l
   ```
4. Check firewall rules

## API Issues

### 404 Not Found

**Symptoms:**
- API endpoint returns 404
- Route not found

**Solutions:**
1. Verify endpoint URL is correct
2. Check if route is registered in `app/backend/api/router.py`
3. Verify API prefix matches (`/api`)
4. Check backend server logs

### 500 Internal Server Error

**Symptoms:**
- API returns 500 error
- Generic server error

**Solutions:**
1. Check backend logs: `app/backend/logs/ggnet2_error.log`
2. Verify database connection
3. Check ZFS pool status
4. Verify system dependencies are installed

## Frontend Issues

### Cannot Connect to Backend

**Symptoms:**
- Frontend shows connection errors
- API requests fail

**Solutions:**
1. Verify backend server is running on port 8000
2. Check CORS configuration in backend
3. Verify API base URL in frontend config
4. Check browser console for errors

### Page Not Loading

**Symptoms:**
- Blank page
- JavaScript errors

**Solutions:**
1. Clear browser cache
2. Check browser console for errors
3. Verify all dependencies are installed:
   ```bash
   npm install
   ```
4. Rebuild frontend:
   ```bash
   npm run build
   ```

## Storage Issues

### ZFS Pool Not Found

**Symptoms:**
- Storage operations fail
- "Pool not found" errors

**Solutions:**
1. Verify ZFS pool exists:
   ```bash
   zpool list
   ```
2. Check pool name in settings: `ZFS_POOL_NAME`
3. Verify pool is imported:
   ```bash
   zpool import pool0
   ```

### Drive Not Detected

**Symptoms:**
- Drive not showing in UI
- Drive operations fail

**Solutions:**
1. Check if drive is detected by system:
   ```bash
   lsblk
   ```
2. Verify drive permissions
3. Check backend logs for drive detection errors
4. Run drive scan manually

### Rebuild Fails

**Symptoms:**
- Array rebuild fails
- Rebuild status shows error

**Solutions:**
1. Check drive health:
   ```bash
   smartctl -a /dev/sdX
   ```
2. Verify sufficient free space
3. Check ZFS pool status:
   ```bash
   zpool status pool0
   ```
4. Review rebuild logs

## Network Issues

### DHCP Not Working

**Symptoms:**
- Machines cannot get IP addresses
- PXE boot fails

**Solutions:**
1. Verify dnsmasq is running:
   ```bash
   systemctl status dnsmasq
   ```
2. Check DHCP configuration
3. Verify network bridge is configured
4. Check firewall rules

### PXE Boot Fails

**Symptoms:**
- Machines cannot boot from network
- iPXE errors

**Solutions:**
1. Verify iPXE configuration
2. Check network connectivity
3. Verify boot image is assigned
4. Check iPXE logs

## Performance Issues

### Slow API Responses

**Symptoms:**
- API requests take long time
- Timeout errors

**Solutions:**
1. Check database query performance
2. Verify database indexes exist
3. Check system resources (CPU, RAM, disk I/O)
4. Review slow query logs

### High Memory Usage

**Symptoms:**
- System runs out of memory
- OOM errors

**Solutions:**
1. Check ARC cache size
2. Reduce RAM allocation for VMs
3. Monitor memory usage:
   ```bash
   free -h
   ```
4. Adjust ZFS ARC max size

## Logs and Debugging

### View Backend Logs

```bash
# Application logs
tail -f app/backend/logs/ggnet2.log

# Error logs
tail -f app/backend/logs/ggnet2_error.log
```

### Enable Debug Mode

Set in `.env`:
```
DEBUG=True
LOG_LEVEL=DEBUG
```

### Check System Status

```bash
# ZFS pool status
zpool status

# Drive status
lsblk

# Network status
ip addr show

# Service status
systemctl status ggnet2
```

## Getting Help

1. Check logs first
2. Review this troubleshooting guide
3. Check GitHub issues
4. Contact support with:
   - Error messages
   - Log excerpts
   - System configuration
   - Steps to reproduce

