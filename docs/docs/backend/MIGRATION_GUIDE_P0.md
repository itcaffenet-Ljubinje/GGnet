# Alembic Migration Guide for P0 Modules

**Datum:** 2025-11-18  
**Status:** ✅ Spremno za kreiranje migracija

---

## 📋 Pregled

Ovaj vodič objašnjava kako kreirati i primeniti Alembic migracije za P0 module.

### Novi Modeli za Migraciju

1. **Authentication:**
   - `users` - User accounts
   - `roles` - User roles
   - `permissions` - Permissions
   - `user_roles` - User-Role association table
   - `role_permissions` - Role-Permission association table

2. **Batch Operations:**
   - `batch_operations` - Machine batch operations
   - `batch_operation_machines` - Batch operation machines
   - `batch_image_operations` - Image batch operations
   - `batch_image_operation_images` - Batch operation images

3. **Drive Management:**
   - `drives` - Physical drives
   - `drive_smart_data` - SMART data history

4. **TRIM Operations:**
   - `trim_operations` - TRIM operation tracking

---

## 🚀 Kreiranje Migracije

### Opcija 1: Automatski (Preporučeno)

**Linux/WSL:**
```bash
chmod +x scripts/create_p0_migration.sh
./scripts/create_p0_migration.sh
```

**Windows PowerShell:**
```powershell
.\scripts\create_p0_migration.ps1
```

### Opcija 2: Ručno

```bash
# Aktiviraj virtual environment (ako postoji)
source venv/bin/activate  # Linux
# ili
venv\Scripts\activate  # Windows

# Kreiraj migraciju
alembic revision --autogenerate -m "Add P0 modules: auth, batch operations, drives, trim"
```

---

## ✅ Provera Migration Fajla

Nakon kreiranja migracije, proveri fajl u `alembic/versions/XXXX_add_p0_modules.py`.

### Proveri da li su uključene sve tabele:

```python
# Authentication tables
op.create_table('users', ...)
op.create_table('roles', ...)
op.create_table('permissions', ...)
op.create_table('user_roles', ...)
op.create_table('role_permissions', ...)

# Batch operations tables
op.create_table('batch_operations', ...)
op.create_table('batch_operation_machines', ...)
op.create_table('batch_image_operations', ...)
op.create_table('batch_image_operation_images', ...)

# Drive management tables
op.create_table('drives', ...)
op.create_table('drive_smart_data', ...)

# TRIM operations table
op.create_table('trim_operations', ...)
```

### Proveri Foreign Keys:

```python
# Users -> Roles (many-to-many)
op.create_foreign_key('fk_user_roles_user', 'user_roles', 'users', ...)
op.create_foreign_key('fk_user_roles_role', 'user_roles', 'roles', ...)

# Roles -> Permissions (many-to-many)
op.create_foreign_key('fk_role_permissions_role', 'role_permissions', 'roles', ...)
op.create_foreign_key('fk_role_permissions_permission', 'role_permissions', 'permissions', ...)

# Batch operations
op.create_foreign_key('fk_batch_operation_machine', 'batch_operation_machines', 'batch_operations', ...)
op.create_foreign_key('fk_batch_image_operation_image', 'batch_image_operation_images', 'batch_image_operations', ...)

# Drive management
op.create_foreign_key('fk_drive_smart_data_drive', 'drive_smart_data', 'drives', ...)

# TRIM operations
op.create_foreign_key('fk_trim_operation_user', 'trim_operations', 'users', ...)
```

### Proveri Indexes:

```python
# Users
op.create_index('ix_users_id', 'users', ['id'])
op.create_index('ix_users_username', 'users', ['username'])
op.create_index('ix_users_email', 'users', ['email'])

# Roles
op.create_index('ix_roles_id', 'roles', ['id'])
op.create_index('ix_roles_name', 'roles', ['name'])

# Permissions
op.create_index('ix_permissions_id', 'permissions', ['id'])
op.create_index('ix_permissions_name', 'permissions', ['name'])

# Batch operations
op.create_index('ix_batch_operations_id', 'batch_operations', ['id'])
op.create_index('ix_batch_operations_status', 'batch_operations', ['status'])

# Drives
op.create_index('ix_drives_id', 'drives', ['id'])
op.create_index('ix_drives_uuid', 'drives', ['uuid'])
op.create_index('ix_drives_status', 'drives', ['status'])

# TRIM operations
op.create_index('ix_trim_operations_id', 'trim_operations', ['id'])
op.create_index('ix_trim_operations_pool_name', 'trim_operations', ['pool_name'])
op.create_index('ix_trim_operations_status', 'trim_operations', ['status'])
```

---

