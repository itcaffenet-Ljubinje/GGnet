# Performance Tuning Guide

Optimization guide for ggNET2 performance.

## Database Optimization

### Connection Pooling

Configure database connection pool size in `.env`:

```env
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

**Recommendations:**
- Pool size: 10-20 connections
- Max overflow: 20-30 connections
- Adjust based on concurrent users

### Query Optimization

1. **Add Indexes**: Ensure all foreign keys and frequently queried columns have indexes
2. **Use Eager Loading**: Use `joinedload()` for relationships to avoid N+1 queries
3. **Limit Results**: Always use `skip` and `limit` for list endpoints
4. **Avoid SELECT ***: Only select needed columns

### Database Maintenance

```bash
# Analyze tables for query planner
psql -U ggnet2 -d ggnet2 -c "ANALYZE;"

# Vacuum database
psql -U ggnet2 -d ggnet2 -c "VACUUM ANALYZE;"
```

## ZFS Optimization

### ARC Cache Size

Configure ZFS ARC (Adaptive Replacement Cache) size:

```bash
# Set ARC max (in bytes, e.g., 8GB)
echo 8589934592 > /sys/module/zfs/parameters/zfs_arc_max

# Or in /etc/modprobe.d/zfs.conf
options zfs zfs_arc_max=8589934592
```

**Recommendations:**
- ARC max: 50-70% of available RAM
- Leave RAM for system and VMs
- Monitor ARC hit rate: `arcstat`

### Compression

Enable compression for better I/O:

```bash
# Set compression on pool
zfs set compression=lz4 pool0

# Or per dataset
zfs set compression=lz4 pool0/ggnet2/images
```

**Compression Options:**
- `lz4`: Fast, good compression (recommended)
- `gzip`: Better compression, slower
- `zstd`: Best balance (if available)

### Deduplication

**⚠️ Warning**: Deduplication requires significant RAM (5GB per 1TB of data)

Only enable if:
- You have sufficient RAM
- High duplicate data ratio
- Performance is critical

```bash
zfs set dedup=on pool0
```

## API Optimization

### Response Caching

Implement caching for frequently accessed data:

```python
# Cache settings for 5 minutes
@lru_cache(maxsize=100, ttl=300)
def get_settings():
    ...
```

### Pagination

Always paginate large datasets:

```python
# Limit to 100 items per page
skip: int = 0
limit: int = 100
```

### Async Operations

Use async for long-running operations:

```python
# Background task for bulk operations
from fastapi import BackgroundTasks

@router.post("/batch")
async def batch_operation(
    background_tasks: BackgroundTasks,
    ...
):
    background_tasks.add_task(process_batch, ...)
    return {"status": "started"}
```

## Frontend Optimization

### Code Splitting

Split large bundles:

```javascript
// Lazy load routes
const Machines = lazy(() => import('./pages/Machines'));
```

### API Request Optimization

1. **Debounce Search**: Debounce search inputs to reduce API calls
2. **Cache Responses**: Use React Query for automatic caching
3. **Batch Requests**: Combine multiple requests when possible
4. **Pagination**: Load data in chunks

### Image Optimization

1. **Lazy Loading**: Load images on demand
2. **Compression**: Compress images before upload
3. **CDN**: Use CDN for static assets

## System Resources

### RAM Allocation

Balance RAM between:
- System: 2-4GB
- ZFS ARC: 50-70% of remaining
- VMs: Remaining RAM

**Example (16GB total):**
- System: 2GB
- ZFS ARC: 8GB (50% of 14GB)
- VMs: 6GB

### CPU Optimization

1. **CPU Affinity**: Pin ZFS processes to specific CPUs
2. **I/O Scheduler**: Use `deadline` or `mq-deadline` for SSDs
3. **NUMA**: Consider NUMA topology for multi-socket systems

### Disk I/O

1. **SSD Optimization**: Use SSDs for ZFS cache and logs
2. **Stripe Width**: Optimize stripe width for RAID
3. **Queue Depth**: Increase queue depth for better throughput

## Monitoring

### Key Metrics

Monitor these metrics:

1. **Database:**
   - Query execution time
   - Connection pool usage
   - Cache hit rate

2. **ZFS:**
   - ARC hit rate
   - I/O throughput
   - Pool health

3. **API:**
   - Response time
   - Request rate
   - Error rate

4. **System:**
   - CPU usage
   - Memory usage
   - Disk I/O

### Tools

```bash
# ZFS statistics
arcstat 1

# System resources
htop
iostat -x 1

# Network
iftop

# Database
pg_stat_statements
```

## Benchmarking

### API Performance

```bash
# Benchmark API endpoint
ab -n 1000 -c 10 http://localhost:8000/api/machines

# With authentication
ab -n 1000 -c 10 -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/machines
```

### Database Performance

```bash
# Test query performance
psql -U ggnet2 -d ggnet2 -c "EXPLAIN ANALYZE SELECT * FROM machines;"
```

## Best Practices

1. **Regular Maintenance**: Run `VACUUM ANALYZE` weekly
2. **Monitor Logs**: Check logs regularly for errors
3. **Update Regularly**: Keep system and dependencies updated
4. **Backup Strategy**: Regular backups prevent data loss
5. **Capacity Planning**: Monitor disk usage and plan expansion

## Troubleshooting Performance

### Slow Queries

1. Enable query logging
2. Identify slow queries
3. Add indexes
4. Optimize query structure

### High Memory Usage

1. Check ARC size
2. Reduce VM RAM allocation
3. Monitor for memory leaks
4. Adjust connection pool size

### High CPU Usage

1. Identify CPU-intensive processes
2. Optimize ZFS operations
3. Balance load across CPUs
4. Consider hardware upgrade

