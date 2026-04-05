# Migration Checklist for P0 Modules

**Datum:** 2025-11-18  
**Status:** ✅ Checklist Spremna

---

## 📋 Pre-Migration Checklist

### 1. Backup Database ✅
- [ ] Create database backup
  ```bash
  pg_dump -U postgres ggnet2 > backup_before_p0_migration_$(date +%Y%m%d_%H%M%S).sql
  ```

### 2. Verify Current State ✅
- [ ] Check current Alembic version
  ```bash
  alembic current
  ```
- [ ] List existing tables
  ```sql
  \dt  -- in psql
  ```

### 3. Verify Alembic Configuration ✅
- [ ] Check `alembic/env.py` - all models imported
- [ ] Check `alembic.ini` - database URL correct
- [ ] Verify database connection

---

## 📝 Migration Creation Checklist

### 1. Create Migration ✅
- [ ] Run migration creation command
  ```bash
  alembic revision --autogenerate -m "Add P0 modules: auth, batch operations, drives, trim"
  ```
- [ ] Migration file created in `alembic/versions/`

### 2. Review Migration File ✅

#### Authentication Tables
- [ ] `users` table
  - [ ] Columns: id, username, email, hashed_password, is_active, force_password_change
  - [ ] Indexes: ix_users_id, ix_users_username (unique), ix_users_email (unique)
- [ ] `roles` table
  - [ ] Columns: id, name, description
  - [ ] Indexes: ix_roles_id, ix_roles_name (unique)
- [ ] `permissions` table
  - [ ] Columns: id, name, description
  - [ ] Indexes: ix_permissions_id, ix_permissions_name (unique)
- [ ] `user_roles` table
  - [ ] Foreign keys: user_id -> users.id, role_id -> roles.id
  - [ ] Primary key: (user_id, role_id)
- [ ] `role_permissions` table
  - [ ] Foreign keys: role_id -> roles.id, permission_id -> permissions.id
  - [ ] Primary key: (role_id, permission_id)

#### Batch Operations Tables
- [ ] `batch_operations` table
  - [ ] Columns: id, operation_type, status, total_machines, completed_machines, failed_machines
  - [ ] Foreign key: created_by -> users.id
  - [ ] Indexes: ix_batch_operations_id, ix_batch_operations_status
- [ ] `batch_operation_machines` table
  - [ ] Foreign keys: batch_operation_id -> batch_operations.id, machine_id -> machines.id
  - [ ] Indexes: ix_batch_operation_machines_id, ix_batch_operation_machines_batch_operation_id
- [ ] `batch_image_operations` table
  - [ ] Columns: id, operation_type, mode, status, total_images, completed_images, failed_images
  - [ ] Foreign key: created_by -> users.id
  - [ ] Indexes: ix_batch_image_operations_id, ix_batch_image_operations_status
- [ ] `batch_image_operation_images` table
  - [ ] Foreign keys: batch_image_operation_id -> batch_image_operations.id, image_id -> images.id (nullable)
  - [ ] Column: image_id nullable (for restore operations)
  - [ ] Indexes: ix_batch_image_operation_images_id

#### Drive Management Tables
- [ ] `drives` table
  - [ ] Columns: id, uuid, name, path, model, serial_number, size_bytes, type, status, pool_name
  - [ ] Indexes: ix_drives_id, ix_drives_uuid (unique), ix_drives_status, ix_drives_pool_name
- [ ] `drive_smart_data` table
  - [ ] Foreign key: drive_id -> drives.id (CASCADE)
  - [ ] Column: smart_data (JSON)
  - [ ] Indexes: ix_drive_smart_data_id, ix_drive_smart_data_drive_id

#### TRIM Operations Table
- [ ] `trim_operations` table
  - [ ] Columns: id, pool_name, status, progress_percent, started_at, suspended_at, resumed_at, completed_at, cancelled_at
  - [ ] Foreign key: created_by -> users.id
  - [ ] Indexes: ix_trim_operations_id, ix_trim_operations_pool_name, ix_trim_operations_status

### 3. Compare with Template ✅
- [ ] Compare migration file with `alembic/versions/TEMPLATE_add_p0_modules.py`
- [ ] Verify all tables are included
- [ ] Verify all indexes are included
- [ ] Verify all foreign keys are included

