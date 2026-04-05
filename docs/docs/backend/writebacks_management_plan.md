# Writebacks Management - Detaljni Plan Implementacije

**Prioritet:** 🔴 P0 - Kritično za MVP  
**Vreme:** 1 nedelja  
**Status:** 📋 Plan

---

## 📋 Pregled

Implementacija writeback management sistema sa:
- Keep writeback (single i bulk)
- Delete writeback
- Writeback state management
- Integration sa postojećim WritebackManager

---

## 🎯 Funkcionalni Zahtevi

### 1. Machine Writebacks Management

**Zahtevi:**
- Keep single writeback
- Keep all writebacks
- Delete writeback
- List writebacks

**Endpoint-i:**
- `POST /api/machines/{id}/writebacks/{writebackPath}/keep` - Keep single writeback
- `POST /api/machines/{id}/writebacks/keep` - Keep all writebacks
- `DELETE /api/machines/{id}/writebacks/{writebackPath}` - Delete writeback
- `GET /api/machines/{id}/writebacks` - List writebacks (opciono)

### 2. Image Writebacks Management

**Zahtevi:**
- Delete writebacks for image
- List writebacks for image

**Endpoint-i:**
- `DELETE /api/images/{path}/writebacks` - Delete writebacks
- `GET /api/images/{path}/writebacks` - List writebacks (opciono)

---

## 🗄️ Database Schema

### Writebacks Table (Opciono - za tracking)

```sql
CREATE TABLE writebacks (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
    writeback_path VARCHAR(500) NOT NULL,  -- ZFS dataset path
    status VARCHAR(50) DEFAULT 'active',    -- 'active', 'kept', 'deleted'
    size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    kept_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_writebacks_machine_id ON writebacks(machine_id);
CREATE INDEX idx_writebacks_image_id ON writebacks(image_id);
CREATE INDEX idx_writebacks_status ON writebacks(status);
CREATE INDEX idx_writebacks_path ON writebacks(writeback_path);
```

**Napomena:** Ova tabela je opciona - writebacks se mogu pronaći direktno iz ZFS sistema. Tabela je korisna za tracking i audit.

---

## 📁 Struktura Fajlova

```
app/backend/
├── machines/
│   └── writeback_manager.py       # Već postoji - proširiti
├── images/
│   └── image_manager.py           # Proširiti sa writeback metodama
└── api/
    ├── machines.py                 # Proširiti sa writeback endpoint-ima
    └── images.py                   # Proširiti sa writeback endpoint-ima
```

---

## 🔧 Implementacija

### 1. WritebackManager Extensions (`app/backend/machines/writeback_manager.py`)

```python
# Dodati metode u postojeći WritebackManager

def list_writebacks(
    self,
    db: Session,
    machine_id: int
) -> List[Dict[str, Any]]:
    """
    List all writebacks for machine
    
    Args:
        db: Database session
        machine_id: Machine ID
        
    Returns:
        List of writeback dictionaries
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise NotFoundError(f"Machine {machine_id} not found")
    
    # Get ZFS clone path
    if not machine.image_id:
        return []
    
    # Find all clones for this machine
    # This depends on how clones are named/stored
    # Example: pool0/ggnet2/clones/machine-{machine_id}-*
    clones = self.zfs_utils.list_clones_for_machine(machine.id)
    
    writebacks = []
    for clone_path in clones:
        # Get clone info
        clone_info = self.zfs_utils.dataset_info(clone_path)
        writebacks.append({
            "path": clone_path,
            "size": clone_info.get("used", 0),
            "created": clone_info.get("creation", None),
            "status": "active"
        })
    
    return writebacks

def keep_writeback(
    self,
    db: Session,
    machine_id: int,
    writeback_path: str
) -> Dict[str, Any]:
    """
    Keep single writeback (promote clone to independent dataset)
    
    Args:
        db: Database session
        machine_id: Machine ID
        writeback_path: ZFS dataset path for writeback
        
    Returns:
        Writeback result dictionary
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise NotFoundError(f"Machine {machine_id} not found")
    
    # Verify writeback path belongs to this machine
    if not writeback_path.startswith(f"pool0/ggnet2/clones/machine-{machine_id}"):
        raise ValidationError(f"Writeback path does not belong to machine {machine_id}")
    
    # Promote clone to independent dataset
    try:
        self.zfs_utils.clone_promote(writeback_path)
        
        return {
            "machine_id": machine_id,
            "writeback_path": writeback_path,
            "status": "kept",
            "message": f"Writeback {writeback_path} kept successfully"
        }
    except ZFSError as e:
        raise MachineError(f"Failed to keep writeback: {e}")

def keep_all_writebacks(
    self,
    db: Session,
    machine_id: int
) -> Dict[str, Any]:
    """
    Keep all writebacks for machine
    
    Args:
        db: Database session
        machine_id: Machine ID
        
    Returns:
        Writeback result dictionary
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise NotFoundError(f"Machine {machine_id} not found")
    
    # Get all writebacks
    writebacks = self.list_writebacks(db, machine_id)
    
    kept = 0
    failed = 0
    errors = []
    
    for writeback in writebacks:
        try:
            self.keep_writeback(db, machine_id, writeback["path"])
            kept += 1
        except Exception as e:
            failed += 1
            errors.append({
                "path": writeback["path"],
                "error": str(e)
            })
    
    return {
        "machine_id": machine_id,
        "total": len(writebacks),
        "kept": kept,
        "failed": failed,
        "errors": errors
    }

def delete_writeback(
    self,
    db: Session,
    machine_id: int,
    writeback_path: str
) -> Dict[str, Any]:
    """
    Delete writeback (destroy ZFS dataset)
    
    Args:
        db: Database session
        machine_id: Machine ID
        writeback_path: ZFS dataset path for writeback
        
    Returns:
        Delete result dictionary
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise NotFoundError(f"Machine {machine_id} not found")
    
    # Verify writeback path belongs to this machine
    if not writeback_path.startswith(f"pool0/ggnet2/clones/machine-{machine_id}"):
        raise ValidationError(f"Writeback path does not belong to machine {machine_id}")
    
    # Destroy dataset
    try:
        self.zfs_utils.dataset_destroy(writeback_path, recursive=True)
        
        return {
            "machine_id": machine_id,
            "writeback_path": writeback_path,
            "status": "deleted",
            "message": f"Writeback {writeback_path} deleted successfully"
        }
    except ZFSError as e:
        raise MachineError(f"Failed to delete writeback: {e}")
```

