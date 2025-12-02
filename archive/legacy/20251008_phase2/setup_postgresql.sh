#!/bin/bash
# Setup PostgreSQL for GGnet

echo "=== POSTGRESQL SETUP FOR GGNET ==="

# Database configuration
DB_USER="ggnet"
DB_PASS="ggnet_password"
DB_NAME="ggnet"

# Install PostgreSQL if not installed
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    
    # Detect OS and install
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL/Rocky
        sudo yum install -y postgresql-server postgresql-contrib
        sudo postgresql-setup --initdb
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        sudo pacman -S postgresql
        sudo -u postgres initdb -D /var/lib/postgres/data
    else
        echo "Unsupported OS. Please install PostgreSQL manually."
        exit 1
    fi
fi

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check if PostgreSQL is running
if ! sudo systemctl is-active --quiet postgresql; then
    echo "Failed to start PostgreSQL service"
    exit 1
fi

echo "PostgreSQL service is running"

# Create database user
echo "Creating database user: $DB_USER"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "User $DB_USER already exists"

# Create database
echo "Creating database: $DB_NAME"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || echo "Database $DB_NAME already exists"

# Grant privileges
echo "Granting privileges..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || echo "Privileges already granted"

# Test connection
echo "Testing database connection..."
if PGPASSWORD="$DB_PASS" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "Database connection successful!"
else
    echo "Database connection failed!"
    exit 1
fi

# Install Python PostgreSQL driver
echo "Installing Python PostgreSQL driver..."
pip3 install psycopg2-binary asyncpg

echo ""
echo "=== POSTGRESQL SETUP COMPLETED ==="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Password: $DB_PASS"
echo "Host: localhost"
echo "Port: 5432"
echo ""
echo "Now run: python3 setup_database_postgresql.py"
