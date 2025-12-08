# ggNET2 Linux Configurator - Detaljni Planovi Modula

**Datum:** 2025-01-XX  
**Verzija:** 1.0.0

---

## 📋 Pregled

Detaljni planovi implementacije za sve module `ggnet2_linux_configurator` sistema.

---

## 1. Preflight Checks Module (`app/backend/system/preflight.py`)

### 📋 Pregled

Modul za preflight checks - proverava i automatski ispravlja sistemske zavisnosti pre pokretanja ggNET2-a.

### 🎯 Funkcionalnosti

1. **Check ggNET2 Installation**
   - Provera da li je ggNET2 service instaliran i enabled
   - Provera da li service postoji u systemd

2. **Check Kernel Headers**
   - Provera da li postoje Linux kernel headers za trenutni kernel
   - Provera `/usr/src/linux-headers-$(uname -r)`
   - Automatska instalacija ako nedostaju

3. **Check DNS Configuration**
   - Provera `/etc/resolv.conf` za nameserver-e
   - Automatsko dodavanje `8.8.8.8` ako nema nameserver-a

4. **Nginx Preflight Configuration**
   - Backup originalnog nginx config fajla
   - Kreiranje privremenog preflight config-a
   - HTML error page generisanje
   - Restore originalnog config-a nakon završetka

### 📐 API Specifikacija

```python
from app.backend.system.preflight import PreflightChecker, PreflightResult

class PreflightChecker:
    """Preflight checks manager"""
    
    def check_ggnet2_installed(self) -> PreflightResult:
        """
        Check if ggNET2 is installed and enabled
        
        Returns:
            PreflightResult with status and message
        """
        pass
    
    def check_kernel_headers(self) -> PreflightResult:
        """
        Check if Linux kernel headers are installed
        
        Returns:
            PreflightResult with status and message
        """
        pass
    
    def check_dns_config(self) -> PreflightResult:
        """
        Check DNS configuration
        
        Returns:
            PreflightResult with status and message
        """
        pass
    
    def fix_kernel_headers(self) -> bool:
        """
        Automatically install missing kernel headers
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def fix_dns_config(self) -> bool:
        """
        Automatically fix DNS configuration
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def run_all_checks(self) -> List[PreflightResult]:
        """
        Run all preflight checks
        
        Returns:
            List of PreflightResult objects
        """
        pass
    
    def fix_all_failures(self, results: List[PreflightResult]) -> bool:
        """
        Fix all failed checks
        
        Args:
            results: List of PreflightResult objects
            
        Returns:
            True if all fixes successful, False otherwise
        """
        pass
    
    def create_preflight_html(self, results: List[PreflightResult]) -> str:
        """
        Create HTML error page for preflight failures
        
        Args:
            results: List of PreflightResult objects
            
        Returns:
            HTML content as string
        """
        pass
    
    def setup_nginx_preflight(self) -> bool:
        """
        Setup nginx for preflight mode
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def cleanup_nginx_preflight(self) -> bool:
        """
        Restore original nginx configuration
        
        Returns:
            True if successful, False otherwise
        """
        pass


class PreflightResult:
    """Preflight check result"""
    
    def __init__(
        self,
        check_name: str,
        status: bool,
        message: str,
        fixable: bool = False
    ):
        self.check_name = check_name
        self.status = status  # True = passed, False = failed
        self.message = message
        self.fixable = fixable
    
    def has_failure(self) -> bool:
        """Check if check failed"""
        return not self.status
```

### 💻 Primer Implementacije