### 2. ImageManager Extensions (`app/backend/images/image_manager.py`)

```python
# Dodati metode u postojeći ImageManager

def delete_writebacks(
    self,
    db: Session,
    image_path: str
) -> Dict[str, Any]:
    """
    Delete all writebacks for image
    
    Args:
        db: Database session
        image_path: Image ZFS dataset path
        
    Returns:
        Delete result dictionary
    """
    # Find image by path
    image = db.query(Image).filter(Image.zfs_dataset == image_path).first()
    if not image:
        raise NotFoundError(f"Image with path {image_path} not found")
    
    # Find all clones of this image
    clones = self.zfs_utils.list_clones_for_image(image_path)
    
    deleted = 0
    failed = 0
    errors = []
    
    for clone_path in clones:
        try:
            self.zfs_utils.dataset_destroy(clone_path, recursive=True)
            deleted += 1
        except Exception as e:
            failed += 1
            errors.append({
                "path": clone_path,
                "error": str(e)
            })
    
    return {
        "image_path": image_path,
        "total": len(clones),
        "deleted": deleted,
        "failed": failed,
        "errors": errors
    }
```

### 3. ZFSUtils Extensions (`app/backend/storage/zfs_utils.py`)

```python
# Dodati metode u postojeći ZFSUtils

def clone_promote(self, clone_path: str) -> None:
    """
    Promote clone to independent dataset
    
    Args:
        clone_path: ZFS clone dataset path
        
    Raises:
        ZFSError: If promotion fails
    """
    try:
        self._run_command([self.zfs_cmd, "promote", clone_path])
        logger.info(f"Promoted clone {clone_path} to independent dataset")
    except ZFSError:
        raise
    except Exception as e:
        raise ZFSError(f"Failed to promote clone {clone_path}: {e}")

def list_clones_for_machine(self, machine_id: int) -> List[str]:
    """
    List all clones for machine
    
    Args:
        machine_id: Machine ID
        
    Returns:
        List of clone dataset paths
    """
    # This depends on clone naming convention
    # Example: pool0/ggnet2/clones/machine-{machine_id}-*
    pattern = f"pool0/ggnet2/clones/machine-{machine_id}-*"
    
    try:
        result = self._run_command([
            self.zfs_cmd, "list", "-H", "-o", "name", "-t", "filesystem,volume",
            "-r", "pool0/ggnet2/clones"
        ])
        
        clones = []
        for line in result.stdout.strip().split("\n"):
            if line and f"machine-{machine_id}-" in line:
                clones.append(line.strip())
        
        return clones
    except Exception as e:
        raise ZFSError(f"Failed to list clones for machine {machine_id}: {e}")

def list_clones_for_image(self, image_path: str) -> List[str]:
    """
    List all clones for image
    
    Args:
        image_path: Image ZFS dataset path
        
    Returns:
        List of clone dataset paths
    """
    try:
        result = self._run_command([
            self.zfs_cmd, "list", "-H", "-o", "name,origin", "-t", "filesystem,volume",
            "-r", "pool0/ggnet2/clones"
        ])
        
        clones = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and image_path in parts[1]:
                clones.append(parts[0].strip())
        
        return clones
    except Exception as e:
        raise ZFSError(f"Failed to list clones for image {image_path}: {e}")
```

