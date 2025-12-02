# Admin Script Migration Notice

**Date:** 2025-01-26

## Unified Admin Script

All admin user creation functionality has been consolidated into a single unified script:

**`backend/scripts/create_admin.py`**

This script replaces the following duplicate scripts:
- `backend/create_admin.py` ❌ Removed
- `backend/create_admin_postgres.py` ❌ Removed  
- `backend/init_admin.py` ❌ Removed
- `backend/seed_admin.py` ✅ Updated to use unified script

## Usage

```bash
# Basic usage
python -m app.scripts.create_admin

# With custom credentials
python -m app.scripts.create_admin --username myadmin --password mypass123

# Update existing admin
python -m app.scripts.create_admin --update

# Skip table creation
python -m app.scripts.create_admin --no-create-tables
```

## Features

- ✅ Works with both SQLite and PostgreSQL (auto-detects)
- ✅ Creates database tables if needed
- ✅ Command-line arguments support
- ✅ Environment variable support
- ✅ Update existing admin option
- ✅ Better error handling

## Migration

If you were using any of the old scripts:
- Use the new unified script instead
- All functionality is preserved and enhanced
- Old scripts have been removed