```python
# app/backend/system/preflight.py

import subprocess
import logging
import platform
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PreflightResult:
    """Preflight check result"""
    check_name: str
    status: bool
    message: str
    fixable: bool = False
    
    def has_failure(self) -> bool:
        """Check if check failed"""
        return not self.status


class PreflightChecker:
    """Preflight checks manager"""
    
    def __init__(self):
        self.nginx_config_path = Path("/etc/nginx/conf.d/ggnet2.conf")
        self.nginx_backup_path = Path("/etc/nginx/conf.d/ggnet2.preflight.backup")
        self.html_path = Path("/opt/ggnet2/html/ggnet2_preflight.html")
        self.service_name = "ggnet2-api"
    
    def check_ggnet2_installed(self) -> PreflightResult:
        """Check if ggNET2 is installed and enabled"""
        try:
            result = subprocess.run(
                ["systemctl", "is-enabled", self.service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                enabled = result.stdout.strip()
                if enabled == "enabled":
                    return PreflightResult(
                        check_name="ggnet2_installed",
                        status=True,
                        message="ggNET2 service is installed and enabled"
                    )
                else:
                    return PreflightResult(
                        check_name="ggnet2_installed",
                        status=False,
                        message=f"ggNET2 service is not enabled (status: {enabled})",
                        fixable=False
                    )
            else:
                return PreflightResult(
                    check_name="ggnet2_installed",
                    status=False,
                    message="ggNET2 service is not installed",
                    fixable=False
                )
        except Exception as e:
            logger.error(f"Error checking ggNET2 installation: {e}")
            return PreflightResult(
                check_name="ggnet2_installed",
                status=False,
                message=f"Error checking installation: {e}",
                fixable=False
            )
    
    def check_kernel_headers(self) -> PreflightResult:
        """Check if Linux kernel headers are installed"""
        try:
            kernel_version = platform.release()
            headers_path = Path(f"/usr/src/linux-headers-{kernel_version}")
            
            if headers_path.exists() and headers_path.is_dir():
                return PreflightResult(
                    check_name="kernel_headers",
                    status=True,
                    message=f"Kernel headers found for {kernel_version}"
                )
            else:
                return PreflightResult(
                    check_name="kernel_headers",
                    status=False,
                    message=f"Kernel headers not found for {kernel_version}",
                    fixable=True
                )
        except Exception as e:
            logger.error(f"Error checking kernel headers: {e}")
            return PreflightResult(
                check_name="kernel_headers",
                status=False,
                message=f"Error checking headers: {e}",
                fixable=False
            )
    
    def check_dns_config(self) -> PreflightResult:
        """Check DNS configuration"""
        try:
            resolv_conf = Path("/etc/resolv.conf")
            
            if not resolv_conf.exists():
                return PreflightResult(
                    check_name="dns_config",
                    status=False,
                    message="/etc/resolv.conf does not exist",
                    fixable=True
                )
            
            content = resolv_conf.read_text()
            if "nameserver" in content:
                return PreflightResult(
                    check_name="dns_config",
                    status=True,
                    message="DNS nameserver found in /etc/resolv.conf"
                )
            else:
                return PreflightResult(
                    check_name="dns_config",
                    status=False,
                    message="No nameserver found in /etc/resolv.conf",
                    fixable=True
                )
        except Exception as e:
            logger.error(f"Error checking DNS config: {e}")
            return PreflightResult(
                check_name="dns_config",
                status=False,
                message=f"Error checking DNS: {e}",
                fixable=False
            )
    
    def fix_kernel_headers(self) -> bool:
        """Automatically install missing kernel headers"""
        try:
            kernel_version = platform.release()
            
            logger.info(f"Installing kernel headers for {kernel_version}")
            
            result = subprocess.run(
                [
                    "apt-get", "update"
                ],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"apt-get update failed: {result.stderr}")
                return False
            
            result = subprocess.run(
                [
                    "apt-get", "install", "-y",
                    f"linux-headers-{kernel_version}"
                ],
                capture_output=True,
                text=True,
                timeout=600,
                env={"DEBIAN_FRONTEND": "noninteractive"}
            )
            
            if result.returncode == 0:
                # Load ZFS module
                subprocess.run(["modprobe", "zfs"], timeout=10)
                logger.info("Kernel headers installed successfully")
                return True
            else:
                logger.error(f"Failed to install headers: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error fixing kernel headers: {e}")
            return False
    
    def fix_dns_config(self) -> bool:
        """Automatically fix DNS configuration"""
        try:
            resolv_conf = Path("/etc/resolv.conf")
            
            # Check if nameserver already exists
            if resolv_conf.exists():
                content = resolv_conf.read_text()
                if "nameserver" in content:
                    return True  # Already configured
            
            # Add nameserver
            with open(resolv_conf, "a") as f:
                f.write("\nnameserver 8.8.8.8\n")
            
            logger.info("DNS configuration fixed")
            return True
        except Exception as e:
            logger.error(f"Error fixing DNS config: {e}")
            return False
    
    def run_all_checks(self) -> List[PreflightResult]:
        """Run all preflight checks"""
        results = []
        
        results.append(self.check_ggnet2_installed())
        results.append(self.check_kernel_headers())
        results.append(self.check_dns_config())
        
        return results
    
    def fix_all_failures(self, results: List[PreflightResult]) -> bool:
        """Fix all failed checks"""
        success = True
        
        for result in results:
            if result.has_failure() and result.fixable:
                if result.check_name == "kernel_headers":
                    if not self.fix_kernel_headers():
                        success = False
                elif result.check_name == "dns_config":
                    if not self.fix_dns_config():
                        success = False
        
        return success
    
    def create_preflight_html(self, results: List[PreflightResult]) -> str:
        """Create HTML error page for preflight failures"""
        html_body = "<h3>ggNET2 has detected the following preflight errors. Please wait while they are automatically corrected.</h3>"
        
        for result in results:
            if result.has_failure():
                if result.check_name == "kernel_headers":
                    html_body += "<p>* A kernel change has been detected since the last configuration. The linux headers will be updated.</p><br>"
                elif result.check_name == "dns_config":
                    html_body += "<p>* DNS configuration will be updated.</p><br>"
        
        html_body += "<br><p>ggNET2 will automatically finish loading when this process is complete. This may take a few minutes.</p><br>"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ggNET2 Preflight</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{
            background-color: #3B4852;
            color: white;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""
        return html
    
    def setup_nginx_preflight(self) -> bool:
        """Setup nginx for preflight mode"""
        try:
            # Backup original config
            if self.nginx_config_path.exists():
                import shutil
                shutil.copy2(
                    self.nginx_config_path,
                    self.nginx_backup_path
                )
            
            # Create HTML directory
            self.html_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create preflight HTML
            results = self.run_all_checks()
            html_content = self.create_preflight_html(results)
            self.html_path.write_text(html_content)
            
            # Create preflight nginx config
            # (Simplified version - full config would be more complex)
            nginx_config = """
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /opt/ggnet2/html;
    index ggnet2_preflight.html;
    
    location / {
        add_header Cache-Control 'no-store';
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
    
    root /opt/ggnet2/html;
    index ggnet2_preflight.html;
    
    # SSL configuration would go here
    
    location / {
        add_header Cache-Control 'no-store';
        try_files $uri $uri/ /;
    }
}
"""
            self.nginx_config_path.write_text(nginx_config)
            
            # Restart nginx
            subprocess.run(
                ["systemctl", "restart", "nginx"],
                timeout=30
            )
            
            return True
        except Exception as e:
            logger.error(f"Error setting up nginx preflight: {e}")
            return False
    
    def cleanup_nginx_preflight(self) -> bool:
        """Restore original nginx configuration"""
        try:
            if self.nginx_backup_path.exists():
                import shutil
                shutil.copy2(
                    self.nginx_backup_path,
                    self.nginx_config_path
                )
                self.nginx_backup_path.unlink()
                
                # Reload nginx
                subprocess.run(
                    ["systemctl", "reload", "nginx"],
                    timeout=30
                )
            
            return True
        except Exception as e:
            logger.error(f"Error cleaning up nginx preflight: {e}")
            return False
```

### 🧪 Test Plan

1. **Unit Tests**
   - Test `check_ggnet2_installed()` - service enabled/disabled/missing
   - Test `check_kernel_headers()` - headers exist/missing
   - Test `check_dns_config()` - DNS configured/missing
   - Test `fix_kernel_headers()` - successful/failed installation
   - Test `fix_dns_config()` - successful/failed fix

2. **Integration Tests**
   - Test `run_all_checks()` - all checks pass/fail
   - Test `fix_all_failures()` - all fixes successful
   - Test `setup_nginx_preflight()` - nginx config backup/restore
   - Test `cleanup_nginx_preflight()` - restore original config

3. **System Tests**
   - Test preflight service startup
   - Test automatic fixes during boot
   - Test nginx preflight mode

