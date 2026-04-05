# Migration Template Reference

Ovaj dokument sadrži template za kreiranje P0 modula migracije.

## Template Struktura

```python
"""Add P0 modules: auth, batch operations, drives, trim

Revision ID: <revision_id>
Revises: <previous_revision>
Create Date: <date>
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '<revision_id>'
down_revision = '<previous_revision>'  # None za prvu migraciju
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Tabele za Authentication
    # Tabele za Batch Operations
    # Tabele za Batch Image Operations
    # Tabele za Drive Management
    # Tabele za TRIM Operations
    pass

def downgrade() -> None:
    # Obrnuti redosled
    pass
```

## Tabele koje treba da budu uključene

### Authentication
- users
- roles
- permissions
- user_roles (association table)
- role_permissions (association table)

### Batch Operations
- batch_operations
- batch_operation_machines

### Batch Image Operations
- batch_image_operations
- batch_image_operation_images

### Drive Management
- drives
- drive_smart_data

### TRIM Operations
- trim_operations

## Napomene

- Prva migracija ima `down_revision = None`
- Sledeće migracije imaju `down_revision = '<previous_revision_id>'`
- Koristi `alembic revision --autogenerate` za automatsko generisanje