### 4. Manual Adjustments (if needed) ✅
- [ ] Add missing tables (if autogenerate missed any)
- [ ] Add missing indexes
- [ ] Fix foreign key constraints
- [ ] Adjust column types if needed

---

## 🚀 Migration Application Checklist

### 1. Pre-Application ✅
- [ ] Database backup verified
- [ ] Migration file reviewed
- [ ] Test environment ready (if applicable)

### 2. Apply Migration ✅
- [ ] Run migration
  ```bash
  alembic upgrade head
  ```
- [ ] Check for errors
- [ ] Verify migration completed successfully

### 3. Post-Application Verification ✅
- [ ] Check new Alembic version
  ```bash
  alembic current
  ```
- [ ] Verify tables created
  ```sql
  \dt  -- in psql
  SELECT table_name FROM information_schema.tables 
  WHERE table_schema = 'public' 
  ORDER BY table_name;
  ```
- [ ] Verify indexes created
  ```sql
  SELECT indexname, tablename FROM pg_indexes 
  WHERE schemaname = 'public' 
  ORDER BY tablename, indexname;
  ```
- [ ] Verify foreign keys created
  ```sql
  SELECT conname, conrelid::regclass, confrelid::regclass 
  FROM pg_constraint 
  WHERE contype = 'f' 
  ORDER BY conrelid::regclass;
  ```

---

## 📊 Data Initialization Checklist

### 1. Initialize Default Data ✅
- [ ] Run initialization script
  ```bash
  python scripts/init_p0_default_data.py
  ```
- [ ] Verify roles created
  ```sql
  SELECT * FROM roles;
  ```
- [ ] Verify permissions created
  ```sql
  SELECT * FROM permissions;
  ```
- [ ] Verify admin user created
  ```sql
  SELECT username, email, is_active FROM users WHERE username = 'admin';
  ```

### 2. Verify Default Data ✅
- [ ] Admin role exists
- [ ] Operator role exists
- [ ] Viewer role exists
- [ ] All permissions assigned to roles
- [ ] Admin user has admin role
- [ ] TRIM settings created (if applicable)

---

## 🧪 Testing Checklist

### 1. Authentication Testing ✅
- [ ] Login with admin/admin123
- [ ] Get current user
- [ ] List users (admin only)
- [ ] Create new user
- [ ] Test permissions

### 2. Bulk Operations Testing ✅
- [ ] Create batch operation
- [ ] Check batch status
- [ ] Verify WebSocket updates
- [ ] Test bulk restart
- [ ] Test bulk shutdown

### 3. Drive Management Testing ✅
- [ ] List drives
- [ ] Get free drives
- [ ] Get SMART data
- [ ] Create array
- [ ] Add drives to array

### 4. TRIM Operations Testing ✅
- [ ] Run TRIM
- [ ] Get TRIM status
- [ ] Suspend TRIM
- [ ] Resume TRIM
- [ ] Cancel TRIM

---

## 🔄 Rollback Checklist (if needed)

### 1. Rollback Preparation ✅
- [ ] Verify backup exists
- [ ] Check current migration version
- [ ] Plan rollback strategy

### 2. Execute Rollback ✅
- [ ] Rollback migration
  ```bash
  alembic downgrade -1
  ```
- [ ] Verify rollback successful
- [ ] Check database state

### 3. Post-Rollback ✅
- [ ] Verify tables removed
- [ ] Verify data integrity
- [ ] Document issues encountered

---

## ✅ Final Verification

### 1. Application Startup ✅
- [ ] Application starts without errors
- [ ] Database connections work
- [ ] API endpoints accessible

### 2. Functionality Verification ✅
- [ ] All P0 features work
- [ ] No errors in logs
- [ ] Performance acceptable

### 3. Documentation ✅
- [ ] Update deployment notes
- [ ] Document any issues
- [ ] Update version information

---

## 📝 Notes

- **Template Migration:** Use `alembic/versions/TEMPLATE_add_p0_modules.py` as reference
- **Migration Guide:** See [MIGRATION_GUIDE_P0.md](./MIGRATION_GUIDE_P0.md)
- **Default Data:** See `scripts/init_p0_default_data.py`

---

*Migration Checklist kreiran - Koristi ovaj checklist za sigurnu primenu migracija!*

