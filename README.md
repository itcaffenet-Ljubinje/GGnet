# GGnet - Diskless Server Management System

[![CI/CD Pipeline](https://github.com/your-org/ggnet/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/ggnet/actions/workflows/ci.yml)
[![Code Coverage](https://codecov.io/gh/your-org/ggnet/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/ggnet)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, scalable diskless server management system built with FastAPI and React. GGnet provides comprehensive management of diskless workstations, iSCSI targets, and network boot infrastructure.

## 🚀 Features

### Core Functionality
- **Diskless Workstation Management**: Complete lifecycle management of diskless machines
- **iSCSI Target Management**: Automated creation and management of iSCSI targets
- **Image Management**: Upload, convert, and manage disk images (VHDX, RAW, QCOW2)
- **Session Orchestration**: Automated session management with PXE/iPXE boot support
- **Real-time Monitoring**: Live monitoring of sessions, targets, and system health

### Technical Features
- **Modern Architecture**: FastAPI backend with React TypeScript frontend
- **Real-time Updates**: WebSocket-based live monitoring and notifications
- **Background Processing**: Asynchronous image conversion and processing
- **Comprehensive Testing**: Unit, integration, and end-to-end tests
- **Production Ready**: Health monitoring, metrics, logging, and CI/CD

### Security & Compliance
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Role-based Access Control**: Granular permissions (Admin, Operator, Viewer)
- **Audit Logging**: Complete audit trail of all user activities
- **Security Scanning**: Automated vulnerability detection and dependency scanning

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (or SQLite for development)
- Redis 7+

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ggnet.git
   cd ggnet
   ```

2. **Start with Docker Compose**
   ```bash
   cd infra
   docker compose up -d --build
   ```

3. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **Default credentials**
   - Username: `admin`
   - Password: `admin123`

### Production Installation

1. **Run the installation script**
   ```bash
   sudo bash infra/install.sh
   ```

2. **Configure the system**
   ```bash
   # Edit configuration
   sudo nano /opt/ggnet/backend/.env
   
   # Start services
   sudo systemctl start ggnet-backend ggnet-worker
   sudo systemctl enable ggnet-backend ggnet-worker
   ```

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Infrastructure│
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (iSCSI/DHCP)  │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • REST API      │    │ • iSCSI Targets │
│ • Machine Mgmt  │    │ • WebSocket     │    │ • DHCP Server   │
│ • Image Upload  │    │ • Background    │    │ • TFTP Server   │
│ • Real-time UI  │    │   Workers       │    │ • PXE/iPXE      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Data Layer    │
                    │                 │
                    │ • PostgreSQL    │
                    │ • Redis Cache   │
                    │ • File Storage  │
                    └─────────────────┘
```

### Component Architecture

#### Backend (FastAPI)
- **Core API**: RESTful endpoints for all operations
- **WebSocket Manager**: Real-time communication
- **Background Workers**: Image conversion and processing
- **Authentication**: JWT-based security
- **Monitoring**: Health checks and metrics

#### Frontend (React)
- **Dashboard**: System overview and statistics
- **Machine Management**: CRUD operations for workstations
- **Image Management**: Upload and conversion tracking
- **Session Monitoring**: Real-time session status
- **Target Management**: iSCSI target configuration

#### Infrastructure
- **iSCSI Targets**: Automated target creation and management
- **Network Boot**: PXE/iPXE boot script generation
- **DHCP Integration**: Dynamic host configuration
- **TFTP Server**: Boot file serving

## 🔧 Installation

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores, 2.4 GHz
- **RAM**: 4 GB
- **Storage**: 50 GB free space
- **Network**: Gigabit Ethernet

#### Recommended Requirements
- **CPU**: 4+ cores, 3.0+ GHz
- **RAM**: 8+ GB
- **Storage**: 100+ GB SSD
- **Network**: 10 Gigabit Ethernet

### Supported Operating Systems
- **Ubuntu**: 20.04 LTS, 22.04 LTS
- **Debian**: 11 (Bullseye), 12 (Bookworm)
- **CentOS**: 8, 9 (with EPEL)
- **RHEL**: 8, 9 (with EPEL)

### Installation Methods

#### 1. Automated Installation (Recommended)
```bash
# Download and run the installation script
curl -fsSL https://raw.githubusercontent.com/your-org/ggnet/main/infra/install.sh | sudo bash

# Or with dry-run to preview changes
sudo bash infra/install.sh --dry-run
```

#### 2. Manual Installation
```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-venv python3-pip redis-server \
  qemu-utils targetcli-fb tftpd-hpa isc-dhcp-server nginx

# Create system user
sudo useradd -r -m -d /opt/ggnet -s /usr/sbin/nologin ggnet

# Setup application
sudo mkdir -p /opt/ggnet/{backend,venv}
sudo chown -R ggnet:ggnet /opt/ggnet

# Install Python dependencies
sudo -u ggnet python3 -m venv /opt/ggnet/venv
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r backend/requirements.txt
```

#### 3. Docker Installation
```bash
# Clone repository
git clone https://github.com/your-org/ggnet.git
cd ggnet

# Start with Docker Compose
cd infra
docker compose up -d --build
```

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration
```bash
# Database
DATABASE_URL=postgresql://ggnet:password@localhost:5432/ggnet

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# File Storage
UPLOAD_DIR=/var/lib/ggnet/uploads
IMAGES_DIR=/var/lib/ggnet/images
MAX_UPLOAD_SIZE=10737418240  # 10GB

# iSCSI Configuration
ISCSI_TARGET_PREFIX=iqn.2025.ggnet
ISCSI_PORTAL_IP=0.0.0.0
ISCSI_PORTAL_PORT=3260

# Network Boot
TFTP_ROOT=/var/lib/tftpboot
IPXE_SCRIPT_PATH=/var/lib/tftpboot/boot.ipxe
```

#### Frontend Configuration
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Application Settings
VITE_APP_NAME=GGnet
VITE_APP_VERSION=1.0.0
```

### Service Configuration

#### Systemd Services
```bash
# Backend service
sudo systemctl edit ggnet-backend

# Worker service
sudo systemctl edit ggnet-worker

# Enable services
sudo systemctl enable ggnet-backend ggnet-worker
```

#### Nginx Configuration
```bash
# Copy configuration
sudo cp infra/nginx/ggnet.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/ggnet.conf /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## 📖 Usage

### Getting Started

1. **Login to the system**
   - Navigate to the web interface
   - Use default credentials or create new users

2. **Add your first machine**
   - Go to Machines → Add Machine
   - Enter MAC address and IP address
   - Configure boot mode (BIOS/UEFI)

3. **Upload a disk image**
   - Go to Images → Upload Image
   - Select VHDX, RAW, or QCOW2 file
   - Wait for conversion to complete

4. **Create an iSCSI target**
   - Go to Targets → Create Target
   - Select machine and image
   - Configure target settings

5. **Start a session**
   - Go to Sessions → Start Session
   - Select target and session type
   - Monitor boot progress

### Common Workflows

#### Setting up a New Workstation
1. Add machine with MAC address
2. Upload or select disk image
3. Create iSCSI target
4. Configure DHCP reservation
5. Start session and boot workstation

#### Managing Disk Images
1. Upload new image files
2. Monitor conversion progress
3. Test images with virtual machines
4. Deploy to production targets

#### Monitoring System Health
1. Check dashboard for overview
2. Review active sessions
3. Monitor system resources
4. Check logs for issues

## 📚 API Documentation

### Authentication
All API endpoints require authentication except health checks and login.

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/machines
```

### Core Endpoints

#### Machines
- `GET /machines` - List all machines
- `POST /machines` - Create new machine
- `GET /machines/{id}` - Get machine details
- `PUT /machines/{id}` - Update machine
- `DELETE /machines/{id}` - Delete machine

#### Images
- `GET /images` - List all images
- `POST /images/upload` - Upload new image
- `GET /images/{id}` - Get image details
- `POST /images/{id}/convert` - Trigger conversion
- `DELETE /images/{id}` - Delete image

#### Targets
- `GET /api/v1/targets` - List all targets
- `POST /api/v1/targets` - Create new target
- `GET /api/v1/targets/{id}` - Get target details
- `DELETE /api/v1/targets/{id}` - Delete target

#### Sessions
- `GET /sessions` - List all sessions
- `POST /sessions` - Start new session
- `POST /sessions/{id}/stop` - Stop session
- `GET /sessions/stats` - Get session statistics

### WebSocket API
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws?token=<jwt_token>');

// Listen for updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

## 🛠️ Development

### Development Setup

1. **Clone and setup**
   ```bash
   git clone https://github.com/your-org/ggnet.git
   cd ggnet
   ```

2. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Start development servers**
   ```bash
   # Backend (terminal 1)
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Frontend (terminal 2)
   cd frontend
   npm run dev
   ```

### Running Tests

#### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

#### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

#### Integration Tests
```bash
cd infra
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### Code Quality

#### Linting and Formatting
```bash
# Backend
cd backend
black app/
isort app/
flake8 app/
mypy app/

# Frontend
cd frontend
npm run lint
npm run format
```

#### Security Scanning
```bash
cd backend
bandit -r app/
safety check
```

## 🚀 Deployment

### Production Deployment

#### 1. Prepare the Server
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo bash infra/install.sh
```

#### 2. Configure Services
```bash
# Edit configuration
sudo nano /opt/ggnet/backend/.env

# Copy systemd services
sudo cp infra/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Configure nginx
sudo cp infra/nginx/ggnet.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/ggnet.conf /etc/nginx/sites-enabled/
```

#### 3. Deploy Application
```bash
# Copy application files
sudo cp -r backend/* /opt/ggnet/backend/
sudo chown -R ggnet:ggnet /opt/ggnet

# Install dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r /opt/ggnet/backend/requirements.txt

# Run database migrations
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head
```

#### 4. Start Services
```bash
# Start and enable services
sudo systemctl start ggnet-backend ggnet-worker
sudo systemctl enable ggnet-backend ggnet-worker

# Check status
sudo systemctl status ggnet-backend ggnet-worker
```

### Docker Deployment

#### Single Server
```bash
cd infra
docker compose up -d --build
```

#### Multi-Server (Kubernetes)
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### High Availability Setup

#### Load Balancer Configuration
```nginx
upstream ggnet_backend {
    server 192.168.1.10:8000;
    server 192.168.1.11:8000;
    server 192.168.1.12:8000;
}

server {
    listen 80;
    server_name ggnet.example.com;
    
    location / {
        proxy_pass http://ggnet_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Database Clustering
```bash
# Setup PostgreSQL cluster
sudo apt install postgresql-15 postgresql-15-repmgr

# Configure replication
sudo nano /etc/postgresql/15/main/postgresql.conf
```

## 📊 Monitoring

### Health Monitoring

#### Health Check Endpoints
- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed component status
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe

#### Example Health Check
```bash
curl http://localhost:8000/health/detailed
```

### Metrics Collection

#### Prometheus Metrics
- `GET /metrics/` - Prometheus-compatible metrics

#### Key Metrics
- `ggnet_http_requests_total` - HTTP request count
- `ggnet_active_sessions` - Active sessions
- `ggnet_system_cpu_percent` - CPU usage
- `ggnet_system_memory_percent` - Memory usage

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "GGnet Monitoring",
    "panels": [
      {
        "title": "Active Sessions",
        "targets": [
          {
            "expr": "ggnet_active_sessions"
          }
        ]
      }
    ]
  }
}
```

### Logging

#### Log Files
- `/opt/ggnet/logs/app.log` - Application logs
- `/opt/ggnet/logs/error.log` - Error logs
- `/opt/ggnet/logs/audit.log` - Audit logs
- `/opt/ggnet/logs/security.log` - Security logs

#### Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/ggnet
```

### Alerting

#### Prometheus Alert Rules
```yaml
groups:
- name: ggnet
  rules:
  - alert: HighCPUUsage
    expr: ggnet_system_cpu_percent > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status ggnet-backend

# Check logs
sudo journalctl -u ggnet-backend -f

# Check configuration
sudo -u ggnet /opt/ggnet/venv/bin/python -c "from app.core.config import get_settings; print(get_settings())"
```

#### 2. Database Connection Issues
```bash
# Test database connection
sudo -u ggnet /opt/ggnet/venv/bin/python -c "
from app.core.database import get_db
import asyncio
async def test():
    async with get_db() as db:
        result = await db.execute('SELECT 1')
        print('Database OK:', result.scalar())
asyncio.run(test())
"
```

#### 3. Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping

# Check Redis logs
sudo journalctl -u redis-server -f
```

#### 4. Image Upload Issues
```bash
# Check disk space
df -h

# Check file permissions
ls -la /var/lib/ggnet/images/

# Check upload limits
grep MAX_UPLOAD_SIZE /opt/ggnet/backend/.env
```

#### 5. iSCSI Target Issues
```bash
# Check targetcli
sudo targetcli ls

# Check iSCSI service
sudo systemctl status target

# Check network connectivity
telnet <server_ip> 3260
```

### Debug Commands

#### Backend Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
sudo systemctl restart ggnet-backend

# Check health endpoints
curl -v http://localhost:8000/health/detailed

# Check metrics
curl http://localhost:8000/metrics/
```

#### Frontend Debugging
```bash
# Check browser console
# Open Developer Tools (F12)

# Check network requests
# Go to Network tab in Developer Tools

# Check WebSocket connection
# Go to Console and run:
# new WebSocket('ws://localhost:8000/ws?token=<token>')
```

### Performance Tuning

#### Database Optimization
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Optimize indexes
CREATE INDEX CONCURRENTLY idx_sessions_status 
ON sessions(status);
```

#### Redis Optimization
```bash
# Check Redis memory usage
redis-cli info memory

# Optimize Redis configuration
sudo nano /etc/redis/redis.conf
```

#### System Optimization
```bash
# Check system resources
htop
iostat -x 1
netstat -i

# Optimize file system
sudo tune2fs -o journal_data_writeback /dev/sda1
```

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   # Backend tests
   cd backend && pytest tests/
   
   # Frontend tests
   cd frontend && npm test
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Create a Pull Request**

### Code Standards

#### Python (Backend)
- Follow PEP 8 style guide
- Use type hints
- Write comprehensive tests
- Document all public functions

#### TypeScript (Frontend)
- Use strict TypeScript
- Follow React best practices
- Write component tests
- Use proper error handling

#### Git Commit Messages
- Use conventional commits format
- Be descriptive and concise
- Reference issues when applicable

### Testing Requirements

#### Backend Tests
- Unit tests for all functions
- Integration tests for API endpoints
- Test coverage > 80%

#### Frontend Tests
- Component tests for all components
- Integration tests for user flows
- Test coverage > 80%

### Documentation Requirements

- Update README for new features
- Document API changes
- Add examples for new functionality
- Update troubleshooting guide

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [React](https://reactjs.org/) - JavaScript library for building user interfaces
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [Redis](https://redis.io/) - In-memory data structure store
- [Docker](https://www.docker.com/) - Containerization platform

## 📞 Support

### Getting Help

- **Documentation**: Check this README and the docs/ directory
- **Issues**: Report bugs and request features on GitHub Issues
- **Discussions**: Join community discussions on GitHub Discussions
- **Email**: Contact the maintainers at support@ggnet.example.com

### Community

- **GitHub**: [https://github.com/your-org/ggnet](https://github.com/your-org/ggnet)
- **Discord**: [Join our Discord server](https://discord.gg/ggnet)
- **Twitter**: [@GGnetProject](https://twitter.com/GGnetProject)

---

**GGnet** - Modern diskless server management made simple.