### 📦 Zavisnosti

```python
# requirements.txt
# No additional dependencies - uses standard library
```

### 🔧 System Dependencies

```bash
# Debian/Ubuntu
apt-get install -y linux-headers-$(uname -r)
```

---

## 2. Upgrade Automation Module (`app/backend/system/upgrade.py`)

### 📋 Pregled

Modul za automatski upgrade sistema - upgrade paketa, database migracije, i full system upgrade.

### 🎯 Funkcionalnosti

1. **Read Upgrade Configuration**
   - Čitanje `/etc/ggnet2/upgrade_env` fajla
   - Parsiranje environment variables

2. **Full System Upgrade**
   - `apt-get dist-upgrade` za full system upgrade
   - Non-interactive mode

3. **Package Upgrade**
   - Upgrade specifičnog paketa (ggnet2, ggnet2-linux-configurator)
   - Podrška za specifične verzije
   - Podrška za `skip` flag

4. **Database Migration**
   - Database backup pre migracije (`pg_dump`)
   - Pokretanje migracije
   - Rollback ako migracija ne uspe

### 📐 API Specifikacija

```python
from app.backend.system.upgrade import UpgradeManager, UpgradeConfig

class UpgradeManager:
    """Upgrade automation manager"""
    
    def read_config(self, config_path: str = "/etc/ggnet2/upgrade_env") -> UpgradeConfig:
        """
        Read upgrade configuration from file
        
        Args:
            config_path: Path to upgrade_env file
            
        Returns:
            UpgradeConfig object
        """
        pass
    
    def run_dist_upgrade(self) -> bool:
        """
        Run full system upgrade (dist-upgrade)
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def upgrade_package(
        self,
        package_name: str,
        version: Optional[str] = None
    ) -> bool:
        """
        Upgrade specific package
        
        Args:
            package_name: Package name (e.g., "ggnet2")
            version: Optional specific version (or "skip" to skip)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Backup database before migration
        
        Args:
            backup_path: Optional backup file path
            
        Returns:
            Path to backup file
        """
        pass
    
    def run_migration(self, migration_name: str) -> bool:
        """
        Run database migration
        
        Args:
            migration_name: Migration name/version
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def run_upgrade(self) -> bool:
        """
        Run upgrade based on configuration
        
        Returns:
            True if successful, False otherwise
        """
        pass


@dataclass
class UpgradeConfig:
    """Upgrade configuration"""
    run_dist_upgrade: bool = False
    app_version: Optional[str] = None
    configurator_version: Optional[str] = None
    migration: Optional[str] = None
```

### 💻 Primer Implementacije

```python
# app/backend/system/upgrade.py

import subprocess
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class UpgradeConfig:
    """Upgrade configuration"""
    run_dist_upgrade: bool = False
    app_version: Optional[str] = None
    configurator_version: Optional[str] = None
    migration: Optional[str] = None


class UpgradeManager:
    """Upgrade automation manager"""
    
    def __init__(self):
        self.config_path = Path("/etc/ggnet2/upgrade_env")
        self.app_name = "ggnet2"
        self.configurator_name = "ggnet2-linux-configurator"
        self.db_name = "ggnet2"
        self.dumps_path = Path("/var/lib/ggnet2/db/dumps")
    
    def read_config(self, config_path: Optional[str] = None) -> UpgradeConfig:
        """Read upgrade configuration from file"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = self.config_path
        
        config = UpgradeConfig()
        
        if not config_file.exists():
            logger.warning(f"Upgrade config file not found: {config_file}")
            return config
        
        try:
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse key=value
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes
                        value = value.strip('"').strip("'")
                        
                        if key == "RUN_DIST_UPGRADE":
                            config.run_dist_upgrade = value.lower() == "true"
                        elif key == "APP_VERSION":
                            config.app_version = value if value != "skip" else None
                        elif key == "CONFIGURATOR_VERSION":
                            config.configurator_version = value if value != "skip" else None
                        elif key == "MIGRATION":
                            config.migration = value if value else None
            
            logger.info(f"Upgrade config loaded: {config}")
            return config
        except Exception as e:
            logger.error(f"Error reading upgrade config: {e}")
            return config
    
    def run_dist_upgrade(self) -> bool:
        """Run full system upgrade"""
        try:
            logger.info("Starting full system upgrade")
            
            # Update package lists
            result = subprocess.run(
                ["apt-get", "update"],
                capture_output=True,
                text=True,
                timeout=300,
                env={"DEBIAN_FRONTEND": "noninteractive"}
            )
            
            if result.returncode != 0:
                logger.error(f"apt-get update failed: {result.stderr}")
                return False
            
            # Run dist-upgrade
            result = subprocess.run(
                ["apt-get", "-y", "dist-upgrade"],
                capture_output=True,
                text=True,
                timeout=3600,
                env={"DEBIAN_FRONTEND": "noninteractive"}
            )
            
            if result.returncode == 0:
                logger.info("Full system upgrade completed successfully")
                return True
            else:
                logger.error(f"dist-upgrade failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running dist-upgrade: {e}")
            return False
    
    def upgrade_package(
        self,
        package_name: str,
        version: Optional[str] = None
    ) -> bool:
        """Upgrade specific package"""
        try:
            if version:
                logger.info(f"Upgrading {package_name} to version {version}")
                cmd = [
                    "apt-get", "-y", "--allow-downgrades",
                    "install", f"{package_name}={version}"
                ]
            else:
                logger.info(f"Upgrading {package_name} to latest version")
                cmd = ["apt-get", "-y", "install", package_name]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                env={"DEBIAN_FRONTEND": "noninteractive"}
            )
            
            if result.returncode == 0:
                logger.info(f"Package {package_name} upgraded successfully")
                return True
            else:
                logger.error(f"Package upgrade failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error upgrading package {package_name}: {e}")
            return False
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Backup database before migration"""
        try:
            # Create dumps directory
            self.dumps_path.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename
            if not backup_path:
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                backup_path = str(self.dumps_path / f"ggnet2-upgrade-{timestamp}.bak")
            
            logger.info(f"Backing up database to {backup_path}")
            
            result = subprocess.run(
                ["pg_dump", "-Fc", self.db_name],
                stdout=open(backup_path, "wb"),
                stderr=subprocess.PIPE,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_path}")
                return backup_path
            else:
                error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                logger.error(f"Database backup failed: {error_msg}")
                raise Exception(f"Database backup failed: {error_msg}")
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            raise
    
    def run_migration(self, migration_name: str) -> bool:
        """Run database migration"""
        try:
            # Backup database first
            backup_path = self.backup_database()
            
            logger.info(f"Running migration: {migration_name}")
            
            # Run migration (assuming we have a migration command)
            # This would depend on your migration system (Alembic, custom, etc.)
            result = subprocess.run(
                [
                    "python3", "-m", "app.backend.config.migrate",
                    migration_name
                ],
                cwd="/opt/ggnet2/app",
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                logger.info(f"Migration {migration_name} completed successfully")
                return True
            else:
                logger.error(f"Migration failed: {result.stderr}")
                # Restart service to rollback
                subprocess.run(["systemctl", "restart", "ggnet2-api"], timeout=30)
                return False
        except Exception as e:
            logger.error(f"Error running migration: {e}")
            # Restart service to rollback
            subprocess.run(["systemctl", "restart", "ggnet2-api"], timeout=30)
            return False
    
    def run_upgrade(self) -> bool:
        """Run upgrade based on configuration"""
        try:
            config = self.read_config()
            
            logger.info(
                f"Upgrade config: RUN_DIST_UPGRADE={config.run_dist_upgrade}, "
                f"APP_VERSION={config.app_version}, "
                f"CONFIGURATOR_VERSION={config.configurator_version}, "
                f"MIGRATION={config.migration}"
            )
            
            # Update package lists
            subprocess.run(
                ["apt-get", "update"],
                capture_output=True,
                timeout=300,
                env={"DEBIAN_FRONTEND": "noninteractive"}
            )
            
            if config.run_dist_upgrade:
                return self.run_dist_upgrade()
            else:
                # Run migration if specified
                if config.migration:
                    if not self.run_migration(config.migration):
                        return False
                
                # Upgrade configurator
                if config.configurator_version is not None:
                    if config.configurator_version:
                        if not self.upgrade_package(
                            self.configurator_name,
                            config.configurator_version
                        ):
                            return False
                    else:
                        if not self.upgrade_package(self.configurator_name):
                            return False
                else:
                    if not self.upgrade_package(self.configurator_name):
                        return False
                
                # Upgrade app
                if config.app_version is not None:
                    if config.app_version:
                        if not self.upgrade_package(
                            self.app_name,
                            config.app_version
                        ):
                            return False
                    else:
                        if not self.upgrade_package(self.app_name):
                            return False
                else:
                    if not self.upgrade_package(self.app_name):
                        return False
            
            logger.info("Upgrade completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error running upgrade: {e}")
            return False
```