### 4. API Endpoints (`app/backend/api/machines.py`)

```python
# Dodati u postojeći machines.py

from app.backend.machines.writeback_manager import WritebackManager
from app.backend.auth.dependencies import get_current_user

writeback_manager = WritebackManager()


@router.get("/{machine_id}/writebacks")
async def list_writebacks(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all writebacks for machine
    
    Args:
        machine_id: Machine ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of writebacks
    """
    try:
        return writeback_manager.list_writebacks(db, machine_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{machine_id}/writebacks/{writeback_path:path}/keep")
async def keep_writeback(
    machine_id: int,
    writeback_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Keep single writeback
    
    Args:
        machine_id: Machine ID
        writeback_path: Writeback ZFS dataset path
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Writeback result
    """
    try:
        return writeback_manager.keep_writeback(db, machine_id, writeback_path)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MachineError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{machine_id}/writebacks/keep")
async def keep_all_writebacks(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Keep all writebacks for machine
    
    Args:
        machine_id: Machine ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Writeback result
    """
    try:
        return writeback_manager.keep_all_writebacks(db, machine_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MachineError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{machine_id}/writebacks/{writeback_path:path}")
async def delete_writeback(
    machine_id: int,
    writeback_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete writeback
    
    Args:
        machine_id: Machine ID
        writeback_path: Writeback ZFS dataset path
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Delete result
    """
    try:
        return writeback_manager.delete_writeback(db, machine_id, writeback_path)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MachineError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 5. API Endpoints (`app/backend/api/images.py`)

```python
# Dodati u postojeći images.py

from app.backend.images.image_manager import ImageManager
from app.backend.auth.dependencies import get_current_user

image_manager = ImageManager()


@router.delete("/{image_path:path}/writebacks")
async def delete_image_writebacks(
    image_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete all writebacks for image
    
    Args:
        image_path: Image ZFS dataset path
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Delete result
    """
    try:
        return image_manager.delete_writebacks(db, image_path)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImageError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🧪 Test Plan

### Unit Tests

1. **WritebackManager Tests**
   - Test list_writebacks
   - Test keep_writeback
   - Test keep_all_writebacks
   - Test delete_writeback
   - Test error handling

2. **ImageManager Tests**
   - Test delete_writebacks
   - Test error handling

3. **ZFSUtils Tests**
   - Test clone_promote
   - Test list_clones_for_machine
   - Test list_clones_for_image

### Integration Tests

1. **Writeback Operations Flow**
   - Test keep single writeback
   - Test keep all writebacks
   - Test delete writeback
   - Test error scenarios

2. **Image Writeback Operations**
   - Test delete writebacks for image
   - Test error scenarios

### Security Tests

1. **Path Validation**
   - Test writeback path validation
   - Test machine ownership validation
   - Test unauthorized access

---

## 📦 Dependencies

### Existing Code

- ✅ `WritebackManager` - već postoji
- ✅ `ImageManager` - već postoji
- ✅ `ZFSUtils` - već postoji
- ✅ `Machine` model - već postoji
- ✅ `Image` model - već postoji

### New Code

- ⚠️ `ZFSUtils.clone_promote()` - treba dodati
- ⚠️ `ZFSUtils.list_clones_for_machine()` - treba dodati
- ⚠️ `ZFSUtils.list_clones_for_image()` - treba dodati

---

## ⚠️ Napomene

### Clone Naming Convention

**Problem:** Plan pretpostavlja specifičan naming convention za clone-ove

**Rešenje:**
- Definirati naming convention u dokumentaciji
- Ili koristiti metadata/relationships u bazi

**Preporučeni Convention:**
- Machine clones: `pool0/ggnet2/clones/machine-{machine_id}-{uuid}`
- VM clones: `pool0/ggnet2/clones/vm-{vm_id}-{uuid}`

### Writeback Detection

**Problem:** Kako detektovati writeback-e?

**Rešenje:**
1. **ZFS origin property** - koristiti `zfs list -o origin` da pronađemo clone-ove
2. **Database tracking** - koristiti writebacks tabelu (opciono)
3. **Naming convention** - koristiti naming pattern

---

## ✅ Checklist

### Setup
- [ ] Definirati clone naming convention
- [ ] Proveriti ZFS clone structure

### Implementation
- [ ] ZFSUtils extensions
- [ ] WritebackManager extensions
- [ ] ImageManager extensions
- [ ] API Endpoints

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Security tests

### Documentation
- [ ] API documentation
- [ ] Clone naming convention documentation

---

*Plan kreiran za Writebacks Management implementaciju.*