## 🔧 Ažuriranje Migration Fajla (Ako je Potrebno)

Ako Alembic ne detektuje neke tabele ili veze, možeš ručno dodati:

```python
def upgrade():
    # Dodaj ručno ako nedostaje
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        # ... ostali kolone
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    # ...
```

---

## 📤 Primena Migracije

### Pre Primenjivanja

1. **Backup baze podataka:**
   ```bash
   pg_dump -U postgres ggnet2 > backup_before_p0_migration.sql
   ```

2. **Proveri trenutnu verziju:**
   ```bash
   alembic current
   ```

### Primena

```bash
# Primeni migraciju
alembic upgrade head
```

### Provera

```bash
# Proveri novu verziju
alembic current

# Proveri da li su tabele kreirane
# (kroz psql ili database client)
psql -U postgres -d ggnet2 -c "\dt"
```

---

## 🔄 Rollback (Ako je Potrebno)

Ako migracija ne uspe, možeš vratiti:

```bash
# Vrati na prethodnu verziju
alembic downgrade -1

# Ili na specifičnu verziju
alembic downgrade <revision_id>
```

---

## 📝 Inicijalizacija Default Podataka

Nakon primene migracije, inicijalizuj default podatke:

### 1. Auth Module - Default Roles i Permissions

```bash
python -m app.backend.auth.init_default_data
```

Ili ručno kroz Python:

```python
from app.backend.config.database import SessionLocal
from app.backend.auth.init_default_data import init_default_roles_and_permissions

db = SessionLocal()
init_default_roles_and_permissions(db)
db.close()
```

### 2. Kreiranje Prvog Admin Korisnika

```python
from app.backend.config.database import SessionLocal
from app.backend.config.models import User, Role
from app.backend.auth.password_manager import PasswordManager

db = SessionLocal()
password_manager = PasswordManager()

# Kreiraj admin korisnika
admin_user = User(
    username="admin",
    email="admin@example.com",
    hashed_password=password_manager.hash_password("admin123"),
    is_active=True
)
db.add(admin_user)

# Dodaj admin role
admin_role = db.query(Role).filter(Role.name == "admin").first()
if admin_role:
    admin_user.roles.append(admin_role)

db.commit()
db.close()
```

### 3. TRIM Settings (Opciono)

```bash
# Via API
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "key": "trim.enabled",
    "value": true,
    "value_type": "boolean",
    "description": "Enable TRIM operations"
  }'
```

---

## 🐛 Troubleshooting

### Problem: Migration ne detektuje sve tabele

**Rešenje:**
1. Proveri da li su svi modeli importovani u `alembic/env.py`
2. Proveri da li su modeli definisani u `app/backend/config/models.py`
3. Ručno dodaj nedostajuće tabele u migration fajl

### Problem: Foreign Key greške

**Rešenje:**
1. Proveri redosled kreiranja tabela (parent tabele prvo)
2. Proveri da li su foreign key kolone ispravno definisane
3. Proveri da li postojeće tabele imaju potrebne kolone

### Problem: Index greške

**Rešenje:**
1. Proveri da li index već postoji
2. Koristi `if_not_exists=True` ako je potrebno
3. Proveri da li su kolone ispravno definisane

### Problem: Migration ne može da se primeni

**Rešenje:**
1. Proveri database connection string u `alembic.ini`
2. Proveri da li baza postoji
3. Proveri da li imaš dozvole za kreiranje tabela
4. Proveri logove za detaljne greške

---

## ✅ Checklist

### Pre Migracije
- [ ] Backup baze podataka
- [ ] Proveri trenutnu verziju (`alembic current`)
- [ ] Proveri da li su svi modeli importovani u `alembic/env.py`
- [ ] Proveri da li su svi modeli definisani

### Kreiranje Migracije
- [ ] Pokreni `alembic revision --autogenerate`
- [ ] Proveri migration fajl
- [ ] Proveri da li su sve tabele uključene
- [ ] Proveri foreign keys
- [ ] Proveri indexes

### Primena Migracije
- [ ] Primeni migraciju (`alembic upgrade head`)
- [ ] Proveri novu verziju (`alembic current`)
- [ ] Proveri da li su tabele kreirane
- [ ] Testiraj da li aplikacija radi

### Post-Migracija
- [ ] Inicijalizuj default roles i permissions
- [ ] Kreiraj prvog admin korisnika
- [ ] Testiraj authentication flow
- [ ] Testiraj API endpoints

---

## 🔗 Reference

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations](https://docs.sqlalchemy.org/en/20/core/metadata.html)
- [P0 Implementation Summary](./P0_IMPLEMENTATION_SUMMARY.md)

---

*Migration Guide kreiran za P0 module.*