### 🧪 Test Plan

1. **Unit Tests**
   - Test `read_config()` - valid/invalid config files
   - Test `run_dist_upgrade()` - successful/failed upgrade
   - Test `upgrade_package()` - with/without version
   - Test `backup_database()` - successful/failed backup
   - Test `run_migration()` - successful/failed migration

2. **Integration Tests**
   - Test `run_upgrade()` - full upgrade flow
   - Test migration with backup
   - Test rollback on migration failure

### 📦 Zavisnosti

```python
# requirements.txt
# No additional dependencies - uses standard library
```

### 🔧 System Dependencies

```bash
# Debian/Ubuntu
apt-get install -y postgresql-client  # For pg_dump
```

---

## 3. Authentication CLI Module (`app/backend/system/auth.py`)

### 📋 Pregled

Modul za CLI authentication - interakcija sa API-jem za dobijanje JWT tokena.

### 🎯 Funkcionalnosti

1. **Interactive Authentication**
   - Prompt za username i password
   - Secure password input (ne prikazuje password)

2. **API Authentication**
   - HTTP POST request na `/api/users/authenticate`
   - JSON request/response handling
   - Error handling

3. **Token Management**
   - JWT token extraction iz response-a
   - Token storage (fajl ili environment variable)
   - Token loading

### 📐 API Specifikacija

```python
from app.backend.system.auth import AuthCLI

class AuthCLI:
    """Authentication CLI manager"""
    
    def authenticate(
        self,
        username: str,
        password: str,
        api_url: str = "https://localhost/api/users/authenticate"
    ) -> Optional[str]:
        """
        Authenticate user and get JWT token
        
        Args:
            username: Username
            password: Password
            api_url: API endpoint URL
            
        Returns:
            JWT token string or None if failed
        """
        pass
    
    def prompt_credentials(self) -> tuple[str, str]:
        """
        Prompt user for credentials interactively
        
        Returns:
            Tuple of (username, password)
        """
        pass
    
    def save_token(self, token: str, token_path: Optional[str] = None) -> bool:
        """
        Save JWT token to file
        
        Args:
            token: JWT token string
            token_path: Optional token file path
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def load_token(self, token_path: Optional[str] = None) -> Optional[str]:
        """
        Load JWT token from file
        
        Args:
            token_path: Optional token file path
            
        Returns:
            JWT token string or None if not found
        """
        pass
```

### 💻 Primer Implementacije

```python
# app/backend/system/auth.py

import json
import logging
import getpass
from pathlib import Path
from typing import Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class AuthCLI:
    """Authentication CLI manager"""
    
    def __init__(self):
        self.default_api_url = "https://localhost/api/users/authenticate"
        self.default_token_path = Path.home() / ".ggnet2" / "token"
        self.timeout = 5
    
    def authenticate(
        self,
        username: str,
        password: str,
        api_url: Optional[str] = None
    ) -> Optional[str]:
        """Authenticate user and get JWT token"""
        if not api_url:
            api_url = self.default_api_url
        
        try:
            logger.info(f"Authenticating user: {username}")
            
            # Create session with retry strategy
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            # Make authentication request
            response = session.post(
                api_url,
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"},
                verify=False,  # Self-signed certificate
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    token = data.get("token") or data.get("access_token")
                    
                    if token:
                        logger.info("Authentication successful")
                        return token
                    else:
                        logger.error("Token not found in response")
                        return None
                except json.JSONDecodeError:
                    logger.error("Invalid JSON response")
                    return None
            else:
                try:
                    error_data = response.json()
                    logger.error(f"Authentication failed: {error_data}")
                except json.JSONDecodeError:
                    logger.error(f"Authentication failed: {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to authentication endpoint")
            return None
        except requests.exceptions.Timeout:
            logger.error("Authentication request timeout")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return None
    
    def prompt_credentials(self) -> Tuple[str, str]:
        """Prompt user for credentials interactively"""
        print("Please enter your ggNET2 credentials.")
        print("Note: Password will not be visible while typing.")
        print()
        
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        
        return username, password
    
    def save_token(self, token: str, token_path: Optional[str] = None) -> bool:
        """Save JWT token to file"""
        try:
            if token_path:
                token_file = Path(token_path)
            else:
                token_file = self.default_token_path
            
            # Create directory if needed
            token_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save token
            token_file.write_text(token)
            
            # Set permissions (readable only by owner)
            token_file.chmod(0o600)
            
            logger.info(f"Token saved to {token_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving token: {e}")
            return False
    
    def load_token(self, token_path: Optional[str] = None) -> Optional[str]:
        """Load JWT token from file"""
        try:
            if token_path:
                token_file = Path(token_path)
            else:
                token_file = self.default_token_path
            
            if not token_file.exists():
                return None
            
            token = token_file.read_text().strip()
            return token if token else None
        except Exception as e:
            logger.error(f"Error loading token: {e}")
            return None
```

### 🧪 Test Plan

1. **Unit Tests**
   - Test `authenticate()` - successful/failed authentication
   - Test `prompt_credentials()` - input handling
   - Test `save_token()` - token file creation
   - Test `load_token()` - token file reading

2. **Integration Tests**
   - Test full authentication flow
   - Test token persistence

### 📦 Zavisnosti

```python
# requirements.txt
requests>=2.31.0
urllib3>=2.0.0
```

---

## 4. dnsmasq Manager Module (`app/backend/network/dnsmasq_manager.py`)

### 📋 Pregled

Modul za dnsmasq konfiguraciju - generisanje PXE/iPXE boot konfiguracije za dnsmasq DHCP server.

### 🎯 Funkcionalnosti

1. **Generate PXE Configuration**
   - Generisanje `pxe.conf` fajla iz template-a
   - Zamena placeholder-a (SERVER_IP, NBP verzije)
   - Podrška za različite NBP verzije (latest, 202006, 202102)

2. **Update dnsmasq Configuration**
   - Kopiranje generisanog config-a u `/etc/dnsmasq.d/pxe.conf`
   - Restart dnsmasq servisa

3. **NBP Version Management**
   - Lista dostupnih NBP verzija
   - Postavljanje NBP verzije
   - Čitanje trenutne NBP verzije

### 📐 API Specifikacija

```python
from app.backend.network.dnsmasq_manager import DNSMasqManager

class DNSMasqManager:
    """dnsmasq configuration manager"""
    
    def generate_pxe_config(
        self,
        server_ip: str,
        nbp_version: str = "latest"
    ) -> str:
        """
        Generate PXE configuration from template
        
        Args:
            server_ip: Server IP address
            nbp_version: NBP version (latest, 202006, 202102)
            
        Returns:
            Generated configuration as string
        """
        pass
    
    def update_dnsmasq_config(
        self,
        server_ip: str,
        nbp_version: str = "latest"
    ) -> bool:
        """
        Update dnsmasq configuration
        
        Args:
            server_ip: Server IP address
            nbp_version: NBP version
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def list_nbp_versions(self) -> List[str]:
        """
        List available NBP versions
        
        Returns:
            List of NBP version strings
        """
        pass
    
    def get_current_nbp(self) -> str:
        """
        Get current NBP version
        
        Returns:
            Current NBP version string
        """
        pass
    
    def set_nbp_version(self, version: str) -> bool:
        """
        Set NBP version
        
        Args:
            version: NBP version to set
            
        Returns:
            True if successful, False otherwise
        """
        pass
```

### 💻 Primer Implementacije

```python
# app/backend/network/dnsmasq_manager.py

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class DNSMasqManager:
    """dnsmasq configuration manager"""
    
    def __init__(self):
        self.template_path = Path("/etc/ggnet2/templates/dnsmasq/pxe.conf")
        self.config_path = Path("/etc/dnsmasq.d/pxe.conf")
        self.nbp_config_path = Path("/etc/ggnet2/nbps")
        self.target_ip_path = Path("/etc/ggnet2/target-ip")
    
    def _get_nbp_files(self, version: str) -> tuple[str, str]:
        """Get NBP file names for version"""
        nbp_map = {
            "latest": ("undionly.kpxe", "ipxe.efi"),
            "202006": ("undionly_202006.kpxe", "ipxe_202006.efi"),
            "202102": ("undionly_202102.kpxe", "ipxe_202102.efi"),
        }
        return nbp_map.get(version, nbp_map["latest"])
    
    def generate_pxe_config(
        self,
        server_ip: str,
        nbp_version: str = "latest"
    ) -> str:
        """Generate PXE configuration from template"""
        try:
            # Load template
            if not self.template_path.exists():
                logger.error(f"Template not found: {self.template_path}")
                raise FileNotFoundError(f"Template not found: {self.template_path}")
            
            template_content = self.template_path.read_text()
            
            # Get NBP files
            legacy_nbp, uefi_nbp = self._get_nbp_files(nbp_version)
            
            # Replace placeholders
            config = template_content.replace("SERVER_IP", server_ip)
            config = config.replace("LEGACY_NBP", legacy_nbp)
            config = config.replace("UEFI_NBP", uefi_nbp)
            
            return config
        except Exception as e:
            logger.error(f"Error generating PXE config: {e}")
            raise
    
    def update_dnsmasq_config(
        self,
        server_ip: str,
        nbp_version: str = "latest"
    ) -> bool:
        """Update dnsmasq configuration"""
        try:
            # Generate config
            config_content = self.generate_pxe_config(server_ip, nbp_version)
            
            # Write config
            self.config_path.write_text(config_content)
            
            # Save target IP
            self.target_ip_path.parent.mkdir(parents=True, exist_ok=True)
            self.target_ip_path.write_text(server_ip)
            
            # Save NBP version
            if nbp_version == "latest":
                if self.nbp_config_path.exists():
                    self.nbp_config_path.unlink()
            else:
                legacy_nbp, uefi_nbp = self._get_nbp_files(nbp_version)
                version_map = {
                    "202006": "v0",
                    "202102": "v1",
                }
                version_code = version_map.get(nbp_version, "v0")
                self.nbp_config_path.write_text(
                    f"{version_code} {legacy_nbp} {uefi_nbp}"
                )
            
            # Restart dnsmasq
            result = subprocess.run(
                ["systemctl", "restart", "dnsmasq"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("dnsmasq configuration updated successfully")
                return True
            else:
                logger.error(f"Failed to restart dnsmasq: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error updating dnsmasq config: {e}")
            return False
    
    def list_nbp_versions(self) -> List[str]:
        """List available NBP versions"""
        return ["latest", "202102", "202006"]
    
    def get_current_nbp(self) -> str:
        """Get current NBP version"""
        try:
            if not self.nbp_config_path.exists():
                return "latest"
            
            content = self.nbp_config_path.read_text().strip()
            parts = content.split()
            
            if len(parts) >= 3:
                version_map = {
                    "v0": "202006",
                    "v1": "202102",
                }
                return version_map.get(parts[0], "latest")
            else:
                return "latest"
        except Exception as e:
            logger.error(f"Error getting current NBP: {e}")
            return "latest"
    
    def set_nbp_version(self, version: str) -> bool:
        """Set NBP version"""
        try:
            if version not in self.list_nbp_versions():
                logger.error(f"Invalid NBP version: {version}")
                return False
            
            # Get target IP
            if self.target_ip_path.exists():
                server_ip = self.target_ip_path.read_text().strip()
            else:
                logger.error("Target IP not configured")
                return False
            
            return self.update_dnsmasq_config(server_ip, version)
        except Exception as e:
            logger.error(f"Error setting NBP version: {e}")
            return False
```

### 🧪 Test Plan

1. **Unit Tests**
   - Test `generate_pxe_config()` - template replacement
   - Test `update_dnsmasq_config()` - config file creation
   - Test `get_current_nbp()` - version reading
   - Test `set_nbp_version()` - version setting

2. **Integration Tests**
   - Test dnsmasq service restart
   - Test PXE boot functionality

### 📦 Zavisnosti

```python
# requirements.txt
# No additional dependencies - uses standard library
```

### 🔧 System Dependencies

```bash
# Debian/Ubuntu
apt-get install -y dnsmasq
```

### 📄 Template Fajl

**`scripts/templates/dnsmasq/pxe.conf`:**
```conf
# This file has been generated by "ggnet2-linux-configurator" tool

# Don't function as a DNS server:
port=0

# Log lots of extra information about DHCP transactions.
log-dhcp

# Set the root directory for files available via FTP.
enable-tftp
tftp-root=/var/lib/tftp

# The boot filename, Server name, Server Ip Address
dhcp-boot=LEGACY_NBP,,SERVER_IP

# Disable re-use of the DHCP servername and filename fields as extra
# option space. That's to avoid confusing some old or broken DHCP clients.
dhcp-no-override

# inspect the vendor class string and match the text to set the tag
dhcp-vendorclass=BIOS,PXEClient:Arch:00000
dhcp-vendorclass=UEFI32,PXEClient:Arch:00006
dhcp-vendorclass=UEFI,PXEClient:Arch:00007
dhcp-vendorclass=UEFI64,PXEClient:Arch:00009

# Set the boot file name based on the matching tag from the vendor class (above)
dhcp-boot=net:UEFI32,i386-efi/UEFI_NBP,,SERVER_IP
dhcp-boot=net:UEFI,UEFI_NBP,,SERVER_IP
dhcp-boot=net:UEFI64,UEFI_NBP,,SERVER_IP

dhcp-match=ipxe,175
dhcp-boot=net:ipxe,http://SERVER_IP/boot/script?mac=${netX/mac}&ip=${netX/ip}&if=${ifname},,SERVER_IP

# PXE menu.  The first part is the text displayed to the user.  The second is the timeout, in seconds.
pxe-prompt="Booting ggNET2 Client", 1

# The known types are x86PC, PC98, IA64_EFI, Alpha, Arc_x86,
# Intel_Lean_Client, IA32_EFI, BC_EFI, Xscale_EFI and X86-64_EFI
# This option is first and will be the default if there is no input from the user.
pxe-service=net:ipxe,X86PC, "Boot to ggNET2", http://SERVER_IP/boot/script?mac=${netX/mac}&ip=${netX/ip}&if=${ifname}
pxe-service=net:ipxe,X86-64_EFI, "Boot to ggNET2 UEFI", http://SERVER_IP/boot/script?mac=${netX/mac}&ip=${netX/ip}&if=${ifname}
pxe-service=net:ipxe,BC_EFI, "Boot to ggNET2 UEFI PXE-BC", http://SERVER_IP/boot/script?mac=${netX/mac}&ip=${netX/ip}&if=${ifname}
pxe-service=X86PC, "Boot to ggNET2", LEGACY_NBP
pxe-service=X86-64_EFI, "Boot to ggNET2 UEFI", UEFI_NBP
pxe-service=BC_EFI, "Boot to ggNET2 UEFI PXE-BC", UEFI_NBP

dhcp-range=SERVER_IP,proxy
```

---

## 5. iSCSI Target Manager Module (`app/backend/network/iscsi_manager.py`)

### 📋 Pregled

Modul za iSCSI target management - kreiranje i brisanje iSCSI target-a za machine boot.

### 🎯 Funkcionalnosti

1. **Create iSCSI Target**
   - Kreiranje BlockStorageObject iz ZFS zvol-a
   - Kreiranje iSCSI Target sa TPG
   - Kreiranje NetworkPortal
   - Kreiranje LUN i NodeACL
   - Mapiranje LUN-a na initiator

2. **Delete iSCSI Target**
   - Brisanje iSCSI Target-a
   - Brisanje svih LUN-ova
   - Brisanje BlockStorageObject
   - Error handling za broken links

3. **List Targets**
   - Lista svih iSCSI target-a
   - Informacije o target-ima

### 📐 API Specifikacija

```python
from app.backend.network.iscsi_manager import ISCSIManager

class ISCSIManager:
    """iSCSI target management"""
    
    def create_target(
        self,
        device_name: str,
        device_path: str,
        target_iqn: str,
        initiator_iqn: str
    ) -> bool:
        """
        Create iSCSI target
        
        Args:
            device_name: Device name (e.g., "pc-100-disk-0")
            device_path: ZFS zvol path (e.g., "/dev/zvol/pool0/ggnet2/clients/pc-100-disk-0")
            target_iqn: Target IQN (e.g., "iqn.2019-08.com.ggnet2.ggnet2-1:pc-100-disk-0")
            initiator_iqn: Initiator IQN (e.g., "iqn.2019-08.com.ggnet2:pc-100")
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def delete_target(
        self,
        target_iqn: str,
        device_name: Optional[str] = None
    ) -> bool:
        """
        Delete iSCSI target
        
        Args:
            target_iqn: Target IQN to delete
            device_name: Optional device name for cleanup
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def list_targets(self) -> List[Dict[str, Any]]:
        """
        List all iSCSI targets
        
        Returns:
            List of target dictionaries
        """
        pass
    
    def target_exists(self, target_iqn: str) -> bool:
        """
        Check if target exists
        
        Args:
            target_iqn: Target IQN
            
        Returns:
            True if exists, False otherwise
        """
        pass
```

### 💻 Primer Implementacije

```python
# app/backend/network/iscsi_manager.py

import logging
from typing import List, Dict, Any, Optional
from rtslib_fb.root import RTSRoot
from rtslib_fb import (
    BlockStorageObject,
    FabricModule,
    Target,
    TPG,
    NetworkPortal,
    NodeACL,
    LUN,
    MappedLUN,
    RTSLibNotInCFS,
    RTSLibBrokenLink
)

logger = logging.getLogger(__name__)


class ISCSIManager:
    """iSCSI target management"""
    
    def __init__(self):
        self.rtsroot = RTSRoot()
        self.iscsi = FabricModule("iscsi")
    
    def create_target(
        self,
        device_name: str,
        device_path: str,
        target_iqn: str,
        initiator_iqn: str
    ) -> bool:
        """Create iSCSI target"""
        try:
            logger.info(
                f"Creating iSCSI target: {target_iqn} "
                f"for device: {device_path}"
            )
            
            # Create BlockStorageObject
            block = BlockStorageObject(device_name, dev=device_path)
            
            # Create Target
            target = Target(self.iscsi, target_iqn, "create")
            
            # Create TPG (Target Portal Group)
            tpg = TPG(target, 1)
            
            # Create NetworkPortal (0.0.0.0:3260)
            portal = NetworkPortal(tpg, "0.0.0.0", 3260)
            
            # Create LUN
            lun = LUN(tpg, 0, block)
            
            # Create NodeACL
            nodeacl = NodeACL(tpg, initiator_iqn)
            
            # Create MappedLUN
            mlun = MappedLUN(nodeacl, 0, lun)
            
            # Enable target and disable authentication
            tpg.enable = 1
            tpg.set_attribute("authentication", 0)
            
            logger.info(f"iSCSI target created successfully: {target_iqn}")
            return True
        except Exception as e:
            logger.error(f"Error creating iSCSI target: {e}")
            return False
    
    def delete_target(
        self,
        target_iqn: str,
        device_name: Optional[str] = None
    ) -> bool:
        """Delete iSCSI target"""
        try:
            logger.info(f"Deleting iSCSI target: {target_iqn}")
            
            target_exists = True
            try:
                target = Target(self.iscsi, target_iqn, "lookup")
            except RTSLibNotInCFS:
                target_exists = False
            
            if target_exists:
                tpg = TPG(target, 1)
                
                # Delete all LUNs
                for lun in tpg.luns:
                    try:
                        lun.storage_object.delete()
                    except RTSLibBrokenLink:
                        # Handle broken links gracefully
                        logger.warning(f"Broken LUN link, skipping: {lun}")
                        pass
                
                # Delete target
                target.delete()
                
                logger.info(f"iSCSI target deleted successfully: {target_iqn}")
                return True
            else:
                logger.warning(f"Target does not exist: {target_iqn}")
                
                # Try to delete BlockStorageObject if device_name provided
                if device_name:
                    try:
                        block = BlockStorageObject(device_name)
                        block.delete()
                        logger.info(f"BlockStorageObject deleted: {device_name}")
                    except RTSLibNotInCFS:
                        pass
                
                return False
        except Exception as e:
            logger.error(f"Error deleting iSCSI target: {e}")
            return False
    
    def list_targets(self) -> List[Dict[str, Any]]:
        """List all iSCSI targets"""
        try:
            targets = []
            
            for target in self.iscsi.targets:
                target_info = {
                    "iqn": target.wwn,
                    "tpg_count": len(target.tpgs),
                }
                
                # Get LUN information
                if target.tpgs:
                    tpg = target.tpgs[0]
                    target_info["luns"] = [
                        {
                            "lun": lun.lun,
                            "storage_object": lun.storage_object.name,
                        }
                        for lun in tpg.luns
                    ]
                
                targets.append(target_info)
            
            return targets
        except Exception as e:
            logger.error(f"Error listing targets: {e}")
            return []
    
    def target_exists(self, target_iqn: str) -> bool:
        """Check if target exists"""
        try:
            target = Target(self.iscsi, target_iqn, "lookup")
            return True
        except RTSLibNotInCFS:
            return False
```

### 🧪 Test Plan

1. **Unit Tests**
   - Test `create_target()` - successful/failed creation
   - Test `delete_target()` - successful/failed deletion
   - Test `list_targets()` - target listing
   - Test `target_exists()` - existence check

2. **Integration Tests**
   - Test iSCSI target creation with ZFS zvol
   - Test machine boot with iSCSI target
   - Test target cleanup

### 📦 Zavisnosti

```python
# requirements.txt
rtslib-fb>=2.1.0
```

### 🔧 System Dependencies

```bash
# Debian/Ubuntu
apt-get install -y targetcli-fb
```

---

## 6. CLI Utility Skripte Plan

### 📋 Pregled

CLI utility skripte su bash/Python wrapperi koji pozivaju Python module i pružaju command-line interfejs.

### 🎯 Struktura

```
scripts/ggnet2_linux_configurator/
├── ggnet2-auth                 # Authentication CLI
├── ggnet2-create-bridge        # Bridge creation wrapper
├── ggnet2-create-target       # iSCSI target creation wrapper
├── ggnet2-delete-target       # iSCSI target deletion wrapper
├── ggnet2-img                 # Image management CLI
├── ggnet2-preflight           # Preflight checks CLI
├── ggnet2-upgrade             # Upgrade automation CLI
└── ggnet2-linux-configurator  # Main configurator tool
```

### 📐 Specifikacije

#### `ggnet2-auth`

```bash
#!/bin/bash
# Wrapper za app.backend.system.auth.AuthCLI

python3 -m app.backend.system.auth "$@"
```

#### `ggnet2-preflight`

```bash
#!/bin/bash
# Wrapper za app.backend.system.preflight.PreflightChecker

case "$1" in
    "start")
        python3 -c "
from app.backend.system.preflight import PreflightChecker
checker = PreflightChecker()
results = checker.run_all_checks()
if any(r.has_failure() for r in results):
    checker.setup_nginx_preflight()
    checker.fix_all_failures(results)
checker.run_preflight_complete()
"
        ;;
    "cleanup")
        python3 -c "
from app.backend.system.preflight import PreflightChecker
checker = PreflightChecker()
checker.cleanup_nginx_preflight()
"
        ;;
    *)
        echo "Usage: ggnet2-preflight {start|cleanup}"
        exit 1
        ;;
esac
```

#### `ggnet2-upgrade`

```bash
#!/bin/bash
# Wrapper za app.backend.system.upgrade.UpgradeManager

python3 -c "
from app.backend.system.upgrade import UpgradeManager
manager = UpgradeManager()
manager.run_upgrade()
"
```

#### `ggnet2-create-bridge`

```bash
#!/bin/bash
# Wrapper za app.backend.network.network_utils.create_bridge

if [ "$#" -ne 2 ]; then
    echo "Usage: ggnet2-create-bridge <nic_name> <bridge_name>"
    exit 1
fi

python3 -c "
from app.backend.network.network_utils import NetworkUtils
utils = NetworkUtils()
utils.create_bridge('$2', '$1')
"
```

#### `ggnet2-create-target`

```bash
#!/bin/bash
# Wrapper za app.backend.network.iscsi_manager.create_target

if [ "$#" -ne 4 ]; then
    echo "Usage: ggnet2-create-target <device_name> <device_path> <target_iqn> <initiator_iqn>"
    exit 1
fi

python3 -c "
from app.backend.network.iscsi_manager import ISCSIManager
manager = ISCSIManager()
manager.create_target('$1', '$2', '$3', '$4')
"
```

#### `ggnet2-delete-target`

```bash
#!/bin/bash
# Wrapper za app.backend.network.iscsi_manager.delete_target

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: ggnet2-delete-target <target_iqn> [device_name]"
    exit 1
fi

python3 -c "
from app.backend.network.iscsi_manager import ISCSIManager
manager = ISCSIManager()
manager.delete_target('$1', '${2:-}')
"
```

#### `ggnet2-img`

```bash
#!/bin/bash
# Wrapper za app.backend.images.image_manager operacije

# Kompleksniji wrapper koji poziva različite funkcije
# zavisno od komande (get_sendsize, list_snapshots, send, receive, export)
```

#### `ggnet2-linux-configurator`

```bash
#!/bin/bash
# Main configurator tool - kompleksniji interaktivni tool
# Koristi dialog za UI ili Python CLI
```

---

## 7. Systemd Service Fajlovi Plan

### 📋 Pregled

Systemd service fajlovi za automatsko pokretanje preflight checks i upgrade servisa.

### 📐 Specifikacije

#### `scripts/systemd/ggnet2-preflight.service`

```ini
[Unit]
Description=Run ggNET2 preflight checks
Wants=network-online.target
After=network-online.target
After=zfs.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ggnet2-preflight start
TimeoutStartSec=0
SyslogIdentifier=ggnet2-preflight
ExecStopPost=-/usr/local/bin/ggnet2-preflight cleanup

[Install]
WantedBy=multi-user.target
```

#### `scripts/systemd/ggnet2-upgrade.service`

```ini
[Unit]
Description=ggNET2 Upgrade Service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ggnet2-upgrade
SyslogIdentifier=ggnet2-upgrade

[Install]
WantedBy=multi-user.target
```

---

## ✅ Implementacioni Redosled

### Faza 1: Backend Moduli (Prioritet 1)
1. ✅ `preflight.py` - Preflight checks
2. ✅ `upgrade.py` - Upgrade automation
3. ✅ `auth.py` - Authentication CLI
4. ✅ `dnsmasq_manager.py` - dnsmasq konfiguracija
5. ✅ `iscsi_manager.py` - iSCSI target management

### Faza 2: CLI Utility Skripte (Prioritet 2)
1. ✅ `ggnet2-preflight` - Preflight CLI
2. ✅ `ggnet2-upgrade` - Upgrade CLI
3. ✅ `ggnet2-auth` - Auth CLI
4. ✅ `ggnet2-create-bridge` - Bridge wrapper
5. ✅ `ggnet2-create-target` - iSCSI create wrapper
6. ✅ `ggnet2-delete-target` - iSCSI delete wrapper
7. ✅ `ggnet2-img` - Image CLI
8. ✅ `ggnet2-linux-configurator` - Main configurator

### Faza 3: Systemd Services (Prioritet 2)
1. ✅ `ggnet2-preflight.service`
2. ✅ `ggnet2-upgrade.service`
3. ✅ Ažurirati `setup_systemd.sh`

### Faza 4: Template-i i Konfiguracije (Prioritet 1)
1. ✅ `scripts/templates/dnsmasq/pxe.conf`
2. ✅ iPXE boot fajlovi distribucija

---

*Detaljni planovi za sve module su kompletan*